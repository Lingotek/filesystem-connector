import configparser
import os
import shutil
import fnmatch
import time
from ltk import exceptions
from ltk.apicalls import ApiCalls
from ltk.utils import detect_format
from ltk.managers import DocumentManager
from ltk.constants import CONF_DIR, CONF_FN, SYSTEM_FILE

from ltk.logger import logger


class Action:
    def __init__(self, path):
        self.host = ''
        self.access_token = ''
        self.project_id = ''
        self.project_name = ''
        self.path = path
        self.community_id = ''
        self.workflow_id = ''  # default workflow id; MT phase only
        self.locale = ''
        self.download_dir = None  # directory where downloaded translation will be stored
        self.watch_dir = None  # if specified, only watch this directory
        self.watch_locales = set()  # if specified, add these target locales to any files in the watch folder
        if not self._is_initialized():
            raise exceptions.UninitializedError("This project is not initialized. Please run init command.")
        self._initialize_self()
        self.api = ApiCalls(self.host, self.access_token)
        self.doc_manager = DocumentManager(self.path)

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
        conf_parser = configparser.ConfigParser()
        conf_parser.read(config_file_name)
        self.host = conf_parser.get('main', 'host')
        self.access_token = conf_parser.get('main', 'access_token')
        self.project_id = conf_parser.get('main', 'project_id')
        self.community_id = conf_parser.get('main', 'community_id')
        self.workflow_id = conf_parser.get('main', 'workflow_id')
        self.locale = conf_parser.get('main', 'default_locale')
        try:
            # todo this try block will stop once one of them gets an exception..
            self.project_name = conf_parser.get('main', 'project_name')
            self.download_dir = conf_parser.get('main', 'download_folder')
            self.watch_dir = conf_parser.get('main', 'watch_folder')
            watch_locales = conf_parser.get('main', 'watch_locales')
            self.watch_locales = set(watch_locales.split(','))
        except configparser.NoOptionError:
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
        conf_parser = configparser.ConfigParser()
        conf_parser.read(config_file_name)
        return config_file_name, conf_parser

    def update_config_file(self, option, value, conf_parser, config_file_name, log_info):
        conf_parser.set('main', option, value)
        with open(config_file_name, 'w') as new_file:
            conf_parser.write(new_file )
        # self._initialize_self()
        logger.info(log_info)

    def config_action(self, locale, workflow_id, download_folder, watch_folder, target_locales):
        config_file_name, conf_parser = self.init_config_file()
        if locale:
            self.locale = locale
            log_info = 'Project default locale has been updated to {0}'.format(locale)
            self.update_config_file('default_locale', locale, conf_parser, config_file_name, log_info)
        if workflow_id:
            response = self.api.patch_project(self.project_id, workflow_id)
            if response.status_code != 204:
                raise_error(response.json(), 'Something went wrong trying to update workflow_id of project')
            self.workflow_id = workflow_id
            log_info = 'Project default workflow has been updated to {0}'.format(workflow_id)
            self.update_config_file('workflow_id', workflow_id, conf_parser, config_file_name, log_info)
            conf_parser.set('main', 'workflow_id', workflow_id)
        if download_folder:
            download_path = os.path.join(self.path, download_folder)
            self.download_dir = download_folder
            log_info = 'Set download folder to {0}'.format(download_folder)
            self.update_config_file('download_folder', download_path, conf_parser, config_file_name, log_info)
        if watch_folder:
            watch_path = os.path.join(self.path, watch_folder)
            self.watch_dir = watch_folder
            log_info = 'Set watch folder to {0}'.format(watch_folder)
            self.update_config_file('watch_folder', watch_path, conf_parser, config_file_name, log_info)
        if target_locales:
            log_info = 'Added target locales: {} for watch folder'.format(
                ', '.join(target for target in target_locales))
            self.watch_locales = set(target_locales)
            target_locales = ','.join(target for target in target_locales)
            self.update_config_file('watch_locales', target_locales, conf_parser, config_file_name, log_info)

        print ('host: {0}\naccess_token: {1}\nproject id: {2}\nproject name: {6}\ncommunity id: {3}\nworkflow id: {4}\n' \
              'locale: {5}\ndownloads folder: {7}\nwatch folder: {8}\nwatch target locales: {9}'.format(
            self.host, self.access_token, self.project_id, self.community_id, self.workflow_id, self.locale,
            self.project_name, self.download_dir, self.watch_dir, ', '.join(x for x in self.watch_locales)))

    def add_document(self, locale, file_name, title, **kwargs):
        response = self.api.add_document(file_name, locale, self.project_id, title, **kwargs)
        if response.status_code != 202:
            raise_error(response.json(), "Failed to add document {0}".format(title), True)
        else:
            logger.info('Added document {0}'.format(title))
            relative_path = file_name.replace(self.path, '')
            self._add_document(relative_path, title, response.json()['properties']['id'])

    def add_action(self, locale, file_patterns, **kwargs):
        if not locale:
            locale = self.locale
        # format will be automatically detected by extension but may not be what user expects
        # use current working directory as root for files instead of project root
        matched_files = get_files(os.getcwd(), file_patterns)
        if not matched_files:
            raise exceptions.ResourceNotFound("Could not find the specified file/pattern")
        for file_name in matched_files:
            # title = os.path.basename(os.path.normpath(file_name)).split('.')[0]
            title = os.path.basename(os.path.normpath(file_name))
            relative_path = file_name.replace(self.path, '')
            if not self.doc_manager.is_doc_new(relative_path):
                if self.doc_manager.is_doc_modified(relative_path, self.path):
                    if 'force' in kwargs and kwargs['force']:
                        confirm = 'Y'
                    else:
                        confirm = 'not confirmed'
                    while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
                        confirm = input("This document already exists. Would you like to overwrite it? [y/N]: ")
                    # confirm if would like to overwrite existing document in Lingotek Cloud
                    if not confirm or confirm in ['n', 'N']:
                        continue
                    else:
                        logger.info('Overwriting document: {0} in Lingotek Cloud...'.format(title))
                        self.update_document_action(file_name, title, **kwargs)
                        continue
                else:
                    logger.error("This document has already been added: {0}".format(title))
                    continue
            # todo separate function somewhere around here maybe..
            self.add_document(locale, file_name, title, **kwargs)
            # response = self.api.add_document(file_name, locale, self.project_id, title, **kwargs)
            # if response.status_code != 202:
            #     raise_error(response.json(), "Failed to add document {0}".format(title), True)
            # else:
            #     logger.info('Added document {0}'.format(title))
            #     self._add_document(relative_path, title, response.json()['properties']['id'])

    def push_action(self):
        entries = self.doc_manager.get_all_entries()
        updated = False
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
        if not updated:
            print('All documents up-to-date with Lingotek Cloud. ')
            logger.info('All documents up-to-date with Lingotek Cloud. ')

    def update_document_action(self, file_name, title=None, **kwargs):
        relative_path = file_name.replace(self.path, '')
        entry = self.doc_manager.get_doc_by_prop('file_name', relative_path)
        try:
            document_id = entry['id']
        except TypeError:
            logger.error("Document name specified for update doesn't exist: {0}".format(title))
            print (file_name, entry['prolerty'])
            return
        if title:
            response = self.api.document_update(document_id, file_name, title=title, **kwargs)
        else:
            response = self.api.document_update(document_id, file_name)
        if response.status_code != 202:
            raise_error(response.json(), "Failed to update document {0}".format(file_name), True)
        self._update_document(relative_path)
      

    def _target_action_db(self, to_delete, locales, document_id):
        if to_delete:
            curr_locales = self.doc_manager.get_doc_by_prop('id', document_id)['locales']
            updated_locales = set(curr_locales) - set(locales)
            self.doc_manager.update_document('locales', updated_locales, document_id)
        else:
            self.doc_manager.update_document('locales', list(locales), document_id)

    def target_action(self, document_name, locales, to_delete, due_date, workflow, document_id=None):
        change_db_entry = True
        if to_delete:
            expected_code = 204
            failure_message = 'Failed to delete target'
            info_message = 'Deleted locale'
        else:
            expected_code = 201
            failure_message = 'Failed to add target'
            info_message = 'Added target'
        if not document_name and not document_id:
            for locale in locales:
                response = self.api.project_add_target(self.project_id, locale, due_date) if not to_delete \
                    else self.api.project_delete_target(self.project_id, locale)
                if response.status_code != expected_code:
                    raise_error(response.json(), '{message} {locale} for project'.format(message=failure_message,
                                                                                         locale=locale), True)
                    change_db_entry = False
                    continue
                logger.info('{message} {locale} for project {project_name}'.format(message=info_message, locale=locale,
                                                                                   project_name=self.project_name))
            document_ids = self.doc_manager.get_doc_ids()
            if change_db_entry:
                for document_id in document_ids:
                    self._target_action_db(to_delete, locales, document_id)
        else:
            # todo: document name or file name? since file name will be relative to root
            # todo: clean this code up some
            if not document_id:
                entry = self.doc_manager.get_doc_by_prop('name', document_name)
                try:
                    document_id = entry['id']
                except TypeError:
                    logger.error('Document name specified for target doesn\'t exist: {0}'.format(document_name))
                    return
                    # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
            if not document_name:
                entry = self.doc_manager.get_doc_by_prop('id', document_id)
                try:
                    document_name = entry['name']
                except TypeError:
                    logger.error('Document specified for target doesn\'t exist: {0}'.format(document_id))
                    return
            for locale in locales:
                response = self.api.document_add_target(document_id, locale, workflow, due_date) if not to_delete \
                    else self.api.document_delete_target(document_id, locale)
                if response.status_code != expected_code:
                    raise_error(response.json(), '{message} {locale} for document'.format(message=failure_message,
                                                                                          locale=locale), True)
                    change_db_entry = False
                    continue
                logger.info('{message} {locale} for document {name}'.format(message=info_message,
                                                                            locale=locale, name=document_name))
            if change_db_entry:
                self._target_action_db(to_delete, locales, document_id)

    def list_ids_action(self):
        """ lists ids of list_type specified """
        ids = []
        titles = []
        locales = []
        entries = self.doc_manager.get_all_entries()
        cwd = os.path.join(os.getcwd(), '')
        for entry in entries:
            if entry['file_name'].startswith(cwd.replace(self.path, '')):
                ids.append(entry['id'])
                relative_path = entry['file_name'].replace(cwd.replace(self.path, ''), '')
                titles.append(relative_path)
                try:
                    locales.append(entry['locales'])
                except KeyError:
                    locales.append(['none'])
        if not ids:
            print ('No local documents')
            return
        print ('Local documents: id, file name, locales')
        for i in range(len(ids)):
            info = '{id} \t {title} \t\t {locales}'.format(id=ids[i], title=titles[i],
                                                           locales=', '.join(locale for locale in locales[i]))
            print (info)

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
        format_mapper = detect_format(None, True)
        print ("Formats Lingotek supports:")
        for format_name in sorted(set(format_mapper.values())):
            print (format_name)

    def list_filter_action(self):
        response = self.api.list_filters()
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filters')
        filter_entities = response.json()['entities']
        print (bytes('Filters: id, title', 'UTF-8'))
        for entry in filter_entities:
            properties = entry['properties']
            title = properties['title']
            filter_id = properties['id']
            print ('{0}\t{1}\t'.format(filter_id, title))

    def print_status(self, title, progress):
        print ('{0}: {1}%'.format(title, progress))
        # print title + ': ' + str(progress) + '%'
        # for each doc id, also call /document/id/translation and get % of each locale

    def print_detailed(self, doc_id):
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
            print("Error listing translations")
            return
            # return detailed_status

    def status_action(self, **kwargs):
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
                if response.json():
                    raise_error(response.json(), "Failed to get status of documents", True)
                else:
                    raise_error("", "Failed to get status of documents", True)
            else:
                for entry in response.json()['entities']:
                    title = entry['entities'][1]['properties']['title']
                    progress = entry['entities'][1]['properties']['progress']
                    self.print_status(title, progress)
                    if 'detailed' in kwargs and kwargs['detailed']:
                        self.print_detailed(entry['properties']['id'])
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
                raise_error(response.json(), "Failed to get status of document", True)
            else:
                title = response.json()['properties']['title']
                progress = response.json()['properties']['progress']
                self.print_status(title, progress)
            if 'detailed' in kwargs and kwargs['detailed']:
                self.print_detailed(doc_id)

    def download_by_name(self, document_name, locale_code, auto_format):
        try:
            document_id = self.doc_manager.get_doc_by_prop('name', document_name)['id']
        except TypeError:
            logger.error("Document name specified for download doesn't exist: {0}".format(document_name))
            return
        self.download_action(document_id, locale_code, auto_format)

    def download_action(self, document_id, locale_code, auto_format, locale_ext=True):
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
                                'Something went wrong trying to download document: {0}'.format(document_id), True)
                    return
                download_path = os.path.join(self.path, title)
                logger.info("Downloaded: {0}".format(title))
            else:
                if not locale_code:
                    logger.info("No target locales, downloading source instead.")
                    locale_code = self.locale
                file_name = entry['file_name']
                download_dir = os.path.join(self.path, os.path.dirname(file_name))
                base_name = os.path.basename(os.path.normpath(file_name))
                if locale_ext:
                    name_parts = base_name.split('.')
                    if len(name_parts) > 1:
                        name_parts.insert(-1, locale_code)
                        downloaded_name = '.'.join(part for part in name_parts)
                    else:
                        downloaded_name = name_parts[0] + '.' + locale_code
                else:
                    downloaded_name = base_name
                download_path = os.path.join(download_dir, downloaded_name)
                logger.info('Downloaded: {0} ({1} - {2})'.format(downloaded_name, base_name, locale_code))
                self.doc_manager.update_document('downloaded', [locale_code], document_id)
            if self.download_dir:
                title = os.path.basename(os.path.normpath(download_path))
                download_path = os.path.join(self.download_dir, title)
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

    def rm_action(self, file_name, **kwargs):
        if not 'id' in kwargs or not kwargs['id']:
            try:
                entry = self.doc_manager.get_doc_by_prop('file_name', file_name)
                #print ('entry :', entry)
                document_id = entry['id']
                #print ('id:', document_id)
            except TypeError:            
                logger.warning("Document name specified for remove doesn't exist locally: {0}".format(file_name))
                return
                # raise exceptions.ResourceNotFound("Document name specified doesn't exist: {0}".format(document_name))
        else:
            document_id = file_name
            doc = self.doc_manager.get_doc_by_prop('id', document_id)
            if doc:
                file_name = doc['file_name']
            else:
                file_name = document_id
        response = self.api.document_delete(document_id)
        #print (response)
        if response.status_code != 204:            
            # raise_error(response.json(), "Failed to delete document {0}".format(document_name), True)
            logger.error("Failed to delete document {0}".format(file_name))
        else:
            logger.info("{0} has been deleted remotely.".format(file_name))
            if 'force' in kwargs and kwargs['force']:               
                self.delete_local(file_name, document_id)
            self.doc_manager.remove_element(document_id)

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

    def clean_action(self, force, dis_all, document_name):
        if dis_all:
            # disassociate everything
            self.doc_manager.clear_all()
            return

        if document_name:
            try:
                entry = self.doc_manager.get_doc_by_prop('name', document_name)
                document_id = entry['id']
                self.doc_manager.remove_element(document_id)
            except TypeError:
                logger.warning("Document name specified for clean doesn't exist: {0}".format(document_name))
            return

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
            logger.info('Local documents already up-to-date with Lingotek cloud')
            return
        logger.info('Cleaned up associations between local documents and Lingotek cloud')

    def delete_local(self, title, document_id, message=None):
        #print('local delete:', title, document_id)
        message = 'Removed local file {0}'.format(title) if not message else message
        file_name = self.doc_manager.get_doc_by_prop('id', document_id)['file_name']        
        try:
            os.remove(os.path.join(self.path, file_name))
            logger.info(message)            
        except OSError:
            logger.info('Something went wrong trying to delete the local file.')


