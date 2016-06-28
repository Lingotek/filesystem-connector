from tinydb import TinyDB, where
import os
from ltk.constants import CONF_DIR, DB_FN

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

    def is_doc_new(self, file_name):
        file_name_exists = self._db.search(where('file_name') == file_name)
        if not file_name_exists:
            return True
        return False

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
