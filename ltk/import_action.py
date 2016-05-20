from ltk.actions import *


class ImportAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def import_action(self, import_all, force, path, ids_to_import=None):
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
                ids_to_import = get_import_ids(import_doc_info)
        else:
            ids_to_import = [ids_to_import]
        for curr_id in ids_to_import:
            self.import_document(curr_id, tms_doc_info[curr_id], force, path)

    def import_check(self, force, path, document_id, title):
        if not path:
            path = self.path
        else:
            path = os.path.join(self.path, path.replace(self.path, ''))
        path_changed = False
        curr_entry = self.doc_manager.get_doc_by_prop('id', document_id)
        curr_path = os.path.join(self.path, curr_entry['file_name'])
        new_path = os.path.join(path, title)
        # print (curr_path, new_path)
        if os.path.normpath(curr_path) != os.path.normpath(new_path):
            path_changed = True
        if not force:
            confirmation_msg = 'Would you like to overwrite the existing document? [y/N]:'
            if path_changed:
                confirmation_msg = 'Would you like to overwrite the existing document ' \
                                   'and its current saved path? [y/N]:'
            confirm = 'none'
            while confirm not in ['y', 'yes', 'n', 'no', '']:
                confirm = raw_input(confirmation_msg).lower()
            if not confirm or confirm in ['n', 'no']:
                logger.info('Skipped importing "{0}"'.format(title))
                path_changed = False

        return path_changed

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
        if document_id in local_ids:
            changed_path = self.import_check(force, path, document_id, title)

        if changed_path:
            self.delete_local(title, document_id, 'Moved local file {0}'.format(title))

        with open(file_path, 'wb') as fh:
            for chunk in response.iter_content(1024):
                fh.write(chunk)

        relative_path = file_path.replace(self.path, '')
        if document_id not in local_ids:
            self._add_document(relative_path, title, document_id)
            self.doc_manager.update_document('locales', locale_info, document_id)
        else:
            # update the document's path
            self.doc_manager.update_document('file_name', relative_path, document_id)
