from ltk import actions
from tests.test_actions import *
import unittest

class TestRm(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = actions.Action(os.getcwd())
        self.action.clean_action(True, False, None)
        self.file_name = 'sample.txt'
        self.file_path = create_txt_file(self.file_name)
        self.action.add_action(None, [self.file_name], force=True)
        self.doc_id = self.action.doc_manager.get_doc_ids()[0]
        assert poll_doc(self.action, self.doc_id)

    def tearDown(self):
        self.action.clean_action(True, False, None)
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
