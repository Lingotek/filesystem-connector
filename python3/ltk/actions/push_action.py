from ltk.actions.action import *

class PushAction(Action):
    def __init__(self, add, path, test, title):
        Action.__init__(self, path)
        self.add = add
        self.title = title
        self.test = test

    def push_action(self, files=None, set_metadata=False, metadata_only=False, **kwargs):
        self.metadata_only = metadata_only
        self.metadata = copy.deepcopy(self.default_metadata)
        if set_metadata:
            self.metadata = self.metadata_wizard()
        elif self.metadata_prompt:
            if yes_no_prompt('Would you like to launch the metadata wizard?', default_yes=True):
                self.metadata = self.metadata_wizard()
        try:
            if files:
                added, updated, failed = self._push_specific_files(files, **kwargs)
            else:
                added = self._add_new_docs(**kwargs)
                updated, failed = self._update_current_docs(**kwargs)
            total = added + updated + failed
            if total is 0:
                report = 'All documents up-to-date with Lingotek Cloud. '
            else:
                report = "Added {0}, Updated {1}, Failed {2} (Total {3})".format(added, updated, failed, total)
            if self.test:
                logger.info("TEST RUN: " + report)
            else:
                logger.info(report)

        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on push: "+str(e))

    def _add_new_docs(self, **kwargs):
        folders = self.folder_manager.get_file_names()
        added = 0
        if len(folders) and not self.metadata_only:
            for folder in folders:
                matched_files = get_files(folder)
                if matched_files:
                    for file_name in matched_files:
                        try:
                            relative_path = self.norm_path(file_name)
                            title = os.path.basename(relative_path)
                            if self.doc_manager.is_doc_new(relative_path) and not self.doc_manager.is_translation(relative_path, title, matched_files, self):
                                display_name = title if self.title else relative_path
                                if self.test:
                                    print('Add {0}'.format(display_name))
                                else:
                                    self.add.add_document(file_name, title, doc_metadata=self.metadata, **kwargs)
                                added += 1
                        except json.decoder.JSONDecodeError as e:
                            log_error(self.error_file_name, e)
                            logger.error("JSON error on adding document.")
        return added

    def _update_current_docs(self, **kwargs):
        updated = 0
        failed = 0
        entries = self.doc_manager.get_all_entries()
        for entry in entries:
            if (len(self.metadata) > 0 or kwargs['due_date'] or kwargs['due_reason']) or (self.doc_manager.is_doc_modified(entry['file_name'], self.path) and not self.metadata_only):
                display_name = entry['name'] if self.title else entry['file_name']
                if self.test:
                    updated += 1 # would be updated
                    print('Update {0}'.format(display_name))
                    continue
                if self.metadata_only or not self.doc_manager.is_doc_modified(entry['file_name'], self.path):
                    response, next_doc_id = self.update_doc_response_manager(self.api.document_update(entry['id'], doc_metadata=self.metadata, **kwargs), entry['id'], doc_metadata=self.metadata, **kwargs)
                else:
                    response, next_doc_id = self.update_doc_response_manager(self.api.document_update(entry['id'], os.path.join(self.path, entry['file_name']), doc_metadata=self.metadata, **kwargs), entry['id'], os.path.join(self.path, entry['file_name']), doc_metadata=self.metadata, **kwargs)
                if response.status_code == 202:
                    try:
                        next_document_id = response.json()['next_document_id']
                    except Exception:
                        next_document_id = None
                    finally:
                        updated += 1
                        logger.info('Updated {0}'.format(display_name))
                        self._update_document(entry['file_name'], next_document_id)
                elif response.status_code == 410:
                    self.doc_manager.remove_element(next_doc_id)
                    print("Document was uploaded, but ID has been archived. Reuploading")
                    self.add.add_document(entry['file_name'], entry['name'])
                else:
                    failed += 1
                    raise_error(response.json(), "Failed to update document {0}".format(entry['name']), True)

        return updated, failed

    def update_doc_response_manager(self, response, document_id, *args, **kwargs):
        if response.status_code == 423 and 'next_document_id' in response.json():
            self.doc_manager.update_document('id', response.json()['next_document_id'], document_id)
            return self.api.document_update(response.json()['next_document_id'], *args, **kwargs), response.json()['next_document_id']
        return response, document_id

    def _push_specific_files(self, patterns, **kwargs):
        files = set()
        added = 0
        updated = 0
        failed = 0
        for pattern in patterns:
            if os.path.isdir(pattern):
                for file in get_files(pattern):
                    relative_path = self.norm_path(file)
                    files.add(relative_path)
            else:
                relative_path = self.norm_path(pattern)
                files.add(relative_path)
        for file in files:
            title = os.path.basename(file)
            if not self.metadata_only and self.doc_manager.is_doc_new(file) and not self.doc_manager.is_translation(file, title, files, self):
                display_name = title if self.title else file
                if self.test:
                    print('Add {0}'.format(display_name))
                else:
                    self.add.add_document(file, title, doc_metadata=self.metadata, **kwargs)
                added += 1
            elif (len(self.metadata) > 0 or kwargs['due_date'] or kwargs['due_reason']) or (self.doc_manager.is_doc_modified(file, self.path) and not self.metadata_only):
                entry = self.doc_manager.get_doc_by_prop('file_name', file)
                if entry:
                    display_name = entry['name'] if self.title else entry['file_name']
                    if self.test:
                        updated += 1 # would be updated
                        print('Update {0}'.format(display_name))
                        continue
                    if self.metadata_only or not self.doc_manager.is_doc_modified(entry['file_name'], self.path):
                        response, next_doc_id = self.update_doc_response_manager(self.api.document_update(entry['id'], doc_metadata=self.metadata, **kwargs), entry['id'], doc_metadata=self.metadata, **kwargs)
                    else:
                        response, next_doc_id = self.update_doc_response_manager(self.api.document_update(entry['id'], os.path.join(self.path, entry['file_name']), doc_metadata=self.metadata, **kwargs), entry['id'], os.path.join(self.path, entry['file_name']), doc_metadata=self.metadata, **kwargs)
                    if response.status_code == 202:
                        try:
                            next_document_id = response.json()['next_document_id']
                        except Exception:
                            next_document_id = None
                        finally:
                            updated += 1
                            logger.info('Updated {0}'.format(display_name))
                            self._update_document(entry['file_name'], next_document_id)
                    elif response.status_code == 410:
                        self.doc_manager.remove_element(next_doc_id)
                        print("Document was uploaded, but ID has been archived. Reuploading")
                        self.add.add_document(entry['file_name'], entry['name'])
                    else:
                        failed += 1
                        raise_error(response.json(), "Failed to update document {0}".format(entry['name']), True)
        return added, updated, failed