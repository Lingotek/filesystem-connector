from tests.test_actions import *
from ltk.actions import Action
from io import BytesIO
import sys
import unittest

class TestDownload(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())

    def tearDown(self):
        cleanup()

    def test_download_name_one(self):
        pass

    def test_download_name_mult(self):
        pass

    def test_pull(self):
        pass
