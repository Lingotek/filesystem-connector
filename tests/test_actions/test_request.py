from tests.test_actions import *
from ltk.actions import Action

import unittest

class TestRequest(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())

    def tearDown(self):
        cleanup()

    def test_request_one_locale_doc(self):
        pass

    def test_request_mult_locale_doc(self):
        pass

    def test_request_one_locale_proj(self):
        pass

    def test_request_mult_locale_proj(self):
        pass

    def test_delete_locale(self):
        pass