def raise_error(json, error_message, is_warning=False, doc_id=None, file_name=None):
    try:
        error = json['messages'][0]
        print("id: "+str(doc_id))
        print("name: "+str(file_name))
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
        confirm = 'not confirmed'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = input(
                "Are you sure you want to delete the current project? "
                "This will also delete the project in your community. [y/N]: ")
        # confirm if would like to delete existing folder
        if not confirm or confirm in ['n', 'N']:
            return False
        else:
            # delete the corresponding project online
            logger.info('Deleting old project folder and creating new one...')
            config_file_name = os.path.join(project_path, CONF_DIR, CONF_FN)
            if os.path.isfile(config_file_name):
                old_config = configparser.ConfigParser()
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
        mapper[index] = {entry[0]: entry[1]}
        index += 1
    for k,v in mapper.items():
        for values in v:
            print ('({0}) {1} ({2})'.format(k, v[values], values))
    return mapper


def get_import_ids(info):
    mapper = choice_mapper(info)
    chosen_indices = ['none-chosen']
    while not set(chosen_indices) <= set(mapper.keys()):
        choice = input('Which documents to import? (Separate indices by comma) ')
        try:
            chosen_indices = map(int, choice.split(','))
        except ValueError:
            print ('Some unexpected, non-integer value was included')
    return [mapper[index].iterkeys().next() for index in chosen_indices]


