from tests.test_actions import *
from ltk.actions.import_action import ImportAction
from ltk.actions.clean_action import CleanAction
from ltk.actions.rm_action import RmAction

import unittest

class TestImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = ImportAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.clean_action.clean_action(False, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.doc_ids = []
        for fn in self.files:
            title = os.path.basename(os.path.normpath(fn))
            response = self.action.api.add_document(self.action.locale, fn, self.action.project_id, title)
            assert response.status_code == 202
            self.doc_ids.append(response.json()['properties']['id'])
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)
        for fn in self.files:
            delete_file(fn)
        self.action.doc_manager.clear_all()
        self.imported = []

    def tearDown(self):
        self.rm_action = RmAction(os.getcwd())
        for doc_id in self.doc_ids:
            self.rm_action.rm_action(doc_id, id=True, remote=True, force=True)
        for file_name in self.imported:
            if os.path.isfile(os.path.join(os.getcwd(), file_name)):
                delete_file(file_name)
        self.clean_action.clean_action(True, False, None)
        self.rm_action.close()
        self.action.close()

    def test_import_single_untracked(self):
        self.action.api.document_cancel(self.doc_ids[0])
        assert poll_rm(self.action, self.doc_ids[0], cancelled=True)
        self.action.import_action(False, False, False, False, False, self.doc_ids[0])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[0]))
        self.imported.append(self.files[0])
        self.action.import_action(False, False, False, False, False, self.doc_ids[1])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[1]))
        self.imported.append(self.files[1])
    
    def test_import_single_tracked(self):
        self.action.api.document_cancel(self.doc_ids[0])
        assert poll_rm(self.action, self.doc_ids[0], cancelled=True)
        self.action.import_action(False, False, False, True, False, self.doc_ids[0])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[0]))
        self.imported.append(self.files[0])
        self.action.import_action(False, False, False, True, False, self.doc_ids[1])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[1]))
        ids_to_check = self.action.doc_manager.get_doc_ids()
        assert self.doc_ids[1] in ids_to_check
        assert self.doc_ids[0] not in ids_to_check

    def test_import_all_untracked(self):
        self.action.api.document_cancel(self.doc_ids[0])
        assert poll_rm(self.action, self.doc_ids[0], cancelled=True)
        self.action.import_action(True, False, False, False, False)
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[0]))
        self.imported.append(self.files[0])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[1]))
        self.imported.append(self.files[1])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[2]))
        self.imported.append(self.files[2])
    
    def test_import_all_tracked(self):
        self.action.api.document_cancel(self.doc_ids[0])
        assert poll_rm(self.action, self.doc_ids[0], cancelled=True)
        self.action.import_action(True, False, False, True, False)
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[0]))
        self.imported.append(self.files[0])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[1]))
        self.imported.append(self.files[1])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[2]))
        self.imported.append(self.files[2])
        ids_to_check = self.action.doc_manager.get_doc_ids()
        assert self.doc_ids[1] in ids_to_check
        assert self.doc_ids[2] in ids_to_check
        assert self.doc_ids[0] not in ids_to_check

    def test_import_path(self):
        dirpath = os.path.join(os.getcwd(), "subdir")
        create_directory(dirpath)
        self.action.import_action(False, False, "subdir", False, False, self.doc_ids[0])
        assert os.path.isfile(os.path.join(dirpath, self.files[0]))
        delete_file(os.path.join("subdir", self.files[0]))
        delete_directory(dirpath)

    def test_import_no_cancel(self):
        self.action.api.document_cancel(self.doc_ids[0])
        assert poll_rm(self.action, self.doc_ids[0], cancelled=True)
        self.action.import_action(True, False, False, False, True)
        assert not os.path.isfile(os.path.join(os.getcwd(), self.files[0]))
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[1]))
        self.imported.append(self.files[1])
        assert os.path.isfile(os.path.join(os.getcwd(), self.files[2]))
        self.imported.append(self.files[2])
