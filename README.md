### Lingotek Command Line Tool ###
* Make API calls to the Lingotek TMS through the command line
* May have to open browser briefly for OAuth

### Set up ###
* You should have `pip` installed. Having `virtualenv` is strongly suggested.
* `pip` is a tool for installing python packages from the Python Package Index, where open-source third party python packages are hosted. 
* I suggest using a virtual environment -- this will let you install dependencies required for the tool without changing anything system-wide. 
* Create the virtual environment:

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
* If you are on Ubuntu/Debian and there are build errors or Insecure Platform warning/errors, your system may be missing some packages needed for secure http requests:

```
sudo apt-get install python-dev libffi-dev libssl-dev
```
* If there are still Insecure Platform warning/errors, you may need to upgrade existing packages:

```

pip install --upgrade ndg-httpsclient 
```
* Start the tool by using `ltk`