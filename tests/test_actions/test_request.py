from tests.test_actions import *
from ltk.actions.request_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
from ltk.actions.config_action import ConfigAction
import time
import unittest

class TestRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.clean_action.clean_action(True, False, None)
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.add_action.add_action(['sample*.txt'], overwrite=True)
        self.doc_ids = self.add_action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.add_action, doc_id)
        self.workflow_id = '2b5498e0-f3c7-4c49-9afa-cca4b3345af7'#need to use a workflow that doesn't have machine translation so we have time to cancel targets before they're completed.  This is a system workflow template, so everyone will have access to it no matter who runs these tests

    def tearDown(self):
        for curr_file in self.files:
            self.rm_action.rm_action(curr_file, remote=True, force=True)
        self.clean_action.clean_action(True, False, None)
        if self.action:
            self.action.close()

    def _check_locales_set(self, document, locales):
        curr_doc = self.add_action.doc_manager.get_doc_by_prop('name', document)
        if 'locales' not in curr_doc:
            return False
        return all(locale in curr_doc['locales'] for locale in locales)

    def _check_locales_unset(self, document, locales, empty=False):
        curr_doc = self.add_action.doc_manager.get_doc_by_prop('name', document)
        if 'locales' not in curr_doc:
            return empty
        return all(locale not in curr_doc['locales'] for locale in locales)

    def test_request_one_locale_doc(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), self.files[0], None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[0])
        response = self.action.api.document_translation_locale_status(entity['id'], 'ja-JP')
        assert response.status_code == 200
        assert response.json()['properties']['status'].upper() != 'CANCELLED'
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[1])
        response = self.action.api.document_translation_locale_status(entity['id'], 'ja-JP')
        assert response.status_code == 404
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[2])
        response = self.action.api.document_translation_locale_status(entity['id'], 'ja-JP')
        assert response.status_code == 404
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_unset(self.files[1], locales, True)
        assert self._check_locales_unset(self.files[2], locales, True)

    def test_request_mult_locale_doc(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), self.files[0], None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[0])
        for locale in locales:
            response = self.action.api.document_translation_locale_status(entity['id'], locale)
            assert response.status_code == 200
            assert response.json()['properties']['status'].upper() != 'CANCELLED'
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[1])
        for locale in locales:
            response = self.action.api.document_translation_locale_status(entity['id'], locale)
            assert response.status_code == 404
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[2])
        for locale in locales:
            response = self.action.api.document_translation_locale_status(entity['id'], locale)
            assert response.status_code == 404
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_unset(self.files[1], locales, True)
        assert self._check_locales_unset(self.files[2], locales, True)

    def test_request_one_locale_proj(self):
        locales = ['ja_JP']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            response = self.action.api.document_translation_locale_status(entity['id'], 'ja-JP')
            assert response.status_code == 200
            assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)

    def test_request_mult_locale_proj(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            for locale in locales:
                response = self.action.api.document_translation_locale_status(entity['id'], 'ja-JP')
                assert response.status_code == 200
                assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)

    def test_delete_locale_doc(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        self.action = RequestAction(os.getcwd(), self.files[0], None, ['ja_JP'], False, True, None, self.workflow_id)
        self.action.target_action()
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[0])
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            for locale in locales:
                response = self.action.api.document_translation_locale_status(entity['id'], locale)
                if file_name == self.files[0] and locale == 'ja_JP':
                    assert response.status_code == 404
                else:
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_unset(self.files[0], ['ja_JP'])
        assert self._check_locales_set(self.files[0], ['zh_CN', 'es_MX'])
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)

    def test_delete_locale_proj(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        self.action = RequestAction(os.getcwd(), None, None, ['ja_JP'], False, True, None, self.workflow_id)
        self.action.target_action()
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            for locale in locales:
                response = self.action.api.document_translation_locale_status(entity['id'], locale)
                if locale == 'ja_JP':
                    assert response.status_code == 404
                else:
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_unset(self.files[0], ['ja_JP'])
        assert self._check_locales_unset(self.files[1], ['ja_JP'])
        assert self._check_locales_unset(self.files[2], ['ja_JP'])
        locales.remove('ja_JP')
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)

    def test_cancel_locale_doc(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        self.action = RequestAction(os.getcwd(), self.files[0], None, ['ja_JP'], True, False, None, self.workflow_id)
        self.action.target_action()
        entity = self.action.doc_manager.get_doc_by_prop('name', self.files[0])
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            for locale in locales:
                response = self.action.api.document_translation_locale_status(entity['id'], locale)
                if file_name == self.files[0] and locale == 'ja_JP':
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() == 'CANCELLED'
                else:
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_unset(self.files[0], ['ja_JP'])
        assert self._check_locales_set(self.files[0], ['zh_CN', 'es_MX'])
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)

    def test_cancel_locale_proj(self):
        locales = ['ja_JP', 'zh_CN', 'es_MX']
        self.action = RequestAction(os.getcwd(), None, None, locales, False, False, None, self.workflow_id)
        self.action.target_action()
        self.action = RequestAction(os.getcwd(), None, None, ['ja_JP'], True, False, None, self.workflow_id)
        self.action.target_action()
        for file_name in self.files:
            entity = self.action.doc_manager.get_doc_by_prop('name', file_name)
            for locale in locales:
                response = self.action.api.document_translation_locale_status(entity['id'], locale)
                if locale == 'ja_JP':
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() == 'CANCELLED'
                else:
                    assert response.status_code == 200
                    assert response.json()['properties']['status'].upper() != 'CANCELLED'
        assert self._check_locales_unset(self.files[0], ['ja_JP'])
        assert self._check_locales_unset(self.files[1], ['ja_JP'])
        assert self._check_locales_unset(self.files[2], ['ja_JP'])
        locales.remove('ja_JP')
        assert self._check_locales_set(self.files[0], locales)
        assert self._check_locales_set(self.files[1], locales)
        assert self._check_locales_set(self.files[2], locales)
