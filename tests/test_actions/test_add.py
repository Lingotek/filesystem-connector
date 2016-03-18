from tests.test_actions import *
from ltk.actions import Action
import os

def test_add_db():
    # check document added to db
    create_config()
    action = Action(os.getcwd())
    file_name = 'sample.txt'
    text_file_path = create_txt_file(file_name)
    action.add_action(None, [file_name])
    # check that document added in db
    assert action.doc_manager.get_doc_by_prop('name', file_name)
    action.rm_action(file_name, False)
    action.clean_action(True, False, None)
    # os.remove(text_file_path)
    cleanup()

def test_add_remote():
    # check that document added to Lingotek
    create_config()
    action = Action(os.getcwd())
    file_name = 'sample.txt'
    text_file_path = create_txt_file(file_name)
    action.add_action(None, [file_name])
    doc_id = action.doc_manager.get_doc_ids()[0]
    # response = action.api.get_document(doc_id)
    # assert response.status_code == 200
    assert poll_doc(action, doc_id)
    action.rm_action(file_name, False)
    action.clean_action(True, False, None)
    # os.remove(text_file_path)
    cleanup()

def test_add_pattern_db():
    # test that adding with a pattern gets all expected matches in local db
    create_config()
    action = Action(os.getcwd())
    files = ['sample.txt', 'sample1.txt', 'sample2.txt']
    file_paths = []
    for fn in files:
        file_paths.append(create_txt_file(fn))
    action.add_action(None, ['sample*.txt'])
    for fn in files:
        assert action.doc_manager.get_doc_by_prop('name', fn)
    # for file_path in file_paths:
    #     os.remove(file_path)
    for fn in files:
        action.rm_action(fn, False)
    action.clean_action(True, False, None)
    cleanup()

def test_add_pattern_remote():
    # test that adding with a pattern gets all expected matches in Lingotek
    create_config()
    action = Action(os.getcwd())
    files = ['sample.txt', 'sample1.txt', 'sample2.txt']
    file_paths = []
    for fn in files:
        file_paths.append(create_txt_file(fn))
    action.add_action(None, ['sample*.txt'])
    doc_ids = action.doc_manager.get_doc_ids()
    for doc_id in doc_ids:
        assert poll_doc(action, doc_id)
    # for file_path in file_paths:
    #     os.remove(file_path)
    for fn in files:
        action.rm_action(fn, False)
    action.clean_action(True, False, None)
    cleanup()

# todo test all those other args
