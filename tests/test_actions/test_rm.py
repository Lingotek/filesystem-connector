from ltk.actions.rm_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from tests.test_actions import *
import unittest

class TestRm(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = RmAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.file_name1 = 'sample.txt'
        self.file_path1 = create_txt_file(self.file_name1)
        self.add_action.add_action([self.file_name1], overwrite=True)
        self.doc_id1 = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, self.doc_id1)
        self.file_name2 = 'othersample.txt'
        self.file_path2 = create_txt_file(self.file_name2)
        self.add_action.add_action([self.file_name2], overwrite=True)
        self.doc_id2 = self.action.doc_manager.get_doc_ids()[1]
        assert poll_doc(self.action, self.doc_id2)
        self.dir_name = 'folder'
        self.dir_path = os.path.join(os.getcwd(),self.dir_name)
        create_directory(self.dir_path)
        self.file_name3 = 'folder'+os.sep+'nestedfile.txt'
        self.file_name3_short = 'nestedfile.txt'
        self.file_path3 = create_txt_file(self.file_name3)
        self.add_action.add_action([self.dir_name], overwrite=True)
        self.doc_id3 = self.action.doc_manager.get_doc_ids()[2]
        assert poll_doc(self.action, self.doc_id3)


    def tearDown(self):
        self.clean_action.clean_action(True, False, None)
        self.clean_action.close()
        self.action.close()
        #delete file in folder manually to be sure the folder is empty so it can be deleted in cleanup
        if(os.path.isfile(self.file_path3)):
            delete_file(self.file_path3)
        if(os.path.isfile(self.file_path2)):
            delete_file(self.file_path2)
        if(os.path.isfile(self.file_path1)):
            delete_file(self.file_path1)
        if(os.path.isdir(self.dir_path)):
            delete_directory(self.dir_path)
        cleanup()

    def test_rm(self):
        self.action.rm_action([self.file_name1], remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.file_name2], remote=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.dir_name], remote=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

    def test_rm_force(self):
        self.action.rm_action([self.file_name1], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        assert not os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)
        self.action.rm_action([self.file_name2], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        assert not os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)
        self.action.rm_action([self.dir_name], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path) #only documents should be deleted, folders should just be removed from tracking

    #rm directory
    def test_rm_directory(self):
        self.action.rm_action([self.dir_name], remote=True, directory=True)
        assert poll_doc(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.file_name1], remote=True)#cleanup, does not need to be tested in this unit test
        self.action.rm_action([self.file_name2], remote=True)#cleanup, does not need to be tested in this unit test
        self.action.rm_action([self.file_name3], remote=True)#cleanup, does not need to be tested in this unit test
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

    #rm by id
    def test_rm_id(self):
        self.action.rm_action([self.doc_id1], id=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.doc_id2], id=True, remote=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.doc_id3], id=True, remote=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

    #rm by name
    def test_rm_name(self):
        self.action.rm_action([self.file_name1], name=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.file_name2], name=True, remote=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        self.action.rm_action([self.file_name3_short], name=True, remote=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

    #rm all
    def test_rm_all(self):
        self.action.rm_action([], all=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

    #rm local
    def test_rm_local(self):
        self.action.rm_action([], remote=True, local=True)
        assert poll_doc(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name)
        assert not os.path.isfile(self.file_path1)
        assert not os.path.isfile(self.file_path2)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path)

        #clean up files remotely
        self.action.rm_action([self.doc_id1, self.doc_id2, self.doc_id3], id=True, remote=True)

    #test cancelling