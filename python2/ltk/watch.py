# Using the following encoding: utf-8
import ctypes
from ltk.actions.action import Action
from ltk.actions import add_action
from ltk.actions import request_action
from ltk.actions import download_action
from ltk.logger import logger
from ltk.utils import map_locale, restart, get_relative_path, log_error
from ltk.locales import locale_list
import time
import requests
from requests.exceptions import ConnectionError
import os
import re
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from ltk.watchhandler import WatchHandler
from ltk.git_auto import Git_Auto
import ltk.check_connection

DEFAULT_COMMIT_MESSAGE  = "Translations updated for "

# retry decorator to retry connections
def retry(logger, timeout=5, exec_type=None):
    if not exec_type:
        exec_type = [requests.exceptions.ConnectionError]

    def decorator(function):
        def wrapper(*args, **kwargs):
            while True:
                try:
                    return function(*args, **kwargs)
                except Exception as e:
                    log_error(self.error_file_name, e)
                    if e.__class__ in exec_type:
                        logger.error("Connection has timed out. Retrying..")
                        time.sleep(timeout)  # sleep for some time then retry
                    else:
                        raise e
        return wrapper
    return decorator

def has_hidden_attribute(file_path):
    """ Detects if a file has hidden attributes """
    try:
        # Python 2
        attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(file_path))
        # End Python 2
        # Python 3
#         attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
        # End Python 3
        assert attrs != -1
        result = bool(attrs & 2)
    except (AttributeError, AssertionError):
        result = False
    return result

