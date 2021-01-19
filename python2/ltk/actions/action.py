# Using the following encoding: utf-8
# Python 2
from ConfigParser import ConfigParser, NoOptionError
# End Python 2
# Python 3
# from configparser import ConfigParser, NoOptionError
# End Python 3
import requests
import ctypes
import ltk.check_connection
import os
import shutil
import fnmatch
import time
import getpass
import itertools
import copy
from ltk import exceptions
from ltk.apicalls import ApiCalls
from ltk.utils import *
from ltk.managers import DocumentManager, FolderManager
from ltk.constants import CONF_DIR, CONF_FN, SYSTEM_FILE, ERROR_FN, METADATA_FIELDS
import json
from ltk.logger import logger
from ltk.git_auto import Git_Auto
from tabulate import tabulate

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
        self.always_check_latest_doc = 'off'
        self.clone_option = 'on'
        self.finalized_file = 'off'
        self.unzip_file = 'on'
        self.auto_format_option = ''
        self.download_option = 'clone'
        self.download_dir = None  # directory where downloaded translation will be stored
        self.watch_locales = set()  # if specified, add these target locales to any files in the watch folder
        self.git_autocommit = None
        self.git_username = ''
        self.git_password = ''
        self.append_option = 'none'
        self.locale_folders = {}
        self.default_metadata = {}
        self.metadata_prompt = False
        self.metadata_fields = METADATA_FIELDS
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

    def is_hidden_file(self, file_path):
        # todo more robust checking for OSX files that doesn't start with '.'
        name = os.path.abspath(file_path).replace(self.path, "")
        if self.has_hidden_attribute(file_path) or ('Thumbs.db' in file_path) or ('ehthumbs.db' in file_path):
            return True
        while name != "":
            if name.startswith('.') or name.startswith('~') or name == "4913":
                return True
            name = name.split(os.sep)[1:]
            name = (os.sep).join(name)
        return False

    def has_hidden_attribute(self, file_path):
        """ Detects if a file has hidden attributes """
        try:
            # Python 2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(file_path))
            # End Python 2
            # Python 3
