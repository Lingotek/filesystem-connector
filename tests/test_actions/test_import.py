from tests.test_actions import *
from ltk.import_action import ImportAction

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
        self.action.import_action(True, False, None)
        for doc_id in self.doc_ids:
            assert self.action.doc_manager.get_doc_by_prop('id', doc_id)

    def test_import_locale(self):
        # test importing a document that already has a locale
        pass

    def test_import_no_locale(self):
        self.action.import_action(False, False, None)


