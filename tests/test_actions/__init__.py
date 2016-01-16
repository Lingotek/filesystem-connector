from ltk.constants import CONF_DIR, CONF_FN
import os
import shutil
import time

def create_config():
    """
    create config folder and file to initialize without auth
    """
    conf_path = os.path.join(os.getcwd(), CONF_DIR)
    try:
        os.mkdir(conf_path)
    except OSError:
        pass
    new_config_file_path = os.path.join(conf_path, CONF_FN)
    config_file_path = os.path.join(os.getcwd(), 'config')
    shutil.copyfile(config_file_path, new_config_file_path)

def create_txt_file(file_name):
    file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, 'w') as txt_file:
        txt_file.write('This is a sample text file. ')
    return file_path

def append_file(file_name):
    file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, 'a') as txt_file:
        txt_file.write('Appended text. ')
    return file_path

def poll_doc(action, doc_id):
    """polls lingotek for the status of a document given id
        :returns True if document imported within 3min, else False
    """
    time_passed = 0
    while time_passed < 180:
        response = action.api.get_document(doc_id)
        if response.status_code == 200:
            return True
        time.sleep(1)
        time_passed += 1
    return False

def cleanup():
    conf_path = os.path.join(os.getcwd(), CONF_DIR)
    try:
        shutil.rmtree(conf_path)
    except OSError:
        print 'OSError in cleanup'

# test delete
# test import single
# test import all
# test clean
