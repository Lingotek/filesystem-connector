from ltk import exceptions
from ltk.actions.status_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
from ltk.actions.request_action import RequestAction
import unittest
from io import StringIO
import sys
from tests.test_actions import *
import logging


class TestStatusAction(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = StatusAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.file_name = 'sample.txt'
        self.file_path = create_txt_file(self.file_name)
        self.add_action.add_action([self.file_name], overwrite=True)
        self.doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, self.doc_id)
        self.targets = ['ja-JP', 'de-DE']

    def tearDown(self):
        # remove the created file
        self.rm_action.rm_action(self.file_name, remote=True, force=True)
        self.clean_action.clean_action(True, False, None)
        self.action.close()
        cleanup()

    def test_status(self):
        # see that there is a status
        try:
            out = StringIO()
            sys.stdout = out
            self.action.get_status(doc_name=self.file_name)
            status = out.getvalue()
            assert status.startswith('Status of {0}'.format(self.file_name))
        finally:
            sys.stdout = sys.__stdout__

    def test_status_detailed(self):
        # see that there are targets
        # request translations
        self.request_action = RequestAction(os.getcwd(), None, self.file_name, self.targets, False, False, None, None)
        self.request_action.target_action()
        try:
            out = StringIO()
            sys.stdout = out
            self.action.get_status(detailed=True, doc_name=self.file_name)
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name) in status
            for target in self.targets:
                assert 'Locale: {0}'.format(target) in status
        finally:
            sys.stdout = sys.__stdout__

    def test_status_no_target(self):
        # when no targets have been added
        try:
            out = StringIO()
            sys.stdout = out
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self.action.get_status(detailed=True)
            info = out.getvalue()
            assert 'No translations exist for document {0}'.format(self.file_name) in info
            logger.removeHandler(handler)
        finally:
            sys.stdout = sys.__stdout__
    
    def test_status_all(self):
        #add a second file
        self.file_name2 = 'sample2.txt'
        self.file_path2 = create_txt_file(self.file_name2)
        self.add_action.add_action([self.file_name2], overwrite=True)
        self.doc_id2 = self.action.doc_manager.get_doc_ids()[1]
        assert poll_doc(self.action, self.doc_id2)
        #remove second file from local tracking
        self.clean_action.clean_action(False, False, [self.file_name2])

        try:
            out = StringIO()
            sys.stdout = out
            #test that a normal status call doesn't see the new file
            self.action.get_status()
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name) in status
            assert 'Status of {0}'.format(self.file_name2) not in status
            #test that a status all call sees both files
            #reset output capture
            out = StringIO()
            sys.stdout = out
            self.action.get_status(all=True)
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name) in status
            assert 'Status of {0}'.format(self.file_name2) in status
        finally:
            sys.stdout = sys.__stdout__

        #remove second file
        self.rm_action.rm_action(self.doc_id2, id=True, remote=True)
        delete_file(self.file_path2)

    def test_status_name(self):
        #add a second file in a directory
        self.dir_name = 'folder'
        self.dir_path = os.path.join(os.getcwd(), self.dir_name)
        create_directory(self.dir_path)
        self.file_name2 = self.dir_name+os.sep+'sample2.txt'
        self.file_name2_short = 'sample2.txt'
        self.file_path2 = create_txt_file(self.file_name2)
        self.add_action.add_action([self.file_name2], overwrite=True)
        self.doc_id2 = self.action.doc_manager.get_doc_ids()[1]
        assert poll_doc(self.action, self.doc_id2)

        try:
            out = StringIO()
            sys.stdout = out
            #test that where the name is the same as the path
            self.action.get_status(doc_name = self.file_name)
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name) in status
            assert 'Status of {0}'.format(self.file_name2_short) not in status
            #test where the name is different than the path
            #reset output capture
            out = StringIO()
            sys.stdout = out
            self.action.get_status(doc_name = self.file_name2_short)
            status = out.getvalue()
            assert 'Status of {0}'.format(self.file_name2_short) in status
            assert 'Status of {0}'.format(self.file_name) not in status
        finally:
            sys.stdout = sys.__stdout__

        #remove second file
        self.rm_action.rm_action(self.file_name2, remote=True, force=True)
        delete_directory(self.dir_path)
