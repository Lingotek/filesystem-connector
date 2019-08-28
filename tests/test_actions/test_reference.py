from tests.test_actions import *
import sys
from ltk.actions.reference_action import *
from ltk.actions.add_action import AddAction
from ltk.actions.clean_action import CleanAction
from ltk.actions.rm_action import RmAction
import os
import unittest
from unittest.mock import patch

class TestReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = ReferenceAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.filename = 'sample.txt'
        create_txt_file(self.filename)
        self.references = []
        self.add_action.add_action([self.filename])
        self.doc_id = self.add_action.doc_manager.get_doc_by_prop('name', self.filename)['id']
        poll_doc(self.action, self.doc_id)

        self.references.append('reference1.txt')
        self.references.append('reference2.txt')
        file_path = os.path.join(os.getcwd(), self.references[0])
        print("create_ref_file")
        with open(file_path, 'w') as ref_file:
            ref_file.write('This is a sample reference file number one.')
            ref_file.close()
        file_path = os.path.join(os.getcwd(), self.references[1])
        print("create_ref_file")
        with open(file_path, 'w') as ref_file:
            ref_file.write('This is a sample reference file number two.')
            ref_file.close()

    def tearDown(self):
        self.rm_action = RmAction(os.getcwd())
        self.rm_action.rm_action(self.filename, remote=True, force=True)
        for fn in self.references:
            delete_file(fn)
        self.clean_action.clean_action(False, False, None)
        self.rm_action.close()
        self.clean_action.close()
        self.action.close()

    def test_add_reference(self):
        with patch('builtins.input', side_effect = [self.references[0], '', '', 'Y', self.references[1], 'Ref 2', 'The second reference', 'N']):
            self.action.reference_add_action(self.filename, False)
        
        #use API instead of list function so it can be tested separately
        response = self.action.api.document_list_reference(self.doc_id)
        assert response.json()['properties']['size'] == 2
        materials = response.json()['entities']

        #order of material in API response is not guaranteed, so we have to run checks
        if materials[0]['properties']['name'] == 'reference1.txt' and materials[1]['properties']['name'] == 'Ref 2':
            assert 'description' not in materials[0]['properties']
            assert 'description' in materials[1]['properties']
            assert materials[1]['properties']['description'] == 'The second reference'
        elif materials[1]['properties']['name'] == 'reference1.txt' and materials[0]['properties']['name'] == 'Ref 2':
            assert 'description' not in materials[1]['properties']
            assert 'description' in materials[0]['properties']
            assert materials[0]['properties']['description'] == 'The second reference'
        else:
            assert False

    def test_get_all_references(self):
        #use API instead of add function so it can be tested separately
        referenceA = {'file': self.references[0]}
        referenceB = {'file': self.references[1], 'name': 'Ref 2', 'description': 'The second reference'}
        self.action.api.document_add_reference(self.doc_id, referenceA)
        self.action.api.document_add_reference(self.doc_id, referenceB)

        pathA = self.references[0]
        pathB = self.references[1]
        delete_file(pathA)
        self.references.remove(pathA)
        delete_file(pathB)
        self.references.remove(pathB)
        assert not os.path.isfile(pathA)
        assert not os.path.isfile(pathB)
        self.action.reference_download_action(self.filename, False, True, False)
        assert os.path.isfile(pathA)
        self.references.append(pathA)
        assert os.path.isfile('Ref 2')
        self.references.append('Ref 2')
        with open(pathA, 'r') as ref_file:
            ref_contents = ref_file.read()
        assert 'This is a sample reference file number one' in ref_contents
        with open('Ref 2', 'r') as ref_file:
            ref_contents = ref_file.read()
        assert 'This is a sample reference file number two' in ref_contents

    def test_list_references(self):
        #use API instead of add function so it can be tested separately
        referenceA = {'file': self.references[0]}
        referenceB = {'file': self.references[1], 'name': 'Ref 2', 'description': 'The second reference'}
        self.action.api.document_add_reference(self.doc_id, referenceA)
        self.action.api.document_add_reference(self.doc_id, referenceB)

        try:
            from io import StringIO
            import re
            out = StringIO()
            sys.stdout = out
            self.action.reference_list_action(self.filename, False)
            info = out.getvalue()
            assert re.search("reference1.txt\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*\n", info)
            assert re.search("Ref 2\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*The second reference", info)
        finally:
            sys.stdout = sys.__stdout__

    def test_remove_reference(self):
        #use API instead of add function so it can be tested separately
        referenceA = {'file': self.references[0]}
        referenceB = {'file': self.references[1], 'name': 'Ref 2', 'description': 'The second reference'}
        self.action.api.document_add_reference(self.doc_id, referenceA)
        self.action.api.document_add_reference(self.doc_id, referenceB)

        #use API instead of list function so it can be tested separately.  Verify that the references exist before deleting them
        response = self.action.api.document_list_reference(self.doc_id)
        assert response.json()['properties']['size'] == 2

        self.action.reference_remove_action(self.filename, False, True)

        #use API instead of list function so it can be tested separately
        response = self.action.api.document_list_reference(self.doc_id)
        assert response.json()['properties']['size'] == 0