from tests.test_actions import *
from ltk.actions.move_action import *
from ltk.actions.list_action import ListAction
from ltk.actions.rm_action import RmAction
from ltk.actions.add_action import AddAction
import unittest
import os
from io import StringIO
import sys

class TestMv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = MoveAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.list_action = ListAction(os.getcwd())
        self.added_dirs = {#dictionary of directory names to directory paths
            'full': 'full',
            'empty': 'empty',
            'hassub': 'hassub',
            'issub': 'hassub'+os.sep+'issub'
        }
        create_directory(os.path.join(os.getcwd(), self.added_dirs['hassub']))
        create_directory(os.path.join(os.getcwd(), self.added_dirs['issub']))
        create_directory(os.path.join(os.getcwd(), self.added_dirs['full']))
        create_directory(os.path.join(os.getcwd(), self.added_dirs['empty']))
        self.added_files = {#dictionary of file names to file paths
            'fileA.txt': 'fileA.txt',
            'fileB.txt': os.path.join(self.added_dirs['full'], 'fileB.txt'),
            'fileC.txt': os.path.join(self.added_dirs['hassub'], 'fileC.txt'), #untracked
            'fileD.txt': os.path.join(self.added_dirs['issub'], 'fileD.txt')
        }
        for filename in self.added_files:
            create_txt_file(os.path.join(os.getcwd(),self.added_files[filename]))
            if filename == 'fileC.txt':
                continue #don't add so we can test with an untracked file
            self.add_action.add_action([self.added_files[filename]])

    def tearDown(self):
        self.rm_action.rm_action((), all=True)
        for file in self.added_files.values():
            delete_file(file, os.getcwd())
        allCleared = False
        while not allCleared:
            allCleared = True
            for dirname in self.added_dirs:
                if os.path.isdir(os.path.join(os.getcwd(), self.added_dirs[dirname])):#stops infinite loop where delete_directory returns false if it doesn't exist
                    if not delete_directory(os.path.join(os.getcwd(), self.added_dirs[dirname])):#directory was full, catch it on the next loop after its contents have been deleted
                        allCleared = False

    def test_mv_file(self):
        self.action.mv_action([self.added_files['fileA.txt']], self.added_dirs['full'])
        self.added_files['fileA.txt'] = os.path.join(self.added_dirs['full'], 'fileA.txt')
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_mv_empty_dir(self):
        self.action.mv_action([self.added_dirs['empty']], self.added_dirs['full'])
        self.added_dirs['empty'] = os.path.join(self.added_dirs['full'], 'empty')
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_mv_dir(self):
        self.action.mv_action([self.added_dirs['full']], self.added_dirs['hassub'])
        self.added_dirs['full'] = os.path.join(self.added_dirs['hassub'], 'full')
        self.added_files['fileB.txt'] = os.path.join(self.added_dirs['full'], 'fileB.txt')
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_mv_subdir(self):
        self.action.mv_action([self.added_dirs['hassub']], self.added_dirs['full'])
        self.added_dirs['hassub'] = os.path.join(self.added_dirs['full'], 'hassub')
        self.added_dirs['issub'] = os.path.join(self.added_dirs['hassub'], 'issub')
        self.added_files['fileC.txt'] = os.path.join(self.added_dirs['hassub'], 'fileC.txt')
        self.added_files['fileD.txt'] = os.path.join(self.added_dirs['issub'], 'fileD.txt')
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_mv_file_untracked(self):
        self.action.mv_action([self.added_files['fileC.txt']], self.added_dirs['full'])
        #fileC.txt should not change location
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info, filename+" not found in "+info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_rename_file(self):
        self.action.mv_action([self.added_files['fileA.txt']], 'fileE.txt')
        self.added_files['fileA.txt'] = 'fileE.txt'
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())

    def test_rename_dir(self):
        self.action.mv_action([self.added_dirs['full']], 'filled')
        self.added_dirs['full'] = 'filled'
        self.added_files['fileB.txt'] = os.path.join(self.added_dirs['full'], 'fileB.txt')
        try:
            out = StringIO()
            sys.stdout = out
            self.list_action.list_ids(False)
            info = out.getvalue()
            for filename in self.added_files:
                if filename == 'fileC.txt':
                    assert 'fileC.txt' not in info #check just the name to cover any possible filepaths
                else:
                    assert self.added_files[filename] in info
        finally:
            sys.stdout = sys.__stdout__
        assert all(os.path.isfile(os.path.join(os.getcwd(), path)) for path in self.added_files.values())
        assert all(os.path.isdir(os.path.join(os.getcwd(), path)) for path in self.added_dirs.values())