#             attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
            # End Python 3
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError):
            result = False
        return result

    def append_location(self, name, path_to_file, in_directory=False):
        repo_directory = path_to_file
        path_sep = os.sep
        config_file_name, conf_parser = self.init_config_file()
        if not conf_parser.has_option('main', 'append_option'): self.update_config_file('append_option', 'none', conf_parser, config_file_name, 'Update: Added optional file location appending (ltk config --help)')
        append_option = conf_parser.get('main', 'append_option')
        if not in_directory:
            while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + os.sep+".ltk")):
                repo_directory = repo_directory.split(path_sep)[:-1]
                repo_directory = path_sep.join(repo_directory)
            if repo_directory == "" and append_option != 'none':
                logger.warning('Error: File must be contained within an ltk-initialized directory')
                return name
            path_to_file = path_to_file.replace(repo_directory, '', 1).strip(os.sep)
        if append_option == 'none': return name
        elif append_option == 'full': return '{0} ({1})'.format(name, path_to_file.rstrip(name).rstrip(os.sep))
        elif len(append_option) > 5 and append_option[:5] == 'name:':
            folder_name = append_option[5:]
            if folder_name in path_to_file:
                return '{0} ({1})'.format(name, path_to_file[path_to_file.find(folder_name)+len(folder_name):].rstrip(name).strip(os.sep))
            else: return '{0} ({1})'.format(name, path_to_file.rstrip(name).rstrip(os.sep))
        elif len(append_option) > 7 and append_option[:7] == 'number:':
            try: folder_number = int(append_option[7:])
            except ValueError:
                logger.warning('Error: Value after "number" must be an integer')
                return name
            if(folder_number >=0):
                return '{0} ({1})'.format(name, path_sep.join(path_to_file.rstrip(name).rstrip(os.sep).split(path_sep)[(-1*folder_number) if folder_number != 0 else len(path_to_file):]))
            else:
                logger.warning('Error: Value after "number" must be a non-negative integer')
                return name
        else:
            logger.warning('Error: Invalid value listed for append option. Please update; see ltk config --help')

    def add_document(self, file_name, title, doc_metadata={}, **kwargs):
        ''' adds the document to Lingotek cloud and the db '''
        if ltk.check_connection.check_for_connection() == False:
            logger.warning("Cannot connect to network. Documents added to the watch folder will be translated after you reconnect to the network.")
            while ltk.check_connection.check_for_connection() == False:
                time.sleep(15)

        if self.is_hidden_file(file_name):
            return
        try:
            if not 'locale' in kwargs or not kwargs['locale']:
                locale = self.locale
            else:
                locale = kwargs['locale']

            # add document to Lingotek cloud
            response = self.api.add_document(locale, file_name, self.project_id, self.append_location(title, file_name), doc_metadata, **kwargs)
            if response.status_code == 402:
                raise_error(response.json(), "", True)
            elif response.status_code != 202:
                raise_error(response.json(), "Failed to add document {0}\n".format(title), True)
            else:
                title = self.append_location(title, file_name)
                logger.info('Added document {0} with ID {1}\n'.format(title,response.json()['properties']['id']))
                relative_path = self.norm_path(file_name)

                # add document to the db
                if 'download_folder' in kwargs and kwargs['download_folder']:
                    self._add_document(relative_path, title, response.json()['properties']['id'], response.json()['properties']['process_id'], kwargs['download_folder'])
                else:
                    self._add_document(relative_path, title, response.json()['properties']['id'], response.json()['properties']['process_id'])
                if 'translation_locale_code' in kwargs and kwargs['translation_locale_code']:
                    self._update_document(relative_path, None, kwargs['translation_locale_code'])
        except KeyboardInterrupt:
            raise_error("", "Canceled adding document\n")
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS\n")
            else:
                logger.error("Error on adding document \n"+str(file_name)+": "+str(e))

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
        self.always_check_latest_doc = conf_parser.get('main', 'always_check_latest_doc')


        self.locale = self.locale.replace('_','-')
        try:
            if conf_parser.has_option('main', 'auto_format'):
                self.auto_format_option = conf_parser.get('main', 'auto_format')
            else:
                self.update_config_file('auto_format', 'on', conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'finalized_file'):
                self.finalized_file = conf_parser.get('main', 'finalized_file')
            else:
                self.update_config_file('finalized_file', 'off', conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'unzip_file'):
                self.unzip_file = conf_parser.get('main', 'unzip_file')
            else:
                self.update_config_file('unzip_file', 'on', conf_parser, config_file_name, "")
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
            if conf_parser.has_option('main', 'always_check_latest_doc'):
                self.always_check_latest_doc = conf_parser.get('main', 'always_check_latest_doc')
            else:
                self.always_check_latest_doc = 'off'
                self.update_config_file('always_check_latest_doc', self.always_check_latest_doc, conf_parser, config_file_name, "")
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
            if conf_parser.has_option('main', 'default_metadata'):
                self.default_metadata = json.loads(conf_parser.get('main', 'default_metadata'))
            else:
                self.default_metadata = {}
                self.update_config_file('default_metadata', json.dumps(self.default_metadata), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'metadata_prompt'):
                self.metadata_prompt = (conf_parser.get('main', 'metadata_prompt').lower() == 'on')
            else:
                self.metadata_prompt = False
                self.update_config_file('metadata_prompt', 'off', conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'metadata_fields'):
                self.metadata_fields = json.loads(conf_parser.get('main', 'metadata_fields'))
            else:
                self.metadata_fields = METADATA_FIELDS
                self.update_config_file('metadata_fields', json.dumps(self.metadata_fields), conf_parser, config_file_name, "")

        except NoOptionError as e:
            if not self.project_name:
                self.api = ApiCalls(self.host, self.access_token)
                project_info = self.api.get_project_info(self.community_id)
                self.project_name = project_info[self.project_id]
                config_file_name, conf_parser = self.init_config_file()
                log_info = 'Updated project name'
                self.update_config_file('project_name', self.project_name, conf_parser, config_file_name, log_info)

    def _add_document(self, file_name, title, doc_id, process_id, dl_folder=''):
        """ adds a document to db """
        now = time.time()
        # doc_id = json['properties']['id']
        full_path = os.path.join(self.path, file_name)
        last_modified = os.stat(full_path).st_mtime
        if dl_folder:
            dl_folder = os.path.relpath(dl_folder, self.path)
        self.doc_manager.add_document(title, now, doc_id, last_modified, now, file_name, process_id, dl_folder)

    def _update_document(self, file_name, next_document_id=None, locales=None):
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
        if next_document_id:
            self.doc_manager.update_document('id', next_document_id, doc_id)
            doc_id = next_document_id
        if locales:
            self.doc_manager.update_document('locales', locales, doc_id)

    def locked_doc_response_manager(self, response, document_id, *args, **kwargs):
        if response.status_code == 423 and 'next_document_id' in response.json():
            self.doc_manager.update_document('id', response.json()['next_document_id'], document_id)
            return self.api.document_update(response.json()['next_document_id'], *args, **kwargs), response.json()['next_document_id']
        return response, document_id

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

    def metadata_wizard(self, set_defaults=False):
        import re
        if set_defaults:
            fields = METADATA_FIELDS
            new_metadata = {}
            prompt_message = "Default Value: "
        else:
            fields = self.metadata_fields
            new_metadata = copy.deepcopy(self.default_metadata) 
            prompt_message = "Value: "
            if all (field in self.default_metadata for field in fields):
                print("All fields have default metadata already set")
                for field in fields:
                    print(field,": ",self.default_metadata[field])
                return self.default_metadata
        for field in fields:
            print("\n===",field,"===")
            if field in self.default_metadata and self.default_metadata[field]:
                if set_defaults:
                    print("Current "+prompt_message,self.default_metadata[field])
                    if not yes_no_prompt("Would you like to change the default value for this field?", default_yes=False):
                        new_metadata[field] = self.default_metadata[field]
                        continue
                else:
                    print(prompt_message,self.default_metadata[field])
                    continue
            # Python 2
            new_value = raw_input(prompt_message)
            # End Python 2
            # Python 3
