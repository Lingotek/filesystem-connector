from ltk.actions.action import *
from ltk.utils import *

class AddAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def add_action(self, file_patterns, **kwargs):
        # format will be automatically detected by extension but may not be what user expects
        # use current working directory as root for files instead of project root

        try:
            # add folders to the db
            added_folder = self.add_folders(file_patterns)
            if 'directory' in kwargs and kwargs['directory']:
                if not added_folder:
                    logger.info("No folders to add at the given path(s).")
                return

            # get files to add and check if they exist
            Action.init_config_file(self)
            matched_files = get_files(file_patterns)
            if not matched_files:
                if added_folder:
                    # folders have been added and there are no documents to add, nothing left to do
                    return
                else:
                    raise exceptions.ResourceNotFound("Could not find the specified file/pattern.")

            # add the documents to the db and lingotek cloud
            self.add_documents(matched_files, **kwargs)

        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on add: "+str(e))

    def add_document(self, file_name, title, **kwargs):
        ''' adds the document to Lingotek cloud and the db '''

        try:
            if not 'locale' in kwargs or not kwargs['locale']:
                locale = self.locale
            else:
                locale = kwargs['locale']

            # add document to Lingotek cloud
            response = self.api.add_document(locale, file_name, self.project_id, self.append_location(title, file_name), **kwargs)
            if response.status_code != 202:
                raise_error(response.json(), "Failed to add document {0}".format(title), True)
            else:
                title = self.append_location(title, file_name)
                logger.info('Added document {0} with ID {1}'.format(title,response.json()['properties']['id']))
                relative_path = self.norm_path(file_name)

                # add document to the db
                self._add_document(relative_path, title, response.json()['properties']['id'])

        except KeyboardInterrupt:
            raise_error("", "Canceled adding document")
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on adding document "+str(file_name)+": "+str(e))

    def add_documents(self, matched_files, **kwargs):
        ''' adds new documents to the lingotek cloud and, after prompting user, overwrites changed documents that
                have already been added '''

        for file_name in matched_files:
            try:
                # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
                relative_path = self.norm_path(file_name)
                title = os.path.basename(relative_path)
                if not self.doc_manager.is_doc_new(relative_path):
                    if self.doc_manager.is_doc_modified(relative_path, self.path):
                        if 'overwrite' in kwargs and kwargs['overwrite']:
                            confirm = 'Y'
                        else:
                            confirm = 'not confirmed'
                        try:
                            while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                                prompt_message = "Document \'{0}\' already exists. Would you like to overwrite it? [y/N]: ".format(title)
                                # Python 2
                                confirm = raw_input(prompt_message)
                                # End Python 2
                                # Python 3
#                                 confirm = input(prompt_message)
                                # End Python 3

                            # confirm if would like to overwrite existing document in Lingotek Cloud
                            if not confirm or confirm in ['n', 'N']:
                                logger.info('Will not overwrite document \'{0}\' in Lingotek Cloud'.format(title))
                                continue
                            else:
                                logger.info('Overwriting document \'{0}\' in Lingotek Cloud...'.format(title))
                                self.update_document_action(file_name, title, **kwargs)
                                continue
                        except KeyboardInterrupt:
                            logger.error("Canceled adding the document")
                            return
                    else:
                        logger.error("This document has already been added: {0}".format(title))
                        continue
            except json.decoder.JSONDecodeError:
                logger.error("JSON error on adding document.")

            self.add_document(file_name, title, **kwargs)

    def add_folders(self, file_patterns):
        ''' checks each file pattern for a directory and adds matching patterns to the db '''
        ''' returns true if folder(s) have been added, otherwise false '''

        added_folder = False
        for pattern in file_patterns:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    if not self._is_folder_added(pattern):
                        self.folder_manager.add_folder(self.norm_path(pattern.rstrip(os.sep)))
                        logger.info("Added folder "+str(pattern))
                    else:
                        logger.warning("Folder "+str(pattern)+" has already been added.")
                    added_folder = True
            else:
                logger.warning("Path \""+str(pattern)+"\" doesn't exist.")

        return added_folder
