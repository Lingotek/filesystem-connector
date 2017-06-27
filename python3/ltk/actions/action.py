# Using the following encoding: utf-8
# Python 2
# from ConfigParser import ConfigParser, NoOptionError
# End Python 2
# Python 3
from configparser import ConfigParser, NoOptionError
# End Python 3
import requests
import os
import shutil
import fnmatch
import time
import getpass
import itertools
from ltk import exceptions
from ltk.apicalls import ApiCalls
from ltk.utils import *
from ltk.managers import DocumentManager, FolderManager
from ltk.constants import CONF_DIR, CONF_FN, SYSTEM_FILE, ERROR_FN
import json
from ltk.logger import logger
from ltk.git_auto import Git_Auto

class Action:
    def __init__(self, path, watch=False, timeout=60):
        self.host = ''
        self.access_token = ''
        self.project_id = ''
        self.project_name = ''
        self.path = path
        self.community_id = ''
        self.workflow_id = ''  # default workflow id; MT phase only
        self.locale = ''
        self.clone_option = 'on'
        self.auto_format_option = ''
        self.download_option = 'clone'
        self.download_dir = None  # directory where downloaded translation will be stored
        self.watch_locales = set()  # if specified, add these target locales to any files in the watch folder
        self.git_autocommit = None
        self.git_username = ''
        self.git_password = ''
        self.append_option = 'none'
        self.locale_folders = {}
        if not self._is_initialized():
            raise exceptions.UninitializedError("This project is not initialized. Please run init command.")
        self._initialize_self()
        self.watch = watch
        self.doc_manager = DocumentManager(self.path)
        self.folder_manager = FolderManager(self.path)
        self.timeout = timeout
        self.api = ApiCalls(self.host, self.access_token, self.watch, self.timeout)
        self.git_auto = Git_Auto(self.path)
        self.error_file_name = os.path.join(self.path, CONF_DIR, ERROR_FN)

    def _is_initialized(self):
        actual_path = find_conf(self.path)
        if not actual_path:
            return False
        self.path = os.path.join(actual_path, '')
        if not is_initialized(self.path):
            return False
        return True

    def _initialize_self(self):
        config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
        conf_parser = ConfigParser()
        conf_parser.read(config_file_name)
        self.host = conf_parser.get('main', 'host')
        self.access_token = conf_parser.get('main', 'access_token')
        self.project_id = conf_parser.get('main', 'project_id')
        self.community_id = conf_parser.get('main', 'community_id')
        self.workflow_id = conf_parser.get('main', 'workflow_id')
        self.locale = conf_parser.get('main', 'default_locale')

        self.locale = self.locale.replace('_','-')
        try:
            if conf_parser.has_option('main', 'auto_format'):
                self.auto_format_option = conf_parser.get('main', 'auto_format')
            else:
                self.update_config_file('auto_format', 'on', conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'project_name'):
                self.project_name = conf_parser.get('main', 'project_name')
            if conf_parser.has_option('main', 'download_folder'):
                self.download_dir = conf_parser.get('main', 'download_folder')
            else:
                self.download_dir = None
                self.update_config_file('download_folder', json.dumps(self.download_dir), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'watch_locales'):
                watch_locales = conf_parser.get('main', 'watch_locales')
                if watch_locales:
                    self.watch_locales = set(watch_locales.split(','))
                else:
                    # there are no watch locales, so set it to an empty set
                    self.watch_locales = set()
            else:
                self.watch_locales = set()
                self.update_config_file('watch_locales', json.dumps(list(self.watch_locales)), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'locale_folders'):
                self.locale_folders = json.loads(conf_parser.get('main', 'locale_folders'))
                locale_folders = {}
                #for key, value in self.locale_folders.items():
                #    key = key.replace('_', '-');
                #    locale_folders[key] = value
                #self.locale_folders = locale_folders
            else:
                self.locale_folders = {}
                self.update_config_file('locale_folders', json.dumps(self.locale_folders), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'download_option'):
                self.download_option = conf_parser.get('main', 'download_option')
            else:
                self.download_option = 'clone'
                self.update_config_file('download_option', self.download_option, conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'clone_option'):
                self.clone_option = conf_parser.get('main', 'clone_option')
            else:
                self.clone_option = 'on'
                self.update_config_file('clone_option', self.clone_option, conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'git_autocommit'):
                self.git_autocommit = conf_parser.get('main', 'git_autocommit')
            else:
                self.git_autocommit = ''
                self.update_config_file('git_autocommit', self.git_autocommit, conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'git_username'):
                self.git_username = conf_parser.get('main', 'git_username')
            else:
                self.git_username = ''
                self.update_config_file('git_username', self.git_username, conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'git_password'):
                self.git_password = conf_parser.get('main', 'git_password')
            else:
                self.git_password = ''
                self.update_config_file('git_password', self.git_password, conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'append_option'):
                self.append_option = conf_parser.get('main', 'append_option')
            else:
                self.append_option = 'none'
                self.update_config_file('append_option', self.append_option, conf_parser, config_file_name, "")
        except NoOptionError as e:
            if not self.project_name:
                self.api = ApiCalls(self.host, self.access_token)
                project_info = self.api.get_project_info(self.community_id)
                self.project_name = project_info[self.project_id]
                config_file_name, conf_parser = self.init_config_file()
                log_info = 'Updated project name'
                self.update_config_file('project_name', self.project_name, conf_parser, config_file_name, log_info)

    def _add_document(self, file_name, title, doc_id):
        """ adds a document to db """
        now = time.time()
        # doc_id = json['properties']['id']
        full_path = os.path.join(self.path, file_name)
        last_modified = os.stat(full_path).st_mtime
        self.doc_manager.add_document(title, now, doc_id, last_modified, now, file_name)

    def _update_document(self, file_name):
        """ updates a document in the db """
        now = time.time()
        file_path = os.path.join(self.path, file_name)
        # sys_last_modified = os.stat(file_name).st_mtime
        sys_last_modified = os.stat(file_path).st_mtime
        entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
        doc_id = entry['id']
        self.doc_manager.update_document('last_mod', now, doc_id)
        self.doc_manager.update_document('sys_last_mod', sys_last_modified, doc_id)
        # whenever a document is updated, it should have new translations
        self.doc_manager.update_document('downloaded', [], doc_id)

    def close(self):
        self.doc_manager.close_db()

    def open(self):
        self.doc_manager.open_db()

    def init_config_file(self):
        config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
        conf_parser = ConfigParser()
        conf_parser.read(config_file_name)
        return config_file_name, conf_parser

    def update_config_file(self, option, value, conf_parser, config_file_name, log_info):
        try:
            conf_parser.set('main', option, value)
            with open(config_file_name, 'w') as new_file:
                conf_parser.write(new_file)
            self._initialize_self()
            if (len(log_info)):
                logger.info(log_info+"\n")
        except IOError as e:
            print(e.errno)
            print(e)

    def get_relative_path(self, path):
        return get_relative_path(self.path, path)

    def get_current_path(self, path):
        cwd = os.getcwd()
        if cwd in path:
            path = path.replace(cwd,"")
            return path
        else:
            cwd_relative_path = cwd.replace(self.path,"")
            return path.replace(cwd_relative_path+os.sep,"")

    def get_current_abs(self, path):
        # print("orig path: "+str(path))
        cwd = os.getcwd()
        if cwd in path:
            path = path.replace(cwd,"")
        else:
            # print("cwd: "+cwd)
            # print("self.path: "+self.path)
            cwd_relative_path = cwd.replace(self.path,"")
            # print("cwd relative path: "+cwd_relative_path)
            cwd_path = path.replace(cwd_relative_path+os.sep,"")
            # print("cwd path: "+cwd_path)
            path = cwd_path
        # print("current path: "+path)
        # print("abs path: "+os.path.abspath(path))
        return os.path.abspath(path)

    def norm_path(self, file_location):
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

    def get_docs_in_path(self, path):
        files = get_files(path)
        db_files = self.doc_manager.get_file_names()
        docs = []
        if files:
            for file in files:
                file_name = self.norm_path(file)
                if file_name in db_files:
                    docs.append(self.doc_manager.get_doc_by_prop('file_name',file_name))
        return docs

    def get_doc_filenames_in_path(self, path):
        files = get_files(path)
        db_files = self.doc_manager.get_file_names()
        docs = []
        if files:
            for file in files:
                file_name = self.norm_path(file)
                if file_name in db_files:
                    docs.append(file_name)
        return docs

    def get_doc_locales(self, doc_id, doc_name):
        locales = []
        response = self.api.document_translation_status(doc_id)
        if response.status_code != 200:
            if check_response(response) and response.json()['messages'] and 'No translations exist' in response.json()['messages'][0]:
                return locales
            if doc_name:
                raise_error(response.json(), 'Failed to check target locales for document '+doc_name, True, doc_id)
            else:
                raise_error(response.json(), 'Failed to check target locales for document '+doc_id, True, doc_id)

        try:
            if 'entities' in response.json():
                for entry in response.json()['entities']:
                    locales.append(entry['properties']['locale_code'])
        except KeyError as e:
            print("Error listing translations")
            return
            # return detailed_status
        return locales

    def is_locale_folder_taken(self, new_locale, path):
        # Python 2
        # for locale, folder in self.locale_folders.iteritems():
        # End Python 2
        # Python 3
        for locale, folder in self.locale_folders.items():
        # End Python 3
            if path == folder and not locale == new_locale:
                return locale
        return False

    def update_document_action(self, file_name, title=None, **kwargs):
        try:
            relative_path = self.norm_path(file_name)
            entry = self.doc_manager.get_doc_by_prop('file_name', relative_path)
            try:
                document_id = entry['id']
            except TypeError as e:
                log_error(self.error_file_name, e)
                logger.error("Document name specified for update doesn't exist: {0}".format(title))
                return
            if title:
                response = self.api.document_update(document_id, file_name, title=title, **kwargs)
            else:
                response = self.api.document_update(document_id, file_name)
            if response.status_code != 202:
                raise_error(response.json(), "Failed to update document {0}".format(file_name), True)
            self._update_document(relative_path)
            return True
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on updating document"+str(file_name)+": "+str(e))

    def _target_action_db(self, to_delete, locales, document_id):
        if to_delete:
            curr_locales = self.doc_manager.get_doc_by_prop('id', document_id)['locales']
            updated_locales = set(curr_locales) - set(locales)
            self.doc_manager.update_document('locales', updated_locales, document_id)
        else:
            self.doc_manager.update_document('locales', list(locales), document_id)

    def update_doc_locales(self, document_id):
        try:
            locale_map = self.import_locale_info(document_id)
            locale_info = list(iter(locale_map))
        except exceptions.RequestFailedError as e:
            log_error(self.error_file_name, e)
            locale_info = []
        self.doc_manager.update_document('locales', locale_info, document_id)

    def added_folder_of_file(self, file_path):
        folders = self.folder_manager.get_file_names()
        if not folders:
            #print("not folders")
            return
        for folder in folders:
            folder = os.path.join(self.path, folder)
            if folder in file_path:
                return folder

    def get_new_name(self, file_name, curr_path):
        i = 1
        file_path = os.path.join(curr_path, file_name)
        name, extension = os.path.splitext(file_name)
        while os.path.isfile(file_path):
            new_name = '{name}({i}){ext}'.format(name=name, i=i, ext=extension)
            file_path = os.path.join(curr_path, new_name)
            i += 1
        return file_path

    def import_locale_info(self, document_id, poll=False):
        locale_progress = {}
        response = self.api.document_translation_status(document_id)
        if response.status_code != 200:
            if poll or response.status_code == 404:
                return {}
            else:
                # raise_error(response.json(), 'Failed to get locale details of document', True)
                raise exceptions.RequestFailedError('Failed to get locale details of document')
        try:
            for entry in response.json()['entities']:
                curr_locale = entry['properties']['locale_code']
                curr_progress = int(entry['properties']['percent_complete'])
                curr_locale = curr_locale.replace('-', '_')
                locale_progress[curr_locale] = curr_progress
        except KeyError:
            pass
        return locale_progress

    def delete_local(self, title, document_id, message=None):
        # print('local delete:', title, document_id)
        if not title:
            title = document_id
        message = '{0} has been deleted locally'.format(title) if not message else message
        try:
            file_name = self.doc_manager.get_doc_by_prop('id', document_id)['file_name']
        except TypeError:
            logger.info('Document to remove not found in the local database')
            return
        try:
            os.remove(os.path.join(self.path, file_name))
            logger.info(message)
        except OSError:
            logger.info('Something went wrong trying to delete the local file')

    def delete_local_translation(self, file_name):
        try:
            if not file_name:
                logger.info('Please provide a valid file name')

            logger.info('{0} (local translation) has been deleted'.format(self.get_relative_path(file_name)))

            os.remove(os.path.join(self.path, file_name))

        except OSError:
            logger.info('Something went wrong trying to download the local translation')

    def delete_local_path(self, path, message=None):
        path = self.norm_path(path)
        message = '{0} has been deleted locally.'.format(path) if not message else message
        try:
            os.remove(path)
            logger.info(message)
        except OSError:
            logger.info('Something went wrong trying to delete the local file')

