''' Python Dependencies '''
import ctypes
import winshell

''' Internal Dependencies '''
from ltk import apicalls
from ltk.actions.action import *
from ltk.actions.config_action import ConfigAction
from ltk.constants import CONF_DIR, ERROR_FN, LOG_FN, EXE_FN, PROGRAM_FILES_FN
from ltk.logger import logger, API_LOG_LEVEL, API_RESPONSE_LOG_LEVEL, CustomFormatter
from utils import set_run_key

''' Globals'''
HIDDEN_ATTRIBUTE = 0x02

class InitActionGUI():
    def __init__(self, path):
        # Action.__init__(self, path)
        self.project_path = path
        self.access_token = ""
        self.communities = None
        self.projects = None
        self.project_info = None
        self.workflows = None
        self.workflow_titles = None
        self.community_id = ""
        self.project_id = ""
        self.workflow_id = ""
        self.apiCall = None
        self.config_parser = ConfigParser()
        self.has_global = False

# Is this nessecary in python or can you just set the value directly?
    def set_community_id(community_id):
        self.communityId = community_id

    def set_project_id(project_id):
        self.projectId = project_id

    def authenticateUser(self, host, username, password):
        ran_oauth = False
        self.apiCall = ApiCalls(host, '')
        login_host = 'https://sso.lingotek.com' if 'myaccount' in host else 'https://cmssso.lingotek.com'

        if self.apiCall.login(login_host, username, password):
            retrieved_token = self.apiCall.authenticate(login_host)
            if retrieved_token:
                self.access_token = retrieved_token
                ran_oauth = True
        if not ran_oauth:
            logger.info("Authentication failed")
            return "Authentication failed"
        logger.info(self.access_token)
        return self.access_token

    def get_communities(self, host):
        if self.access_token is not "":
            self.apiCall = ApiCalls(host, self.access_token)
            # create a directory
            try:
                os.mkdir(os.path.join(self.project_path, CONF_DIR))
            except OSError:
                pass

            # get community id
            self.communities = self.apiCall.get_communities_info()
            if not self.communities:
                # from ltk.auth import run_oauth
                # self.access_token = run_oauth(host)
                self.create_global(self.access_token, host)
                community_info = self.apiCall.get_communities_info()
                if not self.communities:
                    return None
            if len(self.communities) == 0:
                return None
            else:
                self.create_global(self.access_token, host)
                return self.communities

    def get_projects(self, community_id):
        if community_id != None:
            #self.config_parser.set('main', 'community_id', community_id)
            response = self.apiCall.list_projects(community_id)
            if response.status_code != 200:
                return False
            self.project_info = self.apiCall.get_project_info(community_id)
            return self.project_info

    def get_workflows(self, community_id):
