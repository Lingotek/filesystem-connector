from ltk.actions import Action
from logger import logger
import time
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

class WatchAction(Action):
    def __init__(self, path):
    # def __init__(self, path, remote=False):
        Action.__init__(self, path)
        self.observer = Observer()  # watchdog observer that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified
        # if remote:  # poll lingotek cloud periodically if this option enabled
        # self.remote_thread = threading.Thread(target=self.poll_remote(), args=())
        # self.remote_thread.daemon = True
        # self.remote_thread.start()

    def _on_modified(self, event):
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
            logger.info('{0} has been modified'.format(fn))
            self.update_document_action(fn)
            logger.info('PATCHing remote {0}..'.format(fn))

    def _on_create(self, event):
        # get path
        # add action
        file_path = event.src_path
        title = os.path.basename(os.path.normpath(file_path))
        self.add_document(self.locale, file_path, title)


    def poll_remote(self):
        # poll lingotek servers to check if MT finished
        # todo eventually: poll for other jobs (prefill, analyze, etc..)
        # print 'polling remote..'
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
                    logger.info('A document has finished translating! Downloading..')
                    self.download_action(doc_id, locale, False)

    def watch_action(self):
        # print self.path
        print "Watching for updates: {0}".format(self.path)
        self.observer.schedule(self.handler, path=self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                # print 'Watching..'
                self.poll_remote()
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
