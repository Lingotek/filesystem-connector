from ltk.actions.action import *

class ConfigAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.config_file_name, self.conf_parser = self.init_config_file()
        self.print_config = True

    def config_action(self, **kwargs):
        try:
            if 'locale' in kwargs and kwargs['locale']:
                self.set_locale(kwargs['locale'])

            if 'workflow_id' in kwargs and kwargs['workflow_id']:
                self.set_workflow_id(kwargs['workflow_id'])

            if 'download_folder' in kwargs and kwargs['download_folder']:
                self.set_download_folder(kwargs['download_folder'])

            if 'clone_option' in kwargs and kwargs['clone_option']:
                self.set_clone_option(kwargs['clone_option'])

            if 'target_locales' in kwargs and kwargs['target_locales']:
                self.set_target_locales(kwargs['target_locales'])

            if 'locale_folder' in kwargs and kwargs['locale_folder']:
                self.set_locale_folder(kwargs['locale_folder'])

            if 'remove_locales' in kwargs and kwargs['remove_locales']:
                self.remove_locales(kwargs['remove_locales'])

            self.update_config_parser_info()

            if 'git' in kwargs and kwargs['git']:
                self.set_git_autocommit(kwargs['git'])

            if 'git_credentials' in kwargs and kwargs['git_credentials']:
                self.set_git_credentials()

            if 'append_option' in kwargs and kwargs['append_option']:
                self.set_append_option(kwargs['append_option'])

            if 'auto_format' in kwargs and kwargs['auto_format']:
                self.set_auto_format_option(kwargs['auto_format'])

            self.print_output()

        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on config: "+str(e))

    def print_output(self):
        download_dir = "None"
        if self.download_dir and str(self.download_dir) != 'null':
            download_dir = self.download_dir
        locale_folders_str = "None"
        if self.locale_folders:
            locale_folders_str = json.dumps(self.locale_folders).replace("{","").replace("}","").replace("_","-")
        current_git_username = self.conf_parser.get('main', 'git_username')
        current_git_password = self.conf_parser.get('main', 'git_password')
        git_output = ('active' if self.git_autocommit in ['True', 'on'] else 'inactive')
        if self.git_autocommit in ['True', 'on']:
            if current_git_username != "":
                git_output += (' (' + current_git_username + ', password:' + ('YES' if current_git_password != '' else 'NO')) + ')'
            else:
                git_output += (' (password:YES)' if current_git_password != '' else ' (no credentials set, recommend SSH key)')
        if self.print_config:
            watch_locales = set()
            for locale in self.watch_locales:
                watch_locales.add(locale.replace('_','-'))
            watch_locales = ','.join(target for target in watch_locales)

            if str(watch_locales) == "[]" or not watch_locales:
                watch_locales = "None"

            print ('Host: {0}\nLingotek Project: {1} ({2})\nLocal Project Path: {3}\nCommunity ID: {4}\nWorkflow ID: {5}\n'
                'Default Source Locale: {6}\nClone Option: {7}\nAuto Format: {8}\nDownload Folder: {9}\nTarget Locales: {10}\nTarget Locale Folders: {11}\nGit Auto-commit: {12}\nAppend Option: {13}'.format(
                self.host, self.project_id, self.project_name, self.path, self.community_id, self.workflow_id, self.locale, self.clone_option, self.auto_format_option,
                download_dir, watch_locales, locale_folders_str, git_output, self.append_option))
        self.print_config = True

    def remove_locales(self, clear_locales):
        log_info = "Removed all locale specific download folders."
        self.locale_folders = {}
        locale_folders_str = json.dumps(self.locale_folders)
        self.update_config_file('locale_folders', locale_folders_str, self.conf_parser, self.config_file_name, log_info)

    def set_append_option(self, append_option):
        self.print_config = True
        self.append_option = append_option
        if append_option in {'none', 'full'} or append_option[:append_option.find(':')+1] in {'number:', 'name:'}:
            set_option = True
            if append_option[:3] == 'num':
                try: int(append_option[7:])
                except ValueError:
                    logger.warning('Error: Input after "number" must be an integer')
                    self.print_config = False
            elif append_option[:4] == 'name' and len(append_option) <= 5:
                logger.warning('Error: No input given after "name"')
                self.print_config = False
            if not self.conf_parser.has_option('main', 'append_option'):
                self.update_config_file('append_option', 'none', self.conf_parser, self.config_file_name, 'Update: Added optional file location appending (ltk config --help)')
            if self.print_config:
                log_info = 'Append option set to ' + append_option
                self.update_config_file('append_option', append_option, self.conf_parser, self.config_file_name, log_info)
        else:
            logger.warning('Error: Invalid value for "-a" / "--append_option": Must be one of "none", "full", "number:", or "name:"')
            self.print_config = False

    def set_auto_format_option(self, auto_format_option):
        log_info = 'Turned auto format '+auto_format_option
        if auto_format_option == 'on':
            self.auto_format_option = 'on'
            self.update_config_file('auto_format', auto_format_option, self.conf_parser, self.config_file_name, log_info)
        elif auto_format_option == 'off':
            self.auto_format_option = 'off'
            self.update_config_file('auto_format', auto_format_option, self.conf_parser, self.config_file_name, log_info)
        else:
            logger.warning('Error: Invalid value for "-f" / "--auto_format": Must be either "on" or "off"')
            print_config = False

    def set_clone_option(self, clone_option, print_info=True):
        self.clone_action = clone_option
        if print_info:
            log_info = 'Turned clone '+clone_option
        else:
            log_info = ''
        if clone_option == 'on':
            download_option = 'clone'
            self.download_option = download_option

            self.update_config_file('clone_option', clone_option, self.conf_parser, self.config_file_name, log_info)
            self.update_config_file('download_option', download_option, self.conf_parser, self.config_file_name, '')
        elif clone_option == 'off':
            if self.download_dir == '':
                new_download_option = 'same'
                self.download_option = new_download_option

                self.update_config_file('clone_option', clone_option, self.conf_parser, self.config_file_name, log_info)
                self.update_config_file('download_option', new_download_option, self.conf_parser, self.config_file_name, '')
                self.update_config_file('download_folder', self.download_dir, self.conf_parser, self.config_file_name, '')
            else:
                new_download_option = 'folder'
                self.download_option = new_download_option
                self.update_config_file('clone_option', clone_option, self.conf_parser, self.config_file_name, log_info)
                self.update_config_file('download_option', new_download_option, self.conf_parser, self.config_file_name, '')
        else:
            logger.warning('Error: Invalid value for "-c" / "--clone_option": Must be either "on" or "off"')
            print_config = False

    def set_download_folder(self, download_folder):
        if download_folder == '--none':
            if self.download_dir == None or self.download_dir == "" or self.download_dir == "null":
                pass
            else:
                new_download_option = 'same'
                self.download_option = new_download_option
                self.update_config_file('download_folder',"", self.conf_parser, self.config_file_name, "")
                if self.download_option != 'clone':
                    if self.watch_locales != None and len(self.locale_folders) != 0:
                        new_download_option = 'folder'
                    else:
                        new_download_option = 'same'
                    self.download_option = new_download_option
                    log_info = 'Removed download folder'
                    self.update_config_file('download_option', new_download_option, self.conf_parser, self.config_file_name, log_info)
        else:
            download_path = self.norm_path(download_folder)
            if os.path.exists(os.path.join(self.path,download_path)):
                self.download_dir = download_path
                log_info = 'Set download folder to {0}'.format(download_path)
                self.update_config_file('download_folder', download_path, self.conf_parser, self.config_file_name, log_info)

                if self.download_option != 'clone':
                    new_download_option = 'folder'
                    self.download_option = new_download_option
                    self.update_config_file('download_option', new_download_option, self.conf_parser, self.config_file_name, "")
            else:
                logger.warning('Error: Invalid value for "-d" / "--download_folder": The folder {0} does not exist'.format(os.path.join(self.path,download_path)))
                print_config = False

    def set_git_autocommit(self, git_autocommit):
        # if self.git_autocommit == 'True' or self.git_auto.repo_exists(self.path):
        #     log_info = 'Git auto-commit status changed from {0}active'.format(
        #         ('active to in' if self.git_autocommit == "True" else 'inactive to '))
        #     config_file = open(self.config_file_name, 'w')
        #     if self.git_autocommit == "True":
        #         self.update_config_file('git_autocommit', 'False', self.conf_parser, self.config_file_name, log_info)
        #         self.git_autocommit = "False"
        #     else:
        #         self.update_config_file('git_autocommit', 'True', self.conf_parser, self.config_file_name, log_info)
        #         self.git_autocommit = "True"
        self.git_autocommit = git_autocommit
        log_info = 'Turned git auto-commit ' + git_autocommit
        if git_autocommit in ['on', 'off']:
            self.update_config_file('git_autocommit', git_autocommit, self.conf_parser, self.config_file_name, log_info)
        else:
            logger.warning('Error: Invalid value for "-g" / "--clone_option": Must be either "on" or "off"')
            print_config = False

    def set_git_credentials(self):
        if "nt" not in os.name:
            # Python 2
            git_username = raw_input('Username: ')
            # End Python 2
            # Python 3
