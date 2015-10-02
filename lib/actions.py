import ConfigParser
import os
import shutil
import fnmatch
import time
import exceptions
from apicalls import ApiCalls
from managers import DocumentManager
from constants import CONF_DIR, CONF_FN, TRANS_DIR

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
        self.doc_manager = DocumentManager(path)

    def _is_initialized(self):
        if os.path.isdir(os.path.join(self.path, '.Lingotek')):
            config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
            if os.path.isfile(config_file_name):
                return True
            else:
                return False
        return False

    def _initialize_self(self):
        config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(config_file_name)
        self.host = conf_parser.get('main', 'host')
        self.access_token = conf_parser.get('main', 'access_token')
        self.project_id = conf_parser.get('main', 'project_id')
        self.community_id = conf_parser.get('main', 'community_id')
        self.workflow_id = conf_parser.get('main', 'workflow_id')

    def _add_document(self, file_name, title, json):
        """ adds a document to db """
        now = time.time()
        doc_id = json['properties']['id']
        last_modified = os.stat(file_name).st_mtime
        self.doc_manager.add_document(title, now, doc_id, last_modified, now, file_name)

    def _update_document(self, file_name, title):
        """ updates a document in the db """
        now = time.time()
        sys_last_modified = os.stat(file_name).st_mtime
        doc_entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
        doc_id = doc_entry['id']
        self.doc_manager.update_document(doc_id, now, sys_last_modified, file_name, title)

    def add_action(self, locale, file_pattern, **kwargs):
        # todo should only add changed files..
        # todo automatically detect format?
        matched_files = get_files(self.path, file_pattern)
        for file_name in matched_files:
            title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
            if not self.doc_manager.is_doc_new(file_name) and self.doc_manager.is_doc_modified(file_name):
                confirm = 'not confirmed'
                while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                    confirm = raw_input("This document already exists. Would you like to overwrite it? [y/n]: ")
                # confirm if would like to overwrite existing document in TMS
                if not confirm or confirm in ['n', 'N']:
                    return
                else:
                    self.update_document_action(file_name, title, **kwargs)
                    continue
            response = self.api.add_document(file_name, locale, self.project_id, title, **kwargs)
            if response.status_code != 202:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to add document")
            else:
                self._add_document(file_name, title, response.json())

    def push_action(self):
        document_ids = self.doc_manager.get_doc_ids()
        for document_id in document_ids:
            entry = self.doc_manager.get_doc_by_prop('id', document_id)[0]
            if not self.doc_manager.is_doc_modified(entry['file_name']):
                continue
            response = self.api.document_update(document_id, entry['file_name'])
            if response.status_code != 202:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to update document")
            self._update_document(entry['file_name'], entry['name'])

    def update_document_action(self, file_name, title=None, **kwargs):
        entries = self.doc_manager.get_doc_by_prop('file_name', file_name)
        document_id = entries[0]['id']
        if title:
            response = self.api.document_update(document_id, file_name, title=title, **kwargs)
        else:
            response = self.api.document_update(document_id, file_name)
        if response.status_code != 202:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except (AttributeError, IndexError):
                raise exceptions.RequestFailedError("Failed to update document")
        self._update_document(file_name, title)

    def request_action(self, document_name, locales, due_date, workflow):
        if not document_name:
            for locale in locales:
                response = self.api.add_target_project(self.project_id, locale, due_date)
                if response.status_code != 201:
                    try:
                        error = response.json()['messages'][0]
                        raise exceptions.RequestFailedError(error)
                    except (AttributeError, IndexError):
                        raise exceptions.RequestFailedError("Failed to add a target to project")
        else:
            try:
                entry = self.doc_manager.get_doc_by_prop('name', document_name)[0]
            except IndexError:
                raise exceptions.ResourceNotFound("Document name specified doesn't exist")
            document_id = entry['id']
            for locale in locales:
                response = self.api.add_target_document(document_id, locale, workflow, due_date)
                if response.status_code != 201:
                    try:
                        error = response.json()['messages'][0]
                        raise exceptions.RequestFailedError(error)
                    except (AttributeError, IndexError):
                        raise exceptions.RequestFailedError("Failed to add a target to document")

    def list_ids_action(self, list_type):
        """ lists ids of list_type specified """
        ids = []
        titles = []
        if list_type == 'documents':
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                ids.append(entry['id'])
                titles.append(entry['name'])
        elif list_type == 'workflows':
            response = self.api.list_workflows(self.community_id)
            if response.status_code != 200:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to list workflows")
            ids, titles = log_id_names(response.json())
        print list_type
        print 'id\t\t\t\t\t\ttitle'
        for i in range(len(ids)):
            print ids[i] + '\t\t' + titles[i]

    def status_action(self, doc_name=None):
        if doc_name is not None:
            try:
                doc_ids = [self.doc_manager.get_doc_by_prop('title', doc_name)[0]['id']]
            except IndexError:
                raise exceptions.ResourceNotFound("Document name specified doesn't exist")
        else:
            doc_ids = self.doc_manager.get_doc_ids()
        for doc_id in doc_ids:
            response = self.api.document_status(doc_id)
            if response.status_code != 200:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to get status of document")
            else:
                title = response.json()['properties']['title']
                progress = response.json()['properties']['progress']
                print title + ': ' + str(progress) + '%'

    def download_by_name(self, doc_name, locale_code, auto_format):
        try:
            document_id = self.doc_manager.get_doc_by_prop('name', doc_name)[0]['id']
        except IndexError:
            raise exceptions.ResourceNotFound("Document name specified doesn't exist")
        self.download_action(document_id, locale_code, auto_format)

    def download_action(self, document_id, locale_code, auto_format):
        if not os.path.isdir(os.path.join(self.path, TRANS_DIR)):
            os.mkdir(os.path.join(self.path, TRANS_DIR))
        response = self.api.document_content(document_id, locale_code, auto_format)
        if response.status_code == 200:
            if not locale_code:
                locale_code = ''
            file_path = response.headers['content-disposition'].split('filename=')[1].strip("\"'")
            base_name = os.path.basename(os.path.normpath(file_path))
            name_parts = base_name.split('.')
            if len(name_parts) > 1:
                file_name = '.'.join(x for x in name_parts[:-1]) + '-' + locale_code + '.' + name_parts[-1]
            else:
                file_name = name_parts[-1] + locale_code
            download_path = os.path.join(self.path, TRANS_DIR, file_name)
            with open(download_path, 'wb') as fh:
                # todo handle when file too large; can't keep entire file in memory
                encoded = response.text.encode('utf_8')
                # shutil.copyfileobj(encoded, fh)
                fh.write(encoded)
        else:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except (AttributeError, IndexError):
                raise exceptions.RequestFailedError("Failed to download content")

    def pull_action(self, locale_code, auto_format):
        document_ids = self.doc_manager.get_doc_ids()
        for document_id in document_ids:
            self.download_action(document_id, locale_code, auto_format)


def init_action(host, access_token, project_path, project_name, workflow_id):
    api = ApiCalls(host, access_token)
    # check if Lingotek directory already exists
    if os.path.isdir(os.path.join(project_path, CONF_DIR)):
        confirm = 'not confirmed'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = raw_input("Do you want to delete the existing project and create a new one? This will also delete the project in your community. [y/n]: ")
        # confirm if would like to delete existing folder
        if not confirm or confirm in ['n', 'N']:
            return
        else:
            # delete the corresponding project online
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            if os.path.isfile(config_file_name):
                old_config = ConfigParser.ConfigParser()
                old_config.read(config_file_name)
                project_id = old_config.get('main', 'project_id')
                del_status = api.delete_project(project_id)
                if del_status != 204:
                    # todo raise error
                    print 'not successfully deleted'
                # delete existing folder
                to_remove = os.path.join(project_path, CONF_DIR)
                shutil.rmtree(to_remove)
            else:
                # todo raise error
                print 'no config file'

    # create a directory
    os.mkdir(os.path.join(project_path, CONF_DIR))

    config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
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
            try:
                print response.json()['messages'][0]
            except AttributeError:
                print "Something went wrong while adding project"
                return
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
