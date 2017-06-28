from ltk.actions.action import *

class RmAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def rm_action(self, file_patterns, **kwargs):
        try:
            removed_folder = False
            for pattern in file_patterns:
                if os.path.isdir(pattern):
                    # print("checking folder "+self.norm_path(pattern))
                    if self.folder_manager.folder_exists(self.norm_path(pattern)):
                        self.folder_manager.remove_element(self.norm_path(pattern))
                        logger.info("Removed folder "+pattern)
                        removed_folder = True
                    else:
                        logger.warning("Folder "+str(pattern)+" has not been added and so can not be removed")
            if 'directory' in kwargs and kwargs['directory']:
                if not removed_folder:
                    logger.info("No folders to remove at the given path(s)")
                return
            matched_files = None
            if isinstance(file_patterns,str):
                file_patterns = [file_patterns]
            if 'force' in kwargs and kwargs['force']:
                force = True
            else:
                force = False
            if 'id' in kwargs and kwargs['id']:
                useID = True
            else:
                useID = False
            if 'all' in kwargs and kwargs['all']:
                local = False
                self.folder_manager.clear_all()
                removed_folder = True
                logger.info("Removed all folders.")
                if 'remote' in kwargs and kwargs['remote']:
                    matched_files = self.rm_remote(force)
                else:
                    useID = False
                    matched_files = self.doc_manager.get_file_names()
            elif 'local' in kwargs and kwargs['local']:
                local = True
                if 'name' in kwargs and kwargs['name']:
                    matched_files = []

                    for pattern in file_patterns:
                        doc = self.doc_manager.get_doc_by_prop("name",pattern)
                        if doc:
                            matched_files.append(doc['file_name'])
                else:
                    if len(file_patterns) == 0:
                        self.folder_manager.clear_all()
                        removed_folder = True
                        logger.info("Removed all folders.")
                        useID = False
                        matched_files = self.doc_manager.get_file_names()

            elif not useID:
                local = False
                # use current working directory as root for files instead of project root
                if 'name' in kwargs and kwargs['name']:
                    matched_files = []

                    for pattern in file_patterns:
                        doc = self.doc_manager.get_doc_by_prop("name",pattern)
                        if doc:
                            matched_files.append(doc['file_name'])
                else:
                    matched_files = self.get_doc_filenames_in_path(file_patterns)
            else:
                local = False
                matched_files = file_patterns
            if not matched_files or len(matched_files) == 0:
                if useID:
                    raise exceptions.ResourceNotFound("No documents to remove with the specified id")
                elif removed_folder:
                    logger.info("No documents to remove")
                elif local:
                    raise exceptions.ResourceNotFound("Too many agruments, to specify a document to be reomved locally use -l in association with -n")
                elif not 'all' in kwargs or not kwargs['all']:
                    raise exceptions.ResourceNotFound("No documents to remove with the specified file path")
                else:
                    raise exceptions.ResourceNotFound("No documents to remove")
            is_directory = False
            for pattern in file_patterns: # If attemping to remove any directory, don't print failure message
                basename = os.path.basename(pattern)
                if not basename or basename == "":
                    is_directory = True
            for file_name in matched_files:
                # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
                self.rm_document(self.norm_path(file_name).replace(self.path,""), useID, force, local)

        except Exception as e:
            # Python 3
#             log_error(self.error_file_name, e)
            # End Python 3
            if 'string indices must be integers' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on remove: "+str(e))

    def rm_clone(self, file_name):
        trans_files = []
        entry = self.doc_manager.get_doc_by_prop("file_name", file_name)
        if entry:
            if 'locales' in entry and entry['locales']:
                locales = entry['locales']
                for locale_code in locales:
                    if locale_code in self.locale_folders:
                        download_root = self.locale_folders[locale_code]
                    elif self.download_dir and len(self.download_dir):
                        download_root = os.path.join((self.download_dir if self.download_dir and self.download_dir != 'null' else ''),locale_code)
                    else:
                        download_root = locale_code
                    download_root = os.path.join(self.path,download_root)
                    source_file_name = entry['file_name']
                    source_path = os.path.join(self.path,os.path.dirname(source_file_name))

                    trans_files.extend(get_translation_files(file_name, download_root, self.download_option, self.doc_manager))

        return trans_files

    def rm_document(self, file_name, useID, force, local=False, doc_name=None, is_directory=False):
        try:
            doc = None
            if not useID:
                relative_path = self.norm_path(file_name)
                doc = self.doc_manager.get_doc_by_prop('file_name', relative_path)
                title = os.path.basename(self.norm_path(file_name))
                try:
                    document_id = doc['id']
                except TypeError: # Documents specified by name must be found in the local database to be removed.
                    if not is_directory:
                        logger.warning("Document name specified for remove isn't in the local database: {0}".format(relative_path))
                    return
                    # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
            else:
                document_id = file_name
                doc = self.doc_manager.get_doc_by_prop('id', document_id)
                if doc:
                    file_name = doc['file_name']
            if local and not force:
                self.delete_local(file_name, document_id)

            else:
                response = self.api.document_delete(document_id)
                #print (response)
                if response.status_code != 204 and response.status_code != 202:
                    # raise_error(response.json(), "Failed to delete document {0}".format(document_name), True)
                    logger.error("Failed to delete document {0} remotely".format(file_name))
                else:
                    if doc_name:
                        logger.info("{0} ({1}) has been deleted remotely".format(doc_name, file_name))
                    else:
                        logger.info("{0} has been deleted remotely".format(file_name))
                    if doc:
                        if force:
                            #delete local translation file(s) for the document being deleted
                            trans_files = []
                            if 'clone' in self.download_option:
                                trans_files = self.rm_clone(file_name)

                            elif 'folder' in self.download_option:
                                trans_files = self.rm_folder(file_name)

                            elif 'same' in self.download_option:
                                download_path = self.path
                                trans_files = get_translation_files(file_name, download_path, self.download_option, self.doc_manager)

                            self.delete_local(file_name, document_id)
            self.doc_manager.remove_element(document_id)
        except json.decoder.JSONDecodeError:
            logger.error("JSON error on removing document")
        except KeyboardInterrupt:
            raise_error("", "Canceled removing document")
            return
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error("Error on removing document "+str(file_name)+": "+str(e))

    def rm_folder(self, file_name):
        trans_files = []
        entry = self.doc_manager.get_doc_by_prop("file_name", file_name)
        if entry:
            if 'locales' in entry and entry['locales']:
                locales = entry['locales']
                for locale_code in locales:
                    if locale_code in self.locale_folders:
                        if self.locale_folders[locale_code] == 'null':
                            logger.warning("Download failed: folder not specified for "+locale_code)
                        else:
                            download_path = self.locale_folders[locale_code]
                    else:
                        download_path = self.download_dir

                    download_path = os.path.join(self.path,download_path)
                    trans_files.extend(get_translation_files(file_name, download_path, self.download_option, self.doc_manager))
        return trans_files

    def rm_remote(self, force):
        response = self.api.list_documents(self.project_id)
        if response.status_code == 204:
            print("No remote documents to remove.")
            return
        elif response.status_code != 200:
            if check_response(response):
                raise_error(response.json(), "Failed to get status of documents", True)
            else:
                raise_error("", "Failed to get status of documents", True)
            return
        else:
            matched_files = []
            for entry in response.json()['entities']:
                id = entry['properties']['id']
                doc_name = entry['properties']['name']

                doc = self.doc_manager.get_doc_by_prop("id",id)
                matched_files.append(doc["file_name"])
            return matched_files
