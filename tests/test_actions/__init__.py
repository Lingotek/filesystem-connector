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
    # find way to always get correct path to config file, regardless of current working directory
    path = os.path.join(os.getcwd(),'config')
    shutil.copyfile(path, new_config_file_path)

def create_txt_file(file_name, path=None):
    print("create_txt_file")
    if path:
        file_path = os.path.join(path, file_name)
    else:
        file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, 'w') as txt_file:
        txt_file.write('This is a sample text file. ')
        txt_file.close()
    return file_path

def delete_file(file_name, file_path=None):
    print("delete_file")
    if file_path:
        file_path = os.path.join(file_path, file_name)
        print(file_path)
    else:
        file_path = os.path.join(os.getcwd(), file_name)
    os.remove(file_path)

def create_directory(dir_path):
    print("creating directory: "+dir_path)
    try:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        else:
            if delete_directory(dir_path):
                os.mkdir(dir_path)
    except OSError:
        pass

def delete_directory(dir_path):
    print("deleting directory: "+dir_path)
    if os.path.exists(dir_path) and os.path.isdir(dir_path) and os.listdir(dir_path)==[]:
        os.rmdir(dir_path)
        return True
    else:
        print("directory " + dir_path + " is not empty, and could not be deleted")
        return False

def append_file(file_name, path=None):
    if path:
        file_path = os.path.join(path, file_name)
    else:
        file_path = os.path.join(os.getcwd(), file_name)
    with open(file_path, 'a') as txt_file:
        txt_file.write('Appended text. ')
        print("appended text to file "+file_name)
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
            try:
                new_count = response.json()['entities'][0]['properties']['count']['character']
            except KeyError:
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
