# GUI2Exe Examples #

## Introduction ##

Hereafter I show a couple of examples on how to use GUI2Exe.


## Simple one ##

We will build the sample file that comes with py2exe, on:

`/site-packages/py2exe/sample/singlefile/gui/test_wx.py`

  1. With the GUI opened, hit **Ctrl+N** or choose **File => New project...** ;
  1. Enter a name for the new project, i.e. _"pyexe sample file"_;
  1. In the central window that appears, under the **Target Class** box, right click on the list control and select "Add item(s)";
  1. Left click on the new item in **Exe Kind** column and select _"windows"_;
  1. Left click on the new item in the **Python Main Script** column and browse to search for the aforementioned file;
  1. On the **Optimize**, **Compressed** and **Bundle Files** drop down choices, choose 2, 2, 1 respectively;
  1. Scroll down the central window to the bottom and check the **XP Manifest File** option;
  1. Click on the **Compile** button.

And you're done. You can follow the compilation steps in the bottom log window as py2exe builds your executable.


---


## Less simpler one ##

We will build the **wxPython demo** as executable, using py2exe.

  1. With the GUI opened, hit **Ctrl+N** or choose **File => New project...** ;
  1. Enter a name for the new project, i.e. _"wxPython demo"_;
  1. In the central window that appears, under the **Target Class** box, right click on the list control and select "Add item(s)";
  1. Left click on the new item in **Exe Kind** column and select _"windows"_;
  1. Left click on the new item in the **Python Main Script** column and browse to search for the file `/YourPathToTheDemo/demo/Main.py`;
  1. On the **Optimize**, **Compressed** and **Bundle Files** drop down choices, choose 2, 2, 1 respectively;
  1. Check the **Dist Directory** checkbox and write a new name for the distribution directory in the text box below (i.e., _"py2exe"_);
  1. On the **Packages** list, hit Ctrl+A twice and edit the items to be `wx` and `wx.lib` respectively;
  1. On the **Data Files** list, hit Ctrl+A, browse with the file dialog to `/YourPathToTheDemo/demo/bitmaps` and select all the files. Do the same thing for the folders bmp\_source and data.
  1. On the **Data Files** list, hit Ctrl+A, browse with the file dialog to `/YourPathToTheDemo/demo` and select all the files. In the dialog which will appear next simply write "." (a dot);
  1. Scroll down the central window to the bottom and check the **XP Manifest** File option;
  1. Click on the **Compile** button.

And you're done. You can follow the compilation steps in the bottom log window as py2exe builds your executable.