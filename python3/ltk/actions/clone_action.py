from ltk.actions.action import *

class CloneAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def clone_folders(self, dest_path, folders_map, locale, copy_root=False):
        """ Copies subfolders of added folders to a particular destination folder (for a particular locale).
            If there is more than one root folder to copy, each root folder is created inside of the destination folder.
            If there is only one root folder to copy, only the subdirectories are copied."""
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
                folders_map[folder_paths[len(folder_paths)-1]] = get_sub_folders(folder)
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