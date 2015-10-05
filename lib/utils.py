import os

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

# todo possibly put dictionary outside so not built with every function call
def detect_format(file_name):
    name, extension = os.path.splitext(file_name)
    format_mapper = {
        '.csv': 'CSV',
        '.dita': 'DITA',
        '.ditamap': 'DITAMAP',
        '.docx': 'DOCX_OKAPI',
        # 'dox': 'DOXYGEN', # c, h, cpp
        '.dtd': 'DTD',
        '.xslx': 'EXCEL_OKAPI', #xslx, xltx
        # 'html': 'HTML_OKAPI', #htm
        # 'HTML5_ITS',
        '.idml': 'IDML',
        '.properties': 'JAVA_PROPERTIES_OKAPI',
        '.json': 'JSON',
        # 'KV_PAIR',
        # 'odp': 'ODP', # otp
        # 'ods': 'ODS', # ots
        # 'odt': 'ODT', # ott
        '.pdf': 'PDF',
        '.txt': 'PLAINTEXT_OKAPI',
        '.po': 'PO',
        '.ppt': 'PPT_OKAPI',
        '.pptx': 'PPTX_OKAPI',
        # 'yml': 'RAILS_YAML', # yaml
        '.resx': 'RESX',
        '.rtf': 'RTF_OKAPI',
        '.srt': 'SUBTITLE_RIP',
        '.tsv': 'TABLE', #catkeys?
        '.ts': 'TS',
        # 'WIKI_OKAPI',
        # 'WIKITEXT',
        # 'WORD_OKAPI', ?
        # 'xliff': 'XLIFF_OKAPI', #xlf
        # 'XLIFF',
        # 'XLSX_OKAPI',
        '.xml': 'XML_OKAPI'
    }

    format_mapper.update(dict.fromkeys(['.dox', '.c', '.h', '.cpp'], 'DOXYGEN'))
    format_mapper.update(dict.fromkeys(['.html', '.htm'], 'HTML_OKAPI'))
    format_mapper.update(dict.fromkeys(['.odp', '.otp'], 'ODP'))
    format_mapper.update(dict.fromkeys(['.ods', '.ots'], 'ODS'))
    format_mapper.update(dict.fromkeys(['.odt', '.ott'], 'ODT'))
    format_mapper.update(dict.fromkeys(['.yaml', '.yml'], 'RAILS_YAML'))
    format_mapper.update(dict.fromkeys(['.xliff', '.xlf'], 'XLIFF_OKAPI'))
    return format_mapper.get(extension, 'PLAINTEXT_OKAPI')
