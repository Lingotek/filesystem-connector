from tests.test_actions import *
from ltk.actions import Action
import unittest

class TestPush(unittest.TestCase):
    def setUp(self):
        self.files = []
        create_config()
        self.action = Action(os.getcwd())
        self.files.append(create_txt_file('test.txt'))
        self.files.append(create_txt_file('test2.txt'))
        self.action.add_action(None, 'test*.txt')

    def tearDown(self):
        for curr_file in self.files:
            os.remove(curr_file)
        cleanup()

    def test_push_1(self):
        pass

    def test_push_mult(self):
        pass

    def test_push_none(self):
        from io import BytesIO
        import sys

        try:
            out = BytesIO()
            sys.stdout = out
            self.action.push_action()
            info = out.getvalue()
            assert info == 'All documents up-to-date with Lingotek Cloud. '
        finally:
            sys.stdout = sys.__stdout__
