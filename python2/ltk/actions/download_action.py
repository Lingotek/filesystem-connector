from ltk.actions.action import *
import json
import re
import tempfile
import zipfile

class DownloadAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)
        self.download_root = ''
        self.download_path = ''
        self.DOWNLOAD_NUMBER = 1
        self.default_download_ext = "({0})".format(self.DOWNLOAD_NUMBER)
        self.current_doc = ''
        self.DEFAULT_COMMIT_MESSAGE  = "Translations updated for "
        self.documents_downloaded = False

    def download_by_path(self, file_path, locale_codes, locale_ext, no_ext, auto_format, xliff):
        docs = self.get_docs_in_path(file_path)
        if len(docs) == 0:
            logger.warning("No document found with file path "+str(file_path))
        if docs:
            for entry in docs:
                locales = []
                if locale_codes:
                    locales = locale_codes.split(",")
                elif 'locales' in entry:
                    locales = entry['locales']
                if 'clone' in self.download_option and not locale_ext or (no_ext and not locale_ext):
                    self.download_locales(entry['id'], locales, auto_format, xliff, False)
                else:
                    self.download_locales(entry['id'], locales, auto_format, xliff, True)

    def download_locales(self, document_id, locale_codes, auto_format, xliff, locale_ext=True):
        if locale_codes:
            for locale_code in locale_codes:
                locale_code = locale_code.replace("_","-")
                self.download_action(document_id, locale_code, auto_format, xliff, locale_ext)

    def download_action(self, document_id, locale_code, auto_format, xliff=False, locale_ext=True):
        try:
            latest_document_id = self.get_latest_document_version(document_id) or document_id
            response = self.api.document_content(latest_document_id, locale_code, auto_format, xliff, self.finalized_file)
            entry = None
            entry = self.doc_manager.get_doc_by_prop('id', document_id)
            specific_folder = False
            if entry:
                if self.doc_manager.get_doc_target_folder(entry['file_name']):
                    specific_folder = True
            git_commit_message = self.DEFAULT_COMMIT_MESSAGE
            if response.status_code == 410:
                raise_error(response.json(), "Failed to download " + locale_code + ".", True)
                return
            if response.status_code == 200:
                self.download_path = self.path
                if specific_folder:
                    self.download_path = self.doc_manager.get_doc_target_folder(entry['file_name'])
                elif 'clone' in self.download_option:
                    if not locale_code:
                        print("Cannot download "+str(entry['file_name']+" with no target locale."))
                        return
                    self._clone_download(locale_code)
                else:
                    locale_code = locale_code.replace("-","_")#change to be _ to - to be consistent with the other cases.  Currently the default is xx-XX in all cases except this one (clone off, download folder specified) 
                    if locale_code in self.locale_folders:
                        if self.locale_folders[locale_code] == 'null':
                            logger.warning("Download failed: folder not specified for "+locale_code)
                        else:
                            self.download_path = self.locale_folders[locale_code]
                    else:
                        if 'folder' in self.download_option:
                            self.download_path = self.download_dir
                    locale_code = locale_code.replace("_","-")#changing locale code back to xx-XX form
                if not entry:
                    doc_info = self.api.get_document(document_id)
                    try:
                        file_title = doc_info.json()['properties']['title']
                        title, extension = os.path.splitext(file_title)
                        if not extension:
                            extension = doc_info.json()['properties']['extension']
                            extension = '.' + extension
                        if extension and extension != '.none':
                            title += extension
                    except KeyError as e:
                        log_error(self.error_file_name, e)
                        raise_error(doc_info.json(),
                                    'Something went wrong trying to download document: {0}'.format(document_id), True)
                        return
                    self.download_path = os.path.join(self.download_path, title)
                    logger.info('Downloaded: {0} ({1} - {2})'.format(title, self.get_relative_path(self.download_path), locale_code))
                    self.documents_downloaded = True
                else:
                    file_name = entry['file_name']
                    if not file_name == self.current_doc:
                        self.DOWNLOAD_NUMBER = 1
                        self.current_doc = file_name
                    base_name = os.path.basename(self.norm_path(file_name))
                    if not locale_code:
                        # Don't download source document(s), only download translations
                        logger.info("No target locales for "+file_name+".")
                        return
                    if locale_ext or specific_folder:
                        downloaded_name = self.append_ext_to_file(locale_code, base_name, True)
                    else:
                        downloaded_name = base_name
                    if 'xliff' in response.headers['Content-Type'] and xliff == True:
                        downloaded_name = self.change_file_extension('xlf', downloaded_name)
                    if 'same' in self.download_option and not specific_folder:
                        if self.download_path == self.path:
                            self.download_path = os.path.dirname(file_name)
                        new_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                        new_locale = downloaded_name.split('.')[1].lower()
                        new_locale = new_locale.replace('_', '-')
                        if not os.path.isfile(new_path) or (locale_code in new_path) or (locale_code.lower() == new_locale):
                            self.download_path = new_path
                        else:
                            self.default_download_ext = "({0})".format(self.DOWNLOAD_NUMBER)
                            downloaded_name = self.append_ext_to_file(self.default_download_ext, base_name, False)
                            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                            self.DOWNLOAD_NUMBER += 1
                    else:
                        if self.download_path == "null":
                            self.download_path = os.path.join(self.path,downloaded_name)
                        else:
                            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
                self.doc_manager.add_element_to_prop(document_id, 'downloaded', locale_code)
                config_file_name, conf_parser = self.init_config_file()

                # create new file and write contents
                try:
                    if response.headers['Content-Type'] == 'application/zip':
                        if self.unzip_file == 'on':
                            self.unzip_finalized_file(response, base_name, locale_code)
                        else:
                            self.download_path = self.download_path + ".zip"
                            downloaded_name = downloaded_name + '.zip'
                            with open(self.download_path, 'wb') as fh:
                                for chunk in response.iter_content(1024):
                                    fh.write(chunk)
                    else:
                        with open(self.download_path, 'wb') as fh:
                            for chunk in response.iter_content(1024):
                                fh.write(chunk)
                    logger.info('Downloaded: {0} ({1} - {2})\n'.format(downloaded_name, self.get_relative_path(self.download_path), locale_code))

                    # configure commit message
                    if (downloaded_name + ": ") not in git_commit_message:
                        if self.documents_downloaded:
                            git_commit_message += '; '
                        git_commit_message += downloaded_name + ": "
                        document_added = True
                        self.documents_downloaded = True
                    if document_added:
                        git_commit_message += locale_code
                    else:
                        git_commit_message += ', ' + locale_code

                except:
                    logger.warning('Error: Download failed at '+self.download_path)
                    return self.download_path

                git_autocommit = conf_parser.get('main', 'git_autocommit')
                if git_autocommit in ['True', 'on']:
                    if self.git_auto.repo_exists(self.download_path) and os.path.isfile(self.download_path):
                        # add, commit, and push to Github

                        self.git_auto.add_file(self.download_path)
                        self.git_auto.commit(git_commit_message)
                        self.git_auto.push()
                        print("\n")

                        # reset documents downloaded
                        self.documents_downloaded = False

                return self.download_path
            else:
                printResponseMessages(response)
                if entry:
                    raise_error(response.json(), 'Failed to download content for {0} ({1})'.format(entry['name'], document_id), True)
                else:
                    raise_error(response.json(), 'Failed to download content for id: {0}'.format(document_id), True)
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on download: "+str(e))

    def _clone_download(self, locale_code):
        try:
            locale_folders = {}
            for key, value in self.locale_folders.items():
                key = key.replace('_', '-')
                locale_folders[key] = value
            if locale_code in locale_folders:
                self.download_root = locale_folders[locale_code]
            elif self.download_dir and len(self.download_dir):
                self.download_root = os.path.join((self.download_dir if self.download_dir and self.download_dir != 'null' else ''),locale_code)
            else:
                self.download_root = locale_code
            self.download_root = os.path.join(self.path, self.download_root)
            self.download_path = self.download_root
            target_dirs = self.download_path.split(os.sep)
            incremental_path = ""
            if not os.path.exists(self.download_root):
                os.mkdir(self.download_root)
                #print("Created directory: "+ download_root)
            if target_dirs:
                for target_dir in target_dirs:
                    incremental_path += target_dir + os.sep
                    #print("target_dir: "+str(incremental_path))
                    new_path = os.path.join(self.path,incremental_path)
                    # print("new path: "+str(new_path))
                    if not os.path.exists(new_path):
                        try:
                            os.mkdir(new_path)
                            # print("Created directory "+str(new_path))
                        except Exception as e:
                            log_error(self.error_file_name, e)
                            logger.warning("Could not create cloned directory "+new_path)
        except IOError as e:
            print(e.errno)
            print(e)

    def change_file_extension(self, new_ext, base_name):
        name_parts = base_name.split('.')
        new_name = None
        if(len(name_parts) > 1):
            name_parts[-1] = new_ext
            new_name = '.'.join(part for part in name_parts)
        else:
            new_name = name_parts[0] + '.' + new_ext
            self.download_path = os.path.join(self.path, os.path.join(self.download_path, new_name))
            # print("New name: {0}".format(new_name))
            # print("Download path: {0}".format(self.download_path))

        return new_name

    def append_ext_to_file(self, to_append, base_name, append_locale):
        name_parts = base_name.split('.')
        base_locale = None
        loc_check = None
        joined_target = None
        if len(name_parts) > 1:
            for p in name_parts:
                # check locale against global locale
                if p.lower() == self.locale.lower():
                    loc_check = self.locale_check(p)
                    name_parts.remove(p)
                # replace locale '_' with '-' and check against global locale
                elif p.replace('_', '-').lower() == self.locale.lower():
                    loc_check = self.locale_check(p)
                    base_locale = p.replace('_','-')
                    name_parts.remove(p)
            if append_locale:
                if base_locale:  
                    new_target = self.source_to_target(loc_check, to_append.split(to_append[2:3]))
                    joined_target = '_'.join(new_target)
                    name_parts.insert(-1, joined_target)
                else:
                    if loc_check:
                        new_target = self.source_to_target(loc_check, to_append.split(to_append[2:3]))
                        joined_target = '-'.join(new_target)
                        name_parts.insert(-1, joined_target)
                    else:
                        name_parts.insert(-1, to_append)
            else:
                name_parts[0] = name_parts[0] + to_append
            downloaded_name = '.'.join(part for part in name_parts)
            return downloaded_name
        else:
            downloaded_name = name_parts[0] + '.' + to_append
            self.download_path = os.path.join(self.path,os.path.join(self.download_path, downloaded_name))
            return downloaded_name
    
    ''' Splits locale into two parts, i.e. ['en', 'US'] '''
    def locale_check(self, loc):
        parts = re.split('[^a-zA-Z]', loc)
        return parts

    ''' Create new target to match client input '''
    def source_to_target(self, source, target):
        new_target = []
        for x in range(0, len(source)):
            if source[x].isupper():
                new_target.append(target[x].upper())
            else:
                new_target.append(target[x].lower())
        return new_target
            
    def unzip_finalized_file(self, response, base_name, locale_code):
        with tempfile.SpooledTemporaryFile(mode='w+b') as temp_zip:
            for chunk in response.iter_content(1024):
                temp_zip.write(chunk)
            temp_zip.seek(0)
            zip_ref = zipfile.ZipFile(temp_zip)
            with open(self.download_path, 'w+b') as fh:
                filenames = zip_ref.namelist()
                fh.write(zip_ref.open(filenames[0]).read())
            zip_ref.close()
