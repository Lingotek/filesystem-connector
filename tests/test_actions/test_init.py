from tests.test_actions import *
from ltk import exceptions
from ltk.actions.init_action import InitAction
import unittest

class TestInitAction(unittest.TestCase):

    def test_uninitialized(self):
        cwd = os.getcwd()
        os.chdir('/')
        self.assertRaises(exceptions.UninitializedError, InitAction)
        os.chdir(cwd)  # change back to this directory so rest of the tests will work

    def test_init_host(self):
        create_config()
        action = InitAction()
        print (action.host)
        action.close()
        cleanup()

    def test_init_access_token(self):
        create_config()
        action = InitAction()
        assert action.access_token
        action.close()
        cleanup()

    def test_init_project_id(self):
        create_config()
        action = InitAction()
        assert action.project_id
        action.close()
        cleanup()

    def test_init_path(self):
        create_config()
        action = InitAction()
        assert action.path
        action.close()
        cleanup()

    def test_init_community_id(self):
        create_config()
        action = InitAction()
        assert action.community_id
        action.close()
        cleanup()

    def test_init_api(self):
        create_config()
        action = InitAction()
        assert action.api
        action.close()
        cleanup()

    def test_init_doc_manager(self):
        create_config()
        action = InitAction()
        assert action.doc_manager
        action.close()
        cleanup()

#if __name__ == '__main__':
#    unittest.main()