class WatchAction(Action):
    # def __init__(self, path, remote=False):
    def __init__(self, path=None, timeout=60):
        Action.__init__(self, path, True, timeout)
        self.observers = []  # watchdog observers that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified
        self.handler.on_created = self._on_created
        self.handler.on_moved = self._on_moved
        self.watch_queue = []  # not much slower than deque unless expecting 100+ items
        self.locale_delimiter = None
        self.ignore_ext = []  # file types to ignore as specified by the user
        self.detected_locales = {}  # dict to keep track of detected locales
        self.watch_folder = True
        self.timeout = timeout
        self.updated = {}
        self.git_auto = Git_Auto(path)
        self.polled_list = set([])
        self.force_poll = False
        self.add = add_action.AddAction(path)
        self.download = download_action.DownloadAction(path)
        self.root_path = path
        # if remote:  # poll lingotek cloud periodically if this option enabled
        # self.remote_thread = threading.Thread(target=self.poll_remote(), args=())
        # self.remote_thread.daemon = True
        # self.remote_thread.start()

    def is_hidden_file(self, file_path):
        # todo more robust checking for OSX files that doesn't start with '.'
        name = os.path.abspath(file_path).replace(self.path, "")
        if has_hidden_attribute(file_path) or ('Thumbs.db' in file_path) or ('ehthumbs.db' in file_path) or ('desktop.ini' in file_path):
            return True
        while name != "":
            if name.startswith('.') or name.startswith('~') or name == "4913":
                return True
            name = name.split(os.sep)[1:]
            name = (os.sep).join(name)
        return False

    def is_translation(self, file_name):
        locales = locale_list
        if any('.'+locale in file_name for locale in locales):
            locales = {v:k for k,v in enumerate(locales) if v in file_name}.keys()
            replace_target = None
            for locale in locales:
                original = file_name
                file_name = file_name.replace('.'+locale, '')
                if file_name != original:
                    replace_target = locale
                    break
            file_name = re.sub('\.{2,}', '.', file_name)
            file_name = file_name.rstrip('.')
            doc = self.doc_manager.get_doc_by_prop('file_name', file_name.replace(self.path, ''))
            replace_target = replace_target.replace("-", "_")
            if doc:
                if 'locales' in doc and replace_target in doc['locales']:
                    return True
        return False

    def check_remote_doc_exist(self, fn, document_id=None):
        """ check if a document exists remotely """
        if not document_id:
            entry = self.doc_manager.get_doc_by_prop('file_name', fn)
            document_id = entry['id']
        response = self.api.get_document(document_id)
        if response.status_code != 200:
            return False
        return True

    def _on_modified(self, event):
        """ Notify Lingotek cloud when a previously added file is modified """
        try:
            db_entries = self.doc_manager.get_all_entries()
            in_db = False
            fn = ''
            # print event.src_path
            for entry in db_entries:
                # print entry['file_name']
                if event.src_path.endswith(entry['file_name']):
                    fn = entry['file_name']
                    in_db = True
            if not event.is_directory and in_db:
                try:
                    # check that document is added in TMS before updating
                    if self.check_remote_doc_exist(fn) and self.doc_manager.is_doc_modified(fn, self.path):
                        #logger.info('Detected local content modified: {0}'.format(fn))
                        #self.update_document_action(os.path.join(self.path, fn))
                        #logger.info('Updating remote content: {0}'.format(fn))
                        try:
                            self.polled_list.remove(fn)
                        except Exception:
                            pass
                        self.update_content(fn)
                except KeyboardInterrupt:
                    for observer in self.observers:
                        observer.stop()
                except ConnectionError:
                    print("Could not connect to remote server.")
                    restart()
                except ValueError:
                    print(sys.exc_info()[1])
                    restart()
        except KeyboardInterrupt:
            for observer in self.observers:
                observer.stop()
        except Exception as err:
            restart("Error on modified: "+str(err)+"\nRestarting watch.")

    def _on_created(self, event):
        # get path
        # add action
        try:
            db_entries = self.doc_manager.get_all_entries()
            in_db = False
            fn = ''
            for entry in db_entries:
                if event.src_path.endswith(entry['file_name']):
                    fn = entry['file_name']
                    in_db = True
            if not event.is_directory and in_db:
                self._on_modified(event)
            else:
                file_path = event.src_path
                # if it's a hidden document, don't do anything
                if not self.is_hidden_file(file_path) and not self.is_translation(file_path):
                    relative_path = file_path.replace(self.path, '')
                    title = os.path.basename(os.path.normpath(file_path))
                    curr_ext = os.path.splitext(file_path)[1]
                    # return if the extension should be ignored or if the path is not a file
                    if curr_ext in self.ignore_ext or not os.path.isfile(file_path):
                        # logger.info("Detected a file with an extension in the ignore list, ignoring..")
                        return
                    # only add or update the document if it's not a hidden document and it's a new file
                    try:
                        if self.doc_manager.is_doc_new(relative_path, self.root_path) and self.watch_folder:
                            #testing
                            #self.polled_list.add(relative_path) #test that this doesn't break other areas of watch
                            #end testing

                            self.add.add_document(file_path, title, locale=self.locale)

                        elif self.doc_manager.is_doc_modified(relative_path, self.path):
                            self.update_content(relative_path)
                        else:
                            return
                    except KeyboardInterrupt:
                        for observer in self.observers:
                            observer.stop()
                    except ConnectionError:
                        print("Could not connect to remote server.")
                        restart()
                    except ValueError:
                        print(sys.exc_info()[1])
                        restart()
                    doc = self.doc_manager.get_doc_by_prop('file_name', relative_path)
                    if doc:
                        document_id = doc['id']
                    else:
                        return
                    if self.locale_delimiter:
                        try:
                            # curr_locale = title.split(self.locale_delimiter)[1]
                            # todo locale detection needs to be more robust
                            curr_locale = title.split(self.locale_delimiter)[-2]
                            fixed_locale = map_locale(curr_locale)
                            if fixed_locale:
                                print ("fixed locale: ", fixed_locale)
                                # self.watch_locales.add(fixed_locale)
                                self.detected_locales[document_id] = fixed_locale
                            else:
                                logger.warning('This document\'s detected locale: {0} is not supported.'.format(curr_locale))
                        except IndexError:
                            logger.warning('Cannot detect locales from file: {0}, not adding any locales'.format(title))
                    self.watch_add_target(relative_path, document_id)
                    # logger.info('Added new document {0}'.format(title
                # else:
                #     print("Skipping hidden file "+file_path)
        except KeyboardInterrupt:
            for observer in self.observers:
                observer.stop()
        # except Exception as err:
        #     restart("Error on created: "+str(err)+"\nRestarting watch.")

    def _on_moved(self, event):
        """Used for programs, such as gedit, that modify documents by moving (overwriting)
        the previous document with the temporary file. Only the moved event contains the name of the
        destination file."""
        try:
            event = FileSystemEvent(event.dest_path)
            self._on_modified(event)
        except KeyboardInterrupt:
            for observer in self.observers:
                observer.stop()
        except Exception as err:
            restart("Error on moved: "+str(err)+"\nRestarting watch.")

    def get_watch_locales(self, document_id):
        """ determine the locales that should be added for a watched doc """
        locales = []
        if self.detected_locales:
            try:
                locales = [self.detected_locales[document_id]]
            except KeyError:
                logger.error("Something went wrong. Could not detect a locale")
            return locales
        entry = self.doc_manager.get_doc_by_prop("id", document_id)
        try:
            locales = [locale for locale in self.watch_locales if locale not in entry['locales']]
        except KeyError:
            locales = self.watch_locales
        return locales

    def watch_add_target(self, file_name, document_id):
        if not file_name:
            title=self.doc_manager.get_doc_by_prop("id", document_id)
        else:
            title = os.path.basename(file_name)
        if document_id not in self.watch_queue:
            self.watch_queue.append(document_id)
        # Only add target if doc exists on the cloud
        if self.check_remote_doc_exist(title, document_id):
            locales_to_add = self.get_watch_locales(document_id)
            if locales_to_add == ['[]']: locales_to_add = []
            # if len(locales_to_add) == 1:
            #     printStr = "Adding target "+locales_to_add[0]
            # else:
            #     printStr = "Adding targets "
            #     for target in locales_to_add:
            #         printStr += target+","
            # print(printStr)
            if self.api.get_document(document_id):
                request = request_action.RequestAction(self.path, title, file_name, locales_to_add, None, None, None, document_id, True)
                if request.target_action() and document_id in self.watch_queue:
                    self.watch_queue.remove(document_id)

    def process_queue(self):
        """do stuff with documents in queue (currently just add targets)"""
        # todo may want to process more than 1 item every "poll"..
        # if self.watch_queue:
        #     self.watch_add_target(None, self.watch_queue.pop(0))
        for document_id in self.watch_queue:
            self.watch_add_target(None, document_id)

    def update_content(self, relative_path):
        if self.update_document_action(os.path.join(self.path, relative_path)):
            self.updated[relative_path] = 0
            logger.info('Updating remote content: {0}'.format(relative_path))

    def check_modified(self, doc): # Checks if the version of a document on Lingotek's system is more recent than the local version
        old_date = doc['last_mod']
        response = self.api.get_document(doc['id'])
        if response.status_code == 200:
            new_date = response.json()['properties']['modified_date']
            # orig_count = response.json()['entities'][1]['properties']['count']['character']
        else:
            print("Document not found on Lingotek Cloud: "+str(doc['name']))
            return False
        if int(old_date)<int(str(new_date)[0:10]):
            return True
        return False

    @retry(logger)
    def poll_remote(self):
        """ poll lingotek servers to check if translation is finished """
        if self.auto_format_option == 'on':
            autoFormat = True;
        else:
            autoFormat = False;
        documents = self.doc_manager.get_all_entries()  # todo this gets all documents, not necessarily only ones in watch folder
        documents_downloaded = False
        git_commit_message = DEFAULT_COMMIT_MESSAGE
        for doc in documents:
            doc_id = doc['id']
            if doc_id in self.watch_queue:
                # if doc id in queue, not imported yet
                continue
            file_name = doc['file_name']
            # Wait for Lingotek's system to no longer show translation as as completed
            if file_name in self.updated:
                if self.updated[file_name] > 3:
                    self.updated.pop(file_name, None)
                else:
                    self.updated[file_name] += self.timeout
                    continue
            try:
                downloaded = doc['downloaded']
            except KeyError:
                downloaded = []
                self.doc_manager.update_document('downloaded', downloaded, doc_id)
            if file_name not in self.polled_list or self.force_poll:
                locale_progress = self.import_locale_info(doc_id, True)
                # Python 2
                for locale, progress in locale_progress.iteritems():
                # End Python 2
                # Python 3