#             git_username = input('Username: ')
            # End Python 3
            git_password = getpass.getpass()
            if git_username in ['None', 'none', 'N', 'n', '--none']:
                git_username = ""
                log_info = "Git username disabled"
            else:
                log_info = 'Git username set to ' + git_username
            self.update_config_file('git_username', git_username, self.conf_parser, self.config_file_name, log_info)
            if git_password in ['None', 'none', 'N', 'n', '--none']:
                git_password = ""
                log_info = "Git password disabled"
            else:
                log_info = 'Git password set'
            self.update_config_file('git_password', self.git_auto.encrypt(git_password), self.conf_parser, self.config_file_name, log_info)
        else:
            error("Only SSH Key access is enabled on Windows")
            git_username = ""
            git_password = ""

    def set_locale(self, locale):
        self.locale = locale
        log_info = 'Project default locale has been updated to {0}'.format(self.locale)
        self.update_config_file('default_locale', locale, self.conf_parser, self.config_file_name, log_info)

    def set_locale_folder(self, locale_folders):
        count = 0
        folders_count = len(locale_folders)
        folders_string = ""
        log_info = ""
        mult_folders = False
        for folder in locale_folders:
            count += 1
            if not folder[0] or not folder[1]:
                logger.warning("Please specify a valid locale and a directory for that locale.")
                print_config = False
                continue
            locale = folder[0].replace("-","_")
            if not is_valid_locale(self.api, locale):
                logger.warning(str(locale+' is not a valid locale. See "ltk list -l" for the list of valid locales'))
                print_config = False
                continue
            if folder[1] == '--none':
                folders_count -= 1
                if locale in self.locale_folders:
                    self.locale_folders.pop(locale, None)
                    logger.info("Removing download folder for locale "+str(locale)+"\n")
                else:
                    logger.info("The locale "+str(locale)+" already has no download folder.\n")
                    print_config = False
                continue
            path = self.norm_path(os.path.abspath(folder[1]))
            if os.path.exists(os.path.join(self.path,path)):
                taken_locale = self.is_locale_folder_taken(locale, path)
                if taken_locale:
                    logger.info("The folder "+str(path)+" is already taken by the locale "+str(taken_locale)+".\n")
                    print_config = False
                    continue
                else:
                    # print("path of new locale folder: "+path)
                    self.locale_folders[locale] = path
            else:
                logger.warning('Error: Invalid value for "-p" / "--locale_folder": Path "'+path+'" does not exist')
                print_config = False
                continue
            folders_string += str(locale) + ": " + str(path)
            if count < len(locale_folders):
                folders_string += ", "
        if len(folders_string):
            if folders_count > 1:
                log_info = 'Adding locale folders {0}'.format(folders_string)
            else:
                log_info = 'Adding locale folder for {0}'.format(folders_string)
        locale_folders_str = json.dumps(self.locale_folders)
        self.update_config_file('locale_folders', locale_folders_str, self.conf_parser, self.config_file_name, log_info)

    def set_target_locales(self, target_locales):
        locales = []
        for locale in target_locales:
            locales.extend(locale.split(','))
        if len(locales) > 0 and (locales[0].lower() == 'none' or locales[0].lower() == '--none'):
            log_info = 'Removing all target locales'
            self.update_config_file('watch_locales', '', self.conf_parser, self.config_file_name, log_info)
        else:
            target_locales = get_valid_locales(self.api,locales)
            target_locales_str = ','.join(target for target in target_locales)
            if len(target_locales_str) > 0:
                log_info = 'Set target locales to {}'.format(target_locales_str)
                self.update_config_file('watch_locales', target_locales_str, self.conf_parser, self.config_file_name, log_info)
                self.watch_locales = target_locales

    def set_workflow_id(self, workflow_id):
        response = self.api.patch_project(self.project_id, workflow_id)
        if response.status_code != 204:
            raise_error(response.json(), 'Something went wrong trying to update workflow_id of project')
        self.workflow_id = workflow_id
        log_info = 'Project default workflow has been updated to {0}'.format(workflow_id)
        self.update_config_file('workflow_id', workflow_id, self.conf_parser, self.config_file_name, log_info)
        self.conf_parser.set('main', 'workflow_id', workflow_id)

    def update_config_parser_info(self):
        # clone_option = self.conf_parser.get('main', 'clone_option')
        # download_folder = self.conf_parser.get('main', 'download_folder')
        # download_option = self.conf_parser.get('main', 'download_option')
        # if 'download_option' == 'same' or (clone_option == "off" and download_folder == "null"):
        #     self.update_config_file('download_option', 'folder', self.conf_parser, self.config_file_name, "")
        if not self.conf_parser.has_option('main', 'git_autocommit'):
            self.update_config_file('git_autocommit', 'False', self.conf_parser, self.config_file_name, 'Update: Added \'git auto-commit\' option (ltk config --help)')
            self.update_config_file('git_username', '', self.conf_parser, self.config_file_name, 'Update: Added \'git username\' option (ltk config --help)')
            self.update_config_file('git_password', '', self.conf_parser, self.config_file_name, 'Update: Added \'git password\' option (ltk config --help)')
        self.git_autocommit = self.conf_parser.get('main', 'git_autocommit')
