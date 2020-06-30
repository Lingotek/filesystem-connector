''' Python Dependencies '''
import ctypes
import getpass
import os
import subprocess

''' Internal Dependencies '''
from ltk.actions.action import *
from ltk.actions.config_action import ConfigAction
from ltk.git_auto import Git_Auto

''' Globals '''
HIDDEN_ATTRIBUTE = 0x02

class InitAction():
    def __init__(self, path):
        self.path = path
        self.turn_clone_on = True
        #Action.__init__(self, path)

    def init_action(self, host, access_token, client_id, project_path, folder_name, workflow_id, default_locale, browser, delete, reset):
        # Tabulate is used to help create the tables on the init
        client_id = 'ab33b8b9-4c01-43bd-a209-b59f933e4fc4' if not client_id else client_id
        try:
            # check if Lingotek directory already exists
            to_init = self.reinit(host, project_path, delete, reset)
            # print("to_init: "+str(to_init))
            if not to_init:
                return
            elif to_init is not True:
                access_token = to_init
            ran_oauth = False
            if not access_token:
                access_token = self.check_global(host)
                if not access_token or reset:
                    if 'myaccount' not in host and 'clone' not in host:
                        logger.info("Connecting to " + host)
                    if browser:
                        from ltk.auth import run_oauth
                        access_token = run_oauth(host, client_id)
                        ran_oauth = True
                    else:
                        logger.info('---------------------------')
                        logger.info('CONNECT TO LINGOTEK')
                        logger.info('---------------------------')
                        self.api = ApiCalls(host, '')
                        # Python 2
                        # username = raw_input('Username: ')
                        # End Python 2
                        # Python 3
                        username = input('Lingotek Username: ')
                        # End Python 3
                        password = getpass.getpass()
                        if 'myaccount.lingotek.com' in host:
                            login_host = 'https://sso.lingotek.com'
                        elif 'clone.lingotek.com' in host:
                            login_host = 'https://clonesso.lingotek.com'
                        else:
                            if (host.find('sso') != -1):
                                host_env = host.split('sso')[0]
                                login_host = host_env + 'sso.lingotek.com'
                            else:
                                host_env = host.split('.')[0]
                                login_host = host_env + 'sso.lingotek.com'
                            print(login_host)
                        if self.api.login(login_host, username, password):
                            retrieved_token = self.api.authenticate(login_host)
                            if retrieved_token:
                                print('\nAuthentication successful\n')
                                access_token = retrieved_token
                                ran_oauth = True
                        if not ran_oauth:
                            print('Authentication failed.  Initialization canceled.')
                            return
            # print("access_token: "+str(access_token))
            if ran_oauth:
                # create or overwrite global file
                self.create_global(access_token, host)

            self.api = ApiCalls(host, access_token)
            # create a directory
            try:
                if not os.path.isdir(os.path.join(project_path, CONF_DIR)):
                    os.mkdir(os.path.join(project_path, CONF_DIR))

                # if on Windows system, set directory properties to hidden
                if os.name == 'nt':
                    try:
                        subprocess.call(["attrib", "+H", os.path.join(project_path, CONF_DIR)])
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logger.error("Error on init: "+str(e))
                    # # Python 2
                    # # ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(os.path.join(project_path, CONF_DIR)), HIDDEN_ATTRIBUTE)
                    # # End Python 2
                    # # Python 3
                    # ret = ctypes.windll.kernel32.SetFileAttributesW(os.path.join(project_path, CONF_DIR), HIDDEN_ATTRIBUTE)
                    # # End Python 3
                    # if(ret != 1):   # return value of 1 signifies success
                    #     pass

            except OSError as e:
                #logger.info(e)
                pass
            except IOError as e:
                print(e.errno)
                print(e)

            logger.info('Initializing project...\n')
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            # create the config file and add info
            config_file = open(config_file_name, 'w')

            self.config_parser = ConfigParser()
            self.config_parser.add_section('main')
            self.config_parser.set('main', 'access_token', access_token)
            self.config_parser.set('main', 'host', host)
            # self.config_parser.set('main', 'root_path', project_path)
            # get community id
            community_info = self.api.get_communities_info()
            if not community_info:
                from ltk.auth import run_oauth
                access_token = run_oauth(host, client_id)
                self.create_global(access_token, host)
                community_info = self.api.get_communities_info()
                if not community_info:
                    raise exceptions.RequestFailedError("Unable to get user's list of communities")

            if len(community_info) == 0:
                raise exceptions.ResourceNotFound('You are not part of any communities in Lingotek Cloud')
            if len(community_info) > 1:
                logger.info('---------------------------')
                logger.info('SELECT LINGOTEK COMMUNITY')
                logger.info('---------------------------')
                community_id, community_name = self.display_choice('community', community_info)
            else:
                for id in community_info:
                    community_id = id
                #community_id = community_info.iterkeys().next()  --- iterkeys() is not in python 3
            if community_id != None:
                self.config_parser.set('main', 'community_id', community_id)
                response = self.api.list_projects(community_id)
                if response.status_code == 204:#no projects in community
                    project_info = []
                elif response.status_code == 200:
                    project_info = self.api.get_project_info(community_id)
                else:
                    try:
                        raise_error(response.json(), 'Something went wrong trying to find projects in your community')
                    except:
                        logger.error('Something went wrong trying to find projects in your community')
                        return
                project_id = None
                project_name = None
                confirm = 'none'
                logger.info('---------------------------')
                logger.info('SELECT LINGOTEK PROJECT')
                logger.info('---------------------------')
                if len(project_info) > 0:
                    project_id, project_name = self.display_choice('project', project_info)
                else:
                    logger.info('There are no projects')
                if project_id != None:
                    self.config_parser.set('main', 'project_id', project_id)
                    if project_name != None:
                        self.config_parser.set('main', 'project_name', project_name)
                if not project_id:
                    project_id, project_name = self.create_new_project(folder_name, community_id, workflow_id)
                    self.config_parser.set('main', 'project_id', project_id)
                    self.config_parser.set('main', 'project_name', project_name)

                # get workflow
                logger.info('---------------------------------------------------------------')
                logger.info('SELECT WORKFLOW TEMPLATE TO COPY AS A NEW PROJECT WORKFLOW')
                logger.info('---------------------------------------------------------------')
                workflow_id, workflow_updated = self.set_workflow(community_id, project_id)
                if(workflow_updated):
                    self.api.patch_project(project_id, workflow_id)
                self.config_parser.set('main', 'workflow_id', workflow_id)

                # print out locale codes
                logger.info('---------------------------')
                logger.info('SET SOURCE LANGUAGE')
                logger.info('---------------------------')
                self.locale_info = self.print_locale_codes()

                # get source locale
                selected_source_locale = self.set_source_locale()
                self.config_parser.set('main', 'default_locale', selected_source_locale)

                # get target locale(s)
                target_locales = self.set_target_locales()
                self.config_parser.set('main', 'watch_locales', target_locales)

                # get download location
                download_path = self.set_download_path(project_path)
                self.config_parser.set('main', 'download_folder', download_path)

                # get most recent document
                always_check_latest_doc = yes_no_prompt('Always check for the latest document?', default_yes=False)
                if always_check_latest_doc:
                    check = 'on'
                else:
                    check = 'off'
                self.config_parser.set('main', 'always_check_latest_doc', check)
                # ask about advanced settings
                if yes_no_prompt('Would you like to configure advanced options?', default_yes=False):
                    self.show_advanced_settings()

                logger.info("\nAll finished. Use ltk -h to learn more about using Lingotek Filesystem Connector.")
                self.config_parser.write(config_file)
                config_file.close()
        except KeyboardInterrupt:
            # Python 2
            # logger.info("\nInit canceled")
            # End Python 2
            # Python 3
            logger.error("\nInit canceled")
            # End Python 3
            return
        except Exception as e:
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on init: "+str(e))

    def show_advanced_settings(self):
        # git auto-commit
        username, encrypted_password = self.set_git_autocommit()
        if not username == None and not encrypted_password == None:
            self.config_parser.set('main', 'git_autocommit', 'on')
            self.config_parser.set('main', 'git_username', username)
            self.config_parser.set('main', 'git_password', encrypted_password)
        else:
            self.config_parser.set('main', 'git_autocommit', 'off')
            self.config_parser.set('main', 'git_username', '')
            self.config_parser.set('main', 'git_password', '')

        # toggle clone on/off
        print("\n--------------------------------")
        print("CLONE OPTION:")
        print("Toggle clone download option \'on\' and \'off\'.\n\nTurning clone \'on\': Translations will be downloaded to a cloned folder structure, where the root folder for each locale is the locale folder specified in config or a locale folder inside of the default download folder. If a default download folder is not set, then translations will be downloaded to the directory where the project was initialized.\n\nTurning clone \'off\': If a download folder is specified, downloaded translations will download to that folder, but not in a cloned folder structure. If no download folder is specified, downloaded translations will go to the same folder as their corresponding source files.")
        self.turn_clone_on = self.set_clone_option()
        if self.turn_clone_on:
            self.config_parser.set('main', 'clone_option', 'on')
        else:
            self.config_parser.set('main', 'clone_option', 'off')

        # toggle auto-format on/off
        print("--------------------------------")
        print("AUTO-FORMAT:")
        print("Toggle auto format option \'on\' and \'off\'. Applies formatting during download.")
        turn_auto_format_on = self.set_auto_format_option()
        if turn_auto_format_on:
            self.config_parser.set('main', 'auto_format', 'on')
        else:
            self.config_parser.set('main', 'auto_format', 'off')

        # change append options
        print("--------------------------------")
        print("APPEND OPTION:")
        print('Change the format of the default name given to documents on the Lingotek system.\nDefine file information to append to document names as none, full, number:+a number of folders down to include (e.g. number:2), or name:+a name of a directory to start after if found in file path (e.g. name:dir). Default option is none.')
        append_option = self.set_append_option()
        if not append_option == None:
            self.config_parser.set('main', 'append_option', append_option)

        # Toggle finalized file download option
        print("\n--------------------------------")
        print("DOWNLOAD FINALIZED FILE:")
        print("Toggle finalized file download option 'on' or 'off'. Turning this option on downloads the finalized file instead of the raw translation. " +
              "A finalized file is typically a file that has undergone some sort of post editing like Desktop Publishing after the translation has completed.")
        self.finalized_file = self.set_finalized_file_option()
        self.config_parser.set('main', 'finalized_file', self.finalized_file)

        if self.finalized_file == 'on':
            print("\n--------------------------------")
            print("UNZIP FINALIZED FILE:")
            print("Toggle UNZIP finalized file option 'on' or 'off'. Turning this option on unzips the file from TMS. Turning it off leaves the file unzipped.")
            self.unzip_file = self.prompt_unzip_file_option()
            self.config_parser.set('main', 'unzip_file', self.unzip_file)

        # Set default metadata
        print("--------------------------------")
        print("METADATA:")
        self.set_metadata_defaults()
        print('')
        self.set_metadata_prompt()
        print('')
        self.set_metadata_fields()

    def check_global(self, host):
        # check for a global config file and return the access token
        home_path = os.path.expanduser('~')
        sys_file = os.path.join(home_path, SYSTEM_FILE)
        if os.path.isfile(sys_file):
            # get the access token
            print("Using configuration in file "+str(sys_file))
            conf_parser = ConfigParser()
            conf_parser.read(sys_file)
            if conf_parser.has_section(host) and conf_parser.get(host, 'host') == host:
                return conf_parser.get(host, 'access_token')

        return None

    def display_choice(self, display_type, info, w_id='Project Default'):
        if display_type == 'community':
            prompt_message = 'Select Lingotek Community ID: '
        elif display_type == 'project':
            prompt_message = 'Select Project ID [create new]: '
        elif display_type == 'append option':
            prompt_message = 'Which append option should be used? '
        else:
            raise exceptions.ResourceNotFound("Cannot display info asked for")
        mapper = choice_mapper(info)
        choice = 'none-chosen'
        if display_type != 'workflow':
            while choice not in mapper:
                # Python 2
                # choice = raw_input(prompt_message)
                # End Python 2
                # Python 3
                choice = input(prompt_message)
                # End Python 3
                try:
                    if display_type == 'project':
                        if choice == '':
                            return None, None
                        else:
                            choice = int(choice)
                    else:
                        choice = int(choice)
                except ValueError:
                    print("That's not a valid option!")
        for v in mapper[choice]:
            print(v)
            logger.info('\nSelected "{0}" {1}.\n'.format(mapper[choice][v], display_type))
            return v, mapper[choice][v]

    def reinit(self, host, project_path, delete, reset):
        if is_initialized(project_path) and not reset:
            logger.warning('This project is already initialized!')
            if not delete:
                return False
            option = yes_no_prompt("Are you sure you want to delete the current project? " + \
                    "This will also delete the project in your community.", default_yes=True)
            # confirm if deleting existing folder
            if option:
                # delete the corresponding project online
                logger.info('Deleting old project folder and creating new one...')
                config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
                if os.path.isfile(config_file_name):
                    old_config = ConfigParser()
                    old_config.read(config_file_name)
                    project_id = old_config.get('main', 'project_id')
                    access_token = old_config.get('main', 'access_token')
                    self.api = ApiCalls(host, access_token)
                    response = self.api.delete_project(project_id)
                    if response.status_code != 204 and response.status_code != 404:
                        try:
                            error = response.json()['messages'][0]
                            raise exceptions.RequestFailedError(error)
                        except (AttributeError, IndexError):
                            raise exceptions.RequestFailedError("Failed to delete and re-initialize project")
                    # delete existing folder
                    to_remove = os.path.join(project_path, CONF_DIR)
                    shutil.rmtree(to_remove)
                else:
                    raise exceptions.ResourceNotFound("Cannot find config file, please re-initialize project")
                return access_token
            else:
                return False
        return True

    def create_global(self, access_token, host):
        """
        create a .lingotek file in user's $HOME directory
        """
        try:
            # go to the home dir
            home_path = os.path.expanduser('~')
            file_name = os.path.join(home_path, SYSTEM_FILE)
            global_parser = ConfigParser()
            if os.path.isfile(file_name):
                global_parser.read(file_name)
                # if on Windows, temporarily unhide the .lingotek file so we can write to it
                if os.name == 'nt':
                    try:
                        subprocess.call(["attrib", "-H", file_name])
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logger.error("Error on init: "+str(e))
            sys_file = open(file_name, 'w')

            if global_parser.has_section(host):
                global_parser.set(host, 'access_token', access_token)
                global_parser.set(host, 'host', host)
            else:
                global_parser.add_section(host)
                global_parser.set(host, 'access_token', access_token)
                global_parser.set(host, 'host', host)

            global_parser.write(sys_file)
            sys_file.close()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("Error on init: "+str(e))
        # # if on Windows, set file properties to hidden
        if os.name == 'nt':
            try:
                subprocess.call(["attrib", "+H", file_name])
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error("Error on init: "+str(e))

    def create_new_project(self, folder_name, community_id, workflow_id):
        prompt_message = "Please enter a new Lingotek project name [%s]: " % folder_name
        # Python 2
        # project_name = raw_input(prompt_message)
        # End Python 2
        # Python 3
        project_name = input(prompt_message)
        # End Python 3
        if not project_name:
            project_name = folder_name
        response = self.api.add_project(project_name, community_id, workflow_id)
        if response.status_code != 201:
            try:
                raise_error(response.json(), 'Failed to add current project to Lingotek Cloud')
            except:
                logger.error('Failed to add current project to Lingotek Cloud')
                return
        project_id = response.json()['properties']['id']

        return project_id, project_name


    def set_workflow(self, community_id, project_id):
        response = self.api.list_workflows(community_id)
        workflows = response.json()['entities']
        workflow_info = {}

        for workflow in workflows:
            workflow_info[workflow['properties']['id']] = workflow['properties']['title']

        if len(workflow_info) > 0:
            confirm = 'none'
            mapper = choice_mapper(workflow_info)
            choice = 'none-chosen'
            prompt_message = 'Select workflow ID [Project Default]: '
            # Python 2
            # choice = raw_input(prompt_message)
            # End Python 2
            # Python 3
            choice = input(prompt_message)
            # End Python 3
            try:
                if choice == '':
                    workflow_id, workflow_name = 'Project Default', 'Project Default'
                    logger.info('\nKept "{0}" {1}.\n'.format(workflow_name, 'workflow'))
                    return workflow_id, False 
                else:
                    choice = int(choice)
                    for v in mapper[choice]:
                        print(v)
                        logger.info('\nSelected "{0}" {1}.\n'.format(mapper[choice][v], 'workflow'))   
                        workflow_id, workflow_name = v, mapper[choice][v]
                        return workflow_id, True
            except ValueError:
                print('Not a valid option')

    def print_locale_codes(self):
        locale_info = []
        response = self.api.list_locales()
        if response.status_code != 200:
            raise exceptions.RequestFailedError("Failed to get locale codes")
        locale_json = response.json()['entities']
        locale_dict = {}
        for entry in locale_json:
            locale_code = entry['properties']['code']
            language = entry['properties']['language']
            country = entry['properties']['country']
            locale_info.append((locale_code, language, country))
            locale_dict[locale_code] = (language, country),

        locale_info = sorted(locale_info)
        table = []
        for locale in locale_info:
            if not len(locale[2]):  # Arabic
                table.append(["{0}".format(locale[0]), "{0}".format(locale[1])])
            else:
                table.append(["{0}".format(locale[0]), "{0}, {1}".format(locale[1], locale[2])])
        print(tabulate(table, headers=["Code", "Locale Name"]))
        return locale_dict

    def set_source_locale(self):
        selected_locale = ''
        keep_prompting = True
        while selected_locale not in self.locale_info.keys():
            prompt_message = '\nWhat is the default locale for your source content? [en-US]: '
            # Python 2
            # locale = raw_input(prompt_message)
            # End Python 2
            # Python 3
            locale = input(prompt_message)
            # End Python 3
            if(locale == ''):
                selected_locale = 'en-US'
                keep_prompting = False
            else:
                if(locale not in self.locale_info.keys()):
                    logger.warning('\'{0}\' is not a valid locale'.format(locale))
                else:
                    selected_locale = locale
                    keep_prompting = False

        logger.info("Set source locale to: {0}\n".format(selected_locale))
        return selected_locale

    def set_target_locales(self):
        user_input = 'not given'
        locales = []
        prompt_for_input = True
        while prompt_for_input:
            prompt_message = 'What default target locales would you like to translate into (e.g. fr-FR, ja-JP)? [None]: '
            # Python 2
            # user_input = raw_input(prompt_message)
            # End Python 2
            # Python 3
            user_input = input(prompt_message)
            # End Python 3
            if(user_input == '' or user_input == 'none'):
                prompt_for_input = False
            else:
                locales = user_input.replace(" ", "").split(",")

                prompt_for_input = False
                # make sure the locales given are valid
                for l in locales:
                    if l not in self.locale_info:
                        print("Please provide valid locales as a comma seperated list (e.g. fr-FR, ja-JP)\n")
                        prompt_for_input = True

        if(user_input == 'none' or user_input == ''):
            logger.info("Set target locales to: None\n")
            return ""
        elif(len(locales) > 0):
            logger.info("Set target locales to: {0}\n".format(', '.join(locales)))
            return ','.join(locales)

    def set_download_path(self, project_path):
        download_path = ''
        keep_prompting = True
        while keep_prompting:
            prompt_message = 'Where would you like translations to be downloaded? [.]: '
            # Python 2
            # path = raw_input(prompt_message)
            # End Python 2
            # Python 3
            path = input(prompt_message)
            # End Python 3

            if(path == '' or path == '.'):
                # set download path to the current directory
                download_path = self.norm_path(project_path, '.')
            else:
                download_path = self.norm_path(project_path, path)

            if os.path.exists(os.path.join(project_path, download_path)):
                if(path == '' or path == '.'):
                    logger.info("Set download folder to the current working directory\n")
                else:
                    logger.info("Set download folder to: {0}\n".format(download_path))

                keep_prompting = False
            else:
                logger.warning('Error: The folder {0} does not exist\n'.format(os.path.join(project_path,download_path)))

        return download_path

    def norm_path(self, project_path, file_location):
        # print("original path: "+str(file_location))
        if file_location:
            file_location = os.path.normpath(file_location)
            # abspath=os.path.abspath(file_location)
            # print("abspath: "+str(os.path.abspath(os.path.expanduser(file_location))))
            # print("self.path: "+self.path)
            # print("cwd: "+str(os.getcwd()))
            norm_path = os.path.abspath(os.path.expanduser(file_location)).replace(self.path, '')
            # print("normalized path: "+norm_path)
            # print("joined path: "+str(os.path.join(self.path,file_location)))
            # if file_location == ".." and self.path.rstrip('/') in norm_path:
            #     return norm_path.replace(self.path.rstrip('/'), '')
            if file_location is not "." and ".." not in file_location and os.path.exists(os.path.join(self.path,file_location)):
                # print("returning original path: "+str(file_location))
                return file_location.replace(self.path, '')
            elif ".." in file_location and file_location != "..":
                # print("returning norm path: "+norm_path)
                return norm_path.replace(self.path,'')
            if not os.path.exists(os.path.join(self.path,norm_path)) and os.path.exists(os.path.join(self.path,file_location)):
                # print("Starting path at project directory: "+file_location.replace(self.path, ''))
                return os.path.abspath(os.path.expanduser(file_location.replace(self.path, ''))).replace(self.path, '')
            elif file_location == "..":
                return os.path.abspath(os.path.expanduser(file_location.replace(self.path, ''))).replace(self.path, '')
            return norm_path
        else:
            return None
