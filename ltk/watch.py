from ltk.actions import Action
from logger import logger
import time
import os
from watchdog.observers import Observer
from ltk.watchhandler import WatchHandler

import threading

class WatchAction(Action):
    def __init__(self, path, remote=False):
        Action.__init__(self, path)
        self.observer = Observer()  # watchdog observer that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified
        if remote:  # poll lingotek cloud periodically if this option enabled
            self.remote_thread = threading.Thread()
            self.remote_thread.daemon = True
            self.remote_thread.start()

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

    def poll_remote(self):
        # poll lingotek servers for any updates to existing files
        # or, poll for jobs that take a while (MT, prefill, analyze, etc..)
        
        pass

    def watch_action(self):
        # print self.path
        self.observer.schedule(self.handler, path=self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                # print 'Watching..'
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
