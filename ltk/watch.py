from ltk.actions import Action
from logger import logger
import time
import requests
import os
from watchdog.observers import Observer
from ltk.watchhandler import WatchHandler

import threading

# class WatchThread:
#     def __init__(self, interval=5):
#         self.interval = interval
#
#         self.thread = threading.Thread(target=self.run, args=())
#         self.thread.daemon = True
#         self.thread.start()
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


class WatchAction(Action):
    def __init__(self, path):
    # def __init__(self, path, remote=False):
        Action.__init__(self, path)
        self.observer = Observer()  # watchdog observer that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified
        self.handler.on_created = self._on_create
        # if remote:  # poll lingotek cloud periodically if this option enabled
        # self.remote_thread = threading.Thread(target=self.poll_remote(), args=())
        # self.remote_thread.daemon = True
        # self.remote_thread.start()

    def check_remote_doc_exist(self, fn):
        """ check if a document exists remotely """
        entry = self.doc_manager.get_doc_by_prop('file_name', fn)
        doc_id = entry['id']
        response = self.api.get_document(doc_id)
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
                logger.info('Detected local content modified: {0}'.format(fn))
                self.update_document_action(fn)
                logger.info('Updating remote content: {0}'.format(fn))

    def _on_create(self, event):
        # get path
        # add action
        file_path = event.src_path
        title = os.path.basename(os.path.normpath(file_path))
        self.add_document(self.locale, file_path, title)
        # logger.info('Added new document {0}'.format(title))

    @retry(logger)
    def poll_remote(self):
        """ poll lingotek servers to check if MT finished """
        # todo eventually: poll for other jobs (prefill, analyze, etc...)
        # print 'polling remote...'
        documents = self.doc_manager.get_all_entries()
        for doc in documents:
            doc_id = doc['id']
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

    def watch_action(self, watch_path):
        # print self.path
        if not watch_path and not self.watch_dir:
            watch_path = self.path
        elif watch_path:
            watch_path = os.path.join(self.path, watch_path)
        else:
            watch_path = self.watch_dir
        print "Watching for updates in: {0}".format(watch_path)
        self.observer.schedule(self.handler, path=watch_path, recursive=True)
        self.observer.start()
        try:
            while True:
                # print 'Watching....'
                self.poll_remote()
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