#                 for locale in locale_progress:
#                     progress = locale_progress[locale]
                # End Python 3
                    if progress == 100 and locale not in downloaded:
                        document_added = False
                        if (doc['name']+": ") not in git_commit_message:
                            if documents_downloaded: git_commit_message += '; '
                            git_commit_message += doc['name'] + ": "
                            document_added = True
                        if document_added:
                            git_commit_message += locale
                        else:
                            git_commit_message += ', ' + locale
                        documents_downloaded = True
                        logger.info('Translation completed ({0} - {1})'.format(doc_id, locale))
                        if self.locale_delimiter:
                            locale = locale.replace('_','-')
                            self.download.download_action(doc_id, locale, autoFormat, xliff=False, locale_ext=False)
                        else:
                            locale = locale.replace('_','-')
                            if self.clone_option == 'on':
                                self.download.download_action(doc_id, locale, autoFormat, xliff=False, locale_ext=False)
                            else:
                                self.download.download_action(doc_id, locale, autoFormat)
                    elif progress != 100 and locale in downloaded:
                        # print("Locale "+str(locale)+" for document "+doc['name']+" is no longer completed.")
                        self.doc_manager.remove_element_in_prop(doc_id, 'downloaded', locale)
                if set(locale_progress.keys()) == set(downloaded):
                    if all(value == 100 for value in locale_progress.values()):
                        self.polled_list.add(file_name)
        config_file_name, conf_parser = self.init_config_file()
        git_autocommit = conf_parser.get('main', 'git_autocommit')
        if git_autocommit in ['True', 'on'] and documents_downloaded == True:
            self.git_auto.commit(git_commit_message)
            self.git_auto.push()


    def complete_path(self, file_location):
        # print("self.path: "+self.path)
        # print("file_location: "+file_location)
        # print("abs file_location: "+os.path.abspath(file_location))
        abspath=os.path.abspath(file_location)
        # norm_path = os.path.abspath(file_location).replace(self.path, '')
        print
        return abspath.rstrip(os.sep)

    def watch_action(self, ignore, delimiter=None, no_folders=False, force_poll=False): # watch_paths, ignore, delimiter=None, no_folders=False):
        # print self.path
        watch_paths = None
        if not watch_paths:
            watch_paths = self.folder_manager.get_file_names()
            for i in range(len(watch_paths)):
                watch_paths[i] = get_relative_path(self.path, watch_paths[i])
        else:
            watch_paths_list = []
            for path in watch_paths:
                watch_paths_list.append(path.rstrip(os.sep))
            watch_paths = watch_paths_list
        if len(watch_paths) and not no_folders:
            self.watch_folder = True
        else:
            watch_paths = [os.getcwd()]
        if self.watch_folder:
            watch_message = "Watching for updates in "
            for i in range(len(watch_paths)):
                watch_paths[i] = self.complete_path(watch_paths[i])
                watch_message += "{0}".format(watch_paths[i])
                if i < len(watch_paths)-1:
                    watch_message += " "
            print (watch_message)
        else:
            print ("Watching for updates to added documents")
        if force_poll:
            self.force_poll = True
        self.ignore_ext.extend(ignore)
        self.locale_delimiter = delimiter
        for watch_path in watch_paths:
            observer = Observer()
            observer.schedule(self.handler, path=watch_path, recursive=True)
            observer.start()
            self.observers.append(observer)
        queue_timeout = 3
        # start_time = time.clock()
        try:
            while True:
                if ltk.check_connection.check_for_connection():
                    self.poll_remote()
                    current_timeout = self.timeout
                    while len(self.watch_queue) and current_timeout > 0:
                        self.process_queue()
                        time.sleep(queue_timeout)
                        current_timeout -= queue_timeout
                time.sleep(self.timeout)
        except KeyboardInterrupt:
            for observer in self.observers:
                observer.stop()
        # except Exception as err:
        #     restart("Error: "+str(err)+"\nRestarting watch.")
        for observer in self.observers:
            observer.join()
