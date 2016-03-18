from tests.test_actions import *
from ltk.actions import Action
from io import BytesIO

import sys
import unittest

class TestRequest(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.first_doc = 'sample.txt'
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, 'sample*.txt')
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        cleanup()

    def check_locales_exist(self, documents, locales):
        for document in documents:
            try:
                out = BytesIO()
                sys.stdout = out
                self.action.status_action(True, document)
                status = out.getvalue()
                return all(locale in status for locale in locales)
            finally:
                sys.stdout = sys.__stdout__

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
        assert self.check_locales_exist(self.first_doc, locales)
        self.action.target_action(self.first_doc, 'ja_JP', True, None, None)
        assert not self.check_locales_exist(self.first_doc, locales)

    def test_delete_locale_proj(self):
        locales = ['ja_JP']
        self.action.target_action(None, locales, False, None, None)
        assert self.check_locales_exist(self.first_doc, locales)
        self.action.target_action(None, 'ja_JP', True, None, None)
        assert not self.check_locales_exist(self.files, locales)
