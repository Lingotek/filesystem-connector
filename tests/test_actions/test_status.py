from ltk import actions, exceptions
import unittest
import os
from tests.test_actions import create_config


class TestStatusAction(unittest.TestCase):
    def init_self(self):
        create_config()
        self.action = actions.Action(os.getcwd())
        # add file
        # request translations

    def test_status(self):
        self.init_self()
        # see that there is a status

    def test_status_detailed(self):
        self.init_self()
        # see that there are translations present
