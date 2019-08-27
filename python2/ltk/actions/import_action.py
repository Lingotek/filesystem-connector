from ltk.actions.action import *

class ImportAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.skip_ids = []

    def _get_import_ids(self,info):
        mapper = choice_mapper(info)
        chosen_ids = []
        while not len(chosen_ids) > 0:
            prompt_message = 'Documents to import: (Separate indices by comma) '
            # Python 2
            choice = raw_input(prompt_message)
            # End Python 2
            # Python 3
#             choice = input(prompt_message)
            # End Python 3
            try:
                chosen_ids = [list(mapper[int(index)].keys())[0] for index in choice.split(',')]
            except ValueError:
                print ('Some unexpected, non-integer value was included')
        return chosen_ids

    def import_action(self, import_all, force, path, track, no_cancel, ids_to_import=None):
        try:
            path = self.norm_path(path)
            response = self.api.list_documents(self.project_id)
            tms_doc_info = {}
            if response.status_code == 200:
                tms_documents = response.json()['entities']
                for entity in tms_documents:
                    doc_info = {'title': entity['properties']['title'], 'extension': entity['properties']['extension']}
                    if no_cancel or track:
                        statuscheck = self.api.document_status(entity['properties']['id'])
                        if statuscheck.json()['properties']['status'].upper() == 'CANCELLED':
                            if no_cancel:
                                continue
                            self.skip_ids.append(entity['properties']['id'])
                    tms_doc_info[entity['properties']['id']] = doc_info
            elif response.status_code == 204:
                logger.error('No documents to import!')
                return
            else:
                raise_error(response.json(), 'Error finding current documents in Lingotek Cloud')
            if len(tms_doc_info) == 0:
                logger.error('No documents to import!')
                return

            if not ids_to_import:
                if import_all:
                    # Python 2
                    ids_to_import = tms_doc_info.iterkeys()
                    # End Python 2
                    # Python 3
#                     ids_to_import = iter(tms_doc_info)
                    # End Python 3
                else:
                    import_doc_info = {}
                    # Python 2
                    for k, v in tms_doc_info.iteritems():
                    # End Python 2
                    # Python 3
#                     for k, v in tms_doc_info.items():
                    # End Python 3
                        import_doc_info[k] = v['title']
                    ids_to_import = self._get_import_ids(import_doc_info)
            else:
                ids_to_import = [ids_to_import]
            for curr_id in ids_to_import:
                self.import_document(curr_id, tms_doc_info[curr_id], force, path, track)
        except Exception as e:
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on import: "+str(e))

    def import_check(self, document_id, title, force=False, path=False):
        if not path:
            path = self.path
        else:
            path = os.path.join(self.path, path.replace(self.path, ''))
        path_changed = False
        curr_path = False
        write_file = True
        curr_entry = self.doc_manager.get_doc_by_prop('id', document_id)
        new_path = os.path.join(path, title)
        delete_file = False
        if curr_entry:
            curr_path = os.path.join(self.path, curr_entry['file_name'])
            # print (curr_path, new_path)
            if self.norm_path(curr_path) != self.norm_path(new_path):
                path_changed = curr_path
        if not force:
            if not curr_path and not os.path.exists(new_path):
                return path_changed, new_path, write_file, delete_file
            if path_changed and curr_path: # Confirm changing the file path saved in docs.json
                change_option = yes_no_prompt('Would you like to change ' \
                    'the current saved path of '+title+' from '+curr_path+' to '+new_path+'?', default_yes=False)
                if change_option:
                    delete_option = yes_no_prompt('Delete '+curr_path+'?', default_yes=False)
                    if delete_option:
                        delete_file = True
                else:
                    logger.info('Retaining old path "{0}"'.format(curr_path))
                    path_changed = False
                    new_path = curr_path
            # Confirm overwriting a local file
            if os.path.exists(new_path):
                overwrite_option = yes_no_prompt('Would you like to overwrite the existing document at '+new_path+'?', default_yes=False)
                if not overwrite_option:
                    logger.info('Skipped importing "{0}"'.format(title))
                    write_file = False
        # print(str(path_changed)+" "+str(new_path)+" "+str(write_file)+" "+str(delete_file))
        return path_changed, new_path, write_file, delete_file

    def import_document(self, document_id, document_info, force=False, path=False, track=False):
        local_ids = self.doc_manager.get_doc_ids()
        response = self.api.document_content(document_id, None, None, finalized_file=self.finalized_file)
        if(response.status_code == 400):
            if document_info and document_info['title']:
                title = document_info['title']
                logger.info('Failed to import document: {0}'.format(title))
            else:
                logger.info('Failed to import document: {0}'.format(document_id))
            return
        elif (response.status_code == 404):
            if document_info and document_info['title']:
                title = document_info['title']
                logger.info('Document not found {0}'.format(title))
            else:
                logger.info('Document with ID: \'{0}\' not found'.format(document_id))
            return
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
        logger.info('Importing "{0}" to {1}'.format(title, file_path))
        # use status action to get locale info for importing
        try:
            locale_map = self.import_locale_info(document_id)
            # Python 2
            locale_info = list(locale_map.iterkeys())
            # End Python 2
            # Python 3
#             locale_info = list(iter(locale_map))
            # End Python 3
        except exceptions.RequestFailedError:
            print("failed on locale info")
            locale_info = []

        changed_path = False
        changed_path, new_path, write_file, delete_file = self.import_check(document_id, title, force, path)
        if delete_file and changed_path and os.path.exists(changed_path):
            self.delete_local_path(changed_path, 'Deleting local file {0}'.format(changed_path))

        if write_file:
            try:
                with open(new_path, 'wb') as fh:
                    for chunk in response.iter_content(1024):
                        fh.write(chunk)
            except IOError as e:
                print(e.errno)
                print(e)
        new_path = self.norm_path(new_path)
        if track:
            if document_id in self.skip_ids:
                return
            if document_id not in local_ids:
                self._add_document(new_path, title, document_id, 'imported')
                self.doc_manager.update_document('locales', locale_info, document_id)
            elif changed_path:
                # update the document's path
                logger.info('Moved local file {0} to {1}'.format(changed_path, new_path))
                self.doc_manager.update_document('file_name', new_path, document_id)
