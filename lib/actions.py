import ConfigParser
import os
import shutil
import fnmatch
import time
import exceptions
from apicalls import ApiCalls
from managers import DocumentManager
from constants import CONF_DIR, CONF_FN

from logger import logger

class Action:
    def __init__(self, path):
        self.host = ''
        self.access_token = ''
        self.project_id = ''
        self.path = path
        self.community_id = ''
        self.workflow_id = ''  # default workflow id; MT phase only
        self.locale = ''
        if not self._is_initialized():
            raise exceptions.UninitializedError("This project is not initialized. Please run init command.")
        self._initialize_self()
        self.api = ApiCalls(self.host, self.access_token)
        self.doc_manager = DocumentManager(self.path)

    def _is_initialized(self):
        actual_path = find_conf(self.path)
        if not actual_path:
            return False
        self.path = actual_path
        if not is_initialized(self.path):
            return False
        return True

    def _initialize_self(self):
        config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(config_file_name)
        self.host = conf_parser.get('main', 'host')
        self.access_token = conf_parser.get('main', 'access_token')
        self.project_id = conf_parser.get('main', 'project_id')
        self.community_id = conf_parser.get('main', 'community_id')
        self.workflow_id = conf_parser.get('main', 'workflow_id')
        self.locale = conf_parser.get('main', 'default_locale')

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

    def config_action(self, locale, workflow_id):
        config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(config_file_name)
        if locale:
            conf_parser.set('main', 'default_locale', locale)
            with open(config_file_name, 'wb') as new_file:
                conf_parser.write(new_file)
            logger.info('Project default locale has been updated to {0}'.format(locale))
        elif workflow_id:
            response = self.api.patch_project(self.project_id, workflow_id)
            if response.status_code != 204:
                raise_error(response.json(), 'Something went wrong trying to update workflow_id of project')
            conf_parser.set('main', 'workflow_id', workflow_id)
            with open(config_file_name, 'wb') as new_file:
                conf_parser.write(new_file)
            logger.info('Project default workflow has been updated to {0}'.format(workflow_id))
        else:
            print 'host: {0}\naccess_token: {1}\nproject id: {2}\ncommunity id: {3}\nworkflow id: {4}\n' \
                  'locale: {5}'.format(self.host, self.access_token, self.project_id, self.community_id,
                                       self.workflow_id, self.locale)

    def add_action(self, locale, file_patterns, **kwargs):
        if not locale:
            locale = self.locale
        # format will be automatically detected by extension but may not be what user expects
        # todo file pattern not matching subdirectory
        # matched_files = get_files(self.path, file_patterns)
        # use current working directory as root for files instead of project root
        matched_files = get_files(os.getcwd(), file_patterns)
        if not matched_files:
            raise exceptions.ResourceNotFound("Could not find the specified file/pattern")
        for file_name in matched_files:
            # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
            title = os.path.basename(os.path.normpath(file_name))
            if not self.doc_manager.is_doc_new(file_name):
                if self.doc_manager.is_doc_modified(file_name):
                    confirm = 'not confirmed'
                    while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                        confirm = raw_input("This document already exists. Would you like to overwrite it? [y/N]: ")
                    # confirm if would like to overwrite existing document in TMS
                    if not confirm or confirm in ['n', 'N']:
                        # todo may want to change return to continue?
                        return
                    else:
                        logger.info('Overwriting document: {0} in TMS...'.format(title))
                        self.update_document_action(file_name, title, **kwargs)
                        continue
                else:
                    logger.error("This document has already been added: {0}".format(title))
                    return
            response = self.api.add_document(file_name, locale, self.project_id, title, **kwargs)
            if response.status_code != 202:
                raise_error(response.json(), "Failed to add document {0}".format(title), True)
            else:
                logger.info('Added document {0}'.format(title))
                self._add_document(file_name, title, response.json()['properties']['id'])

    def push_action(self):
        entries = self.doc_manager.get_all_entries()
        updated = False
        for entry in entries:
            if not self.doc_manager.is_doc_modified(entry['file_name']):
                continue
            response = self.api.document_update(entry['id'], entry['file_name'])
            if response.status_code != 202:
                raise_error(response.json(), "Failed to update document {0}".format(entry['name']), True)
            updated = True
            logger.info('Updated ' + entry['name'])
            self._update_document(entry['file_name'])
        if not updated:
            logger.info('All documents up to date with TMS. ')

    def update_document_action(self, file_name, title=None, **kwargs):
        entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
        try:
            document_id = entry['id']
        except TypeError:
            logger.error("Document name specified doesn't exist: {0}".format(title))
            return
        if title:
            response = self.api.document_update(document_id, file_name, title=title, **kwargs)
        else:
            response = self.api.document_update(document_id, file_name)
        if response.status_code != 202:
            raise_error(response.json(), "Failed to update document {0}".format(file_name), True)
        self._update_document(file_name)

    def request_action(self, document_name, locales, due_date, workflow):
        add_to_db = True
        if not document_name:
            for locale in locales:
                response = self.api.add_target_project(self.project_id, locale, due_date)
                if response.status_code != 201:
                    raise_error(response.json(), "Failed to add target {0} to project".format(locale), True)
                    add_to_db = False
                    continue
                logger.info('Requested locale {0} for project {1}'.format(locale, self.project_id))
            document_ids = self.doc_manager.get_doc_ids()
            if add_to_db:
                for document_id in document_ids:
                    self.doc_manager.update_document('locales', list(locales), document_id)
        else:
            entry = self.doc_manager.get_doc_by_prop('name', document_name)
            try:
                document_id = entry['id']
            except TypeError:
                logger.warning("Document name specified doesn't exist: {0}".format(document_name))
                return
                # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
            for locale in locales:
                response = self.api.add_target_document(document_id, locale, workflow, due_date)
                if response.status_code != 201:
                    raise_error(response.json(), "Failed to add target {0} to document".format(locale), True)
                    add_to_db = False
                    continue
                logger.info('Requested locale {0} for document {1}'.format(locale, document_name))
            if add_to_db:
                self.doc_manager.update_document('locales', list(locales), document_id)

    def list_ids_action(self, list_type):
        """ lists ids of list_type specified """
        ids = []
        titles = []
        locales = []
        if list_type == 'documents':
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                if entry['file_name'].startswith(os.getcwd()):
                    ids.append(entry['id'])
                    titles.append(entry['name'])
                    try:
                        locales.append(entry['locales'])
                    except KeyError:
                        locales.append(['none'])
        elif list_type == 'workflows':
            response = self.api.list_workflows(self.community_id)
            if response.status_code != 200:
                raise_error(response.json(), "Failed to list workflows")
            ids, titles = log_id_names(response.json())
        if len(ids) == 0:
            print "no", list_type
        # print 'id\t\t\t\t\t\ttitle'
        for i in range(len(ids)):
            if list_type != 'documents':
                if i==0:
                    print "%s: id, title"%list_type
                info = '{id} \t {title}'.format(id=ids[i], title=titles[i])
            else:
                if i==0:
                    print "documents: id, title, locales"
                info = '{id} \t {title} \t\t {locales}'.format(id=ids[i], title=titles[i],
                                                               locales=', '.join(locale for locale in locales[i]))
            print info

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
            if not len(locale[2]): # Arabic
                print "{0} ({1})".format(locale[0], locale[1])
            else:
                print "{0} ({1}, {2})".format(locale[0], locale[1], locale[2])

    def status_action(self, detailed, document_name=None):
        if document_name is not None:
            entry = self.doc_manager.get_doc_by_prop('name', document_name)
            try:
                doc_ids = [entry['id']]
            except TypeError:
                raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
        else:
            doc_ids = self.doc_manager.get_doc_ids()
        for doc_id in doc_ids:
            response = self.api.document_status(doc_id)
            if response.status_code != 200:
                raise_error(response.json(), "Failed to get status of document", True)
            else:
                title = response.json()['properties']['title']
                progress = response.json()['properties']['progress']
                print title + ': ' + str(progress) + '%'
                # for each doc id, also call /document/id/translation and get % of each locale
            if detailed:
                response = self.api.document_translation_status(doc_id)
                if response.status_code != 200:
                    raise_error(response.json(), 'Failed to get detailed status of document', True)
                try:
                    for entry in response.json()['entities']:
                        print '\tlocale: {0} \t percent complete: {1}%'.format(entry['properties']['locale_code'],
                                                                               entry['properties']['percent_complete'])
                except KeyError:
                    continue

    def download_by_name(self, document_name, locale_code, auto_format):
        try:
            document_id = self.doc_manager.get_doc_by_prop('name', document_name)['id']
        except TypeError:
            logger.error("Document name specified doesn't exist: {0}".format(document_name))
            return
        self.download_action(document_id, locale_code, auto_format)

    def download_action(self, document_id, locale_code, auto_format):
        # if not os.path.isdir(os.path.join(self.path, TRANS_DIR)):
        #     os.mkdir(os.path.join(self.path, TRANS_DIR))
        response = self.api.document_content(document_id, locale_code, auto_format)
        if response.status_code == 200:
            entry = self.doc_manager.get_doc_by_prop('id', document_id)
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
                except KeyError:
                    raise_error(doc_info.json(),
                                'Something went wrong trying to import document: {0}'.format(document_id), True)
                    return
                download_path = os.path.join(self.path, title)
                logger.info("Downloaded {0}".format(title))
            elif not locale_code:
                logger.info("Tried to download an existing document, did nothing")
                return
            else:
                file_name = entry['file_name']
                download_dir = os.path.dirname(file_name)
                base_name = os.path.basename(os.path.normpath(file_name))
                name_parts = base_name.split('.')
                if len(name_parts) > 1:
                    name_parts.insert(-1, locale_code)
                    downloaded_name = '.'.join(part for part in name_parts)
                else:
                    downloaded_name = name_parts[0] + '.' + locale_code
                download_path = os.path.join(download_dir, downloaded_name)
                logger.info("Downloaded {0} for locale {1}: {2}".format(name_parts[0], locale_code, downloaded_name))
            with open(download_path, 'wb') as fh:
                for chunk in response.iter_content(1024):
                    fh.write(chunk)
            return download_path
        else:
            raise_error(response.json(), 'Failed to download content for id: {0}'.format(document_id), True)

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
            logger.warn("Document name specified doesn't exist: {0}".format(document_name))
            return
            # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
        response = self.api.delete_document(document_id)
        if response.status_code != 204:
            # raise_error(response.json(), "Failed to delete document {0}".format(document_name), True)
            logger.error("Failed to delete document {0}".format(document_name))
        else:
            logger.info("{0} has been deleted.".format(document_name))
            self.doc_manager.remove_element(document_id)

    def sync_action(self, force, update):
        response = self.api.list_documents(self.project_id)
        tms_doc_ids = []
        local_ids = self.doc_manager.get_doc_ids()
        if response.status_code == 200:
            tms_documents = response.json()['entities']
            for entity in tms_documents:
                tms_doc_ids.append(entity['properties']['id'])
        elif response.status_code == 204:
            pass
        else:
            raise_error(response.json(), 'Error trying to find current documents in TMS')
        ids_to_delete = [x for x in local_ids if x not in tms_doc_ids]
        ids_not_local = [x for x in tms_doc_ids if x not in local_ids]
        if not ids_to_delete and not ids_not_local:
            # todo need to check if content also up to date?
            logger.info('Local documents already up-to-date with documents in TMS')
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
                title = os.path.basename(download_path)
                self._add_document(download_path, title, curr_id)
                response = self.api.document_translation_status(curr_id)
                locales = []
                try:
                    for entity in response.json()['entities']:
                        locales.append(entity['properties']['locale_code'])
                except KeyError:
                    continue
                self.doc_manager.update_document('locales', list(locales), curr_id)