# This # This should be parents self.api
        response = self.apiCall.list_workflows(community_id)
        if response.status_code != 200:
            raise_error(response.json(), "Failed to list workflows")
        ids, titles = log_id_names(response.json())
        self.workflow_info = dict(zip(ids, titles))
        return self.workflow_info

    def create_project(self, project_name, community_id, workflow_id):
        # LOOK MORE INTO PROJECT NAME
        response = self.apiCall.add_project(project_name, community_id, workflow_id)
        if response.status_code != 201:
            try:
                raise_error(response.json(), 'Failed to add current project to Lingotek Cloud')
            except:
                logger.error('Failed to add current project to Lingotek Cloud')
                return
        project_id = response.json()['properties']['id']
        return project_id

    def update_project(self, project_id, workflow_id):
        response = self.apiCall.patch_project(project_id, workflow_id)
        if response.status_code != 204:
            try:
                raise_error(response.json(), 'Failed to update the project with id: {0}'.format(project_id))
                return False
            except:
                logger.error('Failed to update current project')
                return False

        return True

    def set_access_token(self, access_token):
        self.access_token = access_token

    def init_api_call(self, host):
        self.apiCall = ApiCalls(host, self.access_token)

    def finish_config(self, project_id, project_name, workflow_id, project_path, locale, host, access_token, community_id, community_name, watch_locales, download_folder, username, finished_config=False):
        #logger.info("PROJECT PATH "+project_path)
        self.init_logger(project_path)
        startOnStartup = False
        try:
            conf_dir_path = os.path.join(project_path, CONF_DIR)
            if not (os.path.isdir):
                os.mkdir(conf_dir_path)

            ''' Set .ltk folder as hidden '''
            # Python 2
            # attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(file_path))
            ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(conf_dir_path), HIDDEN_ATTRIBUTE)
            # End Python 2
            # Python 3
            #ret = ctypes.windll.kernel32.SetFileAttributesW(str(conf_dir_path), HIDDEN_ATTRIBUTE)
            # End Python 3
            if(ret != 1):   # return value of 1 signifies success
                log_error("Failed to make .ltk folder hidden")

        except OSError, e:
            log_error(str(e))
            pass

        config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
        # create the config file and add info
        config_file = open(config_file_name, 'w')
        config_parser = ConfigParser()

        config_parser.add_section('main')
        config_parser.set('main', 'access_token', access_token)
        config_parser.set('main', 'host', host)
        config_parser.set('main', 'git_autocommit', 'False')
        config_parser.set('main', 'git_username', '')
        config_parser.set('main', 'git_password', '')
        config_parser.set('main', 'community_id', community_id)
        config_parser.set('main', 'root_path', project_path)
        config_parser.set('main', 'default_locale', locale)
        config_parser.set('main', 'workflow_id', workflow_id)
        config_parser.set('main', 'project_id', project_id)
        config_parser.set('main', 'project_name', project_name)

        config_parser.write(config_file)
        config_file.close()

        configAction = ConfigAction(project_path)
        configAction.set_target_locales(watch_locales)
        configAction.set_download_folder(download_folder)

        # create a folder in the AppData folder that will store settings and the log
        self.setLingotekAppDataFolder(project_path, download_folder, username, community_name, startOnStartup, finished_config)

        # configure windows registry key for start on startup '''
        if startOnStartup == True:
            # create registry key so that program runs on startup
            logger.info("Creating windows registry key")
            path_to_exe = os.path.join(winshell.folder("PROGRAM_FILES"),PROGRAM_FILES_FN, EXE_FN)
            #set_run_key.set("Lingotek", path_to_exe)
        else:
            # remove registry key so program does not run on startup
            logger.info("Deleting windows registry key")
            #set_run_key.set("Lingotek", None)

    def init_logger(self, path):
        """
        Initializes logger based on path
        """
        logger.setLevel(logging.DEBUG)
        if not path:
            file_handler = logging.FileHandler(LOG_FN)
        else:
            try:
                file_handler = logging.FileHandler(os.path.join(path, CONF_DIR, LOG_FN))
            except IOError:
                # todo error check when running init without existing conf dir
                os.mkdir(os.path.join(path, CONF_DIR))
                file_handler = logging.FileHandler(os.path.join(path, CONF_DIR, LOG_FN))
        console_handler = logging.StreamHandler(sys.stdout)
        file_handler.setLevel(API_LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter('%(asctime)s  %(levelname)s: %(message)s'))
        console_handler.setLevel(logging.DEBUG)
        custom_formatter = CustomFormatter()
        console_handler.setFormatter(custom_formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    def setLingotekAppDataFolder(self, project_path, download_path, username, community_name, start_on_startup, finished_config):
        if(self.has_global):
            local_appdata = winshell.folder("local_appdata")
            local_appData_folder = os.path.join(local_appdata,"Lingotek")
            local_appData_file = os.path.join(local_appdata,"Lingotek","lingotek.cfg")
            try:
                if not os.path.exists(local_appData_folder):
                    os.mkdir(local_appData_folder)
            except OSError:
                pass
            # create the config file and add info
            config_file = open(local_appData_file, 'w')
            config_parser = ConfigParser()

            config_parser.add_section('main')
            config_parser.set('main', 'source_path', project_path)
            config_parser.set('main', 'download_path', download_path)
            config_parser.set('main', 'username', username)
            config_parser.set('main', 'community_name', community_name)

            if start_on_startup == True:
                config_parser.set('main', 'start_on_startup', "True")
            else:
                config_parser.set('main', 'start_on_startup', "False")

            if finished_config == True:
                config_parser.set('main', 'finished_config', "True")
            else:
                config_parser.set('main', 'finished_config', "False")

            config_parser.set('main', 'running_instance', "True")

            config_parser.write(config_file)
            config_file.close()
            print("finished writing to config file")

    def create_global(self, access_token, host):
        """
        create a .lingotek file in user's $HOME directory
        """
        # go to the home dir
        home_path = os.path.expanduser('~')
        file_name = os.path.join(home_path, SYSTEM_FILE)
        if(os.path.isfile(file_name)):
            os.remove(file_name)
            
        config_parser = ConfigParser()
        try:
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

            ''' Set as hidden file '''
            ret = ctypes.windll.kernel32.SetFileAttributesW(unicode(file_name), HIDDEN_ATTRIBUTE)
            ''' return value of 1 means success '''
            if(ret != 1):
                log_error("Failed making .lingotek file hidden")

            print("has global")
            self.has_global = True
        except IOError, e:
            log_error(ERROR_FN, str(e))
