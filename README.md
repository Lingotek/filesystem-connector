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


## Getting Started ##

Running `ltk` without a command will show all of the commands availble: add, clean, config, delete, download, import, init, list, pull, push, request, status

<a href="http://www.youtube.com/watch?feature=player_embedded&v=CbsvVar2rFs
" target="_blank"><img src="http://img.youtube.com/vi/CbsvVar2rFs/0.jpg" 
alt="Lingotek Client (Command Line Tool)" width="240" height="180" border="10" /></a>

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