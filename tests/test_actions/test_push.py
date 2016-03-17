from tests.test_actions import *
from ltk.actions import Action
import unittest

class TestPush(unittest.TestCase):
    def setUp(self):
        create_config()
        self.action = Action(os.getcwd())
        self.files = ['sample.txt', 'sample1.txt', 'sample2.txt']
        for fn in self.files:
            create_txt_file(fn)
        self.action.add_action(None, 'sample*.txt')
        self.doc_ids = self.action.doc_manager.get_doc_ids()
        for doc_id in self.doc_ids:
            assert poll_doc(self.action, doc_id)

    def tearDown(self):
        for curr_file in self.files:
            self.action.rm_action(curr_file)
        self.action.clean_action(True, False, None)
        cleanup()

    def test_push_1(self):
        # update one document
        # push
        # check results
        append_file(self.files[0])
        self.action.push_action()
        # todo check results

    def test_push_mult(self):
        # update mult docs
        # push
        # check
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
