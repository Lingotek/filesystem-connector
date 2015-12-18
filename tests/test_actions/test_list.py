from tests.test_actions import *
from ltk.actions import Action
from io import BytesIO
import sys
import unittest

class TestList(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())

    def tearDown(self):
        cleanup()

    def test_list_doc(self):
        # add some documents
        # list them
        # check they in list
        pass

    def test_list_workflow(self):
        try:
            out = BytesIO()
            sys.stdout = out
            self.action.list_workflow_action()
            info = out.getvalue()
            assert 'workflows' in info
            assert 'c675bd20-0688-11e2-892e-0800200c9a66' in info
            assert 'Machine Translation' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_locale(self):
        try:
            out = BytesIO()
            sys.stdout = out
            self.action.list_locale_action()
            info = out.getvalue()
            assert 'ar_AE (Arabic, United Arab Emirates)' in info
            assert 'zh_TW (Chinese, Taiwan)' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_format(self):
        try:
            out = BytesIO()
            sys.stdout = out
            self.action.list_format_action()
            info = out.getvalue()
            assert info.startswith('Formats Lingotek supports')
            assert 'CSV' in info
            assert 'XML_OKAPI' in info
        finally:
            sys.stdout = sys.__stdout__

    def test_list_filters_default(self):
        pass

    def test_list_filters_custom(self):
        # create custom filters
        # list
        # check
        pass
