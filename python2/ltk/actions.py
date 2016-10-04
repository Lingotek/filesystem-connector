# Using the following encoding: utf-8
# Python 2
from ConfigParser import ConfigParser, NoOptionError
# End Python 2
# Python 3
# from configparser import ConfigParser, NoOptionError
# End Python 3
import requests
import os
import shutil
import fnmatch
import time
import getpass
from ltk import exceptions
from ltk.apicalls import ApiCalls
from ltk.utils import check_response, detect_format, map_locale, get_valid_locales, is_valid_locale, underline, remove_begin_slashes, remove_end_slashes, remove_last_folder_in_path, get_relative_path, log_error
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
        self.download_option = 'same'
        self.download_dir = None  # directory where downloaded translation will be stored
        self.watch_locales = set()  # if specified, add these target locales to any files in the watch folder
        self.git_autocommit = None
        self.git_username = ''
        self.git_password = ''
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
        try:
            if conf_parser.has_option('main', 'project_name'):
                self.project_name = conf_parser.get('main', 'project_name')
            if conf_parser.has_option('main', 'download_folder'):
                self.download_dir = conf_parser.get('main', 'download_folder')
            else:
                self.download_dir = None
                self.update_config_file('download_folder', json.dumps(self.download_dir), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'watch_locales'):
                watch_locales = conf_parser.get('main', 'watch_locales')
                self.watch_locales = set(watch_locales.split(','))
            else:
                self.watch_locales = set()
                self.update_config_file('watch_locales', json.dumps(list(self.watch_locales)), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'locale_folders'):
                self.locale_folders = json.loads(conf_parser.get('main', 'locale_folders'))
            else:
                self.locale_folders = {}
                self.update_config_file('locale_folders', json.dumps(self.locale_folders), conf_parser, config_file_name, "")
            if conf_parser.has_option('main', 'download_option'):
                self.download_option = conf_parser.get('main', 'download_option')
            else:
                self.download_option = 'same'
                self.update_config_file('download_option', self.download_option, conf_parser, config_file_name, "")
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

    def _is_folder_added(self, file_name):
        """ checks if a folder has been added or is a subfolder of an added folder """
        folder_names = self.folder_manager.get_file_names()
        for folder in folder_names:
            # print("folder: "+str(os.path.join(self.path,folder)))
            # print("folder to be added: "+os.path.abspath(file_name))
            if os.path.join(self.path,folder) in os.path.abspath(file_name):
                return True
        return False

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
        conf_parser.set('main', option, value)
        with open(config_file_name, 'w') as new_file:
            conf_parser.write(new_file)
        self._initialize_self()
        if (len(log_info)):
            logger.info(log_info+"\n")

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

    def append_location(self, name, path_to_file, in_directory=False):
        repo_directory = path_to_file
        path_sep = os.sep
        if not in_directory:
            while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.ltk")):
                repo_directory = repo_directory.split(path_sep)[:-1]
                repo_directory = path_sep.join(repo_directory)
            if repo_directory == "":
                logger.warning('Error: File must be contained within an ltk-initialized directory')
                return name
            path_to_file = path_to_file.replace(repo_directory, '', 1).strip(os.sep)
        config_file_name, conf_parser = self.init_config_file()
        if not conf_parser.has_option('main', 'append_option'): self.update_config_file('append_option', 'none', conf_parser, config_file_name, 'Update: Added optional file location appending (ltk config --help)')
        append_option = conf_parser.get('main', 'append_option')
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

    def norm_path(self, file_location):
        # print("original path: "+str(file_location))
        if file_location:
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
        for locale, folder in self.locale_folders.iteritems():
        # End Python 2
        # Python 3
#         for locale, folder in self.locale_folders.items():
        # End Python 3
            if path == folder and not locale == new_locale:
                return locale
        return False

    def config_action(self, **kwargs):
        try:
            config_file_name, conf_parser = self.init_config_file()
            print_config = True
            if 'locale' in kwargs and kwargs['locale']:
                self.locale = kwargs['locale']
                log_info = 'Project default locale has been updated to {0}'.format(self.locale)
                self.update_config_file('default_locale', locale, conf_parser, config_file_name, log_info)
            if 'workflow_id' in kwargs and kwargs['workflow_id']:
                workflow_id = kwargs['workflow_id']
                response = self.api.patch_project(self.project_id, workflow_id)
                if response.status_code != 204:
                    raise_error(response.json(), 'Something went wrong trying to update workflow_id of project')
                self.workflow_id = workflow_id
                log_info = 'Project default workflow has been updated to {0}'.format(workflow_id)
                self.update_config_file('workflow_id', workflow_id, conf_parser, config_file_name, log_info)
                conf_parser.set('main', 'workflow_id', workflow_id)
            if 'download_folder' in kwargs and kwargs['download_folder']:
                download_path = self.norm_path(kwargs['download_folder'])
                if os.path.exists(os.path.join(self.path,download_path)):
                    self.download_dir = download_path
                    log_info = 'Set download folder to {0}'.format(download_path)
                    self.update_config_file('download_folder', download_path, conf_parser, config_file_name, log_info)
                else:
                    logger.warning('Error: Invalid value for "-d" / "--download_folder": The folder {0} does not exist'.format(os.path.join(self.path,download_path)))
                    print_config = False
            if 'download_option' in kwargs and kwargs['download_option']:
                download_option = kwargs['download_option']
                if download_option in {'same','folder','clone'}:
                    self.download_option = download_option
                    log_info = 'Set download option to {0}'.format(download_option)
                    self.update_config_file('download_option', download_option, conf_parser, config_file_name, log_info)
                else:
                    logger.warning('Error: Invalid value for "-o" / "--download_option": Must be one of "same", "folder", or "clone".')
                    print_config = False
            if 'target_locales' in kwargs and kwargs['target_locales']:
                target_locales = kwargs['target_locales']
                locales = []
                for locale in target_locales:
                    locales.extend(locale.split(','))
                if len(locales) > 0 and locales[0].lower() == 'none':
                    log_info = 'Removing all target locales.'
                    self.update_config_file('watch_locales', "", conf_parser, config_file_name, log_info)
                else:
                    target_locales = get_valid_locales(self.api,locales)
                    target_locales_str = ','.join(target for target in target_locales)
                    if len(target_locales_str) > 0:
                        log_info = 'Set target locales to {}'.format(target_locales_str)
                        self.update_config_file('watch_locales', target_locales_str, conf_parser, config_file_name, log_info)
                        self.watch_locales = target_locales
            if 'locale_folder' in kwargs and kwargs['locale_folder']:
                locale_folders = kwargs['locale_folder']
                mult_folders = False
                folders_count = len(locale_folders)
                folders_string = ""
                count = 0
                log_info = ""
                for folder in locale_folders:
                    count += 1
                    if not folder[0] or not folder[1]:
                        logger.warning("Please specify a valid locale and a directory for that locale.")
                        print_config = False
                        continue
                    locale = folder[0].replace("-","_")
                    if not is_valid_locale(self.api, locale):
                        logger.warning(str(locale+' is not a valid locale. See "ltk list -l" for the list of valid locales.'))
                        print_config = False
                        continue
                    if folder[1] == '--none':
                        folders_count -= 1
                        if locale in self.locale_folders:
                            self.locale_folders.pop(locale, None)
                            logger.info("Removing download folder for locale "+str(locale)+"\n")
                        else:
                            logger.info("The locale "+str(locale)+" already has no download folder.\n")
                            print_config = False
                        continue
                    path = self.norm_path(os.path.abspath(folder[1]))
                    if os.path.exists(os.path.join(self.path,path)):
                        taken_locale = self.is_locale_folder_taken(locale, path)
                        if taken_locale:
                            logger.info("The folder "+str(path)+" is already taken by the locale "+str(taken_locale)+".\n")
                            print_config = False
                            continue
                        else:
                            # print("path of new locale folder: "+path)
                            self.locale_folders[locale] = path
                    else:
                        logger.warning('Error: Invalid value for "-p" / "--locale_folder": Path "'+path+'" does not exist.')
                        print_config = False
                        continue
                    folders_string += str(locale) + ": " + str(path)
                    if count < len(locale_folders):
                        folders_string += ", "
                if len(folders_string):
                    if folders_count > 1:
                        log_info = 'Adding locale folders {0}'.format(folders_string)
                    else:
                        log_info = 'Adding locale folder for {0}'.format(folders_string)
                locale_folders_str = json.dumps(self.locale_folders)
                self.update_config_file('locale_folders', locale_folders_str, conf_parser, config_file_name, log_info)
            if 'clear_locales' in kwargs and kwargs['clear_locales']:
                clear_locales = kwargs['clear_locales']
                log_info = "Cleared all locale specific download folders."
                self.locale_folders = {}
                locale_folders_str = json.dumps(self.locale_folders)
                self.update_config_file('locale_folders', locale_folders_str, conf_parser, config_file_name, log_info)
            #print ('Token: {0}'.format(self.access_token))
            if not conf_parser.has_option('main', 'git_autocommit'):
                self.update_config_file('git_autocommit', 'False', conf_parser, config_file_name, 'Update: Added \'git auto-commit\' option (ltk config --help)')
                self.update_config_file('git_username', '', conf_parser, config_file_name, 'Update: Added \'git username\' option (ltk config --help)')
                self.update_config_file('git_password', '', conf_parser, config_file_name, 'Update: Added \'git password\' option (ltk config --help)')
            self.git_autocommit = conf_parser.get('main', 'git_autocommit')
            if 'git' in kwargs and kwargs['git']:
                if self.git_autocommit == 'True' or self.git_auto.repo_exists(self.path):
                    log_info = 'Git auto-commit status changed from {0}active'.format(
                        ('active to in' if self.git_autocommit == "True" else 'inactive to '))
                    config_file = open(config_file_name, 'w')
                    if self.git_autocommit == "True":
                        self.update_config_file('git_autocommit', 'False', conf_parser, config_file_name, log_info)
                        self.git_autocommit = "False"
                    else:
                        self.update_config_file('git_autocommit', 'True', conf_parser, config_file_name, log_info)
                        self.git_autocommit = "True"
            if 'git_credentials' in kwargs and kwargs['git_credentials']:
                # Python 2
                git_username = raw_input('Username: ')
                # End Python 2
                # Python 3
