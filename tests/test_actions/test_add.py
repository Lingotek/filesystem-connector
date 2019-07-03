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
            self.rm_action.rm_action(fn, remote=True, force=True)

        not_empty = True
        while not_empty:
            not_empty = False
            for d in self.added_directories:
                if os.path.exists(d) and os.path.isdir(d):
                    if len(os.listdir(d)):
                        self.rm_action.rm_action(d, remote=True, force=True)
                        not_empty = True
                    else:
                        self.rm_action.rm_action(d, remote=True, force=True)
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
        self.action.add_action([file_name])
        doc_id = self.action.doc_manager.get_doc_ids()[0]
        poll_doc(self.action, doc_id)

        assert self.action.doc_manager.get_doc_by_prop('name', file_name)

    def test_add_remote(self):
        # check that document is added to Lingotek
        file_name = 'sample.txt'
        self.added_files.append(file_name)
        create_txt_file(file_name)
        self.action.add_action([file_name])
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
        self.action.add_action([dir_path])

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

        self.action.add_action([dir_path])
        assert self.action._is_folder_added(dir_path)
        for fn in files:
            assert self.action.doc_manager.get_doc_by_prop('name', fn)

    ''' Test adding a directory with a document inside gets added to Lingotek '''
    def test_add_remote_directory(self):

        directory = 'test_add_full_directory'
        dir_path = os.path.join(os.getcwd(), directory)
        file_name = 'file_inside_directory.txt'
        self.added_directories.append(dir_path)
        create_directory(dir_path)
        self.added_files.append(file_name)
        create_txt_file(file_name, dir_path)
        self.action.add_action([dir_path])

        doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, doc_id)

    def test_add_target_folders(self):
        #create and add files
        directory1 = os.path.join(os.getcwd(), 'test_dir_1')
        self.added_directories.append(directory1)
        create_directory(directory1)
        directory2 = os.path.join(os.getcwd(), 'test_dir_2')
        self.added_directories.append(directory2)
        create_directory(directory2)
        directory3 = os.path.join(os.getcwd(), 'test_dir_1/test_dir_3')
        self.added_directories.append(directory3)
        create_directory(directory3)
        file1 = 'testfile1.txt'#root to root
        file2 = 'testfile2.txt'#root to sub (dir1)
        file3 = 'test_dir_1/test_dir_3/testfile3.txt'#sub to root
        file4 = 'test_dir_2/testfile4.txt'#sub to sub (dir2 to dir3)
        file5 = 'test_dir_2/testfile5.txt'#sub to same
        file6 = 'testfile6.txt'#root to none
        file7 = 'test_dir_1/testfile7.txt'#sub to none
        self.added_files.append(file1)
        create_txt_file(file1)
        self.added_files.append(file2)
        create_txt_file(file2)
        self.added_files.append(file3)
        create_txt_file(file3)
        self.added_files.append(file4)
        create_txt_file(file4)
        self.added_files.append(file5)
        create_txt_file(file5)
        self.added_files.append(file6)
        create_txt_file(file6)
        self.added_files.append(file7)
        create_txt_file(file7)
        os.system('ltk add '+file1+' -D .')
        os.system('ltk add '+file2+' -D test_dir_1')
        os.system('ltk add '+file3+' -D .')
        os.system('ltk add '+file4+' -D test_dir_1/test_dir_3')
        os.system('ltk add '+file5+' -D test_dir_2')
        os.system('ltk add '+file6)
        os.system('ltk add '+file7)

        #check that they were added correctly
        doc1 = self.action.doc_manager.get_doc_by_prop('file_name', file1)
        assert doc1
        assert doc1['download_folder'] == '.'
        doc2 = self.action.doc_manager.get_doc_by_prop('file_name', file2)
        assert doc2
        assert doc2['download_folder'] == 'test_dir_1'
        doc3 = self.action.doc_manager.get_doc_by_prop('file_name', file3)
        assert doc3
        assert doc3['download_folder'] == '.'
        doc4 = self.action.doc_manager.get_doc_by_prop('file_name', file4)
        assert doc4
        assert doc4['download_folder'] == 'test_dir_1/test_dir_3'
        doc5 = self.action.doc_manager.get_doc_by_prop('file_name', file5)
        assert doc5
        assert doc5['download_folder'] == 'test_dir_2'
        doc6 = self.action.doc_manager.get_doc_by_prop('file_name', file6)
        assert doc6
        assert doc6['download_folder'] == ''
        doc7 = self.action.doc_manager.get_doc_by_prop('file_name', file7)
        assert doc7
        assert doc7['download_folder'] == ''

    ''' Test adding a directory with the -d flag so it only adds the directory and not the files '''
    def test_add_directory_only(self):
        #test add an empty directory
        directory = 'test_add_empty_directory'
        dir_path = os.path.join(os.getcwd(), directory)
        self.added_directories.append(dir_path)
        create_directory(dir_path)
        self.action.add_action([dir_path])

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

        self.action.add_action([dir_path], directory=True)

        assert self.action._is_folder_added(dir_path)
        for fn in files:
            assert not self.action.doc_manager.get_doc_by_prop('name', fn)

        #delete the files here because they are untracked and won't be picked up in teardown
        for fn in files:
            delete_file(fn, dir_path)
        self.added_files.clear()