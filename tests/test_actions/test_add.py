from tests.test_actions import *
from ltk.actions import Action
import os

def test_add_db():
    # check document added to db
    create_config()
    action = Action(os.getcwd())
    file_name = 'sample.txt'
    text_file_path = create_txt_file(file_name)
    action.add_action(None, file_name)
    # check that document added in db
    assert action.doc_manager.get_doc_by_prop('name', file_name)
    os.remove(text_file_path)
    cleanup()

def test_add_remote():
    # check that document added to Lingotek
    create_config()
    action = Action(os.getcwd())
    file_name = 'sample.txt'
    text_file_path = create_txt_file(file_name)
    action.add_action(None, file_name)
    doc_id = action.doc_manager.get_doc_ids()[0]
    response = action.api.get_document(doc_id)
    assert response.status_code == 200
    os.remove(text_file_path)
    cleanup()

def test_add_pattern_db():
    pass

# todo test all those other args
