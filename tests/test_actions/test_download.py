from tests.test_actions import *
from ltk.actions.download_action import *
from ltk.actions.clean_action import CleanAction
from ltk.actions.request_action import RequestAction
from ltk.actions.config_action import ConfigAction
from ltk.actions.pull_action import PullAction
from ltk.actions.rm_action import RmAction
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
        self.config_action = ConfigAction(os.getcwd())
        self.config_action.config_action(clone_option='off')
        self.config_action.config_action(download_folder='--none')
        self.downloaded_files = []
        self.locales = ['ja-JP', 'zh-CN']
        self.action = DownloadAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.request_action = RequestAction(os.getcwd(), None, None, self.locales, False, None, None)
        self.pull_action = PullAction(os.getcwd(), self.action)
        self.clean_action.clean_action(False, False, None)
        self.files = ['sample.txt', 'sample1.txt']
        self.first_doc = 'sample.txt'
        for fn in self.files:
            create_txt_file(fn)
        os.system('ltk add sample*.txt -o') # Let the command line handle parsing the file pattern
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)
        self.request_action.target_action()

    def tearDown(self):
        self.rm_action = RmAction(os.getcwd())
        for curr_file in self.files:
            self.rm_action.rm_action([curr_file], force=True)
        self.clean_action.clean_action(False, False, None)
        for dl_file in self.downloaded_files:
            if os.path.exists(dl_file):
                os.remove(dl_file)
        self.rm_action.close()
        self.clean_action.close()
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
        

        self.action.download_by_path(self.first_doc, self.locales[0], False, False, False)
        dl_file = self.get_dl_path(self.locales[0], self.first_doc)

        assert self.locales[0] in dl_file

        assert os.path.isfile(dl_file)

        self.downloaded_files.append(dl_file)

    def test_pull_all(self):
        for document in self.files:
            for locale in self.locales:
                dl_file = self.get_dl_path(locale, document)
                self.downloaded_files.append(dl_file)

        self.pull_action.pull_translations(None, False, False, False)
        for path in self.downloaded_files:
            assert os.path.isfile(path)

    def test_pull_locale(self):
        for document in self.files:
            dl_file = self.get_dl_path(self.locales[0], document)
            self.downloaded_files.append(dl_file)
        self.pull_action.pull_translations(self.locales[0], False, False, False)
        for path in self.downloaded_files:
            assert os.path.isfile(path)
