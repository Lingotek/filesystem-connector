from ltk.actions.action import *

class CloneAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def clone_folders(self, dest_path, folders_map, locale, copy_root=False):
        """ Copies subfolders of added folders to a particular destination folder (for a particular locale).
            If there is more than one root folder to copy, each root folder is created inside of the destination folder.
            If there is only one root folder to copy, only the subdirectories are copied."""

        try:
            # print("dest_path: "+str(dest_path))
            # print("folders to clone: "+str(folders_map))
            if not folders_map or not len(folders_map):
                logger.warning("No folders to clone for locale "+str(locale)+".")
                return
            folder_created = False
            prefix_folder = False
            if not os.path.exists(dest_path):
                os.mkdir(dest_path)
                folder_created = True
            if len(folders_map) > 1 or copy_root:
                prefix_folder = True
            for root_folder in folders_map:
                # print("root folder: "+root_folder)
                if prefix_folder:
                    new_root_path = dest_path + os.sep + root_folder
                    if not os.path.exists(new_root_path):
                        os.mkdir(new_root_path)
                        folder_created = True
                    for folder in folders_map[root_folder]:
                        new_sub_root_path = dest_path + os.sep + root_folder + os.sep + folder
                        if not os.path.exists(new_sub_root_path):
                            os.mkdir(new_sub_root_path)
                            folder_created = True
                            # print("created folder "+new_sub_root_path)
                else:
                    if folders_map[root_folder]:
                        for folder in folders_map[root_folder]:
                            new_path = dest_path + os.sep + folder
                            if not os.path.exists(new_path):
                                os.mkdir(new_path)
                                folder_created = True
        except IOError as e:
            print(e.errno)
            print(e)
            if folder_created != True:
                folder_created = False
                                    # print("created folder "+ new_path)
        return folder_created

    def clone_action(self, folders, copy_root):
        try:
            if not len(self.watch_locales) or self.watch_locales == set(['[]']):
                logger.warning("There are no locales for which to clone. You can add locales using 'ltk config -t'.")
                return
            folders_map = {}
            are_added_folders = False
            if not folders:
                folders = self.folder_manager.get_file_names()
                are_added_folders = True
            for folder in folders:
                folder_paths = folder.split(os.sep)
                # print("current abs: "+str(self.get_current_abs(folder)))
                if are_added_folders:
                    folder = os.path.join(self.path,folder)
                # print("folder to be cloned: "+str(folder))
                folders_map[folder_paths[len(folder_paths)-1]] = self.get_sub_folders(folder)
            # print("folders: "+str(folders_map))
            cloned_folders = False
            for locale in self.watch_locales:
                dest_path = ""
                if locale in self.locale_folders:
                    dest_path = self.locale_folders[locale]
                else:
                    if self.download_dir and self.download_dir != 'null':
                        dest_path = os.path.join(os.path.join(self.path,self.download_dir),locale)
                    else:
                        dest_path = os.path.join(self.path,locale)
                dest_path = os.path.join(self.path,dest_path)
                if self.clone_folders(dest_path, folders_map, locale, copy_root):
                    logger.info("Cloned locale " + str(locale) + " at " + dest_path)
                    cloned_folders = True
            if not len(self.folder_manager.get_file_names()):
                logger.warning("There are no added folders to clone.")
                return
            if not cloned_folders:
                logger.info("All locales have already been cloned.")
            return
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error("Error on clean: "+str(e))


    def get_sub_folders(self, patterns):
        """ gets all sub-folders matching pattern from root
            pattern supports any unix shell-style wildcards (not same as RE)
            returns the relative paths starting from each pattern"""

        cwd = os.getcwd()
        if isinstance(patterns,str):
            patterns = [patterns]
        allPatterns = []
        if isinstance(patterns,list) or isinstance(patterns,tuple):
            for pattern in patterns:
                # print("pattern in loop: "+str(pattern))
                basename = os.path.basename(pattern)
                if basename and basename != "":
                    allPatterns.extend(self.getRegexDirs(pattern,cwd))
                else:
                    allPatterns.append(pattern)
        else:
            basename = os.path.basename(patterns)
            if basename and basename != "":
                allPatterns.extend(self.getRegexDirs(patterns,cwd))
            else:
                allPatterns.append(patterns)
        matched_dirs = []
        # print("all patterns: "+str(allPatterns))
        for pattern in allPatterns:
            path = os.path.abspath(pattern)
            # print("looking at path "+str(path))
            # check if pattern contains subdirectory
            if os.path.exists(path):
                if os.path.isdir(path):
                    for root, subdirs, files in os.walk(path):
                        split_path = root.split('/')
                        for subdir in subdirs:
                            # print(os.path.join(root, subdir))
                            matched_dirs.append(os.path.join(root,subdir).replace(str(path)+os.sep,""))
            else:
                logger.info("Directory not found: "+pattern)
        if len(matched_dirs) == 0:
            return None
        return matched_dirs

    def getRegexDirs(self, pattern,path):
        dir_name = os.path.dirname(pattern)
        if dir_name:
            path = os.path.join(path,dir_name)
        pattern_name = os.path.basename(pattern)
        # print("path: "+path)
        # print("pattern: "+str(pattern))
        matched_dirs = []
        if pattern_name and not "*" in pattern:
            return [pattern]
        for path, subdirs, files in os.walk(path):
            for dn in fnmatch.filter(subdirs, pattern):
                matched_dirs.append(os.path.join(path, dn))
        print("matched dirs: "+str(matched_dirs))
        return matched_dirs
