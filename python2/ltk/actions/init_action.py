''' Python Dependencies '''
import ctypes

''' Internal Dependencies '''
from ltk.actions.action import *

''' Globals '''
HIDDEN_ATTRIBUTE = 0x02

class InitAction():
    '''def __init__(self, path):
        #Action.__init__(self, path)'''

    def init_action(self, host, access_token, client_id, project_path, folder_name, workflow_id, locale, browserless, delete, reset):
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
                    if not browserless:
                        from ltk.auth import run_oauth
                        access_token = run_oauth(host, client_id)
                        ran_oauth = True
                    else:
                        api = ApiCalls(host, '')
                        # Python 2
                        username = raw_input('Username: ')
                        # End Python 2
                        # Python 3
#                         username = input('Username: ')
                        # End Python 3
                        password = getpass.getpass()
                        login_host = 'https://sso.lingotek.com' if 'myaccount' in host else 'https://cmssso.lingotek.com'

                        if api.login(login_host, username, password):
                            retrieved_token = api.authenticate(login_host)
                            if retrieved_token:
                                print('Authentication successful')
                                access_token = retrieved_token
                                ran_oauth = True
                        if not ran_oauth:
                            print('Authentication failed.  Initialization canceled.')
                            return
            # print("access_token: "+str(access_token))
            if ran_oauth:
                # create or overwrite global file
                self.create_global(access_token, host)

            api = ApiCalls(host, access_token)
            # create a directory
            try:
                if not os.path.isdir(os.path.join(project_path, CONF_DIR)):
                    os.mkdir(os.path.join(project_path, CONF_DIR))

                # if on Windows system, set directory properties to hidden
                if os.name == 'nt':
                    # Python 2
                    ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(os.path.join(project_path, CONF_DIR)), HIDDEN_ATTRIBUTE)
                    # End Python 2
                    # Python 3
#                     ret = ctypes.windll.kernel32.SetFileAttributesW(os.path.join(project_path, CONF_DIR), HIDDEN_ATTRIBUTE)
                    # End Python 3
                    if(ret != 1):   # return value of 1 signifies success
                        pass

            except OSError as e:
                #logger.info(e)
                pass

            logger.info('Initializing project...')
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            # create the config file and add info
            config_file = open(config_file_name, 'w')

            config_parser = ConfigParser()
            config_parser.add_section('main')
            config_parser.set('main', 'access_token', access_token)
            config_parser.set('main', 'host', host)
            # config_parser.set('main', 'root_path', project_path)
            config_parser.set('main', 'workflow_id', workflow_id)
            config_parser.set('main', 'default_locale', locale)
            config_parser.set('main', 'git_autocommit', 'False')
            config_parser.set('main', 'git_username', '')
            config_parser.set('main', 'git_password', '')
            # get community id
            community_info = api.get_communities_info()
            if not community_info:
                from ltk.auth import run_oauth
                access_token = run_oauth(host, client_id)
                self.create_global(access_token, host)
                community_info = api.get_communities_info()
                if not community_info:
                    raise exceptions.RequestFailedError("Unable to get user's list of communities")

            if len(community_info) == 0:
                raise exceptions.ResourceNotFound('You are not part of any communities in Lingotek Cloud')
            if len(community_info) > 1:
                community_id, community_name = self.display_choice('community', community_info)
            else:
                for id in community_info:
                    community_id = id
                #community_id = community_info.iterkeys().next()  --- iterkeys() is not in python 3
            if community_id != None:
                config_parser.set('main', 'community_id', community_id)
                response = api.list_projects(community_id)
                if response.status_code == 204:#no projects in community
                    project_info = []
                elif response.status_code == 200:
                    project_info = api.get_project_info(community_id)
                else:
                    try:
                        raise_error(response.json(), 'Something went wrong trying to find projects in your community')
                    except:
                        logger.error('Something went wrong trying to find projects in your community')
                        return
                if len(project_info) > 0:
                    confirm = 'none'
                    try:
                        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                            prompt_message = 'Would you like to use an existing Lingotek project? [Y/n]: '
                            # Python 2
                            confirm = raw_input(prompt_message)
                            # End Python 2
                            # Python 3
#                             confirm = input(prompt_message)
                            # End Python 3
                        if not confirm or not confirm in ['n', 'N', 'no', 'No']:
                            project_id, project_name = self.display_choice('project', project_info)
                            if project_id != None:
                                config_parser.set('main', 'project_id', project_id)
                                if project_name != None:
                                    config_parser.set('main', 'project_name', project_name)
                                config_parser.write(config_file)
                                config_file.close()
                            return
                    except KeyboardInterrupt:
                        # Python 2
                        logger.info("\nInit canceled")
                        # End Python 2
                        # Python 3
#                         logger.error("\nInit canceled")
                        # End Python 3
                        return
                prompt_message = "Please enter a new Lingotek project name: %s" % folder_name + chr(8) * len(folder_name)
                try:
                    # Python 2
                    project_name = raw_input(prompt_message)
                    # End Python 2
                    # Python 3
#                     project_name = input(prompt_message)
                    # End Python 3
                except KeyboardInterrupt:
                    # Python 2
                    logger.info("\nInit canceled")
                    # End Python 2
                    # Python 3
