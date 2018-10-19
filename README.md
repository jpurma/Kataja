# Kataja

Visualizing Biolinguistics

[Main site](http://www.kataja.purma.fi)

Kataja is an open source visualisation tool for minimalist grammars of human languages. 
Kataja aims to help you with:

 - **EXPERIMENTING** with your own syntactic models
 - **DRAWING** syntax trees
 - **PRESENTING** syntactic phenomena

Kataja is published under GPL3 license. See COPYING. It is designed and developed by Jukka Purma as a part for PhD (Doctor of Arts) research in Aalto University School of Art, Design and Architecture, supervised by doc. Saara Huhmarniemi (University of Helsinki, prev. supervised by Pauli Brattico) and prof. Teemu Leinonen (Aalto ARTS). 

Kataja is built on Qt5, PyQt5, and Python3.

# About current version

The software is alpha and under sporadic development. At this stage there are no actual releases, but the code from the master branch should run. Daily updates may break features here and there.  

# Running and installing

It is recommended to run Kataja as a Python script in virtualenv, directly from the source code. 

Kataja can be built and distributed as a standalone app for MacOS, Windows and Linux, but providing these will wait until the features are stable enough.

## Downloading current version 

Either clone source code or download zip from https://github.com/jpurma/Kataja from green 'Clone or download' button. If you choose to download, expand zip somewhere.

Kataja requires Python 3.6 or newer. Python distributions for various operating systems can be found at http://python.org

## Preparing virtual environment, loading dependencies and running Kataja

It is recommended to run Kataja in virtualenv, so that its dependencies can be kept separated from user and system files.

First navigate into Kataja-folder and create a folder for your virtual environment with virtualenv command:

    virtualenv venv

Then activate virtualenv. While virtualenv is active, 'python' refers to virtualenv's own python and all the libraries and dependancies will be installed into venv-folder.

    source venv/bin/activate

Install requirements defined here in ./requirements.txt:

    pip install -r requirements.txt

Then you should be able to run Kataja:

    python -m kataja

When you want to deactivate virtualenv, use:

    venv/bin/deactivate

You only have to create virtualenv and install requirements once. Subsequent Kataja runs only require that you have activated virtualenv.


### Installing without virtualenv ###

Another option is to skip the virtualenv and install dependencies for user's python framework. In this case there is a small risk that at some point another python project upgrades some of the dependencies into something incompatible and breaks something in Kataja. And cleaning up Kataja's required dependencies is not as straightforward.

Just navigate to Kataja folder and run:

    pip3 install -r requirements.txt
    
Or if installation fails because of `PermissionError: permission denied`, try again with sudo:

    sudo pip3 install -r requirements.txt

Then run Kataja with:

    python3 -m kataja


### Building Kataja as runnable app in MacOS (deprecated)

You will need to have Kataja runnable from script. The only new piece required for building Kataja.app is py2app, ( https://pythonhosted.org/py2app/ ).

Assuming virtualenv, install py2app 
  
    pip install py2app
    

Once py2app is installed, go to Kataja folder and run 

    python setup.py py2app
    
This will take ~10 seconds, and end with `------ Done ------` if everything is right. At first try, it `setup.py` may ask you to edit its `qt_mac` -variable to provide a path to your Qt installation.

The build script will build Kataja.app to `dist/` and Kataja.dmg to folder where it is run. Building of Kataja.dmg can be toggled off with `create_dmg` -variable in `setup.py`. 

 
3rd party resources
-------------------

There are few things that make Kataja so much better:

Apostolos Syropoulos: Asana Math Font.
http://www.ctan.org/pkg/asana-math

Ethan Schoonover: Solarized colors 
http://ethanschoonover.com/solarized

W3C: Unicode characters to LaTeX -mapping
http://www.w3.org/TR/unicode-xml/ 
