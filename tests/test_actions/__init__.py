from ltk.constants import CONF_DIR, CONF_FN
import os
import shutil

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

def cleanup():
    conf_path = os.path.join(os.getcwd(), CONF_DIR)
    try:
        shutil.rmtree(conf_path)
    except OSError:
        pass

# test delete
# test import single
# test import all
# test clean
