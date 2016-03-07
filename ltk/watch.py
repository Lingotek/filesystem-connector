import ctypes
from ltk.actions import Action
from logger import logger
from utils import map_locale
import time
import requests
import os
from watchdog.observers import Observer
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
                        # some logging error here
                        logger.error("Connection has timed out. Retrying..")
                        # sleep for some time then retry
                        time.sleep(timeout)
                    else:
                        raise e
        return wrapper
    return decorator

def is_hidden_file(file_path):
    # todo more robust checking for OSX files that doesn't start with '.'
    name = os.path.basename(os.path.abspath(file_path))
    return name.startswith('.') or has_hidden_attribute(file_path)

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
            # check that document is added in TMS before updating
            if self.check_remote_doc_exist(fn):
                # logger.info('Detected local content modified: {0}'.format(fn))
                # self.update_document_action(os.path.join(self.path, fn))
                # logger.info('Updating remote content: {0}'.format(fn))
                self.update_content(fn)

    def _on_created(self, event):
        # get path
        # add action
        file_path = event.src_path
        relative_path = file_path.replace(self.path, '')
        title = os.path.basename(os.path.normpath(file_path))
        if self.locale_delimiter:
            curr_locale = title.split(self.locale_delimiter)[1]
            fixed_locale = map_locale(curr_locale)
            if fixed_locale:
                self.watch_locales.add(fixed_locale)
            else:
                logger.warning('This document\'s detected locale: {0} is not supported.'.format(curr_locale))
        curr_ext = os.path.splitext(file_path)[1]
        if curr_ext in self.ignore_ext:
            logger.info("Detected a file with an extension in the ignore list, ignoring..")
            return
        # only add the document if it's not a hidden document and it's a new file and it has ok extension
        if not is_hidden_file(file_path) and self.doc_manager.is_doc_new(relative_path):
            self.add_document(self.locale, file_path, title)
        elif self.doc_manager.is_doc_modified(relative_path):
            self.update_content(relative_path)
        document_id = self.doc_manager.get_doc_by_prop('name', title)['id']
        self.watch_add_target(title, document_id)
        # logger.info('Added new document {0}'.format(title))

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
                    self.download_action(doc_id, locale, False)

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
        self.observer.schedule(self.handler, path=watch_path, recursive=True)
        self.observer.start()
        try:
            while True:
                # print 'Watching....'
                self.poll_remote()
                self.process_queue()
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
