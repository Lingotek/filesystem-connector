from tests.test_actions import *
from ltk.watch import WatchAction
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
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
        self.action = WatchAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.clean_action.clean_action(False, False, None)
        # self.action.open()
        self.downloaded = []
        self.files = []
        self.dir_name = "dir1"
        create_directory(self.dir_name)
        self.add_action.add_action([self.dir_name], force=True)
        # todo current problem: watchdog does not seem to detect changes in daemon
        # but not daemonizing watch causes tests to hang..
        watch_thread = Thread(target=self.action.watch_action, args=('.', (), None))
        watch_thread.daemon = True
        watch_thread.start()

    def tearDown(self):
        #delete files
        for fn in self.files:
            self.rm_action.rm_action(fn, force=True)
        self.clean_action.clean_action(False, False, None)
        #delete downloads
        for fn in self.downloaded:
            os.remove(fn)
        #delete directory
        delete_directory(self.dir_name)

    def test_watch_new_file(self):
        file_name = "test_watch_sample_0.txt"
        self.files.append(self.dir_name+"/"+file_name)
        if os.path.exists(self.dir_name+file_name):
            delete_file(file_name)
        create_txt_file(file_name, self.dir_name)

        # check if watch detected file and added it to db
        doc = None
        time_passed = 0
        while doc is None and time_passed < 10:
            doc = self.action.doc_manager.get_doc_by_prop('name', file_name)
            time.sleep(1)
            time_passed += 1
        assert doc
        assert poll_doc(self.action, doc['id'])

    def test_watch_update(self):
        file_name = "test_watch_sample_1.txt"
        self.files.append(self.dir_name+'/'+file_name)
        if os.path.exists(self.dir_name+file_name):
            delete_file(file_name)
        create_txt_file(file_name, self.dir_name)

        doc = None
        time_passed = 0
        while doc is None and time_passed < 10:
            doc = self.action.doc_manager.get_doc_by_prop('name', file_name)
            time.sleep(1)
            time_passed += 1
        assert doc
        assert poll_doc(self.action, doc['id'])

        append_file(file_name, self.dir_name)
        #assert check_updated_ids(self.action, [doc['id']])
        with open(self.dir_name+'/'+file_name, 'r') as f:
            downloaded = f.read()
        assert "Appended text." in downloaded


# todo make download dir for watch, then just delete folder in teardown or teardownclass
