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
        txt_file.close()
    return file_path

def delete_file(file_name):
    file_path = os.path.join(os.getcwd(), file_name)
    os.remove(file_name)

def append_file(file_name):
    file_path = os.path.join(os.getcwd(), file_name)    
    with open(file_path, 'a') as txt_file:
        txt_file.write('Appended text. ')
        txt_file.close()
    return file_path

def poll_doc(action, doc_id):
    """polls Lingotek for the status of a document given an id
        :returns True if document is imported within 3 min, else False
    """
    time_passed = 0
    while time_passed < 180:
        response = action.api.get_document(doc_id)
        if response.status_code == 200:
            return True
        time.sleep(5)
        time_passed += 1
    return False

def poll_rm(action, doc_id):
    """polls Lingotek for the status of a document given an id
        :returns True if document is deleted within 3 min, else False
    """
    time_passed = 0
    while time_passed < 180:
        response = action.api.get_document(doc_id)
        if response.status_code == 404:
            return True
        time.sleep(1)
        time_passed += 1
    return False

def check_updated_ids(action, doc_ids):
    """polls Lingotek for the modification of multiple documents by id
        :returns True if documents are modified within 3 min, else False
    """
    orig_dates = {}
    for doc_id in doc_ids:
        response = action.api.get_document(doc_id)
        if response.status_code == 200:
            orig_date = response.json()['properties']['modified_date']
            orig_dates[doc_id] = orig_date
            # orig_count = response.json()['entities'][1]['properties']['count']['character']
        else:
            print("Document id not found on Lingotek Cloud: "+str(doc_id))
            return False
    for doc_id in doc_ids:
        if not check_updated(action, doc_id, orig_dates[doc_id]):
            return False
    return True

def check_updated(action, doc_id, orig_date):
    """polls Lingotek for modification of a document given an id
        :returns True if document is modified within 3 min, else False
    """
    time_passed = 0
    while time_passed < 180:
        response = action.api.get_document(doc_id)
        if response.status_code == 200:
            mod_date = response.json()['properties']['modified_date']
            # print("mod_date: "+str(mod_date))
            new_count = response.json()['entities'][1]['properties']['count']['character']
            # print("character count: "+str(new_count))
            # if (orig_count != new_count):
            if (mod_date != orig_date):
                return True
        else:
            print("Document id not found on Lingotek Cloud: "+str(doc_id))
            return False
        time.sleep(5)
        time_passed += 1
    return False

def cleanup():
    conf_path = os.path.join(os.getcwd(), CONF_DIR)
    try:
        shutil.rmtree(conf_path)
    except OSError:
        print ('OSError in cleanup')
