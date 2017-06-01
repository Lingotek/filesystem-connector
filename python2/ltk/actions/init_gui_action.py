from ltk.actions.action import *
from ltk.apicalls import ApiCalls
import os.path

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
        self.workflow_info = None
        self.community_id = ""
        self.project_id = ""
        self.workflow_id = ""
        self.apiCall = None

    def authenticateUser(self, host, username, password):
        self.apiCall = ApiCalls(host, '')
        login_host = 'https://sso.lingotek.com' if 'myaccount' in host else 'https://cmssso.lingotek.com'
        if self.apiCall.login(login_host, username, password):
            retrieved_token = self.apiCall.authenticate(login_host)
            if retrieved_token:
                self.access_token = retrieved_token
                ran_oauth = True
            else:
                ran_oauth = False
        if not ran_oauth:
            return "Authentication failed"
        return self.access_token


    def get_communities(self, host):
        if self.access_token is not "":
            self.apiCall = ApiCalls(host, self.access_token)
            self.communities = self.apiCall.get_communities_info()
            if not self.communities:
                self.create_global(self.access_token, host)
                community_info = self.apiCall.get_communities_info()
                if not self.communities:
                    return None
            if len(self.communities) == 0:
                return None
            else:
                return self.communities

    def get_communities_solo(self, host, access_token):
        if access_token is not "":
            self.apiCall = ApiCalls(host, access_token)
            self.communities = self.apiCall.get_communities_info()
            if not self.communities:
                self.create_global(access_token, host)
                community_info = self.apiCall.get_communities_info()
                if not self.communities:
                    return None
            if len(self.communities) == 0:
                return None
            else:
                return self.communities

    def get_projects(self, community_id):
        if community_id != None:
            response = self.apiCall.list_projects(community_id)
            if response.status_code != 200:
                return False
            self.project_info = self.apiCall.get_project_info(community_id)
            return self.project_info

    def get_projects_solo(self, community_id, host, access_token):
        self.apiCall = ApiCalls(host, access_token)
        if community_id != None:
            response = self.apiCall.list_projects(community_id)
            if response.status_code != 200:
                return False
            self.project_info = self.apiCall.get_project_info(community_id)
            return self.project_info

    def get_workflows(self, community_id):
        response = self.apiCall.list_workflows(community_id)
        if response.status_code != 200:
            raise_error(response.json(), "Failed to list workflows")
        ids, titles = log_id_names(response.json())
        self.workflow_info = dict(zip(ids, titles))
        return self.workflow_info

    def get_workflows_solo(self, community_id, host, access_token):
        self.apiCall = ApiCalls(host, access_token)
        response = self.apiCall.list_workflows(community_id)
        if response.status_code != 200:
            raise_error(response.json(), "Failed to list workflows")
        ids, titles = log_id_names(response.json())
        self.workflow_info = dict(zip(ids, titles))
        return self.workflow_info

    def create_project(self, project_name, community_id, workflow_id ):
        response = self.apiCall.add_project(project_name, community_id, workflow_id)
        if response.status_code != 201:
            try:
                raise_error(response.json(), 'Failed to add current project to Lingotek Cloud')
            except:
                logger.error('Failed to add current project to Lingotek Cloud')
                return
        project_id = response.json()['properties']['id']
        return project_id

    def finish_config(self, project_id, project_name, workflow_id, project_path, locale, host, access_token, community_id):
        try:
            os.mkdir(os.path.join(project_path, CONF_DIR))
        except OSError:
            pass
        config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
        # create the config file and add info

        if os.path.isfile(config_file_name):
            os.remove(config_file_name)
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
