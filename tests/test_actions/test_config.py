from tests.test_actions import *
from ltk.actions.config_action import *
from io import StringIO
import unittest


class TestConfig(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = ConfigAction(os.getcwd())

    def tearDown(self):
        cleanup()
        self.action.close()

    def test_config(self):
        from io import BytesIO
        import sys

        try:
            out = StringIO()
            sys.stdout = out
            self.action.config_action(locale=None, target_locales=None, remove_locales=False, append_option=None, git=False, git_credentials=False,
                clone_option=None, locale_folder=None, workflow_id = None, download_folder=None)
            info = out.getvalue()
            key_words = ['Host: https://myaccount.lingotek.com', 'Community ID', 'Locale', 'Workflow ID']

            assert all(word in info for word in key_words)
        finally:
            sys.stdout = sys.__stdout__

    def test_change_locale(self):
        new_locale = 'de-DE'
        self.action.config_action(locale=new_locale)
        assert self.action.locale == new_locale

        new_locale = 'es-AR'
        self.action.config_action(locale=new_locale)
        assert self.action.locale == new_locale

    def test_change_workflow(self):
        new_workflow = '6ff1b470-33fd-11e2-81c1-0800200c9a66'
        self.action.config_action(workflow_id=new_workflow)
        assert self.action.workflow_id == new_workflow

        new_workflow = 'c675bd20-0688-11e2-892e-0800200c9a66'
        self.action.config_action(workflow_id=new_workflow)
        assert self.action.workflow_id == new_workflow

    def test_add_download_folder(self):
        dirName = 'download'
        create_directory(dirName)
        download_folder = dirName
        self.action.config_action(download_folder=dirName)
        delete_directory(dirName)
        assert self.action.download_dir == download_folder

    def test_rm_download_folder(self):
        download_folder = '--none'
        self.action.config_action(download_folder=download_folder)
        assert self.action.download_dir == ""

    def test_single_target_locale(self):
        locale = ['ja_JP']
        self.action.config_action(target_locales = locale)
        assert self.action.watch_locales == locale

    def test_multiple_target_locales(self):
        locales = ['ja_JP', 'zh_CN', 'fr_FR']
        self.action.config_action(target_locales = locales)
        assert self.action.watch_locales == locales

    def test_clear_locales(self):
        self.action.config_action(target_locales = ('none'),)

        assert self.action.watch_locales == {'[]'}

    def test_single_target_locale_folder(self):
        locale_code = 'ja_JP'
        dirName = 'japanese'
        create_directory(dirName)
        self.action.config_action(locale_folder=(('ja_JP', dirName),))
        delete_directory(dirName)

        assert self.action.locale_folders == {locale_code:dirName}

    def test_multiple_target_locale_folders(self):
        create_directory('japanese')
        self.action.config_action(locale_folder=(('ja_JP', 'japanese'),))
        delete_directory('japanese')

        create_directory('chinese')
        self.action.config_action(locale_folder=(('zh_CN', 'chinese'),))
        delete_directory('chinese')

        assert self.action.locale_folders == {'ja_JP':'japanese', 'zh_CN':'chinese'}

    def test_remove_locale_folders(self):
        self.action.config_action(remove_locales=True)

        assert self.action.locale_folders == {}

    def test_turn_clone_on(self):
        self.action.config_action(clone_option = 'on')

        assert self.action.clone_option == 'on'
        assert self.action.download_option == 'clone'

    def test_turn_clone_off_folder(self):
        download_folder = 'translations'
        create_directory(download_folder)
        self.action.config_action(download_folder=download_folder)
        self.action.config_action(clone_option = 'off')

        delete_directory(download_folder)

        assert self.action.clone_option == 'off'
        assert self.action.download_option == 'folder'

    def test_turn_clone_off_same(self):
        download_folder = '--none'
        self.action.config_action(download_folder=download_folder)
        self.action.config_action(clone_option = 'off')

        assert self.action.clone_option == 'off'
        assert self.action.download_option == 'same'
