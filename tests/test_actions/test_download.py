from tests.test_actions import *
from ltk.actions import Action
from io import BytesIO
from io import StringIO
import sys
import unittest


class TestDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.downloaded_files = []
        self.action = Action(os.getcwd())
        self.action.clean_action(False, False, None)
        self.files = ['sample.txt', 'sample1.txt']
        self.locales = ['ja_JP', 'zh_CN']
        self.first_doc = 'sample.txt'
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, ['sample*.txt'], force=True)
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)
        self.action.target_action(None, self.locales, False, None, None)

    def tearDown(self):
        for curr_file in self.files:
            self.action.rm_action(curr_file, force=True)
        self.action.clean_action(False, False, None)
        for dl_file in self.downloaded_files:
            os.remove(dl_file)
        self.action.close()

    def get_dl_path(self, locale, document):
        name_parts = document.split('.')
        if len(name_parts) > 1:
            name_parts.insert(-1, locale)
            downloaded_name = '.'.join(part for part in name_parts)
        else:
            downloaded_name = name_parts[0] + '.' + locale
        dl_path = os.path.join(self.action.path, downloaded_name)
        return dl_path

    def test_download_name(self):
        self.action.download_by_name(self.first_doc, self.locales[0], False)
        dl_file = self.get_dl_path(self.locales[0], self.first_doc)
        assert self.locales[0] in dl_file
        assert os.path.isfile(dl_file)
        self.downloaded_files.append(dl_file)

    def test_pull_all(self):
        for document in self.files:
            for locale in self.locales:
                dl_file = self.get_dl_path(locale, document)
                self.downloaded_files.append(dl_file)

        self.action.pull_action(None, False)
        for path in self.downloaded_files:
            assert os.path.isfile(path)

    def test_pull_locale(self):
        for document in self.files:
            dl_file = self.get_dl_path(self.locales[0], document)
            self.downloaded_files.append(dl_file)
        self.action.pull_action(self.locales[0], False)
        for path in self.downloaded_files:
            assert os.path.isfile(path)
