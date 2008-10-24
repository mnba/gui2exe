.. -*- coding: UTF-8 -*-

=======
GUI2Exe
=======

.. rubric:: **GUI2Exe** is a Graphical User Interface frontend to all the "executable builders" 
   available for the Python programming language. 


**GUI2Exe** can be used to build standalone Windows executables, Linux applications and Mac OS 
application bundles and plugins starting from Python scripts.


What is GUI2Exe
---------------

The aim of **GUI2Exe** was (for me) to create a wxPython GUI tool that unifies and simplifies 
various standalone executable builders for Python, such as py2exe, py2app, cx_Freeze, etc... 
At the moment the supported executable builders are: 

* `py2exe <http://www.py2exe.org/>`_
* `py2app <http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html>`_
* `PyInstaller <http://pyinstaller.python-hosting.com/>`_
* `cx_Freeze <http://cx-freeze.sourceforge.net/>`_
* `bbFreeze <http://pypi.python.org/pypi/bbfreeze>`_

If any executable builder has been left out, please let me know.


Requirements
------------

Running **GUI2Exe** using Python requires: 

1. Python 2.3+ ; 
2. wxPython 2.8.8.0+ ansi/unicode (unicode recommended); 
3. One (or more) of the Python executable builders. 



Features
--------

**GUI2Exe** has a number of features, namely: 

* Saves and stores your work in a database, displaying all your projects in a tree control; 
* Possibility to export the ``setup.py`` file, even though you shouldn't ever need anymore to have 
  a ``setup.py`` file, as everything is done automagically inside **GUI2Exe**; 
* Ability to change the Python version to use to build the executable; 
* Allows the user to insert custom Python code in the "in-memory" ``setup.py`` file, which will be 
  properly included at runtime during the building process; 
* Allows the user to add post-processing custom code, which will be executed at the end of the building
  process. Useful for cleaning up; 
* Possibility to view the full build output coming from the compiler; 
* Allows the user to add *data_files* (for the executable builders that support this option) either by 
  selecting a bunch of files all together or using a directory-recursive approach, which will include 
  all files and sub-folders in the selected folders as *data_files*; 
* "Super" tooltips for the users to better understand the various options; 
* Periodically saves projects if required (AutoSave feature);
* **GUI2Exe** projects can be saved also to a file (and not only in the database): the exported project 
  may then be checked into version control software like *CVS* or *SVN*, modified and then reloaded into 
  **GUI2Exe**; 
* Ability to test the executable: if the executable crashes, **GUI2Exe** will notice it and report to you 
  the traceback for inspection; 
* *[py2exe-only]*: After a building process, choosing the menu ``Builds`` => ``Missing modules`` or ``Builds`` => 
  ``Binary dependencies``, you will be presented respectively with a list of modules ``py2exe`` thinks are 
  missing or a list of binary dependencies (dlls) ``py2exe`` has found. 

And much more :-D 



OK, I'm interested. What do I do next?
--------------------------------------

You can download a `source package of GUI2Exe
<http://code.google.com/p/gui2exe/downloads/list>`_ which includes
the source code for **GUI2Exe**.

At some point, you will want to do something with **GUI2Exe** and it won't be
immediately obvious how to make it happen. After dutifully scouring the `Wiki Pages
<http://code.google.com/p/gui2exe/w/list>`_ examples section, you
decide that is is still not obvious. The `Forum
<http://groups.google.com/group/gui2exe>`_ is the place to find
all your as-yet-unasked questions.

It may even be possible that you might find some undocumented features in the code (also
known as bugs). These "features" can be reported to the `project's Issue Tracker
<http://code.google.com/p/gui2exe/issues/list>`_.

If you would like to ask me a question or suggest an improvement, you can post a message
on the **GUI2Exe** mailing list:

gui2exe@googlegroups.com 

Or you can always write directly to me at:

andrea.gavana@gmail.com


Bleeding-edge source
--------------------

If you are a very keen developer, you can access the SVN repository directly for this
project. The following SVN commands will fetch the most recent version from the repository:

*For developers:*
``svn checkout https://gui2exe.googlecode.com/svn/trunk/ gui2exe --username YOUR_USERNAME``
  
When prompted, enter your generated googlecode.com password. 

*For anonymous checkout:*
``svn checkout http://gui2exe.googlecode.com/svn/trunk/ gui2exe-read-only``
  
The Google code subversion repository can be accessed using many different `client programs
<http://subversion.tigris.org/links.html#clients>`_

Please remember that code within the SVN is bleeding edge. It has not been well-tested and
is almost certainly full of bugs. If you are storing important project setups in **GUI2Exe**, it's
better to stay with the official releases, where the bugs are (hopefully) less obvious.


Site contents
-------------

.. toctree::
   :maxdepth: 1

   whatsnew
   majorClasses