#                 git_username = input('Username: ')
                # End Python 3
                git_password = getpass.getpass()
                if git_username in ['None', 'none', 'N', 'n']:
                    git_username = ""
                    log_info = "Git username disabled"
                else:
                    log_info = 'Git username set to ' + git_username
                self.update_config_file('git_username', git_username, conf_parser, config_file_name, log_info)
                if git_password in ['None', 'none', 'N', 'n']:
                    git_password = ""
                    log_info = "Git password disabled"
                else:
                    log_info = 'Git password set'
                self.update_config_file('git_password', self.git_auto.encrypt(git_password), conf_parser, config_file_name, log_info)
            if 'append_option' in kwargs and kwargs['append_option']:
                append_option = kwargs['append_option']
                if append_option in {'none', 'full'} or append_option[:append_option.find(':')+1] in {'number:', 'name:'}:
                    set_option = True
                    if append_option[:3] == 'num':
                        try: int(append_option[7:])
                        except ValueError:
                            logger.warning('Error: Input after "number" must be an integer')
                            print_config = False
                    elif append_option[:4] == 'name' and len(append_option) <= 5:
                        logger.warning('Error: No input given after "name"')
                        print_config = False
                    if not conf_parser.has_option('main', 'append_option'):
                        self.update_config_file('append_option', 'none', conf_parser, config_file_name, 'Update: Added optional file location appending (ltk config --help)')
                    if print_config:
                        log_info = 'Append option set to ' + append_option
                        self.update_config_file('append_option', append_option, conf_parser, config_file_name, log_info)
                else:
                    logger.warning('Error: Invalid value for "-a" / "--append_option": Must be one of "none", "full", "number:", or "name:".')
                    print_config = False
            download_dir = "None"
            if self.download_dir and str(self.download_dir) != 'null':
                download_dir = self.download_dir
            locale_folders_str = "None"
            if self.locale_folders:
                locale_folders_str = json.dumps(self.locale_folders).replace("{","").replace("}","")
            current_git_username = conf_parser.get('main', 'git_username')
            current_git_password = conf_parser.get('main', 'git_password')
            git_output = ('active' if self.git_autocommit == "True" else 'inactive')
            if self.git_autocommit == "True":
                if current_git_username != "":
                    git_output += (' (' + current_git_username + ', password:' + ('YES' if current_git_password != '' else 'NO')) + ')'
                else:
                    git_output += (' (password:YES)' if current_git_password != '' else ' (no credentials set, recommend SSH key)')
            if print_config:
                watch_locales = ','.join(target for target in self.watch_locales)
                if str(watch_locales) == "[]":
                    watch_locales = ""
                print ('Host: {0}\nLingotek Project: {1} ({2})\nLocal Project Path: {3}\nCommunity ID: {4}\nWorkflow ID: {5}\n' \
                      'Default Source Locale: {6}\nDownload Option: {7}\nDownload Folder: {8}\nTarget Locales (for watch and clone): {9}\nTarget Locale Folders: {10}\nGit Auto-commit: {11}'.format(
                    self.host, self.project_id, self.project_name, self.path, self.community_id, self.workflow_id, self.locale, self.download_option,
                    download_dir, watch_locales, locale_folders_str, git_output))
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on config: "+str(e))

    def add_document(self, file_name, title, **kwargs):
        try:
            if not 'locale' in kwargs or not kwargs['locale']:
                locale = self.locale
            else:
                locale = kwargs['locale']
            response = self.api.add_document(locale, file_name, self.project_id, self.append_location(title, file_name), **kwargs)
            # print("response: "+str(response.json()))
            if response.status_code != 202:
                raise_error(response.json(), "Failed to add document {0}".format(title), True)
            else:
                title = self.append_location(title, file_name)
                logger.info('Added document {0} with ID {1}'.format(title,response.json()['properties']['id']))
                relative_path = self.norm_path(file_name)
                self._add_document(relative_path, title, response.json()['properties']['id'])
        except KeyboardInterrupt:
            raise_error("", "Canceled adding document")
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on adding document "+str(file_name)+": "+str(e))

    def add_action(self, file_patterns, **kwargs):
        # format will be automatically detected by extension but may not be what user expects
        # use current working directory as root for files instead of project root
        try:
            added_folder = False
            for pattern in file_patterns:
                if os.path.exists(pattern):
                    if os.path.isdir(pattern):
                        if not self._is_folder_added(pattern):
                            self.folder_manager.add_folder(self.norm_path(pattern.rstrip(os.sep)))
                            logger.info("Added folder "+str(pattern))
                        else:
                            logger.warning("Folder "+str(pattern)+" has already been added.")
                        added_folder = True
                else:
                    logger.warning("Path \""+str(pattern)+"\" doesn't exist.")
            if 'directory' in kwargs and kwargs['directory']:
                if not added_folder:
                    logger.info("No folders to add at the given path(s).")
                return
            matched_files = get_files(file_patterns)
            if not matched_files:
                if added_folder:
                    return
                else:
                    raise exceptions.ResourceNotFound("Could not find the specified file/pattern.")
            for file_name in matched_files:
                try:
                    # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
                    relative_path = self.norm_path(file_name)
                    title = os.path.basename(relative_path)
                    if not self.doc_manager.is_doc_new(relative_path):
                        if self.doc_manager.is_doc_modified(relative_path, self.path):
                            if 'overwrite' in kwargs and kwargs['overwrite']:
                                confirm = 'Y'
                            else:
                                confirm = 'not confirmed'
                            try:
                                while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                                    prompt_message = "This document already exists. Would you like to overwrite it? [Y/n]: "
                                    # Python 2
                                    confirm = raw_input(prompt_message)
                                    # End Python 2
                                    # Python 3
