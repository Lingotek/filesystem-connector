# Changelog #
# 1.3.5
## NEW FEATURES
* added ability to specify different target download folders for translations of different files using ltk -D
* added option to see target download folders for files, if set, by using ltk pull -d
* implemented API calls to cancel documents instead of disassociate
* added ability to cancel locales for documents with ltk request -c
* added -c flag to ltk import to ignore cancelled documents when importing
* added document ID and status to output from ltk status
## CHANGES:
* ltk import no longer automatically adds documents to tracking, and instead lets the user specify if they want to track the imported documents or not with the -t flag
* changed some text in the command helps to make them more clear
* display "None" instead of blank space or empty brackets when the configuration settings are output and no default download folder or target locales have been set
* downloads files in the correct format when pulling by locale with locale extensions turned on
* locale folders are no longer ignored when both clone and download folders are off
* ltk mv moves files and no longer throws an error when doing so
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
