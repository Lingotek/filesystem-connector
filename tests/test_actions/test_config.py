from tests.test_actions import *
from ltk import actions
from io import StringIO
import unittest


class TestConfig(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = actions.Action(os.getcwd())

    def tearDown(self):
        cleanup()
        self.action.close()

    def test_config(self):
        from io import BytesIO
        import sys

        try:
            out = StringIO()
            sys.stdout = out
            self.action.config_action(**{})
            info = out.getvalue()
            print(out.getvalue())
            assert 'Access_token' in info
            key_words = ['Host: https://cms.lingotek.com', 'Project id', 'Community id', 'Locale', 'Workflow id']
            assert all(word in info for word in key_words)
        finally:
            sys.stdout = sys.__stdout__

    def test_change_locale(self):
        self.action.config_action(**{'locale': 'de_DE'})
        assert self.action.locale == 'de_DE'

    def test_change_workflow(self):
        new_workflow = '6ff1b470-33fd-11e2-81c1-0800200c9a66'
        self.action.config_action(**{'workflow_id': new_workflow})
        assert self.action.workflow_id == new_workflow

    def test_add_download_folder(self):
        dirName = 'download'
        os.mkdir(dirName)
        download_folder = dirName
        self.action.config_action(**{'download_folder': download_folder})
        os.rmdir(dirName)
        print(self.action.download_dir)
        print(download_folder)
        assert self.action.download_dir == download_folder

# We don't use ltk config to add watch folders now; that is currently done by ltk add.
    # def test_add_upload_folder(self):
    #     watch_folder = 'watching'
    #     os.mkdir(watch_folder)
    #     self.action.config_action(None, None, None, watch_folder, [])
    #     os.rmdir(watch_folder)
    #     assert self.action.watch_dir == watch_folder

    def test_watch_locales_1(self):
        locale = {'ja_JP'}
        self.action.config_action(**{'target_locales': locale})
        print (self.action.watch_locales)
        print(locale)
        assert set(self.action.watch_locales) == set(locale)

    def test_watch_locales_mult(self):
        locales = ['ja_JP', 'zh_CN', 'fr_FR',]
        self.action.config_action(**{'target_locales': locales})
        print (set(self.action.watch_locales), set(locales))
        assert set(self.action.watch_locales) == set(locales)
