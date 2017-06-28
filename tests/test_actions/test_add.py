from tests.test_actions import *
import sys
from ltk.actions.add_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.rm_action import RmAction
import os
import unittest

class TestAdd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = AddAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.added_files = []
        self.added_directories = []

    def tearDown(self):
        self.rm_action = RmAction(os.getcwd())
        for fn in self.added_files:
            self.rm_action.rm_action(fn, force=True)

        for d in self.added_directories:
            self.rm_action.rm_action(d, force=True)
            delete_directory(d)

        self.clean_action.clean_action(False, False, None)
        self.rm_action.close()
        self.clean_action.close()
        self.action.close()

    def test_add_db(self):
        # check that document is added to db
        file_name = 'sample.txt'
        self.added_files.append(file_name)
        create_txt_file(file_name)
        self.action.add_action([file_name], force=True)
        doc_id = self.action.doc_manager.get_doc_ids()[0]
        poll_doc(self.action, doc_id)

        assert self.action.doc_manager.get_doc_by_prop('name', file_name)
        delete_file(file_name)

    def test_add_remote(self):
        # check that document is added to Lingotek
        file_name = 'sample.txt'
        self.added_files.append(file_name)
        create_txt_file(file_name)
        self.action.add_action([file_name], force=True)
        doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, doc_id)

    def test_add_pattern_db(self):
        # test that adding with a pattern gets all expected matches in local db
        files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.added_files = files
        for fn in files:
            create_txt_file(fn)
        # self.action.add_action(['sample*.txt'])
        os.system('ltk add sample*.txt') # Let the command line handle parsing the file pattern
        for fn in files:
            doc = self.action.doc_manager.get_doc_by_prop('name', fn)
            assert doc
            assert poll_doc(self.action, doc['id'])

    def test_add_pattern_remote(self):
        # test that adding with a pattern gets all expected matches in Lingotek
        files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.added_files = files
        for fn in files:
            create_txt_file(fn)
        # self.action.add_action(['sample*.txt'])
        os.system('ltk add sample*.txt') # Let the command line handle parsing the file pattern
        doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in doc_ids:
            assert poll_doc(self.action, doc_id)

    ''' Test that a directory, and documents inside directory, are added to the db '''
    def test_add_directory(self):

        #test add an empty directory
        directory = 'test_add_empty_directory'
        dir_path = os.path.join(os.getcwd(), directory)
        self.added_directories.append(dir_path)
        create_directory(dir_path)
        self.action.add_action([dir_path], force=True)

        assert self.action._is_folder_added(dir_path)
        delete_directory(dir_path)

        #test add a directory with documents inside
        directory = 'test_add_full_directory'
        dir_path = os.path.join(os.getcwd(), directory)
        self.added_directories.append(dir_path)
        create_directory(dir_path)

        files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.added_files = files
        for fn in files:
            create_txt_file(fn, dir_path)

        self.action.add_action([dir_path], force=True)

        assert self.action._is_folder_added(dir_path)
        for fn in files:
            assert self.action.doc_manager.get_doc_by_prop('name', fn)

        #delete the files and directories created
        for fn in files:
            delete_file(fn, dir_path)

        delete_directory(dir_path)

    ''' Test adding a directory with a document inside gets added to Lingotek '''
    def test_add_remote_directory(self):

        directory = 'test_add_full_directory'
        dir_path = os.path.join(os.getcwd(), directory)
        file_name = 'file_inside_directory.txt'
        self.added_directories.append(dir_path)
        create_directory(dir_path)
        self.added_files.append(file_name)
        create_txt_file(file_name, dir_path)
        self.action.add_action([dir_path], force=True)

        doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, doc_id)

    # todo test all those other args
