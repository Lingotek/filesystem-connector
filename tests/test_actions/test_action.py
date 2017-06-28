from tests.test_actions import *
from ltk import exceptions
from ltk.actions.action import Action
import unittest

class TestAction(unittest.TestCase):

    def test_uninitialized(self):
        cwd = os.getcwd()
        os.chdir('/')
        with self.assertRaises(exceptions.UninitializedError):
            action = Action(os.getcwd())
        os.chdir(cwd)  # change back to this directory so rest of the tests will work

    def test_host(self):
        create_config()
        action = Action(os.getcwd())
        assert action.host
        action.close()
        cleanup()

    def test_access_token(self):
        create_config()
        action = Action(os.getcwd())
        assert action.access_token
        action.close()
        cleanup()

    def test_project_id(self):
        create_config()
        action = Action(os.getcwd())
        assert action.project_id
        action.close()
        cleanup()

    def test_path(self):
        create_config()
        action = Action(os.getcwd())
        assert action.path
        action.close()
        cleanup()

    def test_community_id(self):
        create_config()
        action = Action(os.getcwd())
        assert action.community_id
        action.close()
        cleanup()

    def test_api(self):
        create_config()
        action = Action(os.getcwd())
        assert action.api
        action.close()
        cleanup()

    def test_doc_manager(self):
        create_config()
        action = Action(os.getcwd())
        assert action.doc_manager
        action.close()
        cleanup()

#if __name__ == '__main__':
#    unittest.main()
