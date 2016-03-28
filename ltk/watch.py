import ctypes
from ltk.actions import Action
from logger import logger
from utils import map_locale
import time
import requests
from requests.exceptions import ConnectionError
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from ltk.watchhandler import WatchHandler

# import Queue

# import threading

# class WatchThread:
#     def __init__(self, interval=5):
#         self.interval = interval
#
#         self.thread = threading.Thread(target=self.run, args=())
#         self.thread.daemon = True
#         self.thread.start()_on_create
#
#     def run(self):
#         while True:
#             time.sleep(self.interval)

def restart():
    """Restarts the program. Used after exceptions. Otherwise, watch doesn't work anymore."""
    print("Restarting watch")
    python = sys.executable
    os.execl(python, python, * sys.argv)

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
                    if e.__class__ in exec_type:
                        logger.error("Connection has timed out. Retrying..")
                        time.sleep(timeout)  # sleep for some time then retry
                    else:
                        raise e
        return wrapper
    return decorator

def is_hidden_file(file_path):
    # todo more robust checking for OSX files that doesn't start with '.'
    name = os.path.basename(os.path.abspath(file_path))
    return name and (name.startswith('.') or has_hidden_attribute(file_path) or name == "4913")

def has_hidden_attribute(file_path):
    """ Detects if a file has hidden attributes """
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(file_path))
        assert attrs != -1
        result = bool(attrs & 2)
    except (AttributeError, AssertionError):
        result = False
    return result

class WatchAction(Action):
    # def __init__(self, path, remote=False):
    def __init__(self, path):
        Action.__init__(self, path)
        self.observer = Observer()  # watchdog observer that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified
        self.handler.on_created = self._on_created
        self.handler.on_moved = self._on_moved
        self.watch_queue = []  # not much slower than deque unless expecting 100+ items
        self.locale_delimiter = None
        self.ignore_ext = []  # file types to ignore as specified by the user
        # if remote:  # poll lingotek cloud periodically if this option enabled
        # self.remote_thread = threading.Thread(target=self.poll_remote(), args=())
        # self.remote_thread.daemon = True
        # self.remote_thread.start()

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
                    # logger.info('Detected local content modified: {0}'.format(fn))
                    # self.update_document_action(os.path.join(self.path, fn))
                    # logger.info('Updating remote content: {0}'.format(fn))
                    self.update_content(fn)
            except KeyboardInterrupt:
                self.observer.stop()
            except ConnectionError:
                print("Could not connect to remote.")
                restart()
            # except:
            #     print(sys.exc_info()[1])
            #     print("Unable to update document.")
            #     restart()

    def _on_created(self, event):
        # get path
        # add action
        file_path = event.src_path
        # if it's a hidden document, don't do anything 
        if not is_hidden_file(file_path):
            relative_path = file_path.replace(self.path, '')
            title = os.path.basename(os.path.normpath(file_path))
            curr_ext = os.path.splitext(file_path)[1]
            # return if the extension should be ignored or if the path is not a file
            if curr_ext in self.ignore_ext or not os.path.isfile(file_path):
                # logger.info("Detected a file with an extension in the ignore list, ignoring..")
                return
            if self.locale_delimiter:
                try:
                    # curr_locale = title.split(self.locale_delimiter)[1]
                    # todo locale detection needs to be more robust
                    curr_locale = title.split(self.locale_delimiter)[-2]
                    fixed_locale = map_locale(curr_locale)
                    if fixed_locale:
                        self.watch_locales.add(fixed_locale)
                    else:
                        logger.warning('This document\'s detected locale: {0} is not supported.'.format(curr_locale))
                except IndexError:
                    logger.warning('Cannot detect locales from file: {0}, not adding any locales'.format(title))
            # only add or update the document if it's not a hidden document and it's a new file
            try:
                if self.doc_manager.is_doc_new(relative_path):
                    self.add_document(self.locale, file_path, title)
                elif self.doc_manager.is_doc_modified(relative_path, self.path):
                    self.update_content(relative_path)
            except KeyboardInterrupt:
                self.observer.stop()
            except ConnectionError:
                print("Could not connect to remote.")
                restart()
            # except:
            #     print(sys.exc_info()[1])
            #     print("Unable to add document on the cloud.")
            #     restart()
            document_id = self.doc_manager.get_doc_by_prop('name', title)['id']
            self.watch_add_target(title, document_id)
            # logger.info('Added new document {0}'.format(title
        # else:
        #     print("Skipping hidden file "+file_path)

    def _on_moved(self, event):
        """Used for programs, such as gedit, that modify documents by moving (overwriting)
        the previous document with the temporary file. Only the moved event contains the name of the
        destination file."""
        event = FileSystemEvent(event.dest_path)
        self._on_modified(event)

    def watch_add_target(self, title, document_id):
        if self.check_remote_doc_exist(title, document_id):
            self.target_action(title, self.watch_locales, None, None, None, document_id)
            if document_id in self.watch_queue:
                self.watch_queue.pop(0)
        else:
            self.watch_queue.append(document_id)

    def process_queue(self):
        """do stuff with documents in queue (currently just add targets)"""
        # todo may want to process more than 1 item every "poll"..
        if self.watch_queue:
            self.watch_add_target(None, self.watch_queue.pop(0))

    def update_content(self, relative_path):
        logger.info('Detected local content modified: {0}'.format(relative_path))
        self.update_document_action(os.path.join(self.path, relative_path))
        logger.info('Updating remote content: {0}'.format(relative_path))

    @retry(logger)
    def poll_remote(self):
        """ poll lingotek servers to check if MT finished """
        # todo eventually: poll for other jobs (prefill, analyze, etc...)
        # print 'polling remote...'
        documents = self.doc_manager.get_all_entries()
        for doc in documents:
            doc_id = doc['id']
            if doc_id in self.watch_queue:
                # if doc id in queue, not imported yet
                continue
            locale_progress = self.import_locale_info(doc_id, True)
            try:
                downloaded = doc['downloaded']
            except KeyError:
                downloaded = []
                self.doc_manager.update_document('downloaded', downloaded, doc_id)
            for locale, progress in locale_progress.iteritems():
                if progress == 100 and locale not in downloaded:
                    logger.info('Translation completed ({0} - {1})'.format(doc_id,locale))
                    self.download_action(doc_id, locale, False, False)

    def watch_action(self, watch_path, ignore, delimiter):
        # print self.path
        if not watch_path and not self.watch_dir:
            watch_path = self.path
        elif watch_path:
            watch_path = os.path.join(self.path, watch_path)
        else:
            watch_path = self.watch_dir
        self.ignore_ext.extend(ignore)
        self.locale_delimiter = delimiter
        print "Watching for updates in: {0}".format(watch_path)
        try:
            self.observer.schedule(self.handler, path=watch_path, recursive=True)
            self.observer.start()
        except KeyboardInterrupt:
            self.observer.stop()
        # except:
        #     print(sys.exc_info()[1])
        #     restart()

        try:
            while True:
                # print 'Watching....'
                self.poll_remote()
                self.process_queue()
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        # except:
        #     print(sys.exc_info()[1])
        #     restart()

        self.observer.join()
