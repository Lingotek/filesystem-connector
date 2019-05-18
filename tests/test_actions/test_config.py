from tests.test_actions import *
from ltk.actions.config_action import *
from io import StringIO
import unittest
from unittest.mock import patch


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
            key_words = ['Community ID', 'Locale', 'Workflow ID']
            import re
            assert re.search('Host\s*https://myaccount.lingotek.com', info) #changed to regex because display uses tabulate, which has an indeterminate amount of whitespace to create the columns
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
    
    def test_git_autocommit(self):
        self.action.config_action(git='on')
        assert self.action.git_autocommit == 'on'

        self.action.config_action(git='off')
        assert self.action.git_autocommit == 'off'

    def test_git_credentials(self):
        with patch('builtins.input', return_value = 'testusername'), patch('getpass.getpass', return_value = 'testpassword'):
            self.action.config_action(git_credentials=True)
        assert self.action.conf_parser.get('main', 'git_username') == 'testusername'
        #using git_auto.encrypt on the password just converts it to base64, so 'testpassword' will always become 'dGVzdHBhc3N3b3Jk' and we can assert that that is so
        assert self.action.conf_parser.get('main', 'git_password') == 'dGVzdHBhc3N3b3Jk\n'#the config parser addes a newline after the password for some reason, but it works with the code so we'll just test around it

        with patch('builtins.input', return_value = 'testusername'), patch('getpass.getpass', return_value = '--none'):
            self.action.config_action(git_credentials=True)
        assert self.action.conf_parser.get('main', 'git_username') == 'testusername'
        assert self.action.conf_parser.get('main', 'git_password') == ''

        with patch('builtins.input', return_value = '--none'), patch('getpass.getpass', return_value = 'testpassword'):
            self.action.config_action(git_credentials=True)
        assert self.action.conf_parser.get('main', 'git_username') == ''
        #using git_auto.encrypt on the password just converts it to base64, so 'testpassword' will always become 'dGVzdHBhc3N3b3Jk' and we can assert that that is so
        assert self.action.conf_parser.get('main', 'git_password') == 'dGVzdHBhc3N3b3Jk\n'#the config parser addes a newline after the password for some reason, but it works with the code so we'll just test around it

        with patch('builtins.input', return_value = '--none'), patch('getpass.getpass', return_value = '--none'):
            self.action.config_action(git_credentials=True)
        assert self.action.conf_parser.get('main', 'git_username') == ''
        assert self.action.conf_parser.get('main', 'git_password') == ''
    
    def test_finalized_file(self):
        with patch('builtins.input', return_value = 'off'):#to skip turning on unzipping when testing turning finalized files on
            self.action.config_action(finalized_file='on')
        assert self.action.finalized_file == 'on'

        self.action.config_action(finalized_file='off')
        assert self.action.finalized_file == 'off'

    def test_unzip_finalized_file(self):
        self.action.config_action(unzip_file='on')
        assert self.action.unzip_file == 'on'

        self.action.config_action(unzip_file='off')
        assert self.action.unzip_file == 'off'

    def test_append_number(self):
        self.action.config_action(append_option='number:3')
        assert self.action.append_option == 'number:3'

        self.action.config_action(append_option='none')
        assert self.action.append_option == 'none'


    def test_append_name(self):
        self.action.config_action(append_option='name:folder')
        assert self.action.append_option == 'name:folder'

        self.action.config_action(append_option='none')
        assert self.action.append_option == 'none'

    def test_autoformat(self):
        self.action.config_action(auto_format='on')
        assert self.action.auto_format_option == 'on'

        self.action.config_action(auto_format='off')
        assert self.action.auto_format_option == 'off'