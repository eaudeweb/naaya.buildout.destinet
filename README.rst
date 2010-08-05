Naaya Buildout
==================

This package is designed to help you install Naaya and its dependencies,
including Zope. It makes use of the Buildout toolkit
(http://pypi.python.org/pypi/zc.buildout) and some of Plone's buildout
recipes.

The buildout has been tested with Python 2.4.6 on Linux (Debian Lenny), Mac
and Windows (see `windows instructions`_).

.. _`windows instructions`: http://naaya.eaudeweb.ro/docs/buildout_windows.html

Prerequisites
-------------

* a working compiler
  - For Debian install the build-essential package.
  - On the Mac install "developer tools".

* Python 2.4, compiled with zlib
  - For Debian, this means python2.4 and python2.4-dev (you may also need
    python-profile from non-free if you want to run unit tests).

* PIL
  - If your distro doesn't support PIL for Python 2.4 then please refer to the
  'Installing PIL' section near the end of this file.

* Glib
  - We need to compile itools which depends on glib (libglib2.0-dev in Debian)
  - By far the simplest way is to install `homebrew`_ and then run::
        brew install glib

.. _`homebrew`: http://mxcl.github.com/homebrew/

Installation
------------

1. Download the buildout kit::
    svn co https://svn.eionet.europa.eu/repositories/Naaya/buildout/Naaya/trunk/ naaya
    cd naaya

2. Run bootstrap::
    python2.4 bootstrap.py -c naaya.cfg
    # replace python2.4 with your local python 2.4 binary

3. Run the buildout::
    bin/buildout -c naaya.cfg

You should end up with a Naaya/Zope distribution in the buildout folder. Zope
and some dependencies are placed in the "parts" folder, and the Naaya egg and
dependencies are placed in the "eggs" folder. bin/zope-instance is a script that
works like zopectl. To start your new Zope, run::
    bin/zope-instance start

A Manager account is created for you in Zope (user: admin, password: admin).


The Buildout directory
----------------------

src/        - contains all Naaya-related namespace packages
products/   - additional Zope Products can be placed here
libs.cfg    - contains common Naaya buildout parts
extfile.ini - this file is used to set the path to where filesystem files are
              stored, by default, the ExtFile Product stores files in the Zope
              instance. Since the Zope instance can be deleted and recreated
              by the buildout script, the extfile.ini file is copied into
              ./parts/zope-instance/etc/ and sets the storage path to
              <buildout-dir>/var/files


Installing PIL
--------------

Reference: http://wiki.python.org/moin/MacPython/UniversalLibrariesAndExtensions
In order to correctly compile and install PIL you have to install the following libraries:
    * libjpeg-dev - for JPEG support
    * libpng-dev - form PNG support
    * zlib1g-dev - for ZIP compression (GIF/PNG), name may differ on other linux distros

Download and unpack PIL to a temporary dir:
        $ wget http://effbot.org/downloads/Imaging-1.1.6.tar.gz
        $ tar zxvf Imaging-1.1.6.tar.gz
        $ cd Imaging-1.1.6

Try to build first, using the python you wish to install to!
        $ <your-python-path>/bin/python setup.py build_ext -i
If all goes well, you should have displayed something like this:
        --------------------------------------------------------------------
        PIL 1.1.6 BUILD SUMMARY
        --------------------------------------------------------------------
        version       1.1.6
        platform      linux2 2.4.6 (#2, Mar 19 2009, 10:00:53)
                    [GCC 4.3.3]
        --------------------------------------------------------------------
        *** TKINTER support not available
        --- JPEG support ok
        --- ZLIB (PNG/ZIP) support ok
        --- FREETYPE2 support ok
        --------------------------------------------------------------------
        To add a missing option, make sure you have the required
        library, and set the corresponding ROOT variable in the
        setup.py script.
You can also run the tests that come with the library:
        $ <your-python-path>/bin/python selftest.py
        57 tests passed.
You may now proceed to installation
        $ <your-python-path>/bin/python setup.py install
