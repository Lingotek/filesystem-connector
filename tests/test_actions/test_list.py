from tests.test_actions import *
from ltk.actions import Action
from io import StringIO
import sys
import unittest

class TestList(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = Action(os.getcwd())
        self.action.clean_action(True, False, None)

    def tearDown(self):
        self.action.clean_action(True, False, None)
        self.action.close()

    def test_list_doc(self):
        files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        file_paths = []
        for fn in files:
            file_paths.append(create_txt_file(fn))
        self.action.add_action(None, ['sample*.txt'], force=True)
        doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in doc_ids:
            assert poll_doc(self.action, doc_id)
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_ids_action()
            info = out.getvalue()
            for doc_id in doc_ids:
                assert doc_id in info
        finally:
            sys.stdout = sys.__stdout__

        for fn in files:
            self.action.rm_action(fn, force=True)
        self.action.clean_action(False, False, None)

    def test_list_no_docs(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_ids_action()
            info = out.getvalue()
            assert 'No local documents' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_workflow(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_workflow_action()
            info = out.getvalue()
            assert 'Workflows' in info
            assert 'c675bd20-0688-11e2-892e-0800200c9a66' in info
            assert 'Machine Translation' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_locale(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_locale_action()
            info = out.getvalue()
            assert 'ar_AE (Arabic, United Arab Emirates)' in info
            assert 'zh_TW (Chinese, Taiwan)' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_format(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_format_action()
            info = out.getvalue()
            assert info.startswith('Formats Lingotek supports')
            assert 'CSV' in info
            assert 'XML_OKAPI' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_filters_default(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_filter_action()
            info = out.getvalue()
            decoded_info = info
            assert 'Filters:' in info
            assert 'okf_html@wordpress.fprm' in info
            assert '0adc9a9d-ca67-4217-9525-d5a6af7ba91f' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_filters_custom(self):
        # create custom filters
        # list
        # check
        pass
