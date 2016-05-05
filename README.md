# Lingotek Filesystem Connector #

The Lingotek Filesystem Connector (`ltk`) links your files and folders to the Translation Network™.  It provides yet another way for continuously globalizing all of your translatable content.

The Lingotek Filesystem Connector allows you to quickly add content, request translations, and pull translations from the Lingotek Cloud.  It can even be quickly setup to automate the entire process by watching files or folders for new translatable content.

Content can be sent up in any a variety of formats including: `csv`, `dita`, `ditamap`, `docx`, `doxygen`, `dtd`, `excel`, `html`, `idml`, `java_properties`, `json`, `odp`, `ods`, `odt`, `pdf`, `plaintext`, `po`, `pptx`, `ppt`, `rails_yaml`, `resx`, `rtf`, `subtitle_rip`, `table`, `ts`, `xliff`, and `xml`.

Developers love how easily it can be used to interact with the Translation Network™.  Using the `-v` and `-vv` switches shows exactly which API calls are being used to help developers code custom connectors.

## Installation ##
```bash
pip install ltk
```

You can also install the latest version by downloading this repository and then, from the root directly, run:

```bash
pip install .
```

If you don't have `pip` installed, then you can [install it](https://pip.pypa.io/en/latest/installing/#using-get-pip) using the following:

```bash
$ curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
$ python get-pip.py
```

* Start the tool by using `ltk`

### Windows Installation ###
For instructions on installing in Windows, go to the [Wiki](https://github.com/Lingotek/filesystem-connector/wiki/Installing-on-Windows).


## Getting Started ##

Running `ltk` without any parameters will show all of the commands available: add, clean, config, delete, import, init, list, pull, push, request, and status

Here is video that shows the basics...

[![Lingotek Filesystem Connector](http://img.youtube.com/vi/CbsvVar2rFs/0.jpg)](http://www.youtube.com/watch?v=CbsvVar2rFs)

Checkout other installation notes [here](https://github.com/Lingotek/translation-utility/wiki/Other-Installation-Notes).