#             new_value = input(prompt_message)
#             #End Python 3
#             if not new_value:
#                 continue
#             #validate campaign rating field, which is a number field with a maximum of seven digits and allows positive and negative numbers but no decimals
#             if field == "campaign_rating":
#                 while not re.fullmatch('-?0*[0-9]{1,7}', new_value):
#                     print("Value must be an integer between -9999999 and 9999999")
#                     new_value = input(prompt_message)
#                     #allow blank value to not set/change the field in defaults
#                     if not new_value:
#                         break
#                 if not new_value: #check if value was unset
#                     continue
#                 #catch -0 and convert it to 0
#                 if re.fullmatch('-0+', new_value):
#                     new_value = "0"
#             #validate require review field, which is either true or false
#             elif field == "require_review":
#                 while new_value.upper() != "TRUE" and new_value.upper() != "FALSE":
#                     print("Value must be either TRUE or FALSE")
#                     new_value = input(prompt_message)
#                     #allow blank value to not set/change the field in defaults
#                     if not new_value:
#                         break
#                 if not new_value: #check if value was unset
#                     continue
#             new_metadata[field] = new_value
#         return new_metadata
# 
#     def validate_metadata_fields(self, field_options):
#         if field_options.lower() == 'all' or field_options == '':
#             return True, METADATA_FIELDS
#         else:
#             converted = field_options.replace(", ",",") #allows for a comma-separated list with or without a single space after commas
#             options = converted.split(",")
#             for option in options:
#                 if option not in METADATA_FIELDS:
#                     logger.warning("Error: {0} is not a valid metadata field".format(option))
#                     return False, None
#             return True, options
# 
#     def get_relative_path(self, path):
#         return get_relative_path(self.path, path)
# 
#     def get_current_path(self, path):
#         cwd = os.getcwd()
#         if cwd in path:
#             path = path.replace(cwd,"")
#             return path
#         else:
#             cwd_relative_path = cwd.replace(self.path,"")
#             return path.replace(cwd_relative_path+os.sep,"")
# 
#     def get_current_abs(self, path):
#         # print("orig path: "+str(path))
#         cwd = os.getcwd()
#         if cwd in path:
#             path = path.replace(cwd,"")
#         else:
#             # print("cwd: "+cwd)
#             # print("self.path: "+self.path)
#             cwd_relative_path = cwd.replace(self.path,"")
#             # print("cwd relative path: "+cwd_relative_path)
#             cwd_path = path.replace(cwd_relative_path+os.sep,"")
#             # print("cwd path: "+cwd_path)
#             path = cwd_path
#         # print("current path: "+path)
#         # print("abs path: "+os.path.abspath(path))
#         return os.path.abspath(path)
# 
#     def norm_path(self, file_location):
#         # print("original path: "+str(file_location))
#         if file_location:
#             file_location = os.path.normpath(file_location)
#             # abspath=os.path.abspath(file_location)
#             # print("abspath: "+str(os.path.abspath(os.path.expanduser(file_location))))
#             # print("self.path: "+self.path)
#             # print("cwd: "+str(os.getcwd()))
#             norm_path = os.path.abspath(os.path.expanduser(file_location)).replace(self.path, '')
#             # print("normalized path: "+norm_path)
#             # print("joined path: "+str(os.path.join(self.path,file_location)))
#             # if file_location == ".." and self.path.rstrip('/') in norm_path:
#             #     return norm_path.replace(self.path.rstrip('/'), '')
#             if file_location is not "." and ".." not in file_location and os.path.exists(os.path.join(self.path,file_location)):
#                 # print("returning original path: "+str(file_location))
#                 return file_location.replace(self.path, '')
#             elif ".." in file_location and file_location != "..":
#                 # print("returning norm path: "+norm_path)
#                 return norm_path.replace(self.path,'')
#             if not os.path.exists(os.path.join(self.path,norm_path)) and os.path.exists(os.path.join(self.path,file_location)):
#                 # print("Starting path at project directory: "+file_location.replace(self.path, ''))
#                 return os.path.abspath(os.path.expanduser(file_location.replace(self.path, ''))).replace(self.path, '')
#             elif file_location == "..":
#                 return os.path.abspath(os.path.expanduser(file_location.replace(self.path, ''))).replace(self.path, '')
#             return norm_path
#         else:
#             return None
# 
#     def get_docs_in_path(self, path):
#         files = get_files(path)
#         db_files = self.doc_manager.get_file_names()
#         docs = []
#         if files:
#             for file in files:
#                 file_name = self.norm_path(file)
#                 if file_name in db_files:
#                     docs.append(self.doc_manager.get_doc_by_prop('file_name',file_name))
#         return docs
# 
#     def get_doc_filenames_in_path(self, path):
#         files = get_files(path)
#         db_files = self.doc_manager.get_file_names()
#         docs = []
#         if files:
#             for file in files:
#                 file_name = self.norm_path(file)
#                 if file_name in db_files:
#                     docs.append(file_name)
#         return docs
# 
#     def get_doc_locales(self, doc_id, doc_name):
#         locales = []
#         response = self.api.document_translation_status(doc_id)
#         if response.status_code != 200:
#             if check_response(response) and response.json()['messages'] and 'No translations exist' in response.json()['messages'][0]:
#                 return locales
#             if doc_name:
#                 raise_error(response.json(), 'Failed to check target locales for document '+doc_name, True, doc_id)
#             else:
#                 raise_error(response.json(), 'Failed to check target locales for document '+doc_id, True, doc_id)
# 
#         try:
#             if 'entities' in response.json():
#                 for entry in response.json()['entities']:
#                     locales.append(entry['properties']['locale_code'])
#         except KeyError as e:
#             print("Error listing translations")
#             return
#             # return detailed_status
#         return locales
# 
#     def is_locale_folder_taken(self, new_locale, path):
        # Python 2
        for locale, folder in self.locale_folders.iteritems():
        # End Python 2
        # Python 3
