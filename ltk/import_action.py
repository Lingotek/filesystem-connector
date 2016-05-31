from ltk.actions import *


class ImportAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)


    def get_import_ids(self,info):
        mapper = choice_mapper(info)
        chosen_ids = []
        while not len(chosen_ids) > 0:
            choice = input('Documents to import: (Separate indices by comma) ')
            try:
                chosen_ids = [list(mapper[int(index)].keys())[0] for index in choice.split(',')]
            except ValueError:
                print ('Some unexpected, non-integer value was included')
        return chosen_ids

    def import_action(self, import_all, force, path, ids_to_import=None):
        path = self.norm_path(path)
        response = self.api.list_documents(self.project_id)
        tms_doc_info = {}
        if response.status_code == 200:
            tms_documents = response.json()['entities']
            for entity in tms_documents:
                doc_info = {'title': entity['properties']['title'], 'extension': entity['properties']['extension']}
                tms_doc_info[entity['properties']['id']] = doc_info
        elif response.status_code == 204:
            logger.error('No documents to import!')
            return
        else:
            raise_error(response.json(), 'Error finding current documents in Lingotek Cloud')

        if not ids_to_import:
            if import_all:
                ids_to_import = iter(tms_doc_info)
            else:
                import_doc_info = {}
                for k, v in tms_doc_info.items():
                    import_doc_info[k] = v['title']
                ids_to_import = self.get_import_ids(import_doc_info)
        else:
            ids_to_import = [ids_to_import]
        for curr_id in ids_to_import:
            self.import_document(curr_id, tms_doc_info[curr_id], force, path)

    def import_check(self, force, path, document_id, title):
        if not path:
            path = self.path
        else:
            path = os.path.join(self.path, path.replace(self.path, ''))
        path_changed = None
        curr_path = None
        write_file = True
        curr_entry = self.doc_manager.get_doc_by_prop('id', document_id)
        new_path = os.path.join(path, title)
        if curr_entry:
            curr_path = os.path.join(self.path, curr_entry['file_name'])
            # print (curr_path, new_path)
            if self.norm_path(curr_path) != self.norm_path(new_path):
                path_changed = curr_path
        if not force:
            if not curr_path and not os.path.exists(new_path):
                return 
            if path_changed and curr_path: # Confirm changing the file path saved in docs.json
                confirmation_msg = 'Would you like to change ' \
                                   'the current saved path of '+title+' from '+curr_path+' to '+new_path+'? [y/n]:'
                confirm = 'none'
                while confirm not in ['y', 'yes', 'n', 'no', '']:
                    confirm = input(confirmation_msg).lower()
                if not confirm or confirm in ['n', 'no']:
                    logger.info('Retaining old path "{0}"'.format(curr_path))
                    path_changed = None
                    new_path = curr_path
            # Confirm overwriting a local file
            if os.path.exists(new_path):
                confirmation_msg = 'Would you like to overwrite the existing document at '+new_path+'? [y/n]:'
                confirm = 'none'
                while confirm not in ['y', 'yes', 'n', 'no', '']:
                    confirm = input(confirmation_msg).lower()
                if not confirm or confirm in ['n', 'no']:
                    logger.info('Skipped importing "{0}"'.format(title))
                    write_file = False
        return path_changed, new_path, write_file

    def import_document(self, document_id, document_info, force, path):
        local_ids = self.doc_manager.get_doc_ids()
        response = self.api.document_content(document_id, None, None)
        title, extension = os.path.splitext(document_info['title'])
        if not extension:
            extension = document_info['extension']
            extension = '.' + extension
        if extension and extension != '.none':
            title += extension
        if path:
            file_path = os.path.join(self.path, path, title)
        else:
            file_path = os.path.join(self.path, title)
        # file_path = os.path.join(os.getcwd(), title)  # import to current working directory
        logger.info('Importing "{0}" to {1}..'.format(title, file_path))
        # use status action to get locale info for importing
        try:
            locale_map = self.import_locale_info(document_id)
            locale_info = list(iter(locale_map))
        except exceptions.RequestFailedError:
            locale_info = []

        changed_path = False
        changed_path, new_path, write_file = self.import_check(force, path, document_id, title)

        if write_file:

            if changed_path and os.path.exists(changed_path):
                self.delete_local(title, document_id, 'Moved local file {0} to {1}'.format(changed_path, new_path))

            with open(new_path, 'wb') as fh:
                for chunk in response.iter_content(1024):
                    fh.write(chunk)

        if document_id not in local_ids:
            self._add_document(new_path, title, document_id)
            self.doc_manager.update_document('locales', locale_info, document_id)
        elif changed_path:
            # update the document's path
            self.doc_manager.update_document('file_name', new_path, document_id)
