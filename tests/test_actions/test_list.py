from tests.test_actions import *
from ltk.actions.list_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
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
        self.action = ListAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.rm_action = RmAction(os.getcwd())        

    def tearDown(self):
        self.clean_action.clean_action(True, False, None)
        self.action.close()

    def test_list_doc(self):
        files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        file_paths = []
        for fn in files:
            file_paths.append(create_txt_file(fn))
        self.add_action.add_action(['sample*.txt'], overwrite=True)
        doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in doc_ids:
            assert poll_doc(self.action, doc_id)
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_ids(False)
            info = out.getvalue()
            for doc_id in doc_ids:
                assert doc_id in info
        finally:
            sys.stdout = sys.__stdout__

        for fn in files:
            self.rm_action.rm_action(fn, force=True)
        self.clean_action.clean_action(False, False, None)

    def test_list_docs_none(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_ids(False)
            info = out.getvalue()
            assert 'No local documents' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_workflow(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_workflows()
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
            self.action.list_locales()
            info = out.getvalue()
            assert 'ar-AE (Arabic, United Arab Emirates)' in info
            assert 'zh-TW (Chinese, Taiwan)' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_format(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_formats()
            info = out.getvalue()
            assert info.startswith('Lingotek Cloud accepts content')
            assert 'CSV' in info
            assert 'XML_OKAPI' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_filters_default(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.list_filters()
            info = out.getvalue()
            decoded_info = info
            assert 'Filters:' in info
            assert 'okf_html@drupal8-subfilter.fprm' in info
            assert '0e79f34d-f27b-4a0c-880e-cd9181a5d265' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_filters_custom(self):
        # create custom filters
        # list
        # check
        pass
