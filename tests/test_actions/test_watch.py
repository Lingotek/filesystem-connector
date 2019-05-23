from tests.test_actions import *
from ltk.watch import WatchAction
from ltk.actions.clean_action import CleanAction
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
from threading import Thread
import unittest
import os

# @unittest.skip("skip testing watch for now")
class TestWatch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = WatchAction(os.getcwd())
        self.clean_action = CleanAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.clean_action.clean_action(False, False, None)
        # self.action.open()
        self.downloaded = []
        self.files = []
        self.dir_name = "dir1"
        create_directory(self.dir_name)
        self.add_action.add_action([self.dir_name], overwrite=True)
        # todo current problem: watchdog does not seem to detect changes in daemon
        # but not daemonizing watch causes tests to hang..
        

    def tearDown(self):
        #delete files
        for fn in self.files:
            self.rm_action.rm_action(fn, force=True)
        self.clean_action.clean_action(False, False, None)
        #delete downloads
        for fn in self.downloaded:
            os.remove(fn)
        #delete directory
        delete_directory(self.dir_name)

    def test_watch_new_file(self):
        file_name = "test_watch_sample_0.txt"
        self.files.append(self.dir_name+"/"+file_name)
        if os.path.exists(self.dir_name+file_name):
            delete_file(file_name)
        #start the watch
        self.action.timeout = 5 #set poll to 5 seconds instead of a minute for testing
        watch_thread = Thread(target=self.action.watch_action, args=((), None, False, False))
        watch_thread.daemon = True
        watch_thread.start()
        time.sleep(10) #Gives watch enough time to start up before creating the document
        create_txt_file(file_name, self.dir_name)

        # check if watch detected file and added it to db
        doc = None
        time_passed = 0
        while doc is None and time_passed < 10:
            doc = self.action.doc_manager.get_doc_by_prop('name', file_name)
            time.sleep(1)
            time_passed += 1
        assert doc
        assert poll_doc(self.action, doc['id'])

    def test_watch_update(self):
        file_name = "test_watch_sample_1.txt"
        self.files.append(self.dir_name+os.sep+file_name)
        if os.path.exists(self.dir_name+file_name):
            delete_file(file_name)
        create_txt_file(file_name, self.dir_name)
        self.add_action.add_action([self.dir_name+os.sep+file_name], overwrite=True) #add the document so we're only testing updating, not adding
        #start the watch
        self.action.timeout = 5 #set poll to 5 seconds instead of a minute for testing
        watch_thread = Thread(target=self.action.watch_action, args=((), None, False, False))
        watch_thread.daemon = True
        watch_thread.start()
        time.sleep(10) #Gives watch enough time to start up before appending to the document

        append_file(file_name, self.dir_name)
        time.sleep(10) #Gives watch enough time to pick up on the append
        doc = self.action.doc_manager.get_doc_by_prop('name', file_name)
        newcontent = str(self.action.api.document_content(doc['id'], None, False).content)
        assert 'Appended text.' in newcontent


    def watch_ignore_thread(self):
        os.system('ltk watch -t 5 --ignore .pdf --ignore .html')

