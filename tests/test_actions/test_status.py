from ltk import actions, exceptions
import unittest
from io import StringIO
import sys
from tests.test_actions import *
import logging


class TestStatusAction(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = actions.Action(os.getcwd())
        self.action.clean_action(True, False, None)
        self.file_name = 'sample.txt'
        self.file_path = create_txt_file(self.file_name)
        self.action.add_action(None, [self.file_name], force=True)
        self.doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, self.doc_id)
        self.targets = ['ja-JP', 'de-DE']

    def tearDown(self):
        # remove the created file
        self.action.rm_action(self.file_name, force=False)
        self.action.clean_action(True, False, None)
        self.action.close()
        cleanup()

    def test_status(self):
        # see that there is a status
        try:
            out = StringIO()
            sys.stdout = out
            self.action.status_action(doc_name=self.file_name)
            status = out.getvalue()
            assert status.startswith('Status of {0}'.format(self.file_name))
        finally:
            sys.stdout = sys.__stdout__

    def test_status_detailed(self):
        # see that there are targets
        # request translations
        self.action.target_action(self.file_name, self.targets, False, None, None)
        try:
            out = StringIO()
            sys.stdout = out
            self.action.status_action(detailed=True, doc_name=self.file_name)
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name) in status
            for target in self.targets:
                assert 'locale: {0}'.format(target) in status
        finally:
            sys.stdout = sys.__stdout__

    # def test_status_no_target(self):
    #     # when no targets have been added
    #     try:
    #         from ltk.logger import logger
    #         logger.setLevel(logging.DEBUG)
    #         out = StringIO()
    #         ch = logging.StreamHandler(out)
    #         ch.setLevel(logging.DEBUG)
    #         logger.addHandler(ch)
    #         self.action.status_action(detailed=True, doc_name=self.file_name)
    #         status = out.getvalue()
    #         # todo this test fails because the error comes from logger not stdout
    #         assert 'ERROR: No translations exist for document {0}'.format(self.doc_id) in status
    #     finally:
    #         sys.stdout = sys.__stdout__
