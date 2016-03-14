from tests.test_actions import *
from ltk.actions import Action

import unittest

class TestClean(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = Action(os.getcwd())

    def tearDown(self):
        pass

    def test_clean(self):
        pass

    def test_clean_force(self):
        # test that force deletes the file
        pass

    def test_disassociate(self):
        pass

    def test_clean_single(self):
        pass