#                                     confirm = input(prompt_message)
                                    # End Python 3
                                # confirm if would like to overwrite existing document in Lingotek Cloud
                                if not confirm or confirm in ['n', 'N']:
                                    continue
                                else:
                                    logger.info('Overwriting document: {0} in Lingotek Cloud...'.format(title))
                                    self.update_document_action(file_name, title, **kwargs)
                                    continue
                            except KeyboardInterrupt:
                                logger.error("Add canceled")
                                return
                        else:
                            logger.error("This document has already been added: {0}".format(title))
                            continue
                except json.decoder.JSONDecodeError:
                    logger.error("JSON error on adding document.")
                self.add_document(file_name, title, **kwargs)
                # response = self.api.add_document(locale, file_name, self.project_id, title, **kwargs)
                # if response.status_code != 202:
                #     raise_error(response.json(), "Failed to add document {0}".format(title), True)
                # else:
                #     logger.info('Added document {0}'.format(title))
                #     self._add_document(relative_path, title, response.json()['properties']['id'])
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on add: "+str(e))

    def push_action(self):
        try:
            entries = self.doc_manager.get_all_entries()
            updated = False
            folders = self.folder_manager.get_file_names()
            if len(folders):
                for folder in folders:
                    matched_files = get_files(folder)
                    if matched_files:
                        for file_name in matched_files:
                            try:
                                relative_path = self.norm_path(file_name)
                                title = os.path.basename(relative_path)
                                if self.doc_manager.is_doc_new(relative_path):
                                    self.add_document(file_name, title)
                                    print
                            except json.decoder.JSONDecodeError as e:
                                log_error(self.error_file_name, e)
                                logger.error("JSON error on adding document.")
            for entry in entries:
                if not self.doc_manager.is_doc_modified(entry['file_name'], self.path):
                    continue
                #print (entry['file_name'])
                response = self.api.document_update(entry['id'], os.path.join(self.path, entry['file_name']))
                if response.status_code != 202:
                    raise_error(response.json(), "Failed to update document {0}".format(entry['name']), True)
                updated = True
                logger.info('Updated ' + entry['name'])
                self._update_document(entry['file_name'])
                return True
            if not updated:
                logger.info('All documents up-to-date with Lingotek Cloud. ')
                return False
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on push: "+str(e))

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

    # def request_action
    def target_action(self, document_name, path, entered_locales, to_delete, due_date, workflow, document_id=None):
        try:
            is_successful = False
            locales = []
            for locale in entered_locales:
                locales.extend(locale.split(','))
            locales = get_valid_locales(self.api, locales)
            if path:
                document_id = None
                document_name = None
            change_db_entry = True
            if to_delete:
                expected_code = 204
                failure_message = 'Failed to delete target'
                info_message = 'Deleted locale'
            else:
                expected_code = 201
                failure_message = 'Failed to add target'
                info_message = 'Added target'
            # print("doc_name: "+str(document_name))
            docs = []
            if not path and not document_name and not document_id:
                docs = self.doc_manager.get_all_entries()
            elif path:
                docs = self.get_docs_in_path(path)
            else:
                # todo: document name or file name? since file name will be relative to root
                # todo: clean this code up some
                if document_id:
                    entry = self.doc_manager.get_doc_by_prop('id', document_id)
                    if not entry:
                        logger.error('Document specified for target doesn\'t exist: {0}'.format(document_id))
                        return
                elif document_name:
                    entry = self.doc_manager.get_doc_by_prop('name', document_name)
                    if not entry:
                        logger.error('Document name specified for target doesn\'t exist: {0}'.format(document_name))
                        return
                        # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
                if not entry:
                    logger.error('Could not add target. File specified is invalid.')
                    return
                docs.append(entry)
            if len(docs) == 0:
                if path and len(path) > 0:
                    logger.info("File "+str(path)+" not found.")
                else:
                    logger.info("No documents to request target locale.")
            for entry in docs:
                document_id = entry['id']
                document_name = entry['file_name']
                for locale in locales:
                    response = self.api.document_add_target(document_id, locale, workflow, due_date) if not to_delete \
                        else self.api.document_delete_target(document_id, locale)
                    if response.status_code != expected_code:
                        if (response.json() and response.json()['messages']):
                            response_message = response.json()['messages'][0]
                            print(response_message.replace(document_id, document_name + ' (' + document_id + ')'))
                            if 'not found' in response_message:
                                return
                        raise_error(response.json(), '{message} {locale} for document {name}'.format(message=failure_message, locale=locale, name=document_name), True)
                        if not 'already exists' in response_message:
                            change_db_entry = False
                        # self.update_doc_locales(document_id)
                        continue
                    logger.info('{message} {locale} for document {name}'.format(message=info_message,
                                                                                locale=locale, name=document_name))
                remote_locales = self.get_doc_locales(document_id, document_name) # Get locales from Lingotek Cloud
                locales_to_add = []
                if change_db_entry:
                    # Make sure that the locales that were just added are added to the database as well as the previous remote locales (since they were only just recently added to Lingotek's system)
                    if to_delete:
                        locales_to_add = locales
                    else:
                        if remote_locales:
                            for locale in remote_locales:
                                if locale not in locales:
                                    locales_to_add.append(locale)
                    self._target_action_db(to_delete, locales_to_add, document_id)
                    is_successful = True
            return is_successful
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on request: "+str(e))

    def list_ids_action(self, hide_docs, title=False):
        try:
            """ lists ids of list_type specified """
            folders = self.folder_manager.get_file_names()
            if len(folders):
                underline("Folder path")
                for folder in folders:
                    if title:
                        print(folder)
                    else:
                        print(self.get_relative_path(folder))
                if hide_docs:
                    return
                print("")
            elif hide_docs:
                print("No added folders")
                return
            ids = []
            titles = []
            locales = []
            max_length = 0
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                # if entry['file_name'].startswith(cwd.replace(self.path, '')):
                ids.append(entry['id'])
                try:
                    if title:
                        name = entry['name']
                    else:
                        name = self.get_relative_path(self.norm_path(entry['file_name']))
                        # print("relative path: "+name)
                    if len(name) > max_length:
                        max_length = len(name)
                    titles.append(name)
                except (IndexError, KeyError) as e:
                    log_error(self.error_file_name, e)
                    titles.append("        ")
                try:
                    locales.append(entry['locales'])
                except KeyError:
                    locales.append([])
            if not ids:
                print ('No local documents.')
                return
            if max_length > 90:
                max_length = 90
            underline('%-*s' % (max_length,'Filename') + ' %-38s' % 'Lingotek ID' + 'Locales')
            for i in range(len(ids)):
                title = titles[i]
                if len(title) > max_length:
                    title = title[(len(titles[i])-30):]
                info = '%-*s' % (max_length,title) + ' %-38s' % ids[i] + ', '.join(locale for locale in locales[i])
                print (info)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on list: "+str(e))

    def list_remote_action(self):
        """ lists ids of all remote documents """
        response = self.api.list_documents(self.project_id)
        if response.status_code == 204:
            print("No documents to report")
            return
        elif response.status_code != 200:
            if check_response(response):
                raise_error(response.json(), "Failed to get status of documents", True)
            else:
                raise_error("", "Failed to get status of documents", True)
        else:
            print ('Remote documents: id, document name')
            for entry in response.json()['entities']:
                title = entry['entities'][1]['properties']['title'].replace("Status of ", "")
                id = entry['entities'][1]['properties']['id']
                info = '{id} \t {title}'.format(id=id, title=title)
                print (info)
            return

    def list_workflow_action(self):
        response = self.api.list_workflows(self.community_id)
        if response.status_code != 200:
            raise_error(response.json(), "Failed to list workflows")
        ids, titles = log_id_names(response.json())
        if not ids:
            print ('No workflows')
            return
        print ('Workflows: id, title')
        for i in range(len(ids)):
            info = '{id} \t {title}'.format(id=ids[i], title=titles[i])
            print (info)

    def list_locale_action(self):
        locale_info = []
        response = self.api.list_locales()
        if response.status_code != 200:
            raise exceptions.RequestFailedError("Failed to get locale codes")
        locale_json = response.json()
        for entry in locale_json:
            locale_code = locale_json[entry]['locale']
            language = locale_json[entry]['language_name']
            country = locale_json[entry]['country_name']
            locale_info.append((locale_code, language, country))
        for locale in sorted(locale_info):
            if not len(locale[2]):  # Arabic
                print ("{0} ({1})".format(locale[0], locale[1]))
            else:
                print ("{0} ({1}, {2})".format(locale[0], locale[1], locale[2]))

    def list_format_action(self):
        format_info = self.api.get_document_formats()
        format_mapper = detect_format(None, True)

        format_list = {}
        for format_name in sorted(set(format_info.values())):
            format_list[format_name] = []

        for extension in format_mapper.keys():
            key = format_mapper[extension]
            if key not in format_list:
                format_list[key] = []
            format_list[key].append(extension)

        print("Lingotek Cloud accepts content using any of the formats listed below. File formats will be auto-detected for the extensions as specified below. Alternatively, formats may be specified explicitly upon add. Lingotek supports variations and customizations on these formats with filters.")
        print()
        print('%-30s' % "Format" + '%s' % "Auto-detected File Extensions")
        print("-----------------------------------------------------------")
        for k,v in sorted(format_list.items()):
            print('%-30s' % k + '%s' % ' '.join(v))

    def list_filter_action(self):
        response = self.api.list_filters()
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filters')
        filter_entities = response.json()['entities']
        print ('Filters: id, title')
        for entry in filter_entities:
            properties = entry['properties']
            title = properties['title']
            filter_id = properties['id']
            print ('{0}\t{1}\t'.format(filter_id, title))

    def print_status(self, title, progress):
        print ('{0}: {1}%'.format(title, progress))
        # print title + ': ' + str(progress) + '%'
        # for each doc id, also call /document/id/translation and get % of each locale

    def print_detailed(self, doc_id, doc_name):
        response = self.api.document_translation_status(doc_id)
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get detailed status of document', True, doc_id, doc_name)
        try:
            if 'entities' in response.json():
                for entry in response.json()['entities']:
                    curr_locale = entry['properties']['locale_code']
                    curr_progress = entry['properties']['percent_complete']
                    print ('\tlocale: {0} \t percent complete: {1}%'.format(curr_locale, curr_progress))
                    # detailed_status[doc_id] = (curr_locale, curr_progress)
        except KeyError as e:
            log_error(self.error_file_name, e)
            print("Error listing translations")
            return
            # return detailed_status

    def status_action(self, **kwargs):
        try:
            # detailed_status = {}
            doc_name = None
            if 'doc_name' in kwargs:
                doc_name = kwargs['doc_name']
            if 'all' in kwargs and kwargs['all']:
                response = self.api.list_documents(self.project_id)
                if response.status_code == 204:
                    print("No documents to report")
                    return
                elif response.status_code != 200:
                    if check_response(response):
                        raise_error(response.json(), "Failed to get status of documents", True)
                    else:
                        raise_error("", "Failed to get status of documents", True)
                else:
                    for entry in response.json()['entities']:
                        title = entry['entities'][1]['properties']['title']
                        progress = entry['entities'][1]['properties']['progress']
                        self.print_status(title, progress)
                        if 'detailed' in kwargs and kwargs['detailed']:
                            self.print_detailed(entry['properties']['id'], title)
                    return
            else:
                if doc_name is not None:
                    entry = self.doc_manager.get_doc_by_prop('name', doc_name)
                    try:
                        doc_ids = [entry['id']]
                    except TypeError:
                        raise exceptions.ResourceNotFound("Document name specified for status doesn't exist: {0}".format(doc_name))
                else:
                    doc_ids = self.doc_manager.get_doc_ids()
                if not doc_ids:
                    print("No documents to report")
                    return
            for doc_id in doc_ids:
                response = self.api.document_status(doc_id)
                if response.status_code != 200:
                    entry = self.doc_manager.get_doc_by_prop('id', doc_id)
                    if entry:
                        error_message = "Failed to get status of document "+entry['name']
                    else:
                        error_message = "Failed to get status of document "+str(doc_id)
                    if check_response(response):
                        raise_error(response.json(), error_message, True, doc_id)
                    else:
                        raise_error("", str(response.status_code)+": "+error_message, True, doc_id)
                else:
                    title = response.json()['properties']['title']
                    progress = response.json()['properties']['progress']
                    self.print_status(title, progress)
                    if 'detailed' in kwargs and kwargs['detailed']:
                        self.print_detailed(doc_id, title)
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to Lingotek")
            exit()
        except ValueError:
            logger.warning("Could not connect to Lingotek")
            exit()
        # Python 3
