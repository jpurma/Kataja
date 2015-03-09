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

# Running and installing

Setting up development environment for Kataja:

In following the versions mentioned are the latest versions available in 8.3. 2015. Until stabilized, Kataja will be using the latest versions available in order to benefit from performance improvements and bug fixes in build stack components. If the version numbers in this document are dated, use latest PyQt5 version and see its installation guide to find out what are the required versions for SIP and Qt. Usually when a new version of Qt is available, new versions of SIP and PyQt are soon made available.    

## Mac OS X ##

### Install Qt ###

Download Qt 5.4.1 for Mac offline installer (or the latest version available) from http://www.qt.io/download-open-source/#

Run installer. Installer suggests Qt installation path of form "yourhome/Qt5.4.1"  accept that, and remember it for further use.

### Install SIP ###

Download SIP, sip-4.16.6.tar.gz or the latest available from http://www.riverbankcomputing.com/software/sip/download
Unpack it to your build folder, let's assume that the resulting folder is ~/build/sip-4.16.6
Move to folder:

    cd sip-4.16.6
    python3 configure.py 
    make
(this should take few seconds and result in ~40 lines of text)

    sudo make install

(this should take a second and result in ~7 lines of text)

### Install PyQt5 ###
Download PyQt5 source package from http://www.riverbankcomputing.com/software/pyqt/download5
PyQt-gpl-5.4.1.tar.gz or later
Unpack it to your build folder, let's assumet that the resulting folder is ~/build/PyQt-gpl-5.4.1

    cd PyQt-gpl-5.4.1
    python3 configure.py --qmake /Users/yourhome/Qt5.4.1/5.4/clang_64/bin/qmake 

(notice that --qmake path is the Qt installation path from earlier, and qmake inside it.)

    sudo make

(this will take several minutes)

    sudo make install

(several seconds)



  
  
  
Standalone apps for Mac OS X, Windows and Linux will be provided when the software is in stage where it is usable.

Development roadmap
-------------------

Dec 2014: Alpha -- Drawing features, including loading, saving, undo, preferences and printing as pdf are stable enough for use.
Builds for OS X, Windows and Linux.

May 2015: Beta1 -- Presenation features, step-by-step derivation and improvements on drawing.

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