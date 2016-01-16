from logger import logger
from watchdog.events import FileSystemEventHandler

class WatchHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def process(self, event):
        logger.info(event.event_type)

    def on_modified(self, event):
        # todo add a check  here so that it only checks for the files in local db
        self.process(event)

    # on modified
    # on moved
    # on deleted
