# Kataja

Visualizing Biolinguistics

[Main site](http://www.kataja.purma.fi)

Kataja is an open source visualization framework for researchers working with syntax of human languages. 
Kataja aims to be the best available tool for:

 - **DRAWING** syntax trees
 - **PRESENTING** syntactic phenomena
 - **EXPERIMENTING** with syntax models

The features will be added to satisfy these needs.

Kataja is designed and developed by Jukka Purma and it is published under GPL3 license. See COPYING.
The work here is the production part for PhD (Doctor of Arts) in Aalto University School of Art, Design and Architecture, supervised by doc. Saara Huhmarniemi (University of Helsinki, prev. supervised by Pauli Brattico) and prof. Teemu Leinonen (Aalto ARTS). 

Kataja is built on Qt5 and Python3, using Riverbank Software's PyQt5 to provide Qt bridge for Python.

# About current version

The software is alpha and under intense development. Daily updates may break features, and generally are not made in order to publish new features, but to help express and maintain the daily progress with the code base.  

# Running and installing on Mac OS X

There are two ways for running Kataja in Mac OS X:

1. As a Kataja.app -- recommended for everyday use, easier to install. 
2. Running as a python script. Necessary for Kataja development and makes plugin development much easier. Requires installation of Qt5, PyQt5, latest sip. Installing these has become easier recently.  See instructions below.

Both options can coexist on same system, though they may share user  preferences. 

## Option 1: download, install and run Kataja.app

1. Download Kataja.dmg, double click to open it. 
2. Drag Kataja -application to your Applications-folder. 
3. Double click Kataja.app to launch it.

Like any well-behaving Mac app, Kataja will on first run create a folder to `~/Library/Application Support/Kataja` and a preferences file in `~/Preferences/fi.purma.Kataja.plist`. The Application Support folder will include folder `plugins`, which is the easiest way to extend Kataja. 

## Option 2a: run with Python

It is recommended to run Kataja in virtualenv, so that its dependencies can be kept separated from user and system files.

First navigate to Kataja folder and create a folder for your virtual environment with virtualenv command:

    virtualenv venv

Then activate the virtualenv. While virtualenv is active, 'python' refers to virtualenv's own python and all the libraries and dependancies will be installed into venv-folder.

    source venv/bin/activate

Install requirements defined here in ./requirements.txt:

    pip installpip install -r requirements.txt

Then you should be able to run Kataja:

    python Kataja.py

When you want to deactivate virtualenv, use:

    venv/bin/deactivate

You only have to create virtualenv and install requirements once. Subsequent Kataja runs only require that you have activated virtualenv.

## Option 2b -- Building Kataja.app from source for distribution

Building Kataja.app is only necessary if you want to distribute your own version of Kataja, and it is necessary to test if you are proposing changes to Kataja that may break the app building, e.g. require new qt dylibs. For normal develop & run -cycle this step is not necessary.

### Use Wheels to install Qt5.x, SIP and PyQt5 ###

A new easy method to install necessary dependencies is made possible with Python 3.5 and Python Wheels. Try:

    pip3 install pyqt5

If it results in PermissionError: permission denied, try again with sudo:

    sudo pip3 install pyqt5

This will install open source versions of Qt and PyQt, just what you needed.

If you really want to use Python 3.4 or pip3-based install fails from other reasons, download PyQt5 and SIP from http://www.riverbankcomputing.com/ and follow instructions there (Software -> PyQt -> PyQt5 Reference Guide -> Building and Installing from Source)

get your own copy of Kataja source files with either "Clone in Desktop" or "Download ZIP" in https://github.com/jpurma/Kataja .

Navigate to Kataja -folder with terminal, and in there:

    python3 Kataja.py

You will need to have Kataja runnable from script. The only new piece required for building Kataja.app is py2app, ( https://pythonhosted.org/py2app/ ).

The thing to note is that you want to install it for Python3, and the installers often default on Python2-series. Depending on what are the installers available for you, install py2app with either:
  
    sudo pip3 install -U py2app
    
or 
    
    sudo easy_install3 -U py2app

Once py2app is installed, go to Kataja folder and run 

    python3 setup.py py2app
    
This will take ~10 seconds, and end with `------ Done ------` if everything is right. At first try, it `setup.py` may sk you to edit its `qt_mac` -variable to provide a path to your Qt installation.

The build script will build Kataja.app to `dist/` and Kataja.dmg to folder where it is run. Building of Kataja.dmg can be toggled off with `create_dmg` -variable in `setup.py`. 

## Windows ##

to be added

## Linux ##

I don't have time or expertise for making Linux distributables, as the variance is great and installing the dependencies is anyways easier and more expectable in linux. The same principles as in Option 2a for Mac OS X apply. You'll need Python3.4>, Qt5.6, PyQt5 and compatible SIP. See instructions on  http://www.riverbankcomputing.com/ to install everything necessary for PyQt5. 

When you have Kataja -folder in your preferred place, navigate there and:
 
    python3 Kataja.py
 
3rd party resources
-------------------

There are few things that make Kataja so much better:

Apostolos Syropoulos: Asana Math Font.
http://www.ctan.org/pkg/asana-math

Ethan Schoonover: Solarized colors 
http://ethanschoonover.com/solarized

W3C: Unicode characters to LaTeX -mapping
http://www.w3.org/TR/unicode-xml/ 
