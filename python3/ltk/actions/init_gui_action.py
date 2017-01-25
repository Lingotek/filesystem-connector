from ltk.actions.action import *

class InitActionGUI(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.access_token = ""
        self.cummunities = None
        self.projects = None
        self.project_info = None
        self.workflows = None
        self.workflow_titles = None
        self.community_id = ""
        self.project_id = ""
        self.workflow_id = ""
        self.apiCall = None

# Is this nessecary in python or can you just set the value directly?
    def set_community_id(community_id):
        self.communityId = community_id

    def set_project_id(project_id):
        self.projectId = project_id

    def authenticateUser(host, username, password):
        self.apiCall = ApiCalls(host, '')
        login_host = 'https://sso.lingotek.com' if 'myaccount' in host else 'https://cmssso.lingotek.com'

        if self.apiCall.login(login_host, username, password):
            retrieved_token = self.apiCall.authenticate(login_host)
            if retrieved_token:
                self.access_token = retrieved_token
                ran_oauth = True
        if not ran_oauth:
            # print('Authentication failed.  Initialization canceled.')
            return False
        return True


    def get_cummunities(host, project_path):
        if self.access_token is not "":
            self.apiCall = ApiCalls(host, self.access_token)
            # create a directory
            try:
                os.mkdir(os.path.join(project_path, CONF_DIR))
            except OSError:
                pass

            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            # create the config file and add info
            config_file = open(config_file_name, 'w')

            config_parser = ConfigParser()
            config_parser.add_section('main')
            config_parser.set('main', 'access_token', self.access_token)
            config_parser.set('main', 'host', host)
            # config_parser.set('main', 'root_path', project_path)
            # config_parser.set('main', 'workflow_id', workflow_id)
            # config_parser.set('main', 'default_locale', locale)
            config_parser.set('main', 'git_autocommit', 'False')
            config_parser.set('main', 'git_username', '')
            config_parser.set('main', 'git_password', '')
            # get community id
            self.cummunities = self.apiCall.get_communities_info()
            if not self.cummunities:
                from ltk.auth import run_oauth
                self.access_token = run_oauth(host)
                create_global(self.access_token, host)
                community_info = self.apiCall.get_communities_info()
                if not self.cummunities:
                    return False
            if len(self.communities) == 0:
                return False
            else:
                return True

    def get_projects():
        if self.community_id != None:
            config_parser.set('main', 'community_id', self.community_id)
            response = self.apiCall.list_projects(self.community_id)
            if response.status_code != 200:
                return False
            self.project_info = self.apiCall.get_project_info(self.community_id)

    def get_workflows():
# This should be parents self.api
        response = self.api.list_workflows(self.community_id)
        if response.status_code != 200:
            raise_error(response.json(), "Failed to list workflows")
        ids, titles = log_id_names(response.json())
        self.workflow_titles = titles

    def create_project():
# LOOK MORE INTO PROJECT NAME
        project_name = folder_name
        response = self.api.add_project(project_name, community_id, workflow_id)
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

    def finish_config():
        if len(self.project_info) > 0:
            if self.project_id != "":
                config_parser.set('main', 'project_id', project_id)
                if self.project_name != "":
                    config_parser.set('main', 'project_name', project_name)
                config_parser.write(config_file)
                config_file.close()
            return True
        return False