#                     logger.error("\nInit canceled")
                    # End Python 3
                    return
                if not project_name:
                    project_name = folder_name
                response = api.add_project(project_name, community_id, workflow_id)
                if response.status_code != 201:
                    try:
                        raise_error(response.json(), 'Failed to add current project to Lingotek Cloud')
                    except:
                        logger.error('Failed to add current project to Lingotek Cloud')
                        return
                project_id = response.json()['properties']['id']
                config_parser.set('main', 'project_id', project_id)
                config_parser.set('main', 'project_name', project_name)

                config_parser.write(config_file)
                config_file.close()
        except KeyboardInterrupt:
            # Python 2
            logger.info("\nInit canceled")
            # End Python 2
            # Python 3
#             logger.error("\nInit canceled")
            # End Python 3
            return
        except Exception as e:
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on init: "+str(e))

    def check_global(self, host):
        # check for a global config file and return the access token
        home_path = os.path.expanduser('~')
        sys_file = os.path.join(home_path, SYSTEM_FILE)
        if os.path.isfile(sys_file):
            # get the access token
            print("Using configuration in file "+str(sys_file))
            conf_parser = ConfigParser()
            conf_parser.read(sys_file)
            if conf_parser.has_section('alternative') and conf_parser.get('alternative', 'host') == host:
                return conf_parser.get('alternative', 'access_token')
            if conf_parser.has_section('main'):
                if not conf_parser.has_option('main','host') or conf_parser.get('main', 'host') == host:
                    return conf_parser.get('main', 'access_token')
        else:
            return None

    def display_choice(self, display_type, info):
        if display_type == 'community':
            prompt_message = 'Which community should this project belong to? '
        elif display_type == 'project':
            prompt_message = 'Which existing project should be used? '
        else:
            raise exceptions.ResourceNotFound("Cannot display info asked for")
        mapper = choice_mapper(info)
        choice = 'none-chosen'
        while choice not in mapper:
            try:
                # Python 2
                choice = raw_input(prompt_message)
                # End Python 2
                # Python 3
#                 choice = input(prompt_message)
                # End Python 3
            except KeyboardInterrupt:
                # Python 2
                logger.info("\nInit canceled")
                # End Python 2
                # Python 3
#                 logger.error("\nInit canceled")
                # End Python 3
                #testing
                return None, None
                #end testing
            try:
                choice = int(choice)
            except ValueError:
                print("That's not a valid option!")
        for v in mapper[choice]:
            logger.info('Selected "{0}" {1}.'.format(mapper[choice][v], display_type))
            return v, mapper[choice][v]

    def reinit(self, host, project_path, delete, reset):
        if is_initialized(project_path) and not reset:
            logger.warning('This project is already initialized!')
            if not delete:
                return False
            try:
                confirm = 'not confirmed'
                while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                    prompt_message = "Are you sure you want to delete the current project? " + \
                        "This will also delete the project in your community. [Y/n]: "
                    # Python 2
                    confirm = raw_input(prompt_message)
                    # End Python 2
                    # Python 3
#                     confirm = input(prompt_message)
                    # End Python 3
            except KeyboardInterrupt:
                # Python 2
                logger.info("\nRenit canceled")
                # End Python 2
                # Python 3
#                 logger.error("\nReinit canceled")
                # End Python 3
                return
            # confirm if deleting existing folder
            if not confirm or confirm in ['n', 'N']:
                return False
            else:
                # delete the corresponding project online
                logger.info('Deleting old project folder and creating new one...')
                config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
                if os.path.isfile(config_file_name):
                    old_config = ConfigParser()
                    old_config.read(config_file_name)
                    project_id = old_config.get('main', 'project_id')
                    access_token = old_config.get('main', 'access_token')
                    api = ApiCalls(host, access_token)
                    response = api.delete_project(project_id)
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
        return True

    def create_global(self, access_token, host):
        """
        create a .lingotek file in user's $HOME directory
        """
        # go to the home dir
        home_path = os.path.expanduser('~')
        file_name = os.path.join(home_path, SYSTEM_FILE)
        config_parser = ConfigParser()
        if os.path.isfile(file_name):
            config_parser.read(file_name)
        sys_file = open(file_name, 'w')
        if config_parser.has_section('main'):
            if not config_parser.has_option('main', host) and config_parser.has_option('main', 'access_token') and config_parser.get('main', 'access_token') == access_token:
                config_parser.set('main', 'host', host)
            elif config_parser.has_option('main', host) and config_parser.get('main', host) == host:
                config_parser.set('main', 'access_token', access_token)
            else:
                if config_parser.has_section('alternative') and config_parser.has_option('alternative', 'host') and config_parser.get('alternative', 'host') == host:
                    config_parser.set('alternative','access_token', access_token)
                config_parser.add_section('alternative')
                config_parser.set('alternative', 'access_token', access_token)
                config_parser.set('alternative', 'host', host)
        else:
            config_parser.add_section('main')
            config_parser.set('main', 'access_token', access_token)
            config_parser.set('main', 'host', host)
        config_parser.write(sys_file)
        sys_file.close()

        # if on Windows system, set file properties to hidden
        if os.name == 'nt':
            # Python 2
            ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(file_name), HIDDEN_ATTRIBUTE)
            # End Python 2
            # Python 3
#             ret = ctypes.windll.kernel32.SetFileAttributesW(file_name, HIDDEN_ATTRIBUTE)
            # End Python 3
            if(ret != 1):   # return value of 1 signifies success
                pass
