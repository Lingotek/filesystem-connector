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
            self.action.config_action(None, None, None, None, [])
            info = out.getvalue()
            assert 'access_token' in info
            key_words = ['host: https://cms.lingotek.com', 'project id', 'community id', 'locale', 'workflow id']
            assert all(word in info for word in key_words)
        finally:
            sys.stdout = sys.__stdout__

    def test_change_locale(self):
        self.action.config_action('de_DE', None, None, None, [])
        assert self.action.locale == 'de_DE'

    def test_change_workflow(self):
        new_workflow = '6ff1b470-33fd-11e2-81c1-0800200c9a66'
        self.action.config_action(None, new_workflow, None, None, [])
        assert self.action.workflow_id == new_workflow

    def test_add_download_folder(self):
        download_folder = 'downloaded'
        self.action.config_action(None, None, download_folder, None, [])
        assert self.action.download_dir == download_folder

    def test_add_upload_folder(self):
        watch_folder = 'watching'
        self.action.config_action(None, None, None, watch_folder, [])
        print ('self action watch dir', self.action.watch_dir)
        assert self.action.watch_dir == watch_folder

    def test_watch_locales_1(self):
        locale = {'ja_JP'}
        self.action.config_action(None, None, None, None, locale)
        assert self.action.watch_locales == locale

    def test_watch_locales_mult(self):
        locales = ['ja_JP', 'zh_CN', 'fr_FR',]
        self.action.config_action(None, None, None, None, locales)
        print (self.action.watch_locales, set(locales))
        assert self.action.watch_locales == set(locales)