#         except json.decoder.JSONDecodeError:
#             logger.warning("Could not connect to Lingotek")
#             exit()
        # End Python 3
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.warning("Error on requesting status: "+str(e))

    def added_folder_of_file(self, file_path):
        folders = self.folder_manager.get_file_names()
        for folder in folders:
            folder = os.path.join(self.path, folder)
            if folder in file_path:
                return folder

    def download_by_path(self, file_path, locale_codes, locale_ext, no_ext, auto_format):
        docs = self.get_docs_in_path(file_path)
        if len(docs) == 0:
            logger.warning("No document found with file path "+str(file_path))
        if docs:
            for entry in docs:
                locales = []
                if locale_codes:
                    locales = locale_codes.split(",")
                elif 'locales' in entry:
                    locales = entry['locales']
                if 'clone' in self.download_option and not locale_ext or (no_ext and not locale_ext):
                    self.download_locales(entry['id'], locales, auto_format, False)
                else:
                    self.download_locales(entry['id'], locales, auto_format, True)


    def download_locales(self, document_id, locale_codes, auto_format, locale_ext=True):
        if locale_codes:
            for locale_code in locale_codes:
                self.download_action(document_id, locale_code, auto_format, locale_ext)

    def download_action(self, document_id, locale_code, auto_format, locale_ext=True):
        try:
            response = self.api.document_content(document_id, locale_code, auto_format)
            entry = None
            entry = self.doc_manager.get_doc_by_prop('id', document_id)
            if response.status_code == 200:
                download_path = self.path
                if 'clone' in self.download_option:
                    if not locale_code:
                        print("Cannot download "+str(entry['file_name']+" with no target locale."))
                        return
                    # download_root is the path to the root of the locale folder.
                    if locale_code in self.locale_folders:
                        download_root = self.locale_folders[locale_code]
                    elif self.download_dir and len(self.download_dir):
                        download_root = os.path.join((self.download_dir if self.download_dir and self.download_dir != 'null' else ''),locale_code)
                    else:
                        download_root = locale_code
                    download_root = os.path.join(self.path,download_root)
                    # print("download_root: "+download_root) 365 253 222 159
                    source_file_name = entry['file_name']
                    source_path = os.path.join(self.path,os.path.dirname(source_file_name))
                    # print("original source_path: "+source_path)
                    # Get the path from the added source folder to the source document.
                    added_folder = self.added_folder_of_file(source_path)
                    if len(self.folder_manager.get_file_names()) > 1 and added_folder:
                        added_folder = remove_last_folder_in_path(added_folder)
                    # print("added folder of file: "+os.sep+remove_begin_slashes(added_folder))
                    if added_folder:
                        source_path = remove_begin_slashes(source_path.replace(os.sep+remove_begin_slashes(added_folder),""))
                    # print("replaced source_path: "+source_path)
                    # Copy the path into the locale folder (download_root).
                    # Something about this line has been causing problems
                    if source_path:
                        download_path = os.path.join(download_root,source_path)
                    else:
                        download_path = download_root
                    # print("download_path: "+download_path)
                    target_dirs = download_path.split(os.sep)
                    incremental_path = ""
                    if not os.path.exists(download_root):
                        os.mkdir(download_root)
                    if target_dirs:
                        for target_dir in target_dirs:
                            incremental_path += target_dir + os.sep
                            # print("target_dir: "+str(incremental_path))
                            new_path = os.path.join(self.path,incremental_path)
                            # print("new path: "+str(new_path))
                            if not os.path.exists(new_path):
                                try:
                                    os.mkdir(new_path)
                                    # print("Created directory "+str(new_path))
                                except Exception as e:
                                    log_error(self.error_file_name, e)
                                    logger.warning("Could not create cloned directory "+new_path)
                elif 'folder' in self.download_option:
                    if locale_code in self.locale_folders:
                        if self.locale_folders[locale_code] == 'null':
                            logger.warning("Download failed: folder not specified for "+locale_code)
                        else: download_path = self.locale_folders[locale_code]
                    else:
                        download_path = self.download_dir
                if not entry:
                    doc_info = self.api.get_document(document_id)
                    try:
                        file_title = doc_info.json()['properties']['title']
                        title, extension = os.path.splitext(file_title)
                        if not extension:
                            extension = doc_info.json()['properties']['extension']
                            extension = '.' + extension
                        if extension and extension != '.none':
                            title += extension
                    except KeyError as e:
                        log_error(self.error_file_name, e)
                        raise_error(doc_info.json(),
                                    'Something went wrong trying to download document: {0}'.format(document_id), True)
                        return
                    download_path = os.path.join(download_path, title)
                    logger.info('Downloaded: {0} ({1} - {2})'.format(title, self.get_relative_path(download_path), locale_code))
                else:
                    file_name = entry['file_name']
                    base_name = os.path.basename(self.norm_path(file_name))
                    if not locale_code:
                        logger.info("No target locales for "+file_name+". Downloading the source document instead.")
                        locale_code = self.locale
                    if locale_ext and not 'clone' in self.download_option:
                        name_parts = base_name.split('.')
                        if len(name_parts) > 1:
                            name_parts.insert(-1, locale_code)
                            downloaded_name = '.'.join(part for part in name_parts)
                        else:
                            downloaded_name = name_parts[0] + '.' + locale_code
                    else:
                        downloaded_name = base_name
                    if 'same' in self.download_option:
                        download_path = os.path.dirname(file_name)
                    download_path = os.path.join(self.path,os.path.join(download_path, downloaded_name))
                    logger.info('Downloaded: {0} ({1} - {2})'.format(downloaded_name, self.get_relative_path(download_path), locale_code))

                self.doc_manager.add_element_to_prop(document_id, 'downloaded', locale_code)
                config_file_name, conf_parser = self.init_config_file()
                git_autocommit = conf_parser.get('main', 'git_autocommit')
                if git_autocommit == "True":
                    if not self.git_auto.repo_is_defined:
                        if self.git_auto.repo_exists(download_path):
                            self.git_auto.initialize_repo()
                    if os.path.isfile(download_path):
                        self.git_auto.add_file(download_path)
                try:
                    with open(download_path, 'wb') as fh:
                        for chunk in response.iter_content(1024):
                            fh.write(chunk)
                except:
                    logger.warning('ERROR: Download failed at '+download_path)
                return download_path
            else:
                printResponseMessages(response)
                if entry:
                    raise_error(response.json(), 'Failed to download content for {0} ({1})'.format(entry['name'], document_id), True)
                else:
                    raise_error(response.json(), 'Failed to download content for id: {0}'.format(document_id), True)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on download: "+str(e))

    def pull_action(self, locale_code, locale_ext, no_ext, auto_format):
        try:
            if 'clone' in self.download_option and not locale_ext or (no_ext and not locale_ext):
                locale_ext = False
            else:
                locale_ext = True
            if not locale_code:
                entries = self.doc_manager.get_all_entries()
                if entries:
                    for entry in entries:
                        try:
                            locales = entry['locales']
                            for locale in locales:
                                self.download_action(entry['id'], locale, auto_format, locale_ext)
                        except KeyError:
                            self.download_action(entry['id'], None, auto_format, locale_ext)
            else:
                document_ids = self.doc_manager.get_doc_ids()
                if document_ids:
                    for document_id in document_ids:
                        self.download_action(document_id, locale_code, auto_format, locale_ext)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on pull: "+str(e))

    def mv_file(self, source, destination, source_type='file', rename=False):
        try:
            path_sep = os.sep
            path_to_source = os.path.abspath(source)
            if not rename: path_to_destination = os.path.abspath(destination)
            else: path_to_destination = path_to_source.rstrip(os.path.basename(path_to_source))+destination
            repo_directory = path_to_source
            while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.ltk")):
                repo_directory = repo_directory.split(path_sep)[:-1]
                repo_directory = path_sep.join(repo_directory)
            if repo_directory not in path_to_source or repo_directory not in path_to_destination:
                logger.error("Error: Operations can only be performed inside ltk directory.")
                return False
            directory_to_source = (path_to_source.replace(repo_directory, '',1)).lstrip(path_sep)
            directory_to_destination = (path_to_destination.replace(repo_directory, '',1)).lstrip(path_sep)
            folder = None
            if source_type == 'file':
                doc = self.doc_manager.get_doc_by_prop("file_name",directory_to_source)
                if not doc:
                    logger.error("Error: File has not been added and so can not be moved.")
                    return False
            elif source_type == 'folder':
                folder = self.folder_manager.get_folder_by_name(directory_to_source)
                if not folder:
                    logger.warning("Notice: This folder has not been added, though it may be in a directory that has")
            try:
                if rename and source_type == 'file' and path_to_source.rstrip(path_sep).rstrip(doc['name']) != path_to_source.rstrip(path_sep):
                    new_name = os.path.basename(path_to_destination)
                    self.doc_manager.update_document('name', new_name, doc['id'])
                    self.api.document_update(doc['id'], title=new_name)
                elif not rename:
                    file_name = os.path.basename(path_to_source)
                    path_to_destination+=path_sep+file_name
                    directory_to_destination+=path_sep+file_name
                os.rename(path_to_source, path_to_destination)
                if source_type == 'file': self.doc_manager.update_document('file_name', directory_to_destination.strip(path_sep), doc['id'])
                elif folder:
                    self.folder_manager.remove_element(directory_to_source)
                    self.folder_manager.add_folder(directory_to_destination)
                if source_type == 'folder':
                    for file_name in self.doc_manager.get_file_names():
                        if file_name.find(directory_to_source) == 0:
                            doc = self.doc_manager.get_doc_by_prop("file_name",file_name)
                            self.doc_manager.update_document('file_name', file_name.replace(directory_to_source, directory_to_destination, 1), doc['id'])
                return True
            except Exception as e:
                log_error(self.error_file_name, e)
                logger.error("ERROR: "+str(e))
                logger.error("An error prevented document {0} from being moved".format(source))
                return False
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on moving file "+str(source)+": "+str(e))

    def mv_action(self, sources, destination):
        try:
            for source in sources:
                if os.path.isdir(source):
                    if os.path.isdir(destination):
                        if self.mv_file(source, destination, source_type='folder'):
                            logger.info("Folder "+source+" has been moved to "+destination)
                        else: logger.error("Failed to move file "+source)
                    elif os.path.isfile(destination):
                        logger.error("mv: cannot overwrite non-directory ‘"+source+"’ with directory ‘"+destination+"’")
                    else:
                        if self.mv_file(source, destination, source_type='folder', rename=True):
                            logger.info("Folder "+source+" has been renamed to "+destination)
                        else: logger.error("Failed to move file "+source)
                elif os.path.isfile(source):
                    if os.path.isdir(destination):
                        if self.mv_file(source, destination):
                            logger.info(source+" has been moved to "+destination)
                        else: logger.error("Failed to move file "+source)
                    elif os.path.isfile(destination):
                        if self.mv_file(source, destination, rename=True):
                            logger.info(source+" has been renamed as "+destination)
                            logger.info(destination+" has been deleted")
                        else: logger.error("Failed to move file "+source)
                    else:
                        if self.mv_file(source, destination, rename=True):
                            logger.info(source+" has been renamed to "+destination)
                        else: logger.error("Failed to move file "+source)
                else:
                    logger.error("Error: Source file does not exist")
        except Exception as e:
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on mv: "+str(e))

    def rm_document(self, file_name, useID, force, doc_name=None, is_directory=False):
        try:
            doc = None
            if not useID:
                relative_path = self.norm_path(file_name)
                doc = self.doc_manager.get_doc_by_prop('file_name', relative_path)
                title = os.path.basename(self.norm_path(file_name))
                # print("relative_path: "+relative_path)
                try:
                    document_id = doc['id']
                except TypeError: # Documents specified by name must be found in the local database to be removed.
                    if not is_directory:
                        logger.warning("Document name specified for remove isn't in the local database: {0}".format(relative_path))
                    return
                    # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
            else:
                document_id = file_name
                doc = self.doc_manager.get_doc_by_prop('id', document_id)
                # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
                if doc:
                    file_name = doc['file_name']
            response = self.api.document_delete(document_id)
            #print (response)
            if response.status_code != 204 and response.status_code != 202:
                # raise_error(response.json(), "Failed to delete document {0}".format(document_name), True)
                logger.error("Failed to delete document {0} remotely".format(file_name))
            else:
                if doc_name:
                    logger.info("{0} ({1}) has been deleted remotely.".format(doc_name, file_name))
                else:
                    logger.info("{0} has been deleted remotely.".format(file_name))
                if doc:
                    if force:
                        self.delete_local(file_name, document_id)
                    self.doc_manager.remove_element(document_id)
        except json.decoder.JSONDecodeError:
            logger.error("JSON error on removing document.")
        except KeyboardInterrupt:
            raise_error("", "Canceled removing document")
            return
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error("Error on removing document "+str(file_name)+": "+str(e))

    def rm_action(self, file_patterns, **kwargs):
        try:
            removed_folder = False
            for pattern in file_patterns:
                if os.path.isdir(pattern):
                    # print("checking folder "+self.norm_path(pattern))
                    if self.folder_manager.folder_exists(self.norm_path(pattern)):
                        self.folder_manager.remove_element(self.norm_path(pattern))
                        logger.info("Removed folder "+str(file_patterns[0]))
                        removed_folder = True
                    else:
                        logger.warning("Folder "+str(pattern)+" has not been added and so can not be removed.")
            if 'directory' in kwargs and kwargs['directory']:
                if not removed_folder:
                    logger.info("No folders to remove at the given path(s).")
                return
            matched_files = None
            if isinstance(file_patterns,str):
                file_patterns = [file_patterns]
            if 'force' in kwargs and kwargs['force']:
                force = True
            else:
                force = False
            if 'id' in kwargs and kwargs['id']:
                useID = True
            else:
                useID = False
            if 'all' in kwargs and kwargs['all']:
                self.folder_manager.clear_all()
                logger.info("Removed all folders.")
                if 'remote' in kwargs and kwargs['remote']:
                    response = self.api.list_documents(self.project_id)
                    if response.status_code == 204:
                        print("No remote documents to remove.")
                        return
                    elif response.status_code != 200:
                        if check_response(response):
                            raise_error(response.json(), "Failed to get status of documents", True)
                        else:
                            raise_error("", "Failed to get status of documents", True)
                        return
                    else:
                        for entry in response.json()['entities']:
                            id = entry['entities'][1]['properties']['id']
                            doc_name = entry['properties']['name']
                            self.rm_document(id, True, force, doc_name)
                        return
                else:
                    useID = False
                    matched_files = self.doc_manager.get_file_names()
            elif not useID:
                # use current working directory as root for files instead of project root
                if 'name' in kwargs and kwargs['name']:
                    matched_files = []

                    for pattern in file_patterns:
                        doc = self.doc_manager.get_doc_by_prop("name",pattern)
                        if doc:
                            matched_files.append(doc['file_name'])
                else:
                    matched_files = self.get_doc_filenames_in_path(file_patterns)
            else:
                matched_files = file_patterns
            if not matched_files or len(matched_files) == 0:
                if useID:
                    raise exceptions.ResourceNotFound("No documents to remove with the specified id")
                elif not 'all' in kwargs or not kwargs['all']:
                    raise exceptions.ResourceNotFound("No documents to remove with the specified file path")
                else:
                    raise exceptions.ResourceNotFound("No documents to remove")
            is_directory = False
            for pattern in file_patterns: # If attemping to remove any directory, don't print failure message
                basename = os.path.basename(pattern)
                if not basename or basename == "":
                    is_directory = True
            for file_name in matched_files:
                # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
                self.rm_document(self.norm_path(file_name).replace(self.path,""), useID, force)
        except Exception as e:
            # Python 2
            # End Python 2
            # Python 3