def raise_error(json, error_message, is_warning=False, doc_id=None, file_name=None):
    try:
        if json:
            error = json['messages'][0]
        file_name = file_name.replace("Status of ", "")
        if file_name is not None and doc_id is not None:
            error = error.replace(doc_id, file_name+" ("+doc_id+")")
        # Sometimes api returns vague errors like 'Unknown error'
        if error == 'Unknown error':
            error = error_message
        if not is_warning:
            raise exceptions.RequestFailedError(error)
        # warnings.warn(error)
        logger.error(error)
    except (AttributeError, IndexError):
        if not is_warning:
            raise exceptions.RequestFailedError(error_message)
        # warnings.warn(error_message)
        logger.error(error_message)

def is_initialized(project_path):
    ltk_path = os.path.join(project_path, CONF_DIR)
    if os.path.isdir(ltk_path) and os.path.isfile(os.path.join(ltk_path, CONF_FN)) and \
            os.stat(os.path.join(ltk_path, CONF_FN)).st_size:
        return True
    return False

def choice_mapper(info):
    mapper = {}
    import operator

    #sorted_info = sorted(info.iteritems(), key=operator.itemgetter(1))
    sorted_info = sorted(info.items(), key = operator.itemgetter(1))

    index = 0
    for entry in sorted_info:
        if entry[0] and entry[1]:
            mapper[index] = {entry[0]: entry[1]}
            index += 1
    for k,v in mapper.items():
        try:
            for values in v:
                print ('({0}) {1} ({2})'.format(k, v[values], values))
        except UnicodeEncodeError:
            continue
    return mapper

