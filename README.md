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

The software is alpha and under sporadic development. At this stage there are no actual releases, but the code from the master branch should run. Daily updates may break features here and there.  

# Running and installing

At this stage it is recommended to run Kataja as a Python module in virtualenv. This requires some understanding of Python,
but Kataja is at its best when it is used to visualise grammar models written in Python.  

Kataja can be built and distributed as a standalone app for MacOS, Windows and Linux, but providing these will wait until the features are stable enough.

## Installing and running Kataja with virtualenv on MacOS

Use Terminal and navigate to some directory that you can use as a workspace. There create a virtualenv named 'venv'

    python3 -m venv venv  

This creates a new folder 'venv' that will contain its own copy of Python and all of the packages and dependencies required for Kataja. Removing Kataja will be as easy as removing this folder.

Then activate the virtual environment.

    source venv/bin/activate
    
Command prompt in terminal will change to indicate you are in venv-environment -- items available from venv will be sought first instead of your normal environment.

Then install Kataja. 

    pip install kataja --extra-index-url https://test.pypi.org/simple/

This will download and install Kataja and its required dependencies, largest of them will be PyQt5. Then you can run Kataja:

    python -m kataja

You can also try to use Kataja as a command line tool to draw pretty trees from bracket notation:

    python -m kataja -image_out test.pdf "[ a [ brown fox ] ]" 

## Installing and running Kataja with virtualenv on Windows

You have to download and install latest version of Python for Windows (3.6 at least, 3.7 preferable) 
from https://python.org

Use PowerShell and navigate to some directory that you can use as a workspace. There create a virtualenv named 'venv'

    py -m venv venv  

This creates a new folder 'venv' that will contain its own copy of Python and all of the packages and dependencies required for Kataja. Removing Kataja will be as easy as removing this folder.

Then activate the virtual environment.

    .\venv\Scripts\activate.bat
    
Command prompt in terminal will change to indicate you are in venv-environment -- items available from venv will be sought first instead of your normal environment.

Then install Kataja. 

    pip install kataja --extra-index-url https://test.pypi.org/simple/

This will download and install Kataja and its required dependencies, largest of them will be PyQt5. Then you can run Kataja:

    python -m kataja

You can also try to use Kataja as a command line tool to draw pretty trees from bracket notation:

    python -m kataja -image_out test.pdf "[ a [ brown fox ] ]" 



# Setting up Kataja development version

Clone or download the source code from https://github.com/jpurma/Kataja by using the green 'Clone or download' button. If you choose to download, expand zip somewhere.

Kataja requires Python 3.6 or newer. Python distributions for various operating systems can be found at http://python.org

## Preparing virtual environment, loading dependencies and running Kataja

It is recommended to run Kataja in virtualenv, so that its dependencies can be kept separated from user and system files.

First navigate into Kataja-folder and create a folder for your virtual environment with virtualenv command:

    python -m venv venv

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


### Building Kataja as runnable app in MacOS (broken now, will fix at some point!)

You will need to have Kataja runnable from script. The only new piece required for building Kataja.app is py2app, ( https://pythonhosted.org/py2app/ ).

Assuming virtualenv, install py2app 
  
    pip install py2app
    

Once py2app is installed, go to Kataja folder and run 

    python setup.py py2app
    
This will take ~10 seconds, and end with `------ Done ------` if everything is right. At first try, it `setup.py` may ask you to edit its `qt_mac` -variable to provide a path to your Qt installation.

The build script will build Kataja.app to `dist/` and Kataja.dmg to folder where it is run. Building of Kataja.dmg can be toggled off with `create_dmg` -variable in `setup.py`. 


# Visualising your own models with Kataja

To understand the work where Kataja aims to help, we should think about three levels where a computer-assisted syntactician has to operate:

1. Developing a linguistic model

2. Creating a software implementation for the linguistic model

3. Creating diagnostic and presentable outputs from the software implementation

Usually 2 and 3 go together. When one creates a software implementation of a linguistic model, one adds output methods and other diagnostic tools to help figure what the model is doing. With recursive structures typical for generative enterprise, our grammars tend to create problems that are difficult to trace and states that are difficult to represent. Kataja will help and save effort in level 3, e.g. in drawing intermediate stages of derivation, tracking movements and feature interactions.

Kataja will also help when your syntactic model is doing something impressive. It can output your derivations as beautiful animated sequences or rich structures for publications and presentations.


## Kataja plugins

If you have a syntactic model of minimalist flavor, written in python, then it can be modified to work as a Kataja plugin. Kataja plugins are syntactic models that have such properties that Kataja can understand their constituent structures and display them in various manners. A syntactic model as a Kataja plugin is not dependant on Kataja: if you have started to develop your MG model as a python project running from command line, a Kataja compatible version should still run from command line without having Kataja present. Kataja is there to handle some outputs of your models you want to give for it. This is also a matter of performance: once there is a successful parser, you'll want to do runs with thousands of inputs and at least temporarily strip off unnecessary overhead.

See `kataja/plugins`...


 
3rd party resources
-------------------

There are few things that make Kataja so much better:

Apostolos Syropoulos: Asana Math Font.
http://www.ctan.org/pkg/asana-math

Ethan Schoonover: Solarized colors 
http://ethanschoonover.com/solarized

W3C: Unicode characters to LaTeX -mapping
http://www.w3.org/TR/unicode-xml/ 
