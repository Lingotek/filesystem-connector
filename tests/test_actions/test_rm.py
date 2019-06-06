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
        self.doc_id1 = self.action.doc_manager.get_doc_by_prop('name', self.file_name1)['id']
        assert poll_doc(self.action, self.doc_id1)
        self.dir_name2 = 'folderA'
        self.dir_path2 = os.path.join(os.getcwd(),self.dir_name2)
        create_directory(self.dir_path2)
        self.file_name2_short = 'otherfile.txt'
        self.file_name2 = os.path.join(self.dir_name2, self.file_name2_short)
        self.file_path2 = create_txt_file(self.file_name2)
        self.add_action.add_action([self.dir_name2], overwrite=True)
        self.doc_id2 = self.action.doc_manager.get_doc_by_prop('name', self.file_name2_short)['id']
        assert poll_doc(self.action, self.doc_id2)
        self.dir_name3 = 'folderB'
        self.dir_path3 = os.path.join(os.getcwd(),self.dir_name3)
        create_directory(self.dir_path3)
        self.file_name3_short = 'nestedfile.txt'
        self.file_name3 = os.path.join(self.dir_name3, self.file_name3_short)
        self.file_path3 = create_txt_file(self.file_name3)
        self.add_action.add_action([self.dir_name3], overwrite=True)
        self.doc_id3 = self.action.doc_manager.get_doc_by_prop('name', self.file_name3_short)['id']
        assert poll_doc(self.action, self.doc_id3)


    def tearDown(self):
        self.clean_action.clean_action(True, False, None)
        self.clean_action.close()
        self.action.close()
        #delete file in folder manually to be sure the folder is empty so it can be deleted in cleanup
        if(os.path.isfile(self.file_path1)):
            delete_file(self.file_path1)
        if(os.path.isfile(self.file_path2)):
            delete_file(self.file_path2)
        if(os.path.isfile(self.file_path3)):
            delete_file(self.file_path3)
        if(os.path.isdir(self.dir_path2)):
            delete_directory(self.dir_path2)
        if(os.path.isdir(self.dir_path3)):
            delete_directory(self.dir_path3)
        #delete files remotely with the API in case the test failed
        self.action.api.document_delete(self.doc_id1)
        self.action.api.document_delete(self.doc_id2)
        self.action.api.document_delete(self.doc_id3)

        self.clean_action.clean_action(False, True, None)
        cleanup()

    def test_cancel(self):
        #single file in root
        self.action.rm_action([self.file_name1])
        assert poll_rm(self.action, self.doc_id1, cancelled=True)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)

        #single file in directory
        self.action.rm_action([self.file_name2])
        assert poll_rm(self.action, self.doc_id2, cancelled=True)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)

        #directory with file
        self.action.rm_action([self.dir_name3])
        assert poll_rm(self.action, self.doc_id3, cancelled=True)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)

        #check that files weren't locally deleted
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_rm(self):
        #single file in root
        self.action.rm_action([self.file_name1], remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)

        #single file in directory
        self.action.rm_action([self.file_name2], remote=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)

        #directory with file
        self.action.rm_action([self.dir_name3], remote=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)

        #check that files weren't locally deleted
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)


    def test_cancel_force(self):
        #single file in root
        self.action.rm_action([self.file_name1], force=True)
        assert poll_rm(self.action, self.doc_id1, cancelled=True)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

        #single file in directory
        self.action.rm_action([self.file_name2], force=True)
        assert poll_rm(self.action, self.doc_id2, cancelled=True)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

        #directory with file
        self.action.rm_action([self.dir_name3], force=True)
        assert poll_rm(self.action, self.doc_id3, cancelled=True)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2) #only documents should be deleted, folders should just be removed from tracking
        assert os.path.isdir(self.dir_path3) #only documents should be deleted, folders should just be removed from tracking

    def test_rm_force(self):
        #single file in root
        self.action.rm_action([self.file_name1], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

        #single file in directory
        self.action.rm_action([self.file_name2], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

        #directory with file
        self.action.rm_action([self.dir_name3], remote=True, force=True)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2) #only documents should be deleted, folders should just be removed from tracking
        assert os.path.isdir(self.dir_path3) #only documents should be deleted, folders should just be removed from tracking

    #no need for a test_cancel_directory because the -d flag can't do anything to the files in TMS, meaning rm -d and rm -rd are the same
    def test_rm_directory(self):
        self.action.rm_action([self.dir_name3], remote=True, directory=True)
        assert poll_doc(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_cancel_id(self):
        self.action.rm_action([self.doc_id1], id=True)
        assert poll_rm(self.action, self.doc_id1, cancelled=True)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)
    
    def test_rm_id(self):
        self.action.rm_action([self.doc_id1], id=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_doc(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_cancel_name(self):
        self.action.rm_action([self.file_name2_short], name=True)
        assert poll_doc(self.action, self.doc_id1)
        assert poll_rm(self.action, self.doc_id2, cancelled=True)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_rm_name(self):
        self.action.rm_action([self.file_name2_short], name=True, remote=True)
        assert poll_doc(self.action, self.doc_id1)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_doc(self.action, self.doc_id3)
        assert self.doc_id1 in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 in self.action.doc_manager.get_doc_ids()
        assert self.action.folder_manager.folder_exists(self.dir_name2)
        assert self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_cancel_all(self):
        self.action.rm_action([], all=True)
        assert poll_rm(self.action, self.doc_id1, cancelled=True)
        assert poll_rm(self.action, self.doc_id2, cancelled=True)
        assert poll_rm(self.action, self.doc_id3, cancelled=True)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_rm_all(self):
        self.action.rm_action([], all=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert os.path.isfile(self.file_path1)
        assert os.path.isfile(self.file_path2)
        assert os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_cancel_local(self):
        self.action.rm_action([], local=True)
        assert poll_rm(self.action, self.doc_id1, cancelled=True)
        assert poll_rm(self.action, self.doc_id2, cancelled=True)
        assert poll_rm(self.action, self.doc_id3, cancelled=True)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path1)
        assert not os.path.isfile(self.file_path2)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)

    def test_rm_local(self):
        self.action.rm_action([], local=True, remote=True)
        assert poll_rm(self.action, self.doc_id1)
        assert poll_rm(self.action, self.doc_id2)
        assert poll_rm(self.action, self.doc_id3)
        assert self.doc_id1 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id2 not in self.action.doc_manager.get_doc_ids()
        assert self.doc_id3 not in self.action.doc_manager.get_doc_ids()
        assert not self.action.folder_manager.folder_exists(self.dir_name2)
        assert not self.action.folder_manager.folder_exists(self.dir_name3)
        assert not os.path.isfile(self.file_path1)
        assert not os.path.isfile(self.file_path2)
        assert not os.path.isfile(self.file_path3)
        assert os.path.isdir(self.dir_path2)
        assert os.path.isdir(self.dir_path3)