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
            self.action.config_action(None, None)
            info = out.getvalue()
            assert info.startswith('host: https://cms.lingotek.com')
        finally:
            sys.stdout = sys.__stdout__

    def test_change_locale(self):
        self.action.config_action('de_DE', None)
        assert self.action.locale == 'de_DE'

    def test_change_workflow(self):
        self.action.config_action(None, '6ff1b470-33fd-11e2-81c1-0800200c9a66')
        assert self.action.workflow_id == '6ff1b470-33fd-11e2-81c1-0800200c9a66'
