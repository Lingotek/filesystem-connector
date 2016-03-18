from tests.test_actions import *
from ltk.actions import Action

import unittest

class TestClean(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())

    def tearDown(self):
        cleanup()

    def test_clean(self):
        pass

    def test_clean_force(self):
        # test that force deletes the file
        pass

    def test_disassociate(self):
        pass

    def test_clean_single(self):
        pass