def raise_error(json, error_message, is_warning=False):
    try:
        error = json['messages'][0]
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

def reinit(host, project_path, delete):
    if is_initialized(project_path):
        logger.warning('This project is already initialized!')
        if not delete:
            return False
        confirm = 'not confirmed'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = raw_input(
                "Are you sure you want to delete the current project? "
                "This will also delete the project in your community. [y/N]: ")
        # confirm if would like to delete existing folder
        if not confirm or confirm in ['n', 'N']:
            return False
        else:
            # delete the corresponding project online
            logger.info('Deleting old project folder and creating new one..')
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            if os.path.isfile(config_file_name):
                old_config = ConfigParser.ConfigParser()
                old_config.read(config_file_name)
                project_id = old_config.get('main', 'project_id')
                access_token = old_config.get('main', 'access_token')
                api = ApiCalls(host, access_token)
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
            return access_token
    return True

def display_choice(display_type, info):
    if display_type == 'community':
        input_prompt = 'Which community should this project belong to? '
    elif display_type == 'project':
        input_prompt = 'Which existing project should be used? '
    else:
        raise exceptions.ResourceNotFound("Cannot display info asked for")
    choice = 'none-chosen'
    import operator
    sorted_info = sorted(info.iteritems(), key=operator.itemgetter(1))
    mapper = {}
    index = 0
    for entry in sorted_info:
        mapper[index] = {entry[0]: entry[1]}
        index += 1
    for k, v in mapper.iteritems():
        print '({0}) {1} ({2})'.format(k, v.itervalues().next(), v.iterkeys().next())
    while choice not in mapper.iterkeys():
        choice = raw_input(input_prompt)
        try:
            choice = int(choice)
        except ValueError:
            print("That's not a valid option!")
    logger.info('Selected "{0}" {1}.'.format(mapper[choice].itervalues().next(), display_type))
    return mapper[choice].iterkeys().next()


