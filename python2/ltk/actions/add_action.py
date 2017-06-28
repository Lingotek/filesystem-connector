from ltk.actions.action import *
import ctypes
import socket
import ltk.check_connection

def has_hidden_attribute(file_path):
    """ Detects if a file has hidden attributes """
    try:
        # Python 2
        attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(file_path))
        # End Python 2
        # Python 3
#         attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        # End Python 3
        assert attrs != -1
        result = bool(attrs & 2)
    except (AttributeError, AssertionError):
        result = False
    return result

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

    def add_document(self, file_name, title, **kwargs):
        ''' adds the document to Lingotek cloud and the db '''

        if ltk.check_connection.check_for_connection() == False:
            logger.warning("Cannot connect to network. Documents added to the watch folder will be translated after you reconnect to the network.")
            while ltk.check_connection.check_for_connection() == False:
                time.sleep(15)

        if self.is_hidden_file(file_name):
            return
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

    def is_hidden_file(self, file_path):
        # todo more robust checking for OSX files that doesn't start with '.'
        name = os.path.abspath(file_path).replace(self.path, "")
        if has_hidden_attribute(file_path) or ('Thumbs.db' in file_path) or ('ehthumbs.db' in file_path):
            return True
        while name != "":
            if name.startswith('.') or name.startswith('~') or name == "4913":
                return True
            name = name.split(os.sep)[1:]
            name = (os.sep).join(name)
        return False

    def add_folders(self, file_patterns):
        ''' checks each file pattern for a directory and adds matching patterns to the db '''
        ''' returns true if folder(s) have been added, otherwise false '''

        added_folder = False
        for pattern in file_patterns:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    if self.is_hidden_file(pattern):
                        logger.warning("Folder is hidden")
                    # elif self.download_dir != None and os.path.samefile(pattern, self.download_dir):
                    #     logger.warning("The folder " + "\'" + pattern + "\'" + " set as the downlaod folder. You cannot add the download folder. To remove downlaod folder use \'ltk config -d --none\' command.")
                    elif not self._is_folder_added(pattern):
                        self.folder_manager.add_folder(self.norm_path(pattern.rstrip(os.sep)))
                        logger.info("Added folder "+str(pattern))
                    else:
                        logger.warning("Folder "+str(pattern)+" has already been added.")
                    added_folder = True
            else:
                logger.warning("Path \""+str(pattern)+"\" doesn't exist.")

        return added_folder

    def _is_folder_added(self, file_name):
        """ checks if a folder has been added or is a subfolder of an added folder """
        folder_names = self.folder_manager.get_file_names()
        for folder in folder_names:
            # print("folder: "+str(os.path.join(self.path,folder)))
            # print("folder to be added: "+os.path.abspath(file_name))
            if os.path.join(self.path,folder) in os.path.abspath(file_name):
                return True
        return False

    def append_location(self, name, path_to_file, in_directory=False):
        repo_directory = path_to_file
        path_sep = os.sep
        config_file_name, conf_parser = self.init_config_file()
        if not conf_parser.has_option('main', 'append_option'): self.update_config_file('append_option', 'none', conf_parser, config_file_name, 'Update: Added optional file location appending (ltk config --help)')
        append_option = conf_parser.get('main', 'append_option')
        if not in_directory:
            while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.ltk")):
                repo_directory = repo_directory.split(path_sep)[:-1]
                repo_directory = path_sep.join(repo_directory)
            if repo_directory == "" and append_option != 'none':
                logger.warning('Error: File must be contained within an ltk-initialized directory')
                return name
            path_to_file = path_to_file.replace(repo_directory, '', 1).strip(os.sep)
        if append_option == 'none': return name
        elif append_option == 'full': return '{0} ({1})'.format(name, path_to_file.rstrip(name).rstrip(os.sep))
        elif len(append_option) > 5 and append_option[:5] == 'name:':
            folder_name = append_option[5:]
            if folder_name in path_to_file:
                return '{0} ({1})'.format(name, path_to_file[path_to_file.find(folder_name)+len(folder_name):].rstrip(name).strip(os.sep))
            else: return '{0} ({1})'.format(name, path_to_file.rstrip(name).rstrip(os.sep))
        elif len(append_option) > 7 and append_option[:7] == 'number:':
            try: folder_number = int(append_option[7:])
            except ValueError:
                logger.warning('Error: Value after "number" must be an integer')
                return name
            if(folder_number >=0):
                return '{0} ({1})'.format(name, path_sep.join(path_to_file.rstrip(name).rstrip(os.sep).split(path_sep)[(-1*folder_number) if folder_number != 0 else len(path_to_file):]))
            else:
                logger.warning('Error: Value after "number" must be a non-negative integer')
                return name
        else:
            logger.warning('Error: Invalid value listed for append option. Please update; see ltk config --help')
