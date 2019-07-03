# Changelog #
# 1.3.5
## NEW FEATURES
* implemented API calls to cancel documents instead of disassociate
* added ability to cancel locales for documents with ltk request -c
* added -c flag to ltk import to ignore cancelled documents when importing
* added document ID and status to output from ltk status
## CHANGES:
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