#             log_error(self.error_file_name, e)
            # End Python 3
            if 'string indices must be integers' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on remove: "+str(e))


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
            if poll:
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

    def clean_action(self, force, dis_all, path):
        try:
            if dis_all:
                # disassociate everything
                self.doc_manager.clear_all()
                return
            locals_to_delete = []
            if path:
                files = get_files(path)
                docs = self.doc_manager.get_file_names()
                # Efficiently go through the files in case of a large number of files to check or a large number of remote documents.
                if len(files) > len(docs):
                    for file_name in docs:
                        if file_name in files:
                            entry = self.doc_manager.get_doc_by_prop('file_name', self.norm_path(file_name))
                            if entry:
                                locals_to_delete.append(entry['id'])
                else:
                    for file_name in files:
                        entry = self.doc_manager.get_doc_by_prop('file_name', self.norm_path(file_name))
                        if entry:
                            locals_to_delete.append(entry['id'])
            else:
                response = self.api.list_documents(self.project_id)
                local_ids = self.doc_manager.get_doc_ids()
                tms_doc_ids = []
                if response.status_code == 200:
                    tms_documents = response.json()['entities']
                    for entity in tms_documents:
                        tms_doc_ids.append(entity['properties']['id'])
                elif response.status_code == 204:
                    pass
                else:
                    raise_error(response.json(), 'Error trying to list documents in TMS for cleaning')
                locals_to_delete = [x for x in local_ids if x not in tms_doc_ids]

                # check local files
                db_entries = self.doc_manager.get_all_entries()
                for entry in db_entries:
                    # if local file doesn't exist, remove entry
                    if not os.path.isfile(os.path.join(self.path, entry['file_name'])):
                        locals_to_delete.append(entry['id'])

            # remove entry for local doc -- possibly delete local file too?
            if locals_to_delete:
                for curr_id in locals_to_delete:
                    removed_doc = self.doc_manager.get_doc_by_prop('id', curr_id)
                    if not removed_doc:
                        continue
                    removed_title = removed_doc['name']
                    # todo somehow this line^ doc is null... after delete files remotely, then delete locally
                    if force:
                        self.delete_local(removed_title, curr_id)
                    self.doc_manager.remove_element(curr_id)
                    logger.info('Removing association for document {0}'.format(removed_title))
            else:
                logger.info('Local documents already up-to-date with Lingotek Cloud')
                return
            logger.info('Cleaned up associations between local documents and Lingotek Cloud')
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on clean: "+str(e))

    def delete_local(self, title, document_id, message=None):
        # print('local delete:', title, document_id)
        if not title:
            title = document_id
        message = '{0} has been deleted locally.'.format(title) if not message else message
        try:
            file_name = self.doc_manager.get_doc_by_prop('id', document_id)['file_name']
        except TypeError:
            logger.info('Document to remove not found in the local database')
            return
        try:
            os.remove(os.path.join(self.path, file_name))
            logger.info(message)
        except OSError:
            logger.info('Something went wrong trying to delete the local file.')

    def delete_local_path(self, path, message=None):
        path = self.norm_path(path)
        message = '{0} has been deleted locally.'.format(path) if not message else message
        try:
            os.remove(path)
            logger.info(message)
        except OSError:
            logger.info('Something went wrong trying to delete the local file.')

    def clone_folders(self, dest_path, folders_map, locale, copy_root=False):
        """ Copies subfolders of added folders to a particular destination folder (for a particular locale).
            If there is more than one root folder to copy, each root folder is created inside of the destination folder.
            If there is only one root folder to copy, only the subdirectories are copied."""
        # print("dest_path: "+str(dest_path))
        # print("folders to clone: "+str(folders_map))
        if not folders_map or not len(folders_map):
            logger.warning("No folders to clone for locale "+str(locale)+".")
            return
        folder_created = False
        prefix_folder = False
        if not os.path.exists(dest_path):
            os.mkdir(dest_path)
            folder_created = True
        if len(folders_map) > 1 or copy_root:
            prefix_folder = True
        for root_folder in folders_map:
            # print("root folder: "+root_folder)
            if prefix_folder:
                new_root_path = dest_path + os.sep + root_folder
                if not os.path.exists(new_root_path):
                    os.mkdir(new_root_path)
                    folder_created = True
                for folder in folders_map[root_folder]:
                    new_sub_root_path = dest_path + os.sep + root_folder + os.sep + folder
                    if not os.path.exists(new_sub_root_path):
                        os.mkdir(new_sub_root_path)
                        folder_created = True
                        # print("created folder "+new_sub_root_path)
            else:
                if folders_map[root_folder]:
                    for folder in folders_map[root_folder]:
                        new_path = dest_path + os.sep + folder
                        if not os.path.exists(new_path):
                            os.mkdir(new_path)
                            folder_created = True
                            # print("created folder "+ new_path)
        return folder_created

    def clone_action(self, folders, copy_root):
        try:
            if not len(self.watch_locales) or self.watch_locales == set(['[]']):
                logger.warning("There are no locales for which to clone. You can add locales using 'ltk config -t'.")
                return
            folders_map = {}
            are_added_folders = False
            if not folders:
                folders = self.folder_manager.get_file_names()
                are_added_folders = True
            for folder in folders:
                folder_paths = folder.split(os.sep)
                # print("current abs: "+str(self.get_current_abs(folder)))
                if are_added_folders:
                    folder = os.path.join(self.path,folder)
                # print("folder to be cloned: "+str(folder))
                folders_map[folder_paths[len(folder_paths)-1]] = get_sub_folders(folder)
            # print("folders: "+str(folders_map))
            cloned_folders = False
            for locale in self.watch_locales:
                dest_path = ""
                if locale in self.locale_folders:
                    dest_path = self.locale_folders[locale]
                else:
                    if self.download_dir and self.download_dir != 'null':
                        dest_path = os.path.join(os.path.join(self.path,self.download_dir),locale)
                    else:
                        dest_path = os.path.join(self.path,locale)
                dest_path = os.path.join(self.path,dest_path)
                if self.clone_folders(dest_path, folders_map, locale, copy_root):
                    logger.info("Cloned locale " + str(locale) + " at " + dest_path)
                    cloned_folders = True
            if not len(self.folder_manager.get_file_names()):
                logger.warning("There are no added folders to clone.")
                return
            if not cloned_folders:
                logger.info("All locales have already been cloned.")
            return
        except Exception as e:
            log_error(self.error_file_name, e)
            logger.error("Error on clean: "+str(e))

