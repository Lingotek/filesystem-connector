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
        self.file_name = 'sample.txt'
        self.file_path = create_txt_file(self.file_name)
        self.add_action.add_action([self.file_name], overwrite=True)
        self.doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, self.doc_id)

    def tearDown(self):
        self.clean_action.clean_action(True, False, None)
        self.clean_action.close()
        self.action.close()
        cleanup()

    def test_rm(self):
        self.action.rm_action(self.file_name, force=False)
        assert poll_rm(self.action, self.doc_id)
        response = self.action.api.get_document(self.doc_id)
        assert response.status_code == 404

    def test_rm_force(self):
        self.action.rm_action(self.file_name, force=True)
        response = self.action.api.get_document(self.doc_id)
        assert response.status_code == 404
        assert not os.path.isfile(self.file_path)
