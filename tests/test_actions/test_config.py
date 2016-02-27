from tests.test_actions import *
from ltk import actions
import unittest

class TestConfig(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = actions.Action(os.getcwd())

    def tearDown(self):
        cleanup()

    def test_config(self):
        from io import BytesIO
        import sys

        try:
            out = BytesIO()
            sys.stdout = out
            self.action.config_action(None, None, None, None, [])
            info = out.getvalue()
            assert info.startswith('host: https://cms.lingotek.com')
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
        assert self.action.download_dir == os.path.join(self.action.path, download_folder)

    def test_add_upload_folder(self):
        watch_folder = 'watching'
        self.action.config_action(None, None, None, watch_folder, [])
        assert self.action.watch_dir == os.path.join(self.action.path, watch_folder)