def raise_error(json, error_message, is_warning=False, doc_id=None, file_name=None):
    try:
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


def reinit(host, project_path, delete, reset):
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
#                 confirm = input(prompt_message)
                # End Python 3
        except KeyboardInterrupt:
            logger.error("Reinit canceled")
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


def display_choice(display_type, info):
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
#             choice = input(prompt_message)
            # End Python 3
        except KeyboardInterrupt:
            logger.error("Init canceled")
            return
        try:
            choice = int(choice)
        except ValueError:
            print("That's not a valid option!")
    for v in mapper[choice]:
        logger.info('Selected "{0}" {1}.'.format(mapper[choice][v], display_type))
        return v, mapper[choice][v]


def check_global(host):
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


def create_global(access_token, host):
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


def init_action(host, access_token, project_path, folder_name, workflow_id, locale, delete, reset):
    try:
        # check if Lingotek directory already exists
        to_init = reinit(host, project_path, delete, reset)
        # print("to_init: "+str(to_init))
        if not to_init:
            return
        elif to_init is not True:
            access_token = to_init

        ran_oauth = False
        if not access_token:
            access_token = check_global(host)
            if not access_token or reset:
                from ltk.auth import run_oauth
                access_token = run_oauth(host)
                ran_oauth = True
        # print("access_token: "+str(access_token))
        if ran_oauth:
            # create or overwrite global file
            create_global(access_token, host)

        api = ApiCalls(host, access_token)
        # create a directory
        try:
            os.mkdir(os.path.join(project_path, CONF_DIR))
        except OSError:
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
            access_token = run_oauth(host)
            create_global(access_token, host)
            community_info = api.get_communities_info()
            if not community_info:
                raise exceptions.RequestFailedError("Unable to get user's list of communities")

        if len(community_info) == 0:
            raise exceptions.ResourceNotFound('You are not part of any communities in Lingotek Cloud')
        if len(community_info) > 1:
            community_id, community_name = display_choice('community', community_info)
        else:
            for id in community_info:
                community_id = id
            #community_id = community_info.iterkeys().next()  --- iterkeys() is not in python 3
        config_parser.set('main', 'community_id', community_id)
        response = api.list_projects(community_id)
        if response.status_code != 200:
            try:
                raise_error(response.json(), 'Something went wrong trying to find projects in your community')
            except:
                logger.error('Something went wrong trying to find projects in your community.')
                return
        project_info = api.get_project_info(community_id)
        if len(project_info) > 0:
            confirm = 'none'
            try:
                while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                    prompt_message = 'Would you like to use an existing Lingotek project? [Y/n]:'
                    # Python 2
                    confirm = raw_input(prompt_message)
                    # End Python 2
                    # Python 3
