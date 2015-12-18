from ltk import actions, exceptions
import unittest
import os
from tests.test_actions import *

class TestStatusAction(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = actions.Action(os.getcwd())
        file_name = 'sample.txt'
        self.file_path = create_txt_file(file_name)
        self.action.add_action(None, file_name)
        self.targets = ['ja_JP', 'de_DE']
        # request translations
        self.action.target_action(file_name, self.targets, False, None, None)

    def tearDown(self):
        # remove the created file
        os.remove(self.file_path)
        cleanup()

    def test_status(self):
        # see that there is a status
        pass

    def test_status_detailed(self):
        # see that there are targets
        pass
