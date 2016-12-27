from ltk.actions.action import *

class ConfigAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def config_action(self, **kwargs):
        try:
            config_file_name, conf_parser = self.init_config_file()
            print_config = True
            if 'locale' in kwargs and kwargs['locale']:
                self.locale = kwargs['locale']
                log_info = 'Project default locale has been updated to {0}'.format(self.locale)
                self.update_config_file('default_locale', locale, conf_parser, config_file_name, log_info)
            if 'workflow_id' in kwargs and kwargs['workflow_id']:
                workflow_id = kwargs['workflow_id']
                response = self.api.patch_project(self.project_id, workflow_id)
                if response.status_code != 204:
                    raise_error(response.json(), 'Something went wrong trying to update workflow_id of project')
                self.workflow_id = workflow_id
                log_info = 'Project default workflow has been updated to {0}'.format(workflow_id)
                self.update_config_file('workflow_id', workflow_id, conf_parser, config_file_name, log_info)
                conf_parser.set('main', 'workflow_id', workflow_id)
            if 'download_folder' in kwargs and kwargs['download_folder']:
                if kwargs['download_folder'] == '--none':
                    new_download_option = 'same'
                    self.download_option = new_download_option
                    self.update_config_file('download_folder',"", conf_parser, config_file_name, "")

                    if self.download_option != 'clone':
                        new_download_option = 'same'
                        self.download_option = new_download_option
                        log_info = 'Removed download folder'
                        self.update_config_file('download_option', new_download_option, conf_parser, config_file_name, log_info)

                else:
                    download_path = self.norm_path(kwargs['download_folder'])
                    if os.path.exists(os.path.join(self.path,download_path)):
                        self.download_dir = download_path
                        log_info = 'Set download folder to {0}'.format(download_path)
                        self.update_config_file('download_folder', download_path, conf_parser, config_file_name, log_info)

                        if self.download_option != 'clone':
                            new_download_option = 'folder'
                            self.download_option = new_download_option
                            self.update_config_file('download_option', new_download_option, conf_parser, config_file_name, "")
                    else:
                        logger.warning('Error: Invalid value for "-d" / "--download_folder": The folder {0} does not exist'.format(os.path.join(self.path,download_path)))
                        print_config = False
            if 'clone_option' in kwargs and kwargs['clone_option']:
                clone_option = kwargs['clone_option']
                self.clone_action = clone_option
                log_info = 'Turned clone '+clone_option
                if clone_option == 'on':
                    download_option = 'clone'
                    self.download_option = download_option

                    self.update_config_file('clone_option', clone_option, conf_parser, config_file_name, log_info)
                    self.update_config_file('download_option', download_option, conf_parser, config_file_name, '')
                elif clone_option == 'off':
                    if self.download_dir == '':
                        new_download_option = 'same'
                        self.download_option = new_download_option

                        self.update_config_file('clone_option', clone_option, conf_parser, config_file_name, log_info)
                        self.update_config_file('download_option', new_download_option, conf_parser, config_file_name, '')
                        self.update_config_file('download_folder', self.download_dir, conf_parser, config_file_name, '')
                    else:
                        new_download_option = 'folder'
                        self.download_option = new_download_option
                        self.update_config_file('clone_option', clone_option, conf_parser, config_file_name, log_info)
                        self.update_config_file('download_option', new_download_option, conf_parser, config_file_name, '')
                else:
                    logger.warning('Error: Invalid value for "-c" / "--clone_option": Must be either "on" or "off"')
                    print_config = False

            if 'target_locales' in kwargs and kwargs['target_locales']:
                target_locales = kwargs['target_locales']
                locales = []
                for locale in target_locales:
                    locales.extend(locale.split(','))
                if len(locales) > 0 and locales[0].lower() == 'none':
                    log_info = 'Removing all target locales'
                    self.update_config_file('watch_locales', '', conf_parser, config_file_name, log_info)
                else:
                    target_locales = get_valid_locales(self.api,locales)
                    target_locales_str = ','.join(target for target in target_locales)
                    if len(target_locales_str) > 0:
                        log_info = 'Set target locales to {}'.format(target_locales_str)
                        self.update_config_file('watch_locales', target_locales_str, conf_parser, config_file_name, log_info)
                        self.watch_locales = target_locales

            if 'locale_folder' in kwargs and kwargs['locale_folder']:
                locale_folders = kwargs['locale_folder']
                mult_folders = False
                folders_count = len(locale_folders)
                folders_string = ""
                count = 0
                log_info = ""
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
                self.update_config_file('locale_folders', locale_folders_str, conf_parser, config_file_name, log_info)
            if 'remove_locales' in kwargs and kwargs['remove_locales']:
                clear_locales = kwargs['remove_locales']
                log_info = "Removed all locale specific download folders."
                self.locale_folders = {}
                locale_folders_str = json.dumps(self.locale_folders)
                self.update_config_file('locale_folders', locale_folders_str, conf_parser, config_file_name, log_info)
            #print ('Token: {0}'.format(self.access_token))
            if not conf_parser.has_option('main', 'git_autocommit'):
                self.update_config_file('git_autocommit', 'False', conf_parser, config_file_name, 'Update: Added \'git auto-commit\' option (ltk config --help)')
                self.update_config_file('git_username', '', conf_parser, config_file_name, 'Update: Added \'git username\' option (ltk config --help)')
                self.update_config_file('git_password', '', conf_parser, config_file_name, 'Update: Added \'git password\' option (ltk config --help)')
            self.git_autocommit = conf_parser.get('main', 'git_autocommit')
            if 'git' in kwargs and kwargs['git']:
                if self.git_autocommit == 'True' or self.git_auto.repo_exists(self.path):
                    log_info = 'Git auto-commit status changed from {0}active'.format(
                        ('active to in' if self.git_autocommit == "True" else 'inactive to '))
                    config_file = open(config_file_name, 'w')
                    if self.git_autocommit == "True":
                        self.update_config_file('git_autocommit', 'False', conf_parser, config_file_name, log_info)
                        self.git_autocommit = "False"
                    else:
                        self.update_config_file('git_autocommit', 'True', conf_parser, config_file_name, log_info)
                        self.git_autocommit = "True"
            if 'git_credentials' in kwargs and kwargs['git_credentials']:
                if "nt" not in os.name:
                    # Python 2
                    git_username = raw_input('Username: ')
                    # End Python 2
                    # Python 3
#                     git_username = input('Username: ')
                    # End Python 3
                    git_password = getpass.getpass()
                    if git_username in ['None', 'none', 'N', 'n']:
                        git_username = ""
                        log_info = "Git username disabled"
                    else:
                        log_info = 'Git username set to ' + git_username
                    self.update_config_file('git_username', git_username, conf_parser, config_file_name, log_info)
                    if git_password in ['None', 'none', 'N', 'n']:
                        git_password = ""
                        log_info = "Git password disabled"
                    else:
                        log_info = 'Git password set'
                    self.update_config_file('git_password', self.git_auto.encrypt(git_password), conf_parser, config_file_name, log_info)
                else:
                    error("Only SSH Key access is enabled on Windows")
                    git_username = ""
                    git_password = ""
            if 'append_option' in kwargs and kwargs['append_option']:
                append_option = kwargs['append_option']
                self.append_option = append_option
                if append_option in {'none', 'full'} or append_option[:append_option.find(':')+1] in {'number:', 'name:'}:
                    set_option = True
                    if append_option[:3] == 'num':
                        try: int(append_option[7:])
                        except ValueError:
                            logger.warning('Error: Input after "number" must be an integer')
                            print_config = False
                    elif append_option[:4] == 'name' and len(append_option) <= 5:
                        logger.warning('Error: No input given after "name"')
                        print_config = False
                    if not conf_parser.has_option('main', 'append_option'):
                        self.update_config_file('append_option', 'none', conf_parser, config_file_name, 'Update: Added optional file location appending (ltk config --help)')
                    if print_config:
                        log_info = 'Append option set to ' + append_option
                        self.update_config_file('append_option', append_option, conf_parser, config_file_name, log_info)
                else:
                    logger.warning('Error: Invalid value for "-a" / "--append_option": Must be one of "none", "full", "number:", or "name:"')
                    print_config = False
            download_dir = "None"
            if self.download_dir and str(self.download_dir) != 'null':
                download_dir = self.download_dir
            locale_folders_str = "None"
            if self.locale_folders:
                locale_folders_str = json.dumps(self.locale_folders).replace("{","").replace("}","").replace("_","-")
            current_git_username = conf_parser.get('main', 'git_username')
            current_git_password = conf_parser.get('main', 'git_password')
            git_output = ('active' if self.git_autocommit == "True" else 'inactive')
            if self.git_autocommit == "True":
                if current_git_username != "":
                    git_output += (' (' + current_git_username + ', password:' + ('YES' if current_git_password != '' else 'NO')) + ')'
                else:
                    git_output += (' (password:YES)' if current_git_password != '' else ' (no credentials set, recommend SSH key)')
            if print_config:
                watch_locales = set()
                for locale in self.watch_locales:
                    watch_locales.add(locale.replace('_','-'))
                watch_locales = ','.join(target for target in watch_locales)

                if str(watch_locales) == "[]" or not watch_locales:
                    watch_locales = "None"

                print ('Host: {0}\nLingotek Project: {1} ({2})\nLocal Project Path: {3}\nCommunity ID: {4}\nWorkflow ID: {5}\n'
                    'Default Source Locale: {6}\nClone Option: {7}\nDownload Folder: {8}\nTarget Locales: {9}\nTarget Locale Folders: {10}\nGit Auto-commit: {11}\nAppend Option: {12}'.format(
                    self.host, self.project_id, self.project_name, self.path, self.community_id, self.workflow_id, self.locale, self.clone_option,
                    download_dir, watch_locales, locale_folders_str, git_output, self.append_option))
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on config: "+str(e))