#                     confirm = input(prompt_message)
                    # End Python 3
                if not confirm or not confirm in ['n', 'N', 'no', 'No']:
                    project_id, project_name = display_choice('project', project_info)
                    config_parser.set('main', 'project_id', project_id)
                    config_parser.set('main', 'project_name', project_name)
                    config_parser.write(config_file)
                    config_file.close()
                    return
            except KeyboardInterrupt:
                logger.error("Init canceled")
                return
        prompt_message = "Please enter a new Lingotek project name: %s" % folder_name + chr(8) * len(folder_name)
        try:
            # Python 2
            project_name = raw_input(prompt_message)
            # End Python 2
            # Python 3
#             project_name = input(prompt_message)
            # End Python 3
        except KeyboardInterrupt:
            logger.error("Init canceled")
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
        logger.error("Init canceled")
        return
    except Exception as e:
        if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
            logger.error("Error connecting to Lingotek's TMS")
        else:
            logger.error("Error on init: "+str(e))


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

def get_sub_folders(patterns):
    """ gets all sub-folders matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE)
        returns the relative paths starting from each pattern"""

    cwd = os.getcwd()
    if isinstance(patterns,str):
        patterns = [patterns]
    allPatterns = []
    if isinstance(patterns,list) or isinstance(patterns,tuple):
        for pattern in patterns:
            # print("pattern in loop: "+str(pattern))
            basename = os.path.basename(pattern)
            if basename and basename != "":
                allPatterns.extend(getRegexDirs(pattern,cwd))
            else:
                allPatterns.append(pattern)
    else:
        basename = os.path.basename(patterns)
        if basename and basename != "":
            allPatterns.extend(getRegexDirs(patterns,cwd))
        else:
            allPatterns.append(patterns)
    matched_dirs = []
    # print("all patterns: "+str(allPatterns))
    for pattern in allPatterns:
        path = os.path.abspath(pattern)
        # print("looking at path "+str(path))
        # check if pattern contains subdirectory
        if os.path.exists(path):
            if os.path.isdir(path):
                for root, subdirs, files in os.walk(path):
                    split_path = root.split('/')
                    for subdir in subdirs:
                        # print(os.path.join(root, subdir))
                        matched_dirs.append(os.path.join(root,subdir).replace(str(path)+os.sep,""))
        else:
            logger.info("Directory not found: "+pattern)
    if len(matched_dirs) == 0:
        return None
    return matched_dirs

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
                    split_path = root.split(os.sep)
                    for file in files:
                        # print(os.path.join(root, file))
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

def getRegexDirs(pattern,path):
    dir_name = os.path.dirname(pattern)
    if dir_name:
        path = os.path.join(path,dir_name)
    pattern_name = os.path.basename(pattern)
    # print("path: "+path)
    # print("pattern: "+str(pattern))
    matched_dirs = []
    if pattern_name and not "*" in pattern:
        return [pattern]
    for path, subdirs, files in os.walk(path):
        for dn in fnmatch.filter(subdirs, pattern):
            matched_dirs.append(os.path.join(path, dn))
    print("matched dirs: "+str(matched_dirs))
    return matched_dirs

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
