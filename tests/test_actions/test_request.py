from tests.test_actions import *
from ltk.actions.request_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
import time
import unittest

class TestRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.first_doc = 'sample.txt'
        for fn in self.files:
            create_txt_file(fn)
        self.add_action.add_action(['sample*.txt'], overwrite=True)
        self.doc_ids = self.add_action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.add_action, doc_id)

    def tearDown(self):
        for curr_file in self.files:
            self.rm_action.rm_action(curr_file, force=True)
        self.clean_action.clean_action(True, False, None)
        if self.action:
            self.action.close()

    def check_locales_exist(self, documents, locales):
        self.action = None
        for document in documents:
            curr_doc = self.add_action.doc_manager.get_doc_by_prop('name', document)
            return all(locale in curr_doc['locales'] for locale in locales)

    def test_request_one_locale_doc(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), self.first_doc, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist([self.first_doc], locales)

    def test_request_mult_locale_doc(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), self.first_doc, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist([self.first_doc], locales)

    def test_request_one_locale_proj(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist(self.files, locales)

    def test_request_mult_locale_proj(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist(self.files, locales)

    def test_delete_locale_doc(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), self.first_doc, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist([self.first_doc], locales)
        self.action = RequestAction(os.getcwd(), self.first_doc, None, locales, True, None, None)
        self.action.target_action()
        assert not self.check_locales_exist([self.first_doc], locales)

    def test_delete_locale_proj(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, None, None)
        self.action.target_action()
        assert self.check_locales_exist([self.first_doc], locales)
        self.action = RequestAction(os.getcwd(), None, None, locales, True, None, None)
        self.action.target_action()
        assert not self.check_locales_exist(self.files, locales)
