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
        action.close()
        cleanup()

    def test_init_access_token(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.access_token
        action.close()
        cleanup()

    def test_init_project_id(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.project_id
        action.close()
        cleanup()

    def test_init_path(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.path
        action.close()
        cleanup()

    def test_init_community_id(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.community_id
        action.close()
        cleanup()

    def test_init_api(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.api
        action.close()
        cleanup()

    def test_init_doc_manager(self):
        create_config()
        action = actions.Action(os.getcwd())
        assert action.doc_manager
        action.close()
        cleanup()

#if __name__ == '__main__':
#    unittest.main()
