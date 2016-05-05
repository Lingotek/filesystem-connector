from tests.test_actions import *
from ltk import actions, exceptions
import unittest

class TestInitAction(unittest.TestCase):

    def test_uninitialized(self):
        cwd = os.getcwd()
        os.chdir('/')
        self.assertRaises(exceptions.UninitializedError, actions.Action, os.getcwd())
        os.chdir(cwd)  # change back to this directory so rest of the tests will work

    def test_init_host(self):
        create_config()
        action = actions.Action(os.getcwd())
        print (action.host)
        cleanup()

    def test_init_access_token(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.access_token
        cleanup()

    def test_init_project_id(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.project_id
        cleanup()

    def test_init_path(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.path
        cleanup()

    def test_init_community_id(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.community_id
        cleanup()

    def test_init_api(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.api
        cleanup()

    def test_init_doc_manager(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.doc_manager
        cleanup()

#if __name__ == '__main__':
#    unittest.main()
