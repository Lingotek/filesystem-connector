from tests.test_actions import *
from ltk.actions import Action

import unittest

class TestClean(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = Action(os.getcwd())
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        self.forced = []
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, ['sample*.txt'], force=True)
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        print(self.forced)
        for curr_file in self.files:
            if curr_file in self.forced:
                continue
            self.action.rm_action(curr_file, True)
        self.action.clean_action(False, False, None)

    def test_clean(self):
        delete_id = self.doc_ids[0]
        r = self.action.api.document_delete(delete_id)
        assert r.status_code == 204
        assert self.action.doc_manager.get_doc_by_prop('id', delete_id)
        self.action.clean_action(False, False, None)
        assert not self.action.doc_manager.get_doc_by_prop('id', delete_id)

    def test_clean_force(self):
        delete_id = self.doc_ids[0]
        doc_name = self.action.doc_manager.get_doc_by_prop('id', delete_id)['file_name']
        r = self.action.api.document_delete(delete_id)
        assert r.status_code == 204
        assert self.action.doc_manager.get_doc_by_prop('id', delete_id)
        self.action.clean_action(True, False, None)
        self.forced.append(self.files[0])
        assert not self.action.doc_manager.get_doc_by_prop('id', delete_id)
        assert not os.path.isfile(os.path.join(self.action.path, doc_name))

    def test_disassociate(self):
        self.action.clean_action(False, True, None)
        for curr_id in self.doc_ids:
            assert not self.action.doc_manager.get_doc_by_prop('id', curr_id)

    def test_clean_single(self):
        delete_id = self.doc_ids[0]
        doc_name = self.action.doc_manager.get_doc_by_prop('id', delete_id)['file_name']
        self.action.clean_action(False, False, doc_name)
        assert not self.action.doc_manager.get_doc_by_prop('id', delete_id)
