from tests.test_actions import *
from ltk.watch import WatchAction
from threading import Thread
import unittest
import os

# @unittest.skip("skip testing watch for now")
class TestWatch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = WatchAction(os.getcwd(), 1)
        self.action.clean_action(False, False, None)
        # self.action.open()
        self.downloaded = []
        self.files = []
        # todo current problem: watchdog does not seem to detect changes in daemon
        # but not daemonizing watch causes tests to hang..
        watch_thread = Thread(target=self.action.watch_action, args=('.', (), None))
        watch_thread.daemon = True
        watch_thread.start()

    def tearDown(self):
        for fn in self.files:
            self.action.rm_action(fn, force=True)
        self.action.clean_action(False, False, None)
        for fn in self.downloaded:
            os.remove(fn)

    def test_watch_new_file(self):
        file_name = "new_file.txt"
        self.files.append(file_name)
        if os.path.exists(file_name):
            delete_file(file_name)
        create_txt_file(file_name)
        # # check if watch detected file and added it to db
        doc = None
        time_passed = 0
        while doc is None and time_passed < 10:
            doc = self.action.doc_manager.get_doc_by_prop('file_name', file_name)
            time.sleep(1)
            time_passed += 1
        assert doc
        assert poll_doc(self.action, doc['id'])

    def test_watch_update(self):
        file_name = "new_file.txt"
        self.files.append(file_name)
        if os.path.exists(file_name):
            delete_file(file_name)
        create_txt_file(file_name)
        doc = None
        time_passed = 0
        while doc is None and time_passed < 10:
            doc = self.action.doc_manager.get_doc_by_prop('file_name', file_name)
            time.sleep(1)
            time_passed += 1
        assert doc
        assert poll_doc(self.action, doc['id'])
        append_file(file_name)
        check_updated_ids(self.action, [doc['id']])
        downloaded_path = self.action.download_action(doc['id'], None, False)
        self.downloaded.append(downloaded_path)
        with open(downloaded_path, 'r') as f:
            downloaded = f.read()
        assert "Appended text. " in downloaded


# todo make download dir for watch, then just delete folder in teardown or teardownclass
