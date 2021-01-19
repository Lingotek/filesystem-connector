from ltk.actions.action import *
from tabulate import tabulate

class ListAction(Action):
    def __init__(self, path):
        Action.__init__(self, path)

    def list_action(self, **kwargs):
        if 'id_type' in kwargs and kwargs['id_type']:
            id_type = kwargs['id_type']
            if id_type == 'workflow':
                self.list_workflows()
            elif id_type == 'locale':
                self.list_locales()
            elif id_type == 'format':
                self.list_formats()
            elif id_type == 'filter':
                self.list_filters()
            elif id_type == 'remote':
                self.list_remote()

        elif 'hide_docs' in kwargs and 'title' in kwargs and 'show_dests' in kwargs:
            self.list_ids(kwargs['hide_docs'], kwargs['title'], kwargs['show_dests'])

        else: logger.error("Error on command line input for 'ltk list'")

    def list_filters(self):
        response = self.api.list_filters()
        if response.status_code != 200:
            raise_error(response.json(), 'Failed to get filters')
        filter_entities = response.json()['entities']
        # print ('Filters: id, created, title')
        table = []
        headers=["ID","Created","Title"]
        for entry in sorted(filter_entities, key=lambda entry: entry['properties']['upload_date'], reverse=True):
            properties = entry['properties']
            title = properties['title']
            filter_id = properties['id']
            upload_date = time.strftime("%Y-%m-%d", time.localtime(int(properties['upload_date']/1000)))
            is_public = " (public)" if properties['is_public'] else ""
            table.append([
                str(filter_id), #ID
                str(upload_date), #Created
                title #Title
            ])
        print(tabulate(table, headers=headers))

    def list_formats(self):
        format_info = self.api.get_document_formats()
        format_mapper = detect_format(None, True)

        format_list = {}
        for format_name in sorted(set(format_info.values())):
            format_list[format_name] = []

        for extension in format_mapper.keys():
            key = format_mapper[extension]
            if key not in format_list:
                format_list[key] = []
            format_list[key].append(extension)

        print("Lingotek Cloud accepts content using any of the formats listed below. File formats will be auto-detected for the extensions as specified below. Alternatively, formats may be specified explicitly upon add. Lingotek supports variations and customizations on these formats with filters.\n")
        table = []
        for k,v in sorted(format_list.items()):
            table.append([
                k, # Format
                ' | '.join([str(x) for x in v]) # Auto-detected File Extensions
            ])
        print(tabulate(table, headers=["Format","Auto-detected File Extensions"]))
        
    def list_ids(self, hide_docs, title=False, downloads=False):
        try:
            """ lists ids of list_type specified """
            folders = self.folder_manager.get_file_names()
            if len(folders):
                # underline("Folder path")
                table = []
                for folder in folders:
                    if title:
                        table.append([folder])
                    else:
                        table.append([self.get_relative_path(folder)])
                print(tabulate(table, headers=["Folder Path"]))
                if hide_docs:
                    return
                print("")
            elif hide_docs:
                print("No added folders")
                return
            ids = []
            titles = []
            locales = []
            dests = []
            max_length = 0
            entries = self.doc_manager.get_all_entries()
            for entry in entries:
                # if entry['file_name'].startswith(cwd.replace(self.path, '')):
                ids.append(entry['id'])
                try:
                    if title:
                        name = entry['name']
                    else:
                        name = self.get_relative_path(self.norm_path(entry['file_name']))
                    if len(name) > max_length:
                        max_length = len(name)
                    titles.append(name)
                except (IndexError, KeyError) as e:
                    log_error(self.error_file_name, e)
                    titles.append("        ")
                try:
                    locales.append(entry['locales'])
                except KeyError:
                    locales.append([])
                if downloads:
                    try:
                        folder = entry['download_folder']
                        dests.append(folder)
                    except KeyError:
                        dests.append('')
            if not ids:
                print ('No local documents')
                return
            if max_length > 90:
                max_length = 90
            table = []
            for i in range(len(ids)):
                filetitle = titles[i]
                if len(filetitle) > max_length:
                    filetitle = filetitle[(len(titles[i])-30):]
                for locale in locales[i]:
                    locale.replace('_', '-')
                if title:
                    headers = ["Title","Lingotek ID","Locales"]
                else:
                    headers = ["Filename","Lingotek ID","Locales"]
                if downloads:
                    headers.append("Target Download Folder")
                    table.append([
                        filetitle,
                        str(ids[i]),
                        ', '.join([str(x).replace('_', '-') for x in locales[i]]),
                        str(dests[i])
                    ])
                else:
                    table.append([
                        filetitle,
                        str(ids[i]),
                        ', '.join([str(x).replace('_', '-') for x in locales[i]])
                    ])
            print(tabulate(table, headers=headers))
        except Exception as e:
            log_error(self.error_file_name, e)
            if 'string indices must be integers' in str(e) or 'Expecting value: line 1 column 1' in str(e):
                logger.error("Error connecting to Lingotek's TMS")
            else:
                logger.error("Error on list: "+str(e))

    def list_locales(self):
        locale_info = []
        table = []
        response = self.api.list_locales()
        if response.status_code != 200:
            raise exceptions.RequestFailedError("Failed to get locale codes")
        locale_json = response.json()
        for entry in locale_json:
            locale_code = locale_json[entry]['locale'].replace('_','-')
            language = locale_json[entry]['language_name']
            country = locale_json[entry]['country_name']
            locale_info.append((locale_code, language, country))
        for locale in sorted(locale_info):
            if not len(locale[2]):  # Arabic
                table.append(["{0}".format(locale[0]), "({0})".format(locale[1])])
            else:
                table.append(["{0}".format(locale[0]), "({0}, {1})".format(locale[1], locale[2])])
        print(tabulate(table))
    def list_remote(self):
        """ lists ids of all remote documents """
        response = self.api.list_documents(self.project_id)
        if response.status_code == 204:
            print("No documents to report")
            return
        elif response.status_code != 200:
            if check_response(response):
                raise_error(response.json(), "Failed to get status of documents", True)
            else:
                raise_error("", "Failed to get status of documents", True)
        else:
            table = []
            headers=["Name", "Lingotek ID"]
            for entry in response.json()['entities']:
                title = entry['properties']['title']
                id = entry['properties']['id']
                table.append([title, id])
            print(tabulate(table, headers=headers))

    def list_workflows(self):
        try:
            response = self.api.list_workflows(self.community_id)
            if response.status_code != 200:
                raise_error(response.json(), "Failed to list workflows")

            table = []
            headers=["Workflow Name", "ID"]
            for entry in response.json()['entities']:
                title = entry['properties']['title']
                id = entry['properties']['id']
                table.append([title, id])
            print(tabulate(table, headers=headers))

        except:
            logger.error("An error occurred while attempting to connect to remote.")