def display_choice(display_type, info):
    if display_type == 'community':
        input_prompt = 'Which community should this project belong to? '
    elif display_type == 'project':
        input_prompt = 'Which existing project should be used? '
    else:
        raise exceptions.ResourceNotFound("Cannot display info asked for")
    mapper = choice_mapper(info)
    choice = 'none-chosen'
    while choice not in mapper:
        choice = input(input_prompt)
        try:
            choice = int(choice)
        except ValueError:
            print("That's not a valid option!")
    for v in mapper[choice]:
        logger.info('Selected "{0}" {1}.'.format(mapper[choice][v], display_type))
        return v, mapper[choice][v]


def check_global():
    # check for a global config file
    home_path = os.path.expanduser('~')
    sys_file = os.path.join(home_path, SYSTEM_FILE)
    if os.path.isfile(sys_file):
        # get the access token
        conf_parser = configparser.ConfigParser()
        conf_parser.read(sys_file)
        return conf_parser.get('main', 'access_token')
    else:
        return None


def create_global(access_token):
    """
    create a .lingotek file in user's $HOME directory
    """
    # go to the home dir
    home_path = os.path.expanduser('~')
    file_name = os.path.join(home_path, SYSTEM_FILE)
    sys_file = open(file_name, 'w')

    config_parser = configparser.ConfigParser()
    config_parser.add_section('main')
    config_parser.set('main', 'access_token', access_token)
    config_parser.write(sys_file)
    sys_file.close()


