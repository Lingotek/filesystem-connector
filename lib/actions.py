import ConfigParser
import os
import shutil
import fnmatch
from exceptions import UninitializedError
from apicalls import ApiCalls

class Action:
    def __init__(self, path):
        self.host = ''
        self.access_token = ''
        self.project_id = ''
        self.path = path
        self.community_id = ''
        self.workflow_id = ''  # default workflow id; MT phase only
        if not self._is_initialized():
            # todo prompt user to initialize project first, raise error and exit
            raise UninitializedError("This project is not initialized. Please run init command.")
        self._initialize_self()
        self.api = ApiCalls(self.host, self.access_token)

    def _is_initialized(self):
        if os.path.isdir(os.path.join(self.path, '.Lingotek')):
            config_file_name = os.path.join(self.path, '.Lingotek', 'Lingotek.cfg')
            if os.path.isfile(config_file_name):
                return True
            else:
                return False
        return False

    def _initialize_self(self):
        config_file_name = os.path.join(self.path, '.Lingotek', 'Lingotek.cfg')
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(config_file_name)
        self.host = conf_parser.get('main', 'host')
        self.access_token = conf_parser.get('main', 'access_token')
        self.project_id = conf_parser.get('main', 'project_id')
        self.community_id = conf_parser.get('main', 'community_id')
        self.workflow_id = conf_parser.get('main', 'workflow_id')

    def add_action(self, locale, file_pattern, file_path=None, document_name=None):
        if not file_path:
            file_path = self.path
        matched_files = get_files(file_path, file_pattern)
        for file_name in matched_files:
            if document_name:
                title = document_name
            else:
                base_name = os.path.basename(os.path.normpath(file_name))
                title = base_name.split('.')[0]
            response = self.api.add_document(title, file_name, locale, self.project_id)
            if response.status_code != 202:
                print 'Error when adding document'


def init_action(host, access_token, project_path, project_name, workflow_id):
    api = ApiCalls(host, access_token)
    # check if Lingotek directory already exists
    if os.path.isdir(os.path.join(project_path, '.Lingotek')):
        # todo: re-initialize
        confirm = 'not confirmed'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = raw_input("Do you want to delete the existing project and create a new one? This will also delete the project in your community. [y/n]: ")
        # confirm if would like to delete existing folder
        if not confirm or confirm in ['n', 'N']:
            return
        else:
            # delete the corresponding project online
            config_file_name = os.path.join(project_path, '.Lingotek', 'Lingotek.cfg')
            if os.path.isfile(config_file_name):
                old_config = ConfigParser.ConfigParser()
                old_config.read(config_file_name)
                project_id = old_config.get('main', 'project_id')
                del_status = api.delete_project(project_id)
                if del_status != 204:
                    # todo raise error
                    print 'not successfully deleted'
                # delete existing folder
                to_remove = os.path.join(project_path, '.Lingotek')
                shutil.rmtree(to_remove)
            else:
                # todo raise error
                print 'no config file'

    # create a directory
    os.mkdir(os.path.join(project_path, '.Lingotek'))

    config_file_name = os.path.join(project_path, '.Lingotek', 'Lingotek.cfg')
    if not os.path.exists(config_file_name):
        # create the config file and add info
        config_file = open(config_file_name, 'w')

        config_parser = ConfigParser.ConfigParser()
        config_parser.add_section('main')
        config_parser.set('main', 'access_token', access_token)
        config_parser.set('main', 'host', host)
        config_parser.set('main', 'root_path', project_path)
        config_parser.set('main', 'workflow_id', workflow_id)
        # get community id
        community_ids = api.get_community_ids()
        if len(community_ids) > 1:
            # todo handle when user in multiple communities
            community_id = ''
            pass
        else:
            community_id = community_ids[0]
        config_parser.set('main', 'community_id', community_id)

        # todo handle when project already exists online
        response = api.add_project(project_name, community_id, workflow_id)
        if response.status_code != 201:
            # todo raise error
            print 'error initializing project'
        project_id = response.json()['properties']['id']
        config_parser.set('main', 'project_id', project_id)

        config_parser.write(config_file)
        config_file.close()

def get_files(root, pattern):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """
    matched_files = []
    for path, subdirs, files in os.walk(root):
        for name in fnmatch.filter(files, pattern):
            matched_files.append(os.path.join(path, name))
    return matched_files