#         for locale, folder in self.locale_folders.items():
        # End Python 3
            if path == folder and not locale == new_locale:
                return locale
        return False

    def get_latest_document_version(self, document_id):
        if self.always_check_latest_doc == 'off':
            return False
        try:
            response = self.api.get_latest_document(document_id)
            if response.status_code != 200:
                print('Latest document was not found')
                return False
            else:
                latest_id = response.json()['properties']['id']
                return latest_id
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error('Error on getting latest document')
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
                response, previous_doc_id = self.locked_doc_response_manager(self.api.document_update(document_id, file_name, title=title, **kwargs), document_id, file_name, title=title, **kwargs)
            else:
                response, previous_doc_id = self.locked_doc_response_manager(self.api.document_update(document_id, file_name), document_id, file_name, **kwargs)

            if response.status_code == 410:
                target_locales = entry['locales']
                self.doc_manager.remove_element(previous_doc_id)
                print('Document has been archived. Reuploading...')
                self.add_document(file_name, title, self.default_metadata, translation_locale_code=target_locales)
                return True
            elif response.status_code == 402:
                raise_error(response.json(), "Community has been disabled. Please contact support@lingotek.com to re-enable your community", True)
            elif response.status_code == 202:
                try:
                    next_document_id = response.json()['next_document_id']
                except Exception:
                    next_document_id = None
                finally:
                    self._update_document(relative_path, next_document_id)
                    return True
            else:
                raise_error(response.json(), "Failed to update document {0}".format(file_name), True)
                return False
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on updating document"+str(file_name)+": "+str(e))
            return False

    def _target_action_db(self, to_delete, locales, document_id):
        locale_set = set()
        for locale in locales:
            locale_set.add(locale.replace("-", "_"))
        if to_delete:
            curr_locales = self.doc_manager.get_doc_by_prop('id', document_id)['locales']
            updated_locales = set(curr_locales) - locale_set
            self.doc_manager.update_document('locales', updated_locales, document_id)
        else:
            self.doc_manager.update_document('locales', list(locales), document_id)

    def update_doc_locales(self, document_id, include_cancelled=False):
        try:
            locale_map = self.import_locale_info(document_id, include_cancelled)
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

    def import_locale_info(self, document_id, poll=False, include_cancelled=False):
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
                curr_status = entry['properties']['status']
                curr_locale = curr_locale.replace('-', '_')
                if include_cancelled or (curr_status.upper() != 'CANCELLED'):
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

def is_initialized(project_path):
    ltk_path = os.path.join(project_path, CONF_DIR)
    if os.path.isdir(ltk_path) and os.path.isfile(os.path.join(ltk_path, CONF_FN)) and \
            os.stat(os.path.join(ltk_path, CONF_FN)).st_size:
        return True
    return False

def choice_mapper(info):
    mapper = {}
    import operator

    sorted_info = sorted(info.items(), key = operator.itemgetter(1))

    index = 0
    for entry in sorted_info:
        if entry[0] and entry[1]:
            mapper[index] = {entry[0]: entry[1]}
            index += 1
    table = []
    for k,v in mapper.items():
        try:
            headers=["ID","Name","UUID"]
            for values in v:
                table.append([ k, v[values], values ])
        except UnicodeEncodeError:
            continue
    print(tabulate(table, headers=headers))
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
