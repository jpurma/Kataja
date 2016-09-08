---
layout: page
title: Download
---

Kataja can be run as a prebuilt desktop application in Windows<a href="#win10">*</a> or Mac OSX or run directly from source code in Windows, OSX or Linux environments. You can download prebuilt binaries here.

{% include image name="katajaicon.png" %}

## Kataja v. 0.8

 * download Windows 10 Kataja, 64bit 
 * download Mac OS X Kataja, 64bit 

<div class="message">
In current state of development I cannot guarantee that save files across different versions remain usable.
</div>

<a name="win10">*</a>Tested with Windows 10, backwards compatibility is uncertain.

## Kataja.app in macOS / OS X

1. Download Kataja.dmg from link above, double click to open it. 
2. Drag Kataja -application to your Applications-folder. 
3. Double click Kataja.app to launch it.

Like any well-behaving Mac app, Kataja will on first run create a folder to `~/Library/Application Support/Kataja` and a preferences file in `~/Preferences/fi.purma.Kataja.plist`. The Application Support folder will include folder `plugins`, which is the easiest way to extend Kataja. 

## Kataja.exe in Windows

1. Download katajainstaller.exe from link above, double click to open it. 
2. Run the installer by double clicking it. 
3. Start Kataja by double clicking new Kataja.exe or by choosing it from start menu. 

## Running from source code

This option means setting up development environment for Kataja. As Kataja is all python code, the development environment can be easily used for daily linguistic work, teaching or studying: there is no separate build phase for launching Kataja, Kataja can always be launched from terminal in Kataja directory with command `python3 Kataja.py`. 

Until stabilized, Kataja will be using the latest versions available from Qt and PyQt in order to benefit from performance improvements and bug fixes.

Here are the preparations you need to do before Kataja can be run:

### Install Python3.5 ###

You will need Python 3.5 or greater for easy install of Kataja's dependencies (PyQt5) with Python Wheels. Check your python3 version in Terminal with: 

    python3 --version
    
If the version starts with 3.5, good, otherwise run the latest python 3.x installer from [http://python.org](http://python.org) 

### Use Wheels to install Qt5.x, SIP and PyQt5 ###

A new easy method to install necessary dependencies is made possible with Python 3.5 and Python Wheels. Try: 

    pip3 install pyqt5 

If it results in PermissionError: permission denied, try again with sudo:

    sudo pip3 install pyqt5 

This will install open source versions of Qt and PyQt, just what you needed.

If you really want to use Python 3.4 or pip3-based install fails from some other reasons, download PyQt5 and SIP from [http://www.riverbankcomputing.com/](http://www.riverbankcomputing.com/) and follow instructions there (Software -> PyQt -> PyQt5 Reference Guide -> Building and Installing from Source)

### Download Kataja source and run Kataja ###

get your own copy of Kataja source files with either "Clone in Desktop" or "Download ZIP" in [https://github.com/jpurma/Kataja](https://github.com/jpurma/Kataja).
 
Navigate to Kataja -folder with terminal, and in there:

    python3 Kataja.py
    
 





