from ltk.actions import *


class ImportAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def import_action(self, import_all, force, path):
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

        if import_all:
            ids_to_import = tms_doc_info.iterkeys()
        else:
            import_doc_info = {}
            for k, v in tms_doc_info.iteritems():
                import_doc_info[k] = v['title']
            ids_to_import = get_import_ids(import_doc_info)
        for curr_id in ids_to_import:
            self.import_document(curr_id, tms_doc_info[curr_id], force, path)

    def import_check(self, force, path, document_id, title):
        # local_ids = self.doc_manager.get_doc_ids()
        # if document_id in local_ids:
        #     if path:
        #         curr_entry = self.doc_manager.get_doc_by_prop('id', document_id)
        #         curr_path = os.path.join(self.path, curr_entry['file_name'])
        #         confirmation_msg = 'Would you like to overwrite the existing document? [y/N]:'
        #         if os.path.normpath(curr_path) != os.path.normpath(path):
        #             confirmation_msg = 'Would you like to overwrite the existing document and ' \
        #                                'its current saved path? [y/N]:'
        #         confirm = 'none'
        #         while confirm not in ['y', 'yes', 'n', 'no', '']:
        #             confirm = raw_input(confirmation_msg).lower()
        #         if not confirm or confirm in ['n', 'no']:
        #             logger.info('Skipped importing "{0}"'.format(title))
        #             return False
        #     else:
        #         logger.error('This document already exists somewhere locally. \
        #         Use the -p option to import it to a specified path or -f to force an update')
        #         return False
        # return True
        # check if document id is in local ids
        # if it is, document already exists -- check the path associated with local id
        # check current given path
        # if same, prompt for overwrite
        # if not same, prompt for overwrite for both path and file
        # move the file to the new path
        # if not just write to new file?
        if not path:
            path = self.path
        else:
            path = os.path.join(self.path, path.replace(self.path, ''))
        path_changed = False
        curr_entry = self.doc_manager.get_doc_by_prop('id', document_id)
        curr_path = os.path.join(self.path, curr_entry['file_name'])
        new_path = os.path.join(path, title)
        print curr_path, new_path
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
            locale_info = list(locale_map.iterkeys())
        except exceptions.RequestFailedError:
            locale_info = []

        changed_path = False
        if document_id in local_ids:
            changed_path = self.import_check(force, path, document_id, title)

            # if not force:
            #     self.import_check(path, document_id, title)
            # if document_id in local_ids:
            #     confirm = 'none'
            #     while confirm not in ['y', 'yes', 'n', 'no', '']:
            #         confirm = raw_input('Would you like to overwrite the existing document? [y/N]:').lower()
            #     if not confirm or confirm in ['n', 'no']:
            #         logger.info('Skipped importing "{0}"'.format(title))
            #         return
            # else:
            #     if self.doc_manager.get_doc_by_prop('file_name', file_path.replace(self.path, '')):
            #         # change file_path
            #         file_path = self.get_new_name(title, os.getcwd())
            #         orig_title = title
            #         title = os.path.basename(os.path.normpath(file_path))
            #         logger.warning(
            #             'Imported "{0}" as "{1}" because "{0}" already exists locally'.format(orig_title, title))
        # logger.info('Imported "{0}"'.format(title))
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
