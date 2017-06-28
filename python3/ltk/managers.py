from tinydb import TinyDB, where
import os
import requests
import json
from ltk.constants import CONF_DIR, DB_FN, FOLDER_DB_FN
from ltk.apicalls import ApiCalls

# Python 2
# from ConfigParser import ConfigParser, NoOptionError
# End Python 2
# Python 3
from configparser import ConfigParser, NoOptionError
# End Python 3

class DocumentManager:
    def __init__(self, path):
        self.db_file = os.path.join(path, CONF_DIR, DB_FN)
        self._db = TinyDB(self.db_file)

    def open_db(self):
        self._db = TinyDB(self.db_file)

    def close_db(self):
        self._db.close()

    def doc_exists(self, file_name, title):
        entries = self._db.search((where('file_name') == file_name) & (where('name') == title))
        if entries:
            return True
        else:
            return False

    def is_doc_new(self, file_name, root_path=None):
        if root_path != None:
            config = ConfigParser()
            config.read( root_path + "/.ltk/config")
            download_folder = config.get('main','download_folder')
            locale_folders = config.get('main','locale_folders')
            locale_folders = json.loads(locale_folders)
            #if doc is in the user specified download folder return false
            download_is_watched = False
            if file_name[:len(download_folder)] == download_folder and download_folder is not "":
                with open(root_path + '/.ltk/folders.json') as json_data:
                    folders_json = json.load(json_data)
                folders = folders_json['_default']
                for folder in folders:
                    name = folders_json['_default'][folder]['file_name']
                    if name == download_folder:
                        download_is_watched = True

                if download_is_watched == False:
                    return False
            #if doc is in a user specified locale download folder return false
            for k,v in locale_folders.items():
                if file_name[:len(v)] == v:
                    return False
            #if doc is in a clone folder of a locale name return false
            content = self._db.all()
            for doc in content:
                if 'file_name' in doc.keys():
                    name = doc.get('file_name')
                if 'downloaded' in doc.keys():
                    locales = doc.get('downloaded')
                    name_parts = name.strip().split(".")
                    file_name_name = ""
                    for x in range(0, len(name_parts)-1):
                        file_name_name += name_parts[x]
                    for locale in locales:
                        possible_no_clone_file_name = file_name_name + "." + locale + "." + name_parts[len(name_parts)-1]
                        if download_is_watched:
                            possible_file_name = os.path.join(download_folder, os.path.join(locale, (os.path.basename(file_name_name) + "." + name_parts[len(name_parts)-1])))
                        else:
                            possible_file_name = os.path.join(locale, name)
                        possible_file_name = possible_file_name.replace("_","-")
                        if possible_file_name == file_name or possible_no_clone_file_name == file_name:
                            return False

        file_name_exists = self._db.search(where('file_name') == file_name)
        if not file_name_exists:
            return True
        return False

    ''' receives a translation file and checks if there are corresponding source files'''
    def is_translation(self, file_name, title, matched_files, actions):
        ''' check if the file is a translation file'''

        for myFile in matched_files:
            relative_path = actions.norm_path(myFile)
            myFileTitle = os.path.basename(relative_path)

            ''' only compare the file being checked against source files that have already been added '''
            entry = self._db.get(where("file_name") == relative_path)
            if entry:
                ''' check the source file's download codes to see if the file being checked is a translation file '''
                downloads = self.get_doc_downloads(relative_path)
                if downloads:
                    for d in downloads:
                        ''' append the download code to the source file for comparison '''
                        temp = myFileTitle.split(".")
                        newString = temp[0]+"."+ d +"."+temp[1]
                        if newString == title:
                            return True

        return False

    ''' receives a source file and finds the source files associated with it '''
    #def delete_local_translations(self, file_name, path, actions):


    def is_doc_modified(self, file_name, path):
        entry = self._db.get(where('file_name') == file_name)
        full_path = os.path.join(path, file_name)
        last_modified = os.stat(full_path).st_mtime
        if entry and entry['added'] < last_modified and entry['last_mod'] < last_modified:
            return True
        return False

    def add_document(self, title, create_date, doc_id, sys_mtime, last_mod, file_name):
        entry = {'name': title, 'added': create_date, 'id': doc_id,
                 'sys_last_mod': sys_mtime, 'last_mod': last_mod, 'file_name': file_name,
                 'downloaded': []}
        self._db.insert(entry)

    def update_document(self, field, new_val, doc_id):
        if type(new_val) is list:
            self._db.update(_update_entry_list(field, new_val), where('id') == doc_id)
        else:
            if type(new_val) is set:
                new_val = list(new_val)
            self._db.update({field: new_val}, where('id') == doc_id)

    def get_doc_by_prop(self, prop, expected_value):
        """ get documents by the specified property """
        entry = self._db.get(where(prop) == expected_value)
        return entry

    def get_all_entries(self):
        return self._db.all()

    def get_doc_ids(self):
        """ returns all the ids of documents that the user has added """
        doc_ids = []
        for entry in self._db.all():
            doc_ids.append(entry['id'])
        return doc_ids

    def get_file_names(self):
        """ returns all the file names of documents that the user has added """
        file_names = []
        for entry in self._db.all():
            file_names.append(entry['file_name'])
        return file_names

    def get_names(self):
        """ returns all the names of documents that the user has added """
        file_names = []
        for entry in self._db.all():
            file_names.append(entry['name'])
        return file_names

    def get_doc_name(self, file_name):
        """ returns the file name of a document for a given file path """
        entry = self._db.get(where("file_name") == file_name)
        if entry:
            return entry['name']
        else:
            return None

    def get_doc_locales(self, file_name):
        """ returns the target locales of a document for a given file """
        locales = []
        entry = self._db.get(where("file_name") == file_name)
        if entry:
            locales.append(entry['locales'])

        return locales

    def get_doc_downloads(self, file_name):
        """ returns all the downloaded translations for a given file """
        entry = self._db.get(where("file_name") == file_name)
        if entry:
            downloads = entry['downloaded']
            return downloads

    def remove_element(self, doc_id):
        self._db.remove(where('id') == doc_id)

    def clear_prop(self, doc_id, prop):
        """ Clear specified property of a document according to its type """
        entry = self._db.get(where('id') == doc_id)
        if isinstance(entry[prop],str):
            self.update_document(prop,"",doc_id)
        elif isinstance(entry[prop],int):
            self.update_document(prop,0,doc_id)
        elif isinstance(entry[prop],list):
            self.update_document(prop,[],doc_id)
        elif isinstance(entry[prop],dict):
            self.update_document(prop,{},doc_id)

    def remove_element_in_prop(self, doc_id, prop, element):
        doc_prop = self.get_doc_by_prop('id', doc_id)[prop]
        if element in doc_prop:
            doc_prop.remove(element)
        self.update_document(prop, doc_prop, doc_id)

    def add_element_to_prop(self, doc_id, prop, element):
        doc_prop = self.get_doc_by_prop('id',doc_id)[prop]
        if element not in doc_prop:
            doc_prop.append(element)
        self.update_document(prop, doc_prop, doc_id)

    def clear_all(self):
        self._db.purge()

