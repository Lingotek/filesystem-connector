from ltk.logger import logger
from watchdog.events import FileSystemEventHandler

class WatchHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    def process(self, event):
        logger.info(event.event_type)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    # on modified
    # on moved
    # on deleted
