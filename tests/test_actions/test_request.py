from tests.test_actions import *
from ltk.actions import Action

import unittest

class TestRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = Action(os.getcwd())
        self.action.clean_action(True, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.first_doc = 'sample.txt'
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, ['sample*.txt'], force=True)
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        for curr_file in self.files:
            self.action.rm_action(curr_file, force=True)
        self.action.clean_action(True, False, None)
        self.action.close()

    def check_locales_exist(self, documents, locales):
        for document in documents:
            curr_doc = self.action.doc_manager.get_doc_by_prop('name', document)
            return all(locale in curr_doc['locales'] for locale in locales)

    def test_request_one_locale_doc(self):
        locales = ['ja_JP']
        self.action.target_action(self.first_doc, locales, False, None, None)
        assert self.check_locales_exist([self.first_doc], locales)

    def test_request_mult_locale_doc(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action.target_action(self.first_doc, locales, False, None, None)
        assert self.check_locales_exist([self.first_doc], locales)

    def test_request_one_locale_proj(self):
        locales = ['ja_JP']
        self.action.target_action(None, locales, False, None, None)
        assert self.check_locales_exist(self.files, locales)

    def test_request_mult_locale_proj(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action.target_action(None, locales, False, None, None)
        assert self.check_locales_exist(self.files, locales)

    def test_delete_locale_doc(self):
        locales = ['ja_JP']
        self.action.target_action(self.first_doc, locales, False, None, None)
        assert self.check_locales_exist([self.first_doc], locales)
        self.action.target_action(self.first_doc, locales, True, None, None)
        assert not self.check_locales_exist([self.first_doc], locales)

    def test_delete_locale_proj(self):
        locales = ['ja_JP']
        self.action.target_action(None, locales, False, None, None)
        assert self.check_locales_exist([self.first_doc], locales)
        self.action.target_action(None, locales, True, None, None)
        assert not self.check_locales_exist(self.files, locales)