def find_conf(curr_path):
    """
    check if the conf folder exists in current directory's parent directories
    """
    if os.path.isdir(os.path.join(curr_path, CONF_DIR)):
        return curr_path
    elif curr_path == os.path.abspath(os.sep):
        return None
    else:
        return find_conf(os.path.abspath(os.path.join(curr_path, os.pardir)))

def printResponseMessages(response):
    for message in response.json()['messages']:
        logger.info(message)

def get_files(patterns):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """

    cwd = os.getcwd()
    if isinstance(patterns,str):
        patterns = [patterns]
    allPatterns = []
    if isinstance(patterns,list) or isinstance(patterns,tuple):
        for pattern in patterns:
            basename = os.path.basename(pattern)
            if basename and basename != "":
                allPatterns.extend(getRegexFiles(pattern,cwd))
            else:
                allPatterns.append(pattern)
    else:
        basename = os.path.basename(patterns)
        if basename and basename != "":
            allPatterns.extend(getRegexFiles(patterns,cwd))
        else:
            allPatterns.append(patterns)
    matched_files = []
    # print("all patterns: "+str(allPatterns))
    for pattern in allPatterns:
        path = os.path.abspath(pattern)
        # print("looking at path "+str(path))
        # check if pattern contains subdirectory
        if os.path.exists(path):
            if os.path.isdir(path):
                for root, subdirs, files in os.walk(path):
                    # split_path = root.split(os.sep)
                    # print("split_path: {0}".format(split_path))
                    for file in files:
                        if not (("desktop.ini" in file) or ('Thumbs.db' in file) or ('ehthumbs.db' in file)):   # don't add desktop.ini, Thumbs.db, or ehthumbs.db files
                            matched_files.append(os.path.join(root, file))
            else:
                matched_files.append(path)
        # else:
        #     logger.info("File not found: "+pattern)
        # subdir_pat, fn_pat = os.path.split(pattern)
        # if not subdir_pat:
        #     for path, subdirs, files in os.walk(root):
        #         for fn in fnmatch.filter(files, pattern):
        #             matched_files.append(os.path.join(path, fn))
        # else:
        #     for path, subdirs, files in os.walk(root):
        #         # print os.path.split(path)
        #         # subdir = os.path.split(path)[1]  # get current subdir
        #         search_root = os.path.join(root, '')
        #         subdir = path.replace(search_root, '')
        #         # print subdir, subdir_pat
        #         if fnmatch.fnmatch(subdir, subdir_pat):
        #             for fn in fnmatch.filter(files, fn_pat):
        #                 matched_files.append(os.path.join(path, fn))
    if len(matched_files) == 0:
        return None
    return matched_files

def getRegexFiles(pattern,path):
    dir_name = os.path.dirname(pattern)
    if dir_name:
        path = os.path.join(path,dir_name)
    pattern_name = os.path.basename(pattern)
    # print("path: "+path)
    # print("pattern: "+str(pattern))
    matched_files = []
    if pattern_name and not "*" in pattern:
        return [pattern]
    for path, subdirs, files in os.walk(path):
        for fn in fnmatch.filter(files, pattern):
            matched_files.append(os.path.join(path, fn))
    # print("matched files: "+str(matched_files))
    return matched_files

def log_id_names(json):
    """
    logs the id and titles from a json object
    """
    ids = []
    titles = []
    for entity in json['entities']:
        ids.append(entity['properties']['id'])
        titles.append(entity['properties']['title'])
    return ids, titles
