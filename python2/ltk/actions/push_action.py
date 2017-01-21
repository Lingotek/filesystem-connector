from ltk.actions.action import *

class PushAction(Action):
    def __init__(self, add, path):
        Action.__init__(self, path)
        self.add = add

    def push_action(self):
        try:
            self._add_new_docs()
            updated = self._update_current_docs()

            return updated

        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on push: "+str(e))

    def _add_new_docs(self):
        folders = self.folder_manager.get_file_names()

        if len(folders):
            for folder in folders:
                matched_files = get_files(folder)
                if matched_files:
                    for file_name in matched_files:
                        try:
                            relative_path = self.norm_path(file_name)
                            title = os.path.basename(relative_path)
                            if self.doc_manager.is_doc_new(relative_path) and not self.doc_manager.is_translation(relative_path, title, matched_files, self):
                                self.add.add_document(file_name, title)
                        except json.decoder.JSONDecodeError as e:
                            log_error(self.error_file_name, e)
                            logger.error("JSON error on adding document.")

    def _update_current_docs(self):
        updated = False
        entries = self.doc_manager.get_all_entries()

        for entry in entries:
            if not self.doc_manager.is_doc_modified(entry['file_name'], self.path):
                continue

            response = self.api.document_update(entry['id'], os.path.join(self.path, entry['file_name']))
            if response.status_code == 202:
                updated = True
                logger.info('Updated ' + entry['name'])
                self._update_document(entry['file_name'])
            else:
                raise_error(response.json(), "Failed to update document {0}".format(entry['name']), True)
                return updated

        if not updated:
            logger.info('All documents up-to-date with Lingotek Cloud. ')

        return updated
