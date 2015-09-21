**GUI2Exe** is a Graphical User Interface frontend to all the "executable builders" available for the Python programming language. It can be used to build standalone Windows executables, Linux applications and Mac OS application bundles and plugins starting from Python scripts.


![http://img413.imageshack.us/img413/5804/gui2exesplashaq7.png](http://img413.imageshack.us/img413/5804/gui2exesplashaq7.png)


## News ##

  * **07 May 2012** Version 0.5.3 released, correcting some major flaws in the user interface, mostly due to changes in wxPython 2.9
  * **05 May 2012** Version 0.5.2 released
  * **24 Aug 2011** Version 0.5.1 released
  * **16 Oct 2009** Version 0.5.0 released
  * **06 Oct 2009** Version 0.4.0 released
  * **05 Feb 2009** Version 0.3 released
  * **21 Oct 2008** Version 0.2 released


## What is **GUI2Exe** ##

**GUI2Exe** is my first attempt to unify all the available "executable builders" for Python in a single and simple to use graphical user interface. At the moment the supported executable builders are:

  * py2exe;
  * py2app;
  * PyInstaller;
  * cx\_Freeze;
  * bbFreeze;
  * vendorID.


## Description ##

The aim of **GUI2Exe** was (for me) to create a wxPython GUI tool that unifies and simplifies various standalone executable builders for Python, such as py2exe, py2app, cx\_Freeze, etc...

Currently **GUI2Exe** is under heavy development, I will provide only Python source code for the moment, which can be grabbed from googlecode using any SVN tool available.


## Requirements ##

Running **GUI2Exe** using Python requires:

  1. Python 2.4+ ;
  1. wxPython 2.8.8.0+ ansi/unicode (unicode recommended);
  1. One (or more) of the Python executable builders;
  1. The bsddb module (it's in the standard library on most Python installations).


## Important Note ##

**GUI2Exe** is **not** meant to be installed as site-package with this command:

```
python Setup.py install
```

Nor to be compiled as executable. **GUI2Exe** should be used as-is, like a normal Python file, i.e., double-clicking on the `GUI2Exe.py` file on Windows or writing:

```
python GUI2Exe.py
```


## Downloads ##

Use "Featured Downloads" on the right hand side. For more options and information, go to the [Downloads](http://code.google.com/p/gui2exe/downloads/list) tab.


## Features ##

**GUI2Exe** has a number of features, namely:

  * Saves and stores your work in a database, displaying all your projects in a tree control;
  * Possibility to export the Setup.py file, even though you shouldn't ever need anymore to have a Setup.py file, as everything is done automagically inside **GUI2Exe**;
  * Ability to change the Python version to use to build the executable;
  * Allows the user to insert custom Python code in the "in-memory" Setup.py file, which will be properly included at runtime during the building process;
  * Allows the user to add post-processing custom code, which will be executed at the end of the building process. Useful for cleaning up;
  * Possibility to view the full build output coming from the compiler;
  * Allows the user to add data\_files (for the executable builders that support this option) either by selecting a bunch of files all together or using a directory-recursive approach, which will include all files and sub-folders in the selected folders as data\_files;
  * "Super" tooltips for the users to better understand the various options;
  * **GUI2Exe** projects can be saved also to a file (and not only in the database): the exported project may then be checked into version control software like CVS or SVN, modified and then reloaded into **GUI2Exe**;
  * Ability to test the executable: if the executable crashes, **GUI2Exe** will notice it and report to you the traceback for inspection;
  * **py2exe-only**: After a building process, choosing the menu Builds => Missing modules or Builds => Binary dependencies, you will be presented respectively with a list of modules py2exe thinks are missing or a list of binary dependencies (dlls) py2exe has found;
  * **py2exe-only**: Possibility to use UPX compression on dlls/exes while compiling;
  * **py2exe-only**: Automatic generation of simple Inno Setup scripts;
  * **py2exe-only**: Support for more keywords in the Target class (i.e., all distutils keywords are now supported);
  * **py2exe-only**: Easy access to the most recent error log file via the menu Builds => Examine error log file;
  * Easy access to the distribution folder via the menu Builds => Open distribution folder;
  * **py2exe-only**: A new distribution folder "Explorer" dialog allows to check which PYDs and DLLs are included, and to quickly exclude them and then rebuild the script, with "undo" capabilities;
  * **py2exe-only**: Support for services, com\_servers and ctypes\_com\_servers (testers required!!);
  * Ability to switch between standard menus and custom FlatMenus (MSW and GTK only);
  * Support for a pure-Python RibbonBar in place of the standard menus (MSW only).


And much more :-D