from ltk.actions.action import *

class MoveAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.uploadWaitTime = 300
        self.rename = False
        self.source_type = ''
        self.path_to_source = ''
        self.path_to_destination = ''
        self.path_sep = ''
        self.directory_to_destination = ''
        self.source = ''
        self.doc = ''
        self.folder = ''
        self.directory_to_source = ''

    def mv_file(self, source, destination):
        doc = None
        self.source = source
        try:
            self.path_sep = os.sep
            self.path_to_source = os.path.abspath(self.source)
            if not self.rename:
                self.path_to_destination = os.path.abspath(destination)
            else:
                self.path_to_destination = self.path_to_source.rstrip(os.path.basename(self.path_to_source))+destination
            repo_directory = self.path_to_source
            while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.ltk")):
                repo_directory = repo_directory.split(self.path_sep)[:-1]
                repo_directory = self.path_sep.join(repo_directory)
            if repo_directory not in self.path_to_source or repo_directory not in self.path_to_destination:
                logger.error("Error: Operations can only be performed inside ltk directory.")
                return False
            directory_to_source = (self.path_to_source.replace(repo_directory, '',1)).lstrip(self.path_sep)
            self.directory_to_destination = (self.path_to_destination.replace(repo_directory, '',1)).lstrip(self.path_sep)
            folder = None
            if self.source_type == 'file':
                doc = self.doc_manager.get_doc_by_prop("file_name",directory_to_source)
                if not doc:
                    logger.error("Error: File has not been added and so can not be moved.")
                    return False
            elif self.source_type == 'folder':
                folder = self.folder_manager.get_folder_by_name(directory_to_source)
                if not folder:
                    logger.warning("Notice: This folder has not been added, though it may be in a directory that has")
            return self._do_move(doc, folder, directory_to_source)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on moving "+str(self.source)+": "+str(e))

    def _do_move(self, sself.source = ''doc, folder, directory_to_source):
        try:
            if self.rename and self.source_type == 'file' and self.path_to_source.rstrip(self.path_sep).rstrip(doc['name']) != self.path_to_source.rstrip(self.path_sep):
                new_name = os.path.basename(self.path_to_destination)
                self.doc_manager.update_document('name', new_name, doc['id'])
                self.api.document_update(doc['id'], title=new_name)
            elif not self.rename:
                file_name = os.path.basename(self.path_to_source)
                self.path_to_destination+=self.path_sep+file_name
                self.directory_to_destination+=self.path_sep+file_name
            os.rename(self.path_to_source, self.path_to_destination)
            if self.source_type == 'file':
                self.doc_manager.update_document('file_name', self.directory_to_destination.strip(self.path_sep), doc['id'])
            elif folder:
                self.folder_manager.remove_element(directory_to_source)
                self.folder_manager.add_folder(self.directory_to_destination)
            if self.source_type == 'folder':
                for file_name in self.doc_manager.get_file_names():
                    if file_name.find(directory_to_source) == 0:
                        doc = self.doc_manager.get_doc_by_prop("file_name",file_name)
                        self.doc_manager.update_document('file_name', file_name.replace(directory_to_source, self.directory_to_destination, 1), doc['id'])
            return True
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error("Error: "+str(e))
            logger.error("An error prevented document {0} from being moved".format(self.source))
            return False

    def mv_action(self, sources, destination):
        try:
            for source in sources:
                if os.path.isdir(source):
                    if os.path.isdir(destination):
                        self.source_type = 'folder'
                        if self.mv_file(source, destination):
                            logger.info("Folder "+source+" has been moved to "+destination)
                        else: logger.error("Failed to move folder "+source)
                    elif os.path.isfile(destination):
                        logger.error("mv: cannot overwrite non-directory ‘"+source+"’ with directory ‘"+destination+"’")
                    else:
                        self.rename = True
                        self.source_type = 'folder'
                        if self.mv_file(source, destination):
                            logger.info("Folder "+source+" has been renamed to "+destination)
                        else: logger.error("Failed to move folder "+source)
                elif os.path.isfile(source):
                    if os.path.isdir(destination):
                        if self.mv_file(source, destination):
                            logger.info(source+" has been moved to "+destination)
                        else: logger.error("Failed to move file "+source)
                    elif os.path.isfile(destination):
                        self.rename = True
                        if self.mv_file(source, destination):
                            logger.info(source+" has been renamed as "+destination)
                            logger.info(destination+" has been deleted")
                        else: logger.error("Failed to move file "+source)
                    else:
                        self.rename = True
                        if self.mv_file(source, destination):
                            logger.info(source+" has been renamed to "+destination)
                        else: logger.error("Failed to move file "+source)
                else:
                    logger.error("Error: Source file does not exist")
        except Exception as e:
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on mv: "+str(e))