def init_action(host, access_token, project_path, folder_name, workflow_id, locale, delete, reset):
    # check if Lingotek directory already exists
    print("init_action")
    to_init = reinit(host, project_path, delete, reset)
    print("to_init: "+str(to_init))
    if not to_init:
        return
    elif to_init is not True:
        access_token = to_init

    ran_oauth = False
    if not access_token:
        access_token = check_global()
        if not access_token or reset:
            from ltk.auth import run_oauth

            access_token = run_oauth(host)
            ran_oauth = True
    print("access_token: "+str(access_token))
    if ran_oauth:
        # create or overwrite global file
        create_global(access_token)

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

    config_parser = configparser.ConfigParser()
    config_parser.add_section('main')
    config_parser.set('main', 'access_token', access_token)
    config_parser.set('main', 'host', host)
    # config_parser.set('main', 'root_path', project_path)
    config_parser.set('main', 'workflow_id', workflow_id)
    config_parser.set('main', 'default_locale', locale)
    # get community id
    community_info = api.get_communities_info()
    # print("Community INFO")
    # print(len(community_info))
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
        raise_error(response.json(), 'Something went wrong trying to find projects in your community')
    project_info = api.get_project_info(community_id)
    if len(project_info) > 0:
        confirm = 'none'
        while confirm != 'y' and confirm != 'Y' and confirm != 'N' and confirm != 'n' and confirm != '':
            confirm = input('Would you like to use an existing Lingotek project? [y/N]:')
        if confirm and confirm in ['y', 'Y', 'yes', 'Yes']:
            project_id, project_name = display_choice('project', project_info)
            config_parser.set('main', 'project_id', project_id)
            config_parser.set('main', 'project_name', project_name)
            config_parser.write(config_file)
            config_file.close()
            return
    project_name = input("Please enter a new Lingotek project name: %s" % folder_name + chr(8) * len(folder_name))
    if not project_name:
        project_name = folder_name
    response = api.add_project(project_name, community_id, workflow_id)
    if response.status_code != 201:
        raise_error(response.json(), 'Failed to add current project to Lingotek Cloud')
    project_id = response.json()['properties']['id']
    config_parser.set('main', 'project_id', project_id)
    config_parser.set('main', 'project_name', project_name)

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
        return find_conf(os.path.abspath(os.path.join(curr_path, os.pardir)))


def get_files(root, patterns):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """
    matched_files = []
    # print root
    for pattern in patterns:
        # check if pattern contains subdirectory
        subdir_pat, fn_pat = os.path.split(pattern)
        if not subdir_pat:
            for path, subdirs, files in os.walk(root):
                for fn in fnmatch.filter(files, pattern):
                    matched_files.append(os.path.join(path, fn))
        else:
            for path, subdirs, files in os.walk(root):
                # print os.path.split(path)
                # subdir = os.path.split(path)[1]  # get current subdir
                search_root = os.path.join(root, '')
                subdir = path.replace(search_root, '')
                # print subdir, subdir_pat
                if fnmatch.fnmatch(subdir, subdir_pat):
                    for fn in fnmatch.filter(files, fn_pat):
                        matched_files.append(os.path.join(path, fn))

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
