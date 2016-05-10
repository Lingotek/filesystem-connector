from tests.test_actions import *
from ltk.import_action import ImportAction
import time
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
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.doc_ids = []
        for fn in self.files:
            title = os.path.basename(os.path.normpath(fn))
            response = self.action.api.add_document(fn, self.action.locale, self.action.project_id, title)
            assert response.status_code == 202
            self.doc_ids.append(response.json()['properties']['id'])
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        for fn in self.files:
            self.action.rm_action(fn, True)
        self.action.clean_action(False, False, None)

    def test_import_all(self):
        time.sleep(10)
        self.action.import_action(True, False, None)
        print ('import ALL')
        for doc_id in self.doc_ids:
            #print (doc_id)
            assert self.action.doc_manager.get_doc_by_prop('id', doc_id)

    def test_import_locale(self):
        locale = "ja_JP"
        doc_id = self.doc_ids[0]
        response = self.action.api.document_add_target(doc_id, locale)
        assert response.status_code == 201
        self.action.import_action(False, False, None, doc_id)
        entry = self.action.doc_manager.get_doc_by_prop("id", doc_id)
        assert locale in entry["locales"]

    def test_import_no_locale(self):
        self.action.import_action(False, False, None, self.doc_ids[0])
        entry = self.action.doc_manager.get_doc_by_prop("id", self.doc_ids[0])
        assert not entry.get("locales")
