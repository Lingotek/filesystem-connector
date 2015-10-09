import ConfigParser
import os
import shutil
import fnmatch
import time
import exceptions
from apicalls import ApiCalls
from managers import DocumentManager
from constants import CONF_DIR, CONF_FN, TRANS_DIR, LOG_FN
import logging

# todo handle errors/log them

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
        logging.basicConfig(filename=LOG_FN, level=logging.DEBUG)

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

    def _add_document(self, file_name, title, doc_id):
        """ adds a document to db """
        now = time.time()
        # doc_id = json['properties']['id']
        last_modified = os.stat(file_name).st_mtime
        self.doc_manager.add_document(title, now, doc_id, last_modified, now, file_name)

    def _update_document(self, file_name):
        """ updates a document in the db """
        now = time.time()
        sys_last_modified = os.stat(file_name).st_mtime
        entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
        doc_id = entry['id']
        self.doc_manager.update_document('last_mod', now, doc_id)
        self.doc_manager.update_document('sys_last_mod', sys_last_modified, doc_id)

    def add_action(self, locale, file_patterns, **kwargs):
        # todo should only add changed files..
        # format will be automatically detected by extension but may not be what user expects
        # todo expecting file pattern, if enter multiple files, nothing happens since can't match tuple
        matched_files = get_files(self.path, file_patterns)
        if not matched_files:
            raise exceptions.ResourceNotFound("Could not find the specified file/pattern")
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
                    logging.info('Overwriting current document in TMS...%s', title)
                    self.update_document_action(file_name, title, **kwargs)
                    continue
            response = self.api.add_document(file_name, locale, self.project_id, title, **kwargs)
            if response.status_code != 202:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to add document %s", title)
            else:
                self._add_document(file_name, title, response.json()['properties']['id'])

    def push_action(self):
        entries = self.doc_manager.get_all_entries()
        for entry in entries:
            if not self.doc_manager.is_doc_modified(entry['file_name']):
                continue
            print 'Updating...' + str(entry['name'])
            logging.info('Updating...' + entry['name'])
            response = self.api.document_update(entry['id'], entry['file_name'])
            if response.status_code != 202:
                try:
                    error = response.json()['messages'][0]
                    raise exceptions.RequestFailedError(error)
                except (AttributeError, IndexError):
                    raise exceptions.RequestFailedError("Failed to update document %s", entry['name'])
            self._update_document(entry['file_name'])

    def update_document_action(self, file_name, title=None, **kwargs):
        entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
        try:
            document_id = entry['id']
        except TypeError:
            raise exceptions.ResourceNotFound("Document name specified (%s) doesn't exist", file_name)
        if title:
            response = self.api.document_update(document_id, file_name, title=title, **kwargs)
        else:
            response = self.api.document_update(document_id, file_name)
        if response.status_code != 202:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except (AttributeError, IndexError):
                raise exceptions.RequestFailedError("Failed to update document %s", file_name)
        self._update_document(file_name, title)

    def request_action(self, document_name, locales, due_date, workflow):
        if not document_name:
            for locale in locales:
                response = self.api.add_target_project(self.project_id, locale, due_date)
                if response.status_code != 201:
                    try:
                        error = response.json()['messages'][0]
                        raise exceptions.RequestFailedError('Error: ' + error)
                    except (AttributeError, IndexError):
                        raise exceptions.RequestFailedError("Failed to add target %s to project", locale)
            document_ids = self.doc_manager.get_doc_ids()
            for document_id in document_ids:
                self.doc_manager.update_document('locales', list(locales), document_id)
        else:
            entry = self.doc_manager.get_doc_by_prop('name', document_name)
            try:
                document_id = entry['id']
            except TypeError:
                raise exceptions.ResourceNotFound("Document name specified (%s) doesn't exist", document_name)
            for locale in locales:
                response = self.api.add_target_document(document_id, locale, workflow, due_date)
                if response.status_code != 201:
                    try:
                        error = response.json()['messages'][0]
                        raise exceptions.RequestFailedError(error)
                    except (AttributeError, IndexError):
                        raise exceptions.RequestFailedError("Failed to add target %s to document", locale)
            self.doc_manager.update_document('locales', list(locales), document_id)

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
            entry = self.doc_manager.get_doc_by_prop('name', doc_name)
            try:
                doc_ids = [entry['id']]
            except TypeError:
                raise exceptions.ResourceNotFound("Document name specified (%s) doesn't exist", doc_name)
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
            document_id = self.doc_manager.get_doc_by_prop('name', doc_name)['id']
        except TypeError:
            raise exceptions.ResourceNotFound("Document name specified (%s) doesn't exist", doc_name)
        self.download_action(document_id, locale_code, auto_format)

    def download_action(self, document_id, locale_code, auto_format):
        # if not os.path.isdir(os.path.join(self.path, TRANS_DIR)):
        #     os.mkdir(os.path.join(self.path, TRANS_DIR))
        # if not locale_code:
        #     raise exceptions.RequestFailedError("No locale code specified to download")
        response = self.api.document_content(document_id, locale_code, auto_format)
        if response.status_code == 200:
            entry = self.doc_manager.get_doc_by_prop('id', document_id)
            if not entry:
                file_path = response.headers['content-disposition'].split('filename=')[1].strip("\"'")
                print file_path
                base_name = os.path.basename(file_path)
                download_path = os.path.join(self.path, base_name)
                print "Downloaded {0}".format(base_name)
                logging.info("Downloaded {0}".format(base_name))
            elif not locale_code:
                logging.info("Tried to download an existing document, did nothing")
                return
            else:
                file_name = entry['file_name']
                download_dir = os.path.dirname(file_name)
                base_name = os.path.basename(os.path.normpath(file_name))
                name_parts = base_name.split('.')
                if name_parts > 1:
                    name_parts.insert(-1, locale_code)
                    downloaded_name = '.'.join(part for part in name_parts)
                else:
                    downloaded_name = name_parts[0] + '.' + locale_code
                download_path = os.path.join(download_dir, downloaded_name)
                print "Downloaded {0} for locale {1}: {2}".format(name_parts[0], locale_code, downloaded_name)
                logging.info("Downloaded {0} for locale {1}: {2}".format(name_parts[0], locale_code, downloaded_name))
            # # if not locale_code:
            # #     locale_code = ''
            # file_path = response.headers['content-disposition'].split('filename=')[1].strip("\"'")
            # base_name = os.path.basename(os.path.normpath(file_path))
            # name_parts = base_name.split('.')
            # if not locale_code and len(name_parts) < 3:
            #     print 'Downloaded ' + str(name_parts[0]) + ' in its source language: ' + str(base_name)
            #     logging.info('Downloaded ' + str(name_parts[0]) + ' in its source language: ' + str(base_name))
            # else:
            #     print 'Downloaded ' + str(name_parts[0]) + ' for locale ' + str(name_parts[1]) + ': ' + str(base_name)
            #     logging.info('Downloaded ' + str(name_parts[0]) + ' for locale ' + str(name_parts[1]) + ': ' + str(base_name))
            # # name_parts = base_name.split('.')
            # # if len(name_parts) > 1:
            # #     file_name = '.'.join(x for x in name_parts[:-1]) + '-' + locale_code + '.' + name_parts[-1]
            # # else:
            # #     file_name = name_parts[-1] + locale_code
            # # todo possibly put downloaded file next to original file
            # # download_path = os.path.join(self.path, TRANS_DIR, file_name)
            # download_path = os.path.join(self.path, TRANS_DIR, base_name)
            # # download_path = os.path.join(self.path, base_name)
            # # with open(download_path, 'wb') as fh:
            with open(download_path, 'wb') as fh:
                for chunk in response.iter_content(1024):
                    fh.write(chunk)
                # encoded = response.text.encode('utf_8')
                # fh.write(encoded)
            return download_path
        else:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except (AttributeError, IndexError):
                raise exceptions.RequestFailedError("Failed to download content")

    def pull_action(self, locale_code, auto_format):
        if not locale_code:
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                try:
                    locales = entry['locales']
                    for locale in locales:
                        self.download_action(entry['id'], locale, auto_format)
                except KeyError:
                    self.download_action(entry['id'], None, auto_format)
        else:
            document_ids = self.doc_manager.get_doc_ids()
            for document_id in document_ids:
                self.download_action(document_id, locale_code, auto_format)

    def delete_action(self, document_name):
        try:
            entry = self.doc_manager.get_doc_by_prop('name', document_name)
            document_id = entry['id']
        except TypeError:
            raise exceptions.ResourceNotFound("Document name specified doesn't exist")
        response = self.api.delete_document(document_id)
        self.doc_manager.remove_element(document_id)
        if response.status_code != 204:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except (AttributeError, IndexError):
                raise exceptions.RequestFailedError("Failed to delete document %s", document_name)
        else:
            print "%s has been deleted." % document_name
            logging.info("%s has been deleted." % document_name)

    def sync_action(self, force, update):
        # upload_date in get document tells which day but not specific time
        # get list of documents in TMS, under this project
        # if local document exists but not in TMS, delete from local db
        # if force, delete local files
        # possibly check TMS documents upload_date and compare to local db last modified
        # if update, download src and overwrite local files
        response = self.api.list_documents(self.project_id)
        tms_documents = response.json()['entities']
        local_ids = self.doc_manager.get_doc_ids()
        tms_doc_ids = []
        for entity in tms_documents:
            tms_doc_ids.append(entity['properties']['id'])
        ids_to_delete = [x for x in local_ids if x not in tms_doc_ids]
        ids_not_local = [x for x in tms_doc_ids if x not in local_ids]
        if not ids_to_delete and not ids_not_local:
            # todo need to check if content also up to date?
            logging.info('Local documents up to date with documents in TMS')
            print 'Local up to date with TMS'
            return
        if ids_to_delete:
            for curr_id in ids_to_delete:
                if force:
                    file_name = self.doc_manager.get_doc_by_prop('id', curr_id)['file_name']
                    os.remove(file_name)
                self.doc_manager.remove_element(curr_id)
        if ids_not_local:
            # download files from TMS
            for curr_id in ids_not_local:
                download_path = self.download_action(curr_id, None, None)
                title = os.path.basename(download_path).split('.')[0]
                self._add_document(download_path, title, curr_id)


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
            logging.info('Deleting old project folder and creating new one..')
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            if os.path.isfile(config_file_name):
                old_config = ConfigParser.ConfigParser()
                old_config.read(config_file_name)
                project_id = old_config.get('main', 'project_id')
                response = api.delete_project(project_id)
                if response.status_code != 204:
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
        # community_ids = api.get_communities_info()
        community_info = api.get_communities_info()
        if len(community_info) > 1:
            choice = 'none-chosen'
            for k, v in community_info.iteritems():
                print k, v
            while choice not in community_info.iterkeys():
                choice = raw_input('Which community should this project belong to? Please enter community id:')
            community_id = choice
        else:
            community_id = community_info.iterkeys().next()
        config_parser.set('main', 'community_id', community_id)

        # todo handle when project already exists online?
        response = api.add_project(project_name, community_id, workflow_id)
        if response.status_code != 201:
            try:
                error = response.json()['messages'][0]
                raise exceptions.RequestFailedError(error)
            except AttributeError:
                raise exceptions.RequestFailedError('Failed to add current project to TMS')
        project_id = response.json()['properties']['id']
        config_parser.set('main', 'project_id', project_id)

        config_parser.write(config_file)
        config_file.close()

def get_files(root, patterns):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """
    matched_files = []
    for path, subdirs, files in os.walk(root):
        # matched_files = any(fnmatch.fnmatch(files, p) for p in patterns)
        for pattern in patterns:
            # if os.path.exists(pattern):
            #     # print 'files----'
            #     # print files
            #     # print '----'
            #     subdir_files = []
            #     for file_name in files:
            #         subdir_files.extend([os.path.join(path, subdir, file_name) for subdir in subdirs])
            #     print subdir_files
            #     if 'test_content' in subdir_files:
            #         print 'test_content'
            #         print subdir_files
            #     for subdir_file in subdir_files:
            #         if fnmatch.fnmatch(subdir_file, os.path.join(path, os.path.basename(pattern))):
            #             print 'found, with subdir'
                # for name in fnmatch.fnmatch(subdir_files, pattern):
                #     print 'found, with subdir'
                    # matched_files.append(os.path.join(path, name))
            # else:
            for name in fnmatch.filter(files, pattern):
                # print 'found without subdir'
                # print os.path.join(path, name)
                matched_files.append(os.path.join(path, name))
    print patterns
    print matched_files
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