def init_action(host, access_token, project_path, folder_name, workflow_id, locale, delete):
    # check if Lingotek directory already exists
    to_init = reinit(host, project_path, delete)
    if not to_init:
        return
    elif to_init is not True:
        access_token = to_init

    if not access_token:
        from auth import run_oauth
        access_token = run_oauth(host)

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

    config_parser = ConfigParser.ConfigParser()
    config_parser.add_section('main')
    config_parser.set('main', 'access_token', access_token)
    config_parser.set('main', 'host', host)
    config_parser.set('main', 'root_path', project_path)
    config_parser.set('main', 'workflow_id', workflow_id)
    config_parser.set('main', 'default_locale', locale)
    # get community id
    community_info = api.get_communities_info()
    if len(community_info) == 0:
        raise exceptions.ResourceNotFound('You are not part of any communities in the Lingotek TMS')
    if len(community_info) > 1:
        community_id = display_choice('community', community_info)
    else:
        community_id = community_info.iterkeys().next()
    config_parser.set('main', 'community_id', community_id)

    response = api.list_projects(community_id)
    if response.status_code != 200:
        raise_error(response.json(), 'Something went wrong trying to find projects in your community')
    project_info = api.get_project_info(community_id)
    if len(project_info) > 0:
        confirm = 'none'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = raw_input(
                'Would you like to use an existing Lingotek project? [y/N]:')
        if confirm or confirm in ['y', 'Y', 'yes', 'Yes']:
            project_id = display_choice('project', project_info)
            config_parser.set('main', 'project_id', project_id)
            config_parser.write(config_file)
            config_file.close()
            return
    project_name = raw_input("Please enter a new Lingotek project name: %s"%folder_name + chr(8)*len(folder_name))
    if not project_name:
        project_name = folder_name
    response = api.add_project(project_name, community_id, workflow_id)
    if response.status_code != 201:
        raise_error(response.json(), 'Failed to add current project to TMS')
    project_id = response.json()['properties']['id']
    config_parser.set('main', 'project_id', project_id)

    config_parser.write(config_file)
    config_file.close()

def find_conf(curr_path):
    """
    check if the conf folder exists in current directory's parent directories
    """
    if os.path.isdir(os.path.join(curr_path, CONF_DIR)):
        return curr_path
    elif curr_path == os.path.abspath(os.sep):
        return None
    else:
        return os.path.abspath(os.path.join(curr_path, os.pardir))

def get_files(root, patterns):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """
    matched_files = []
    for path, subdirs, files in os.walk(root):
        # matched_files = any(fnmatch.fnmatch(files, p) for p in patterns)
        for pattern in patterns:
            for name in fnmatch.filter(files, pattern):
                # print 'found without subdir'
                # print os.path.join(path, name)
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