#test watch new file when a download directory is in the config file (currently broken)
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_ignore(self):#currently not working because watch is broken
        file_name1 = "test_watch_text.txt"
        self.files.append(self.dir_name+os.sep+file_name1)
        if os.path.exists(self.dir_name+file_name1):
            delete_file(file_name1)
        file_name2 = "test_watch_html.html"
        self.files.append(self.dir_name+os.sep+file_name2)
        if os.path.exists(self.dir_name+file_name2):
            delete_file(file_name2)
        file_name3 = "test_watch_pdf.pdf"
        self.files.append(self.dir_name+os.sep+file_name3)
        if os.path.exists(self.dir_name+file_name3):
            delete_file(file_name3)
        #create and add a file to ignore for append testing
        create_txt_file(file_name2, self.dir_name)
        self.add_action.add_action([self.dir_name+os.sep+file_name2], overwrite=True)
        #start the watch
        watch_thread = Thread(target=self.watch_ignore_thread)#if not done with an os.system call, something happens to the document database when new documents are added and they somehow overwrite ignored documents.
        watch_thread.daemon = True
        watch_thread.start()
        time.sleep(10) #Gives watch enough time to start up before creating the document
        create_txt_file(file_name1, self.dir_name)#create control file that should be added/appended
        create_txt_file(file_name3, self.dir_name)#create a file to ignore for add testing
        
        time.sleep(10) #Gives watch enough time to pick up on the new files
        assert file_name1 in self.action.doc_manager.get_names()
        assert file_name2 in self.action.doc_manager.get_names()
        assert file_name3 not in self.action.doc_manager.get_names()
        doc1 = self.action.doc_manager.get_doc_by_prop('name', file_name1)
        doc2 = self.action.doc_manager.get_doc_by_prop('name', file_name2)
        assert poll_doc(self.action, doc1['id'])
        assert poll_doc(self.action, doc2['id'])

        append_file(file_name1, self.dir_name)
        append_file(file_name2, self.dir_name)
        time.sleep(10) #Gives watch enough time to pick up on the changes
        doc1 = self.action.doc_manager.get_doc_by_prop('name', file_name1)
        newcontent1 = str(self.action.api.document_content(doc1['id'], None, False).content)
        assert 'Appended text.' in newcontent1
        doc2 = self.action.doc_manager.get_doc_by_prop('name', file_name2)
        newcontent2 = str(self.action.api.document_content(doc2['id'], None, False).content)
        assert 'Appended text.' not in newcontent2

#test watch auto with new file (currently broken, can't test until expected behavior is better defined)
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_auto(self):
        pass

#test watch no_folders with update and new file (currently broken)
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_no_folders(self):
        file_name1 = "test_watch_text_1.txt"
        self.files.append(self.dir_name+os.sep+file_name1)
        if os.path.exists(self.dir_name+file_name1):
            delete_file(file_name2)
        file_name2 = "test_watch_text_2.txt"
        self.files.append(self.dir_name+os.sep+file_name2)
        if os.path.exists(self.dir_name+file_name2):
            delete_file(file_name2)
        #create and add a file that won't be ignored
        create_txt_file(file_name1, self.dir_name)
        self.add_action.add_action([self.dir_name+os.sep+file_name1], overwrite=True)
        #start the watch
        self.action.timeout = 5 #set poll to 5 seconds instead of a minute for testing
        watch_thread = Thread(target=self.action.watch_action, args=((), None, True, False))
        watch_thread.daemon = True
        watch_thread.start()
        time.sleep(10) #Gives watch enough time to start up before creating the document
        create_txt_file(file_name2, self.dir_name)#create a file to add and be ignored
        
        time.sleep(10) #Gives watch enough time to pick up on the new files
        assert file_name1 in self.action.doc_manager.get_names(), self.action.doc_manager.get_names()
        assert file_name2 not in self.action.doc_manager.get_names(), self.action.doc_manager.get_names()
        doc1 = self.action.doc_manager.get_doc_by_prop('name', file_name1)
        assert poll_doc(self.action, doc1['id'])

        append_file(file_name1, self.dir_name)
        append_file(file_name2, self.dir_name)
        time.sleep(10) #Gives watch enough time to pick up on the changes
        doc1 = self.action.doc_manager.get_doc_by_prop('name', file_name1)
        newcontent1 = str(self.action.api.document_content(doc1['id'], None, False).content)
        assert 'Appended text.' in newcontent1
        assert file_name2 not in self.action.doc_manager.get_names()

        #check in progress - get a list of remote files and ensure that the one that was supposed to be ignored isn't there
        #print(str(self.action.api.list_documents(self.action.project_id)['entities']['properties']['title']))

#the following three tests are for a functionality that is currently broken in watch, so they are not yet implemented
#test watch downloading 
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_translation(self):
        pass

#test watch downloading translations with a download folder specified
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_translation_download(self):
        pass

#test watch downloading translations with clone specified
    @unittest.skip("skipping until watch is fully functional")
    def test_watch_translation_clone(self):
        pass