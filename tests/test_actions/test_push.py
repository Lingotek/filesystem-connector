from tests.test_actions import *
from ltk.actions.push_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
from ltk.actions.request_action import RequestAction
from ltk.actions.download_action import DownloadAction
from io import StringIO
import os # Delete later
import sys
import unittest
import time

class TestPush(unittest.TestCase):
    def setUp(self):
        create_config()
        self.downloaded = []
        self.add_action = AddAction(os.getcwd())
        self.action = PushAction(self.add_action,os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.download_action = DownloadAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        os.system('ltk add sample*.txt -o') # Let the command line handle parsing the file pattern
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        # delete files added to lingotek cloud
        for curr_file in self.files:
            self.rm_action.rm_action(curr_file, force=True)

        # delete downloaded translations
        for df in self.downloaded:
            os.remove(df)

        delete_directory("es-AR")

        self.downloaded = []
        self.clean_action.clean_action(True, False, None)
        self.action.close()
        cleanup()

    def test_push_1(self):
        append_file(self.files[0])
        locales = ['es-AR']
        test_doc_id = self.action.doc_manager.get_doc_by_prop('file_name',self.files[0])['id']
        self.request_action = RequestAction(os.getcwd(), self.files[0], None, locales, False, None, None, test_doc_id)
        self.request_action.target_action()
        with open(self.files[0]) as f:
            downloaded = f.read()
        self.action.push_action()
        assert check_updated_ids(self.action, [test_doc_id]) # Poll and wait until the modification has taken effect in the cloud
        downloaded_path = self.download_action.download_action(test_doc_id, locales[0], False)
        #print("downloaded_path: "+str(downloaded_path))
        self.downloaded.append(downloaded_path)
        with open(downloaded_path, 'r') as f:
            downloaded_text = f.read()
            #print ("Downloaded_text: " + downloaded)

        assert "Texto agregado." in downloaded_text
        assert "Este es un ejemplo de archivo de texto." in downloaded_text

    def test_push_mult(self):
        append_file(self.files[0])
        append_file(self.files[1])
        locales = ['es-AR']
        test_doc_id_0 = self.action.doc_manager.get_doc_by_prop('file_name',self.files[0])['id']
        test_doc_id_1 = self.action.doc_manager.get_doc_by_prop('file_name',self.files[1])['id']
        self.request_action = RequestAction(os.getcwd(), self.files[0], None, locales, False, None, None, test_doc_id_0)
        target1 = self.request_action.target_action()
        self.request_action = RequestAction(os.getcwd(), self.files[1], None, locales, False, None, None, test_doc_id_1)
        target2 = self.request_action.target_action()
        push = self.action.push_action()
        assert check_updated_ids(self.action, [test_doc_id_0, test_doc_id_1]) # Poll and wait until the modification has taken effect on the cloud
        dl_path_0 = self.download_action.download_action(test_doc_id_0, locales[0], False)
        dl_path_1 = self.download_action.download_action(test_doc_id_1, locales[0], False)
        self.downloaded = [dl_path_0, dl_path_1]
        for path in self.downloaded:
            with open(path, 'r') as f:
                downloaded_text = f.read()
                #print("downloaded_text: "+downloaded_text)

            assert "Texto agregado." in downloaded_text
            assert "Este es un ejemplo de archivo de texto." in downloaded_text

    def test_push_none(self):
        try:
            # out = StringIO()
            # sys.stdout = out
            assert not self.action.push_action()
            # info = out.getvalue()
            # assert 'All documents up-to-date with Lingotek Cloud.' in info
        finally:
            sys.stdout = sys.__stdout__