#This can never be reached.  Commenting it out for now
#        # go to the home dir
#        home_path = os.path.expanduser('~')
#        file_name = os.path.join(home_path, SYSTEM_FILE)
#        self.config_parser = ConfigParser()
#        if os.path.isfile(file_name):
#            self.config_parser.read(file_name)
#        sys_file = open(file_name, 'w')
#
#        if self.config_parser.has_section(host):
#            self.config_parser.set(host, 'access_token', access_token)
#            self.config_parser.set(host, 'host', host)
#        else:
#            self.config_parser.add_section(host)
#            self.config_parser.set(host, 'access_token', access_token)
#            self.config_parser.set(host, 'host', host)
#
#        self.config_parser.write(sys_file)
#        sys_file.close()

    def set_git_autocommit(self):
        if not(os.name == 'nt'):
            option = yes_no_prompt('Would you like to use Git auto-commit?', default_yes=False)
            if option:
                # get git credentials
                return self.get_git_credentials()

        return None, None

    def get_git_credentials(self):
        git_username = None
        encrypted_password = None

        if not os.name == 'nt':
            # Python 2
            # git_username = raw_input('Username: ')
            # End Python 2
            # Python 3
            git_username = input('Username: ')
            # End Python 3
            git_password = getpass.getpass()
            if git_username in ['None', 'none', 'N', 'n', '--none']:
                git_username = ""
                # log_info = "Git username disabled"
            else:
                log_info = 'Git username set to ' + git_username
            # self.update_config_file('git_username', git_username, self.conf_parser, self.config_file_name, log_info)
            if git_password in ['None', 'none', 'N', 'n', '--none']:
                git_password = ""
                # log_info = "Git password disabled"
            else:
                log_info = 'Git password set'
            # self.update_config_file('git_password', self.git_auto.encrypt(git_password), self.conf_parser, self.config_file_name, log_info)
        # else:
        #     error("Only SSH Key access is enabled on Windows")
        #     git_username = ""
        #     git_password = ""

        if not encrypted_password == None:
            git_auto = Git_Auto(self.path)
            encrypted_password = git_auto.encrypt(git_password)

        return git_username, encrypted_password

    def set_clone_option(self):
        turn_clone_on = True
        confirm = 'none'
        while confirm != 'on' and confirm != 'On' and confirm != 'ON' and confirm != 'off' and confirm != 'Off' and confirm != '':
            prompt_message = 'Would you like to turn clone on or off? [ON/off]: '
            # Python 2
            # confirm = raw_input(prompt_message)
            # End Python 2
            # Python 3
            confirm = input(prompt_message)
            # End Python 3
            if confirm in ['on', 'On', 'ON', 'off', 'Off', '']:
                if confirm in ['on', 'On', 'ON', '']:
                    logger.info("Clone set to ON\n")
                    turn_clone_on = True
                    return turn_clone_on
                else:
                    logger.info("Clone set to OFF\n")
                    turn_clone_on = False
                    return turn_clone_on

        return turn_clone_on

    def set_auto_format_option(self):
        turn_auto_format_on = True
        confirm = 'none'
        while confirm != 'on' and confirm != 'On' and confirm != 'ON' and confirm != 'off' and confirm != 'Off' and confirm != '':
            prompt_message = 'Would you like to turn auto-format on or off? [ON/off]: '
            # Python 2
            # confirm = raw_input(prompt_message)
            # End Python 2
            # Python 3
            confirm = input(prompt_message)
            # End Python 3
            if confirm in ['on', 'On', 'ON', 'off', 'Off', '']:
                if confirm in ['on', 'On', 'ON', '']:
                    logger.info("Auto format set to ON\n")
                    turn_auto_format_on = True
                    return turn_auto_format_on
                else:
                    logger.info("Auto format set to OFF\n")
                    turn_auto_format_on = False
                    return turn_auto_format_on

        return turn_auto_format_on

    def set_append_option(self):
        append_option = None
        option = yes_no_prompt('Would you like to change the append options?', default_yes=False)
        if option:
            option = self.get_user_append_option()
            return append_option

        return None

    def get_user_append_option(self):
        option = 'not chosen'
        while not 'none' in option or not 'full' in option or not 'name' in option:
            prompt_message = 'Input the append option you would like to use: '
            # Python 2
            # confirm = raw_input(prompt_message)
            # End Python 2
            # Python 3
            option = input(prompt_message)
            # End Python 3
            if self.validate_append_option(option) == True:
                logger.info("Append option set to \'{0}\'\n".format(option))
                return option

    def validate_append_option(self, append_option):
        if append_option in {'none', 'full'} or append_option[:append_option.find(':')+1] in {'number:', 'name:'}:
            if append_option[:3] == 'num':
                try: int(append_option[7:])
                except ValueError:
                    logger.warning('Error: Input after "number" must be an integer')
                    return False
                return True
            elif append_option[:4] == 'name' and len(append_option) <= 5:
                logger.warning('Error: No input given after "name"')
                return False
            else:
                return True
        else:
            logger.warning('Error: Not a valid option')
            return False

    def set_finalized_file_option(self):
        finalized_file = 'off'
        confirm = 'none'
        while confirm.lower() not in ['on', 'off', '']:
            prompt_message = 'Would you like to turn finalized file download on or off? [on/OFF]: '
            # Python 2
            # confirm = raw_input(prompt_message)
            # End Python 2
            # Python 3
            confirm = input(prompt_message)
            # End Python 3
        if confirm.lower() == 'on':
            logger.info("Finalized file download set to ON\n")
            finalized_file = 'on'
        else:
            logger.info("Finalized file download set to OFF\n")
            finalized_file = 'off'

        return finalized_file

    def prompt_unzip_file_option(self):
        unzip_file = 'on'
        confirm = 'none'
        while confirm != 'on' and confirm != 'On' and confirm != 'ON' and confirm != 'off' and confirm != 'Off' and confirm != '':
            prompt_message = 'Would you like to turn finalized file UNZIP on or off? [ON/off]: '
            # Python 2
            # confirm = raw_input(prompt_message)
            # End Python 2
            # Python 3
            confirm = input(prompt_message)
            # End Python 3
            if confirm in ['on', 'On', 'ON', 'off', 'Off', '']:
                if confirm in ['on', 'On', 'ON', '']:
                    logger.info("Finalized file UNZIP set to ON\n")
                    unzip_file = 'on'
                else:
                    logger.info("Finalized file UNZIP set to OFF\n")
                    unzip_file = 'off'

        return unzip_file

    def set_metadata_defaults(self):
        print("Set default metadata to be sent with every document that is uploaded to Lingotek.")
        option = yes_no_prompt('Would you like to set default metadata?', default_yes=True)
        if option:
            Action.default_metadata = {}
            metadata = Action.metadata_wizard(Action, set_defaults=True)
        else:
            metadata = {}
        self.config_parser.set('main', 'default_metadata', json.dumps(metadata))
        logger.info("Default metadata set to {0}".format(metadata))

    def set_metadata_prompt(self):
        print("Toggle an automatic prompt for metadata with every document upload/update.  Turning this on will display a prompt every time an add or push command is run that asks if metadata should be sent, and if it should be sent, it gives the option to define the metadata.  Leaving this off will require a command flag to be used to send metadata.")
        option = yes_no_prompt('Would you like to always prompt for metadata?', default_yes=False)
        if option:
            self.config_parser.set('main', 'metadata_prompt', 'on')
            logger.info("Metadata prompting set to ON")
        else:
            self.config_parser.set('main', 'metadata_prompt', 'off')
            logger.info("Metadata prompting set to OFF")

    def set_metadata_fields(self):
        print("Set the fields that will be displayed when adding, editing, and viewing document metadata.  The possible fields are:\n")
        print(', '.join(str(field) for field in METADATA_FIELDS)+"\n")
        valid = False
        while not valid:
            prompt_message = "Enter a comma-separated list of fields to include, or enter 'all' to include all the fields [all]: "
            # Python 2
            # options = raw_input(prompt_message)
            # End Python 2
            # Python 3
            options = input(prompt_message)
            # End Python 3
            valid, fields = Action.validate_metadata_fields(Action, options)
        self.config_parser.set('main', 'metadata_fields', json.dumps(fields))
        logger.info("Metadata fields set to {0}".format(fields))