def _update_entry_list(field, new_val):
    """ updates a list in an entry """
    def transform(element):
        try:
            element[field]
        except KeyError:
            element[field] = []
        if new_val:
            # element[field].extend(new_val)
            for i in range(len(new_val)):
                new_val[i] = new_val[i].replace('-', '_')
            # element[field].extend([val.replace('-', '_') for val in new_val])
            # element[field] = list(set(element[field]))
            element[field] = new_val
        else:
            element[field] = []

    return transform

class FolderManager:
    def __init__(self, path):
        self.db_file = os.path.join(path, CONF_DIR, FOLDER_DB_FN)
        self._db = TinyDB(self.db_file)

    def open_db(self):
        self._db = TinyDB(self.db_file)

    def close_db(self):
        self._db.close()

    def add_folder(self, file_name):
        if not self.folder_exists(file_name):
            entry = {'file_name': file_name}
            self._db.insert(entry)

    def get_all_entries(self):
        return self._db.all()

    def folder_exists(self, file_name):
        """ checks if a folder has been added """
        entries = self._db.search(where('file_name') == file_name)
        if entries:
            return True
        else:
            return False

    def remove_element(self, file_name):
        self._db.remove(where('file_name') == file_name)

    def get_file_names(self):
        """ returns all the file names of folders that the user has added """
        file_names = []
        for entry in self._db.all():
            file_names.append(entry['file_name'])
        return file_names

    def get_folder_by_name(self, expected_name):
        """ get documents by the specified property """
        entry = self._db.get(where('file_name') == expected_name)
        return entry

    def clear_all(self):
        self._db.purge()
