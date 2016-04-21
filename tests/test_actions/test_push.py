from tests.test_actions import *
from ltk.actions import Action
import unittest
import time

class TestPush(unittest.TestCase):
    def setUp(self):
        create_config()
        self.downloaded = []
        self.action = Action(os.getcwd())
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, ['sample*.txt'])
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        for curr_file in self.files:
            self.action.rm_action(curr_file, True)
        for df in self.downloaded:
            os.remove(df)
        self.action.clean_action(False, False, None)
        cleanup()

    def test_push_1(self):
        append_file(self.files[0])
        self.action.push_action()
        # currently sleep for some arbitrary time while document updates in Lingotek
        # replace when api call or some way to check if update is finished is available
        time.sleep(30)
        downloaded_path = self.action.download_action(self.doc_ids[0], None, False)
        self.downloaded.append(downloaded_path)
        with open(downloaded_path, 'r') as f:
            downloaded = f.read()
        assert "Appended text. " in downloaded
        assert "This is a sample text file. " in downloaded

    def test_push_mult(self):
        append_file(self.files[0])
        append_file(self.files[1])
        self.action.push_action()
        time.sleep(45)  # see test_push_1 comment
        dl_path = self.action.download_action(self.doc_ids[0], None, False)
        dl_path1 = self.action.download_action(self.doc_ids[1], None, False)
        self.downloaded = [dl_path, dl_path1]
        for path in self.downloaded:
            with open(path, 'r') as f:
                downloaded = f.read()
            assert "Appended text. " in downloaded
            assert "This is a sample text file. " in downloaded

    def test_push_none(self):
        from io import BytesIO
        import sys

        try:
            out = BytesIO()
            sys.stdout = out
            self.action.push_action()
            info = out.getvalue()
            assert 'All documents up-to-date with Lingotek Cloud.' in info
        finally:
            sys.stdout = sys.__stdout__
