# Lingotek Client #

The Lingotek Client (`ltk`) is a command line tool that connects your content to the Translation Network™.  It provides yet another way for continuously globalizing all of your translatable content.

The Lingotek Client allows you to quickly add content, request translations, and pull translations from the Lingotek Cloud.  

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


## Getting Started ##

Running `ltk` without any parameters will show all of the commands available: add, clean, config, delete, import, init, list, pull, push, request, and status

Here is video that shows the basics...

[![Lingotek Client (Command Line Tool)](http://img.youtube.com/vi/CbsvVar2rFs/0.jpg)](http://www.youtube.com/watch?v=CbsvVar2rFs)

## Tips ##
The Lingotek Client is written in Python, so it runs on most systems. Should you run into any issues, below are some suggestions and troubleshooting tips.

### virtualenv ###
Like most Python development tools, you might consider installing inside a virtualenv (with a virtualenv wrapper), but it can be installed globally using sudo as well.


```
virtualenv venv
```
Where venv is the name of the virtual environment -- it can be anything you want. 
Start the virtual environment:

```
. venv/bin/activate
```
To exit the virtual environment:

```
deactivate
```

Once virtualenv is activated, install the tool and its dependencies:
```
pip install ltk
```


### Insecure Platform Warnings ###

If you are on Ubuntu/Debian and there are build errors or Insecure Platform warning/errors, your system may be missing some packages needed for secure http requests:

```
sudo apt-get install python-dev libffi-dev libssl-dev
```
If there are still Insecure Platform warning/errors, you may need to upgrade existing packages:

```

pip install --upgrade ndg-httpsclient 
```
