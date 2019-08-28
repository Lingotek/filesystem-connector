from tests.test_actions import *
from ltk.actions.filters_action import *
import unittest
from io import StringIO
import sys
from unittest.mock import patch
import re

class TestFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = FiltersAction(os.getcwd())
        self.added_ids = []
        self.added_files = []
        self.filter_name = 'testfilter'
        self.filter_type = 'SRX'
        if self.filter_type == 'SRX':
            self.filter_ext = '.srx'
        elif self.filter_type == 'FPRM':
            self.filter_ext = '.fprm'
        elif self.filter_type == 'ITS':
            self.filter_ext = '.its'
        else:
            self.filter_ext = ''
        file_path = os.path.join(os.getcwd(), self.filter_name)
        with open(file_path, 'w') as txt_file:
            txt_file.write('This is a test filter')
            txt_file.close()
        self.added_files.append(file_path)
        response = self.action.api.post_filter(self.filter_name, self.filter_type)
        self.added_ids.append(response.json()['properties']['id'])

    def tearDown(self):
        for filter_id in self.added_ids:
            self.action.api.delete_filter(filter_id)
        for file in self.added_files:
            delete_file(file)
        #the following is for troubleshooting the teardown
        #self.action.filter_list_action()
        #check = input('Was the filter cleaned up? ("yes" to continue, anything else to loop) ')
        #loop = (check != 'yes')
        #while loop:
        #    rm_id = input('Enter the id to delete: ')
        #    self.action.filter_rm_action(rm_id)
        #    self.action.filter_list_action()
        #    check = input('Was the filter cleaned up? ("yes" to continue, anything else to loop) ')
        #    loop = (check != 'yes')

    def test_filters_add(self):
        file_path = os.path.join(os.getcwd(), 'testfilter2')
        with open(file_path, 'w') as txt_file:
            txt_file.write('This is another test filter')
            txt_file.close()
        self.added_files.append(file_path)
        self.action.filter_add_action('testfilter2', 'SRX')
        response = self.action.api.list_filters()
        for entry in sorted(response.json()['entities'], key=lambda entry: entry['properties']['upload_date'], reverse=True): #sort by upload date, most recent first, to be sure we get our filter in case the project being used for testing already has a testfilter2.srx that isn't part of the test
            if entry['properties']['title'] == 'testfilter2.srx':
                self.added_ids.append(entry['properties']['id'])
                assert True
                return
        assert False

    def test_filters_get(self):
        with patch('builtins.input', return_value = 'y'):#handles overwriting if the file already exists.  Automatically overwriting is tested in a different unit test
            self.action.filter_get_action(self.added_ids[0], None)
        filter_path = os.path.join(os.getcwd(), self.filter_name+self.filter_ext)
        assert os.path.isfile(filter_path)
        self.added_files.append(filter_path)
        with open(filter_path, 'r') as filterfile:
            filtercontents = filterfile.read()
        assert 'This is a test filter' in filtercontents

    def test_filters_get_info(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.filter_info_action(self.added_ids[0])
            info = out.getvalue()
            assert re.search('title:\s*?'+self.filter_name+self.filter_ext, info)
            assert re.search('id:\s*?'+self.added_ids[0], info)
            assert re.search('type:\s*?'+self.filter_type, info)
        finally:
            sys.stdout = sys.__stdout__
        filter_path = os.path.join(os.getcwd(), self.filter_name+self.filter_ext)
        assert not os.path.isfile(filter_path)

    def test_filters_get_filename(self):
        with patch('builtins.input', return_value = 'y'):#handles overwriting if the file already exists.  Automatically overwriting is tested in a different unit test
            self.action.filter_get_action(self.added_ids[0], 'filterfile')
        filter_path = os.path.join(os.getcwd(), 'filterfile')
        assert os.path.isfile(filter_path)
        self.added_files.append(filter_path)
        with open(filter_path, 'r') as filterfile:
            filtercontents = filterfile.read()
        assert 'This is a test filter' in filtercontents

    def test_filters_get_overwrite(self):
        filter_path = os.path.join(os.getcwd(), self.filter_name+self.filter_ext)
        with open(filter_path, 'w') as txt_file:
            txt_file.write('This should be overwritten')
            txt_file.close()
        self.added_files.append(filter_path)
        self.action.filter_get_action(self.added_ids[0], None, True)
        assert os.path.isfile(filter_path)
        with open(filter_path, 'r') as filterfile:
            filtercontents = filterfile.read()
        assert not 'This should be overwritten' in filtercontents
        assert 'This is a test filter' in filtercontents

    def test_filters_list(self):
        try:
            out = StringIO()
            sys.stdout = out
            self.action.filter_list_action()
            info = out.getvalue()
            assert all(header in info for header in ['Title', 'Created', 'ID'])
            assert re.search(self.filter_name+self.filter_ext+'\s*?[0-9]{4}-[0-9]{2}-[0-9]{2}\s*?'+self.added_ids[0], info)
        finally:
            sys.stdout = sys.__stdout__

    def test_filters_rm(self):
        assert self.action.api.get_filter_info(self.added_ids[0]).status_code == 200 #make sure the filter is there from the setup
        self.action.filter_rm_action(self.added_ids[0])
        assert self.action.api.get_filter_info(self.added_ids[0]).status_code == 404 #check that filter is gone
        self.added_ids.remove(self.added_ids[0]) #remove filter from list so teardown doesn't try and remove a nonexistent filter

    def test_filters_save(self):
        #verify filter before changing and saving
        response = self.action.api.get_filter_content(self.added_ids[0])
        assert 'I am changing the test filter' not in str(response.content)
        assert 'This is a test filter' in str(response.content)

        #change and save filter
        file_path = os.path.join(os.getcwd(), 'testfilter2')
        with open(file_path, 'w') as txt_file:
            txt_file.write('I am changing the test filter')
            txt_file.close()
        self.added_files.append(file_path)
        self.action.filter_save_action(self.added_ids[0], 'testfilter2')
        response = self.action.api.get_filter_content(self.added_ids[0])
        assert 'I am changing the test filter' in str(response.content)
        assert 'This is a test filter' not in str(response.content)