# Kataja

Visualizing Biolinguistics

Kataja is an open source visualization framework for researchers working with syntax of human languages. 
Kataja aims to be the best available tool for:

 - **DRAWING** syntactic trees
 - **PRESENTING** syntactic phenomena
 - **CRAFTING** syntactic hypotheses

The features will be added to satisfy these needs, in this order.

Kataja is designed and developed by Jukka Purma and it is published under GPL3 license. See COPYING.
The work here is the production part for PhD (Doctor of Arts) in Aalto University School of Art, Design and Architecture, supervised by doc. Pauli Brattico (University of Helsinki) and prof. Teemu Leinonen (Aalto ARTS). 

Kataja is built on Qt5 and Python3.4, using Riverbank Software's PyQt5 to provide Qt bridge for Python.

# About current version

The software is pre-alpha, under development. Daily updates may break features, and generally are not made in order to publish new features, but to help express and maintain the daily progress with the code base.  

# Running and installing on Mac OS X

There are two ways for running Kataja in Mac OS X:

1. As a Kataja.app -- recommended for everyday use, easier to install. 
2. Running as a python script. Necessary for Kataja development and makes plugin development much easier. Requires installation of Qt5.5, PyQt5, sip. See instructions below.

Both options can coexist on same system, but in this case they share the user preferences. (fixme: should they?) 

## Option 1: download, install and run Kataja.app

1. Download Kataja.dmg, double click to open it. 
2. Drag Kataja -application to your Applications-folder. 
3. Double click Kataja.app to launch it.

Like any well-behaving Mac app, Kataja will on first run create a folder to `~/Library/Application Support/Kataja` and a preferences file in `~/Preferences/fi.aalto.jpurma.Kataja.plist`. The Application Support folder will include folder `plugins`, which is the easiest way to extend Kataja. 

## Option 2a: run as a Python3 script 

This option means setting up development environment for Kataja. As Kataja is all python code, the development environment can be easily used for daily linguistic work, teaching or studying: there is no separate build phase for launching Kataja, Kataja can always be launched from terminal in Kataja directory with command `python3 Kataja.py`. It starts faster than Kataja.app-version.

In following the versions mentioned are the latest versions available in 8.3. 2015. Until stabilized, Kataja will be using the latest versions available in order to benefit from performance improvements and bug fixes in build stack components. If the version numbers in this document are dated, use latest PyQt5 version and see its installation guide to find out what are the required versions for SIP and Qt. Usually when a new version of Qt is available, new versions of SIP and PyQt are soon made available.    

Here are the preparations you need to do before Kataja can be run:

### Install Python3.4 ###

I'm not sure if this step is necessary and what is the default Python3 provided by OS X, however in terminal do:

    python3 --version
    
If the version starts with 3.4, good, otherwise run the recommended python installer from http://python.org (On Downloads-menu, it should recommend Python 3.4.3 or newer, and Python 2.7.9 or newer, click the 3.4.3 button. Proceed as instructed. 

### Install Qt ###

Download Qt 5.5 for Mac installer (or the latest version available) from http://www.qt.io/download-open-source/#

Run installer. Installer suggests Qt installation path of form "yourhome/Qt5.5" or "yourhome/Qt"  accept that, and remember it for further use.

### Install SIP ###

Download SIP, sip-4.16.9.tar.gz or the latest available from http://www.riverbankcomputing.com/software/sip/download
Unpack it to your build folder, let's assume that the resulting folder is ~/build/sip-4.16.9
Move to folder:

    cd sip-4.16.9
    python3 configure.py 
    make
(this should take few seconds and result in ~40 lines of text)

    sudo make install

(this should take a second and result in ~7 lines of text)

### Install PyQt5 ###
Download PyQt5 source package from http://www.riverbankcomputing.com/software/pyqt/download5
PyQt-gpl-5.5.tar.gz or later
Unpack it to your build folder, let's assumet that the resulting folder is ~/build/PyQt-gpl-5.5

    cd PyQt-gpl-5.5
    python3 configure.py --qmake /Users/yourhome/Qt5.5/5.5/clang_64/bin/qmake

(notice that --qmake path is the Qt installation path from earlier, and qmake inside it.)

    sudo make

(this will take several minutes)

    sudo make install

(several seconds)

### Download Kataja source and run Kataja ###

get your own copy of Kataja source files with either "Clone in Desktop" or "Download ZIP" in https://github.com/jpurma/Kataja .
 
Navigate to Kataja -folder with terminal, and in there:

    python3 Kataja.py
    
 

## Option 2b -- Building Kataja.app from source for distribution

Building Kataja.app is only necessary if you want to distribute your own version of Kataja, and it is necessary to test if you are proposing changes to Kataja that may break the app building, e.g. require new qt dylibs. For normal develop & run -cycle this step is not necessary.
  
You will need to have Kataja runnable from script (2a). The only new piece required for building Kataja.app is py2app, ( https://pythonhosted.org/py2app/ ). 

The thing to note is that you want to install it for Python3, and the installers often default on Python2-series. Depending on what are the installers available for you, install py2app with either:
  
    sudo pip3 install -U py2app
    
or 
    
    sudo easy_install3 -U py2app

(To see which one, if either, is available just try if `pip3` or `easy_install3` give any response other than "command not found".) 

Once py2app is installed, go to Kataja folder and run 

    python3 setup.py py2app
    
This will take ~10 seconds, and end with `------ Done ------` if everything is right. At first try, it `setup.py` may sk you to edit its `qt_mac` -variable to provide a path to your Qt installation.

The build script will build Kataja.app to `dist/` and Kataja.dmg to folder where it is run. Building of Kataja.dmg can be toggled off with `create_dmg` -variable in `setup.py`. 


## Windows ##

to be added

## Linux ##

I don't have time or expertise for making Linux distributables, as the variance is great and installing the dependencies is anyways easier and more expectable in linux. The same principles as in Option 2a for Mac OS X apply. You'll need Python3.4, Qt5.4, PyQt5 (and compatible SIP).  

When you have Kataja -folder in your preferred place, navigate there and:
 
    python3 Kataja.py
 
Development roadmap
-------------------

April 2014: Pre-alpha -- Builds for OS X, Windows and Linux.

May 2014 Alpha -- Drawing features, including loading, saving, undo, preferences and printing as pdf are stable enough for use.

July 2015: Beta1 -- Presenation features, step-by-step derivation and improvements on drawing.

September 2015: Beta2 -- Crafting features: API for making derivation rules, interface for feature and lexicon creation and running derivations for given input files.


3rd party resources
-------------------

There are few things that make Kataja so much better:

Apostolos Syropoulos: Asana Math Font.
http://www.ctan.org/pkg/asana-math

Ethan Schoonover: Solarized colors 
http://ethanschoonover.com/solarized

W3C: Unicode characters to LaTeX -mapping
http://www.w3.org/TR/unicode-xml/ 