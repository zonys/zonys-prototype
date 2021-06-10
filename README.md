# zonys
zonys is another container and execution environment manager for the FreeBSD operating system. It provides a powerful command line application with convenient ways for management, configuration and deployment. It utilizes FreeBSD jails, ZFS and is written in python.

Although being used in a production environment, zonys has to be declared as *experimental*. Configuration directives and APIs might change in the future.

## Installing
As for now, zonys can be downloaded from pypi only. Nevertheless, a port will be provided in the future.

### Without virtualenv (not recommended)
```
pkg install curl python38 py38-setuptools py38-pip py38-libzfs
pip install zonys
```

### With virtualenv
```
pkg install curl python38 py38-setuptools py38-pip py38-virtualenv

virtualenv environment
cd environment
source bin/activate

pip install cython

git clone git@github.com:truenas/py-libzfs.git
cd py-libzfs
python3 setup.py install

pip install zonys
```
