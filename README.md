# Lingotek Client #

The Lingotek Client (`ltk`) is a command line tool that enables you to connect your content to the Lingotek Translation Network.  It provides yet another way to continuously globalization of your translatable content.

The Lingotek Client allows you to quickly add content (e.g., HTML, JSON, properties, TXT), request translations, and pull translations from the Lingotek Cloud.  

Developers love using it to interact with the Lingotek Translation Network.  Using the `-v` (and `-vv`) switches API calls are displayed for convenience in seeing API calls that can be used to develop custom connectors.

## Installation ##

You can install the latest version by downloading this repository and then, from the root directly, running:

```bash
pip install .
```

If you don't have `pip` installed, then you can [install it|https://pip.pypa.io/en/latest/installing/#using-get-pip] using the following:

```bash
$ curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
$ python get-pip.py
```

* Start the tool by using `ltk`

```
## Commands ##

Usage: ltk [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  -q         will only show warnings
  -v         show API calls. -vv for API responses.
  --help     Show this message and exit.

Commands:
  add       adds content, could be one file or multiple...
  clean     cleans up the associations between local...
  config    view or change local configuration
  delete    disassociate local document(s) from remote...
  download  downloads translated content of document(s)
  import    import documents from Lingotek
  init      initializes a Lingotek project
  list      lists ids and titles of documents added with...
  pull      pulls all translations for added documents
  push      sends updated content to Lingotek for...
  request   add targets to document(s) to start...
  status    gets the status of a specific document or all...

```


## Tips ##
The Lingotek Client is written in Python, so it runs on most systems. Should you run into any issues, below are some suggestions and troubleshooting tips.

### virtualenv ###
Like most Python development tools, you might consider installing inside a virtualenv (with a virtualenv wrapper), but it can be installed globally using sudo as well.


```
virtualenv venv
```
* Where venv is the name of the virtual environment -- it can be anything you want. 
* Start the virtual environment:

```
. venv/bin/activate
```
* To exit the virtual environment:

```
deactivate
```

* Once virtualenv is activated, install the tool and its dependencies:
```
pip install --editable .
```

* The above command is temporary, it installs the tool in development mode

### Insecure Platform Warnings ###

* If you are on Ubuntu/Debian and there are build errors or Insecure Platform warning/errors, your system may be missing some packages needed for secure http requests:

```
sudo apt-get install python-dev libffi-dev libssl-dev
```
* If there are still Insecure Platform warning/errors, you may need to upgrade existing packages:

```

pip install --upgrade ndg-httpsclient 
```