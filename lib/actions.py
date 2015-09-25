import ConfigParser
import os
import shutil
import fnmatch
import exceptions
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
            raise exceptions.UninitializedError("This project is not initialized. Please run init command.")
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
        # todo should only add changed files..
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

    def request_action(self, document_id, is_project, locales, due_date, workflow):
        if is_project:
            for locale in locales:
                response = self.api.add_target_project(self.project_id, locale, due_date)
                if response.status_code != 201:
                    print 'Error when requesting translation for project'
        else:
            if not document_id:
                raise exceptions.NoIdSpecified("No document id specified and not requesting for project")
            for locale in locales:
                response = self.api.add_target_document(document_id, locale, workflow, due_date)
                if response.status_code == 404:
                    raise exceptions.ResourceNotFound("This document doesn't exist")
                if response.status_code != 201:
                    print 'Error when requesting translation'

    def list_ids_action(self, list_type, project_id=None):
        """ lists ids of list_type specified """
        if list_type == 'projects':
            response = self.api.list_projects(self.community_id)
            # todo organize and print response
        elif list_type == 'documents':
            response = self.api.list_documents(project_id)
        elif list_type == 'workflows':
            response = self.api.list_workflows(self.community_id)
        else:
            raise exceptions.ResourceNotFound("No such resource to list")

        if response.status_code != 200:
            print 'Error with listing'
        else:
            ids, titles = log_id_names(response.json())
            print list_type
            print 'id\t\t\t\t\t\ttitle'
            for i in range(len(ids)):
                print ids[i] + '\t\t' + titles[i]

    def status_action(self, status_type, given_id):
        if status_type == 'project':
            response = self.api.project_status(given_id)
        elif status_type == 'document':
            response = self.api.document_status(given_id)
        else:
            raise exceptions.ResourceNotFound("No such resource to get status for")

        if response.status_code != 200:
            print 'Error trying to get status'
        else:
            title = response.json()['properties']['title']
            progress = response.json()['properties']['progress']
            print title + ': ' + str(progress) + '%'

    def download_action(self, document_ids, locale_code, auto_format):
        pass

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

def log_id_names(json):
    # entities array
    # title, id in properties
    ids = []
    titles = []
    for entity in json['entities']:
        ids.append(entity['properties']['id'])
        titles.append(entity['properties']['title'])
    return ids, titles
