# Changelog #
# 1.3.10
### CHANGES:
* Added the ability to request generic locales da, de, en, es, fr, it, ja, nl, no, pt, tr, zh
# 1.3.7
### CHANGES:
* no longer incorrectly reports errors on successful uploads

## 1.3.6
### NEW FEATURES
* added ability to specify different target download folders for translations of different files using ltk add -D
* added option to see target download folders for files, if set, by using ltk pull -d
* added the ability to set default metadata to be sent with every document
* created a metadata wizard for sending metadata
* added ability to send metadata when pushing documents
* added a set of commands (ltk reference add, ltk reference list, ltk reference get, and ltk reference rm) to upload, download, list, and remove reference material to/from documents
* added a warning to ltk watch if trying to watch too many folders/files
### CHANGES:
* ltk import no longer automatically adds documents to tracking, and instead lets the user specify if they want to track the imported documents or not with the -t flag
* ltk mv correctly moves files and no longer throws an error when doing so
* downloads files in the correct format when pulling by locale with locale extensions turned on
* changed the error message when documents aren't found when requesting status to be more specific on whether or not the file is still uploading or failed to upload
* ltk status now removes documents that failed to upload from local tracking
* locales of downloaded files are in xx-XX format (unless the source file has a specified format) even when clone is disabled and a default download folder is specified
* watch doesn't add and upload downloaded translations
* displays more info on some errors when uploading or pushing documents

## 1.3.5
### NEW FEATURES
* added ability to specify different target download folders for translations of different files using ltk add -D
* added option to see target download folders for files, if set, by using ltk pull -d
* implemented API calls to cancel documents instead of disassociate
* added ability to cancel locales for documents with ltk request -c
* added -c flag to ltk import to ignore cancelled documents when importing
* added document ID and status to output from ltk status
### CHANGES:
* ltk import no longer automatically adds documents to tracking, and instead lets the user specify if they want to track the imported documents or not with the -t flag
* changed some text in the command helps to make them more clear
* display "None" instead of blank space or empty brackets when the configuration settings are output and no default download folder or target locales have been set
* locale folders are no longer ignored when both clone and download folders are off
* ltk rm cancels documents by default unless the -r flag is present, in which case it deletes them
* ltk clean cancels documents that it disassociates
* deprecated the -l flag for ltk rm

## 1.3.4
### NEW FEATURES
* added ability to download finalized files
* added ability to unzip finalized file downloads
* added option to ltk push to do a test run
* added option to ltk push to display titles instead of file paths
### CHANGES:
* cleaned up interface during init wizard
* improved experience when user runs the init wizard with no projects in their community
