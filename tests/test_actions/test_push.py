from tests.test_actions import *
from ltk.actions import Action
from io import StringIO
import sys
import unittest
import time

class TestPush(unittest.TestCase):
    def setUp(self):
        create_config()
        self.downloaded = []
        self.action = Action(os.getcwd())
        self.action.clean_action(True, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, ['sample*.txt'], force=True)
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        for curr_file in self.files:
            self.action.rm_action(curr_file, force=True)
        for df in self.downloaded:
            os.remove(df)
        self.action.clean_action(True, False, None)
        self.action.close()
        cleanup()

    def test_push_1(self):
        append_file(self.files[0])
        locales = ['ja_JP']
        test_doc_id = self.action.doc_manager.get_doc_by_prop('file_name',self.files[0])['id']
        self.action.target_action(None, locales, False, None, None, test_doc_id)
        with open(self.files[0]) as f:
            downloaded = f.read()
        self.action.push_action()
        assert check_updated_ids(self.action, [test_doc_id]) # Poll and wait until the modification has taken effect on the cloud
        downloaded_path = self.action.download_action(test_doc_id, None, False)
        self.downloaded.append(downloaded_path)
        with open(downloaded_path, 'r') as f:
            downloaded = f.read()
        print (downloaded)
        assert "Appended text. " in downloaded
        assert "This is a sample text file. " in downloaded

    def test_push_mult(self):
        append_file(self.files[0])
        append_file(self.files[1])
        doc_id0 = self.action.doc_manager.get_doc_by_prop('file_name',self.files[0])['id']
        doc_id1 = self.action.doc_manager.get_doc_by_prop('file_name',self.files[1])['id']
        locales = ['ja_JP']
        self.action.target_action(None, locales, False, None, None, doc_id0)
        self.action.target_action(None, locales, False, None, None, doc_id1)
        self.action.push_action()
        assert check_updated_ids(self.action, [doc_id0, doc_id1]) # Poll and wait until the modification has taken effect on the cloud
        dl_path = self.action.download_action(doc_id0, None, False)
        dl_path1 = self.action.download_action(doc_id1, None, False)
        self.downloaded = [dl_path, dl_path1]        
        for path in self.downloaded:
            with open(path, 'r') as f:
                downloaded = f.read()
            print (downloaded)
            assert "Appended text. " in downloaded
            assert "This is a sample text file. " in downloaded

    def test_push_none(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.push_action()
            info = out.getvalue()
            assert 'All documents up-to-date with Lingotek Cloud.' in info
        finally:
            sys.stdout = sys.__stdout__
