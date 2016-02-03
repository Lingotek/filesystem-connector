from ltk.actions import Action
from logger import logger
import time
from watchdog.observers import Observer
from ltk.watchhandler import WatchHandler

class WatchAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.observer = Observer()  # watchdog observer that will watch the files
        self.handler = WatchHandler()
        self.handler.on_modified = self._on_modified

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

    def watch_action(self):
        print "Watching for updates: {0}".format(self.path)
        self.observer.schedule(self.handler, path=self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                # print 'Watching...'
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
