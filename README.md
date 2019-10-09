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

At current stage of development, I recommend running Kataja from its source code with Python and its required libraries installed in virtual environment.

Kataja can be built and distributed as a standalone app for MacOS, Windows and Linux, but creating these packages should wait until Kataja is stable enough.


## Setting up Kataja development version

Clone or download the source code from https://github.com/jpurma/Kataja by using the green 'Clone or download' button. If you choose to download, expand the zip file into a suitable location.

Kataja requires Python 3.6 or later. Python distributions for various operating systems can be found at http://python.org

If you are new to Python, the following references to `python`, `python3` and `py3` can be a source of confusion and the names can be even be wrong. They aim to refer to two things, either a) the installed Python3 -interpreter in your operating system. b) the local virtual environment version of Python3. How they are named depends on the operating system and its pre-existing installations: if there exists Python2.x in the system, installer may use python3 to avoid breaking existing things that expect Python2.x to exist. Also in Windows python may use 'py'-alias for reasons I don't know. Python in sense (a) can be used to run and install Kataja, or it can be used to set up a local virtual environment, which once activated will provide Python (b). The same variance with naming and applies for `pip` and `pip3`-commands. You'll want to use the one that is associated with your Python3.x installation. Try `pip --version` to see if the command refers to Python3 or 2.

### Preparing virtual environment, loading dependencies and running Kataja

It is recommended to run Kataja in virtualenv, so that its dependencies can be kept separated from user's Python libraries and system's Python libraries.

First navigate into Kataja-folder and create a folder for your virtual environment with virtualenv command:

    python -m venv venv

Then activate virtualenv. While virtualenv is active, 'python' refers to virtualenv's own python and all the libraries and dependancies will be installed into venv-folder.

In MacOS:

    source venv/bin/activate

In Windows:

    .\venv\Scripts\activate.bat

Then install Kataja's requirements. They are defined in file ./requirements.txt:

    pip install -r requirements.txt

Now you should be able to run Kataja:

    python -m kataja

You only have to create virtualenv and install requirements once. Subsequent Kataja runs only require that you are in an activated virtualenv.

You can also try to use Kataja as a command line tool to draw pretty trees from bracket notation:

    python -m kataja -image_out test.pdf "[ a [ brown fox ] ]"


### Installing without virtualenv ###

Another option is to skip the virtualenv and install dependencies permanently into user's python framework.

Just navigate to Kataja folder and run:

    pip3 install -r requirements.txt
    
Or if installation fails because of `PermissionError: permission denied`, try again with sudo:

    sudo pip3 install -r requirements.txt

Then run Kataja with:

    python3 -m kataja


### Installing Kataja itself from PyPI

There is an experimental build of Kataja in Python Package Index (PyPI)'s test index. It lags behind the current version, but it can be tried out. In (preferably) an activated virtualenv, try:

    pip install kataja --extra-index-url https://test.pypi.org/simple/

Then try to run it:

    python -m kataja

or to see command line arguments:

    python -h

### Building Kataja as runnable app in MacOS (broken now, will fix at some point!)

You will need to have Kataja runnable from script. The only new piece required for building Kataja.app is py2app, ( https://pythonhosted.org/py2app/ ).

Assuming virtualenv, install py2app 
  
    pip install py2app
    

Once py2app is installed, go to Kataja folder and run 

    python setup.py py2app
    
This will take ~10 seconds, and end with `------ Done ------` if everything is right. At first try, it `setup.py` may ask you to edit its `qt_mac` -variable to provide a path to your Qt installation.

The build script will build Kataja.app to `dist/` and Kataja.dmg to folder where it is run. Building of Kataja.dmg can be toggled off with `create_dmg` -variable in `setup.py`. 

# Running Kataja from command line

There are following command line arguments:

    python -m kataja -h
    
Will display 

    positional arguments:
      tree                  bracket tree or source tree filename
    
    optional arguments:
      -h, --help            show this help message and exit
      --reset_prefs         reset the current preferences file to default
      --no_prefs            don't use preferences file -- don't save it either
      -image_out IMAGE_OUT  draw tree into given file (name.pdf or name.png) and
                            exit
      -plugin PLUGIN        start with the given plugin

The combination of positional argument `tree` and `-image_out IMAGE_OUT` can be used to draw tidy bracket trees without launching Kataja UI:   

    python -m kataja -image_out abc.pdf "[A [B C]]"

Drawing will use Kataja's current preferences file. 

At this point the preferences file often breaks with new version -- I assume that no-one is yet using this in such serious manner that avoiding this would be worth the effort. The easy way to fix broken preferences file is to not load it, and let Kataja create a new one and overwrite the old one. This can be done with:   

    python -m kataja --reset_prefs

Also there is 

    python -m kataja --no_prefs
    
for cases when the access to location where preferences files are loaded and saved is providing problems.

The current active plugin is saved into Kataja preferences and when Kataja is restarted, it will try to load that plugin. Sometimes, especially if integrating a specific Kataja plugin into some script or workflow, you'll want to directly launch with a specific plugin. The plugin names are those defined in plugin's folder's plugin.json. So:

    python -m kataja -plugin Monorail

Would start plugin Monorail, as defined by `./kataja/plugins/Monorail/plugin.json`   

# What is it about?

Kataja is built to help me experiment with syntactic models with minimalistic or biolinguistic flavor. These are models that attempt to create syntactic phenomena recognizable by linguists from more primitive operations. These operations should be as simple as possible and sensible for the subject matter. In practice these operations are varieties of Merge, following Chomsky (1995) and later variants.  A model by itself is often an inert object, unless we have ways to provide some input into model or challenge it somehow. Syntactic models are often closely associated to some parser that uses the model. A parser is fed sentences, and the model states what can be done with the elements of the sentence. Though the models itself aim for few simple operations, models in action rely on repetitive and recursive use of these operations, creating complex and hard to track interactions. Kataja aims to help visualie these interactions and the workings of the model/parser. It assumes that the model provides _syntax states_. These states it freezes, stores and visualizes, and provides tools for navigating between states.          

 
3rd party resources
-------------------

There are few things that make Kataja so much better:

Apostolos Syropoulos: Asana Math Font.
http://www.ctan.org/pkg/asana-math

Ethan Schoonover: Solarized colors 
http://ethanschoonover.com/solarized

W3C: Unicode characters to LaTeX -mapping
http://www.w3.org/TR/unicode-xml/ 
