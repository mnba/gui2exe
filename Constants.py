########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

import wx
from Resources import *

# Get the translation thing
_ = wx.GetTranslation

_defaultCompilers = ["py2exe", "py2app", "cx_Freeze", "PyInstaller", "bbfreeze", "vendorid"]

ListType = type([])

_lbStyle = INB_BORDER | INB_USE_PIN_BUTTON | INB_RIGHT | INB_GRADIENT_BACKGROUND | INB_FIT_BUTTON

_auiImageList = ["project_ok", "project_unsaved", "project_broken"]
_treeIcons = ["project_home", "project", "project_edit"]
_iconFromName = {"includes": ["modules"],
                 "excludes": ["modules"],
                 "ignores": ["modules"],
                 "packages": ["packages"],
                 "dll_excludes": ["dllicon"],
                 "data_files": ["datafiles"],
                 "icon_resources": ["icon"],
                 "bitmap_resources": ["bitmap"],
                 "other_resources": ["resource"],
                 "messages": ["message_info", "message_warning", "message_error",
                              "message_find", "message_compile", "message_copy",
                              "message_skip", "message_filter", "message_compress",
                              "message_ccode", "message_link"],
                 "missingmodules": ["missingmodules"],
                 "binarydependencies": ["binarydependencies"],
                 "multipleexe": ["python"],
                 "scripts": ["python"],
                 "dll_includes": ["dllicon"],
                 "pathex": ["pathicon"],
                 "hookspath": ["hooksicon"],
                 "path": ["pathicon"],
                 "frameworks": ["frameworks"],
                 "dylib_excludes": ["dylib"],
                 "datamodels": ["datamodels"],
                 "resources": ["datafiles"],
                 "extrakeywords": ["keywords2", "values"],
                 "explorerdll": ["dllicon", "file_size"],
                 "explorerpyd": ["pydicon", "file_size"]
                 }

_unWantedLists = ["messages", "missingmodules", "binarydependencies", "explorerdll", "explorerpyd"]
_bookIcons = ["py2exe", "py2app", "cx_Freeze", "PyInstaller", "bbFreeze", "VendorID"]
_iconMapper = {"Message": 0, "Warning": 1, "Error": 2, "Find": 3, "Compile": 4,
               "Copy": 5, "Skip": 6, "Filter": 7, "Compress": 8}
_sizeIcons = ["py2exe_small", "py2app_small", "cx_Freeze_small", "PyInstaller_small",
              "bbFreeze_small", "VendorID_small", "file_size", "numfiles"]

_distutilsKeys = {"description": "", "long_description": "", "author": "", "author_email": "",
                  "maintainer": "", "maintainer_email": "", "url": "", "download_url": "",
                  "license": ""}

_distutilsTips = {"description": "A single line describing the package",
                  "long_description": "Longer description of the package",
                  "author": "The name of the package author",
                  "author_email": "The email address of the package author",
                  "maintainer": "The name of the current maintainer, if different from the author",
                  "maintainer_email": "The email address of the current maintainer, if different from the author",
                  "url": "A URL for the package (homepage)",
                  "download_url": "A URL to download the package",
                  "license": "The license for the package"}

_stcKeywords = ["includes", "excludes", "ignores", "packages", "dll_excludes", "data_files",
                "icon_resources", "bitmap_resources", "other_resources", "dest_base",
                "initScript", "base", "targetDir", "targetName", "compress", "script", 
                "copyDependentFiles", "appendScriptToExe", "appendScriptToLibrary", "icon",
                "dll_includes", "pathex", "hookspath", "exclude_binaries", "name", "debug",
                "console", "strip", "upx", "version", "options", "level", "path",
                "executables", "description", "author", "dylib_excludes", "frameworks",
                "datamodels", "resources", "iconfile", "plist", "extension", "graph",
                "no_chdir", "no_strip", "semi_standalone", "argv_emulation", "use_pythonpath",
                "site_packages", "prefer_ppc", "debug_modulegraph", "debug_skip_macholib", "zipfile",
                "windows", "com_server", "service", "ctypes_com_server", "company_name", "copyright",
                "create_exe", "create_dll"] + _distutilsKeys.keys()

_pywild = "Python source (*.py)|*.py"
_pywildspec = "Python source (*.py)|*.py|" \
              "PyInstaller spec (*.spec)|*.spec"
_iconwild = "Icon files (*.icns)|*.icns"
_plistwild = "PList files (*.plist)|*.plist"
_dylibwild = "Dylib/Framework files (*.dylib, *.framework)|*.dylib;*.framework"
_xcdatawild = "XC Data Models files (*.xcdatamodels)|*.xcdatamodels"
_pypackages = "Python packages (*.pkg)|*.pkg"
_dllbinaries = "DLL/Binary files (*.dll, *.exe)|*.dll;*.exe"  \
               "All files (*.*)|*.*"

_pyInstallerTOC = {"includes": "PYMODULE",
                   "packages": "PKG",
                   "dll_excludes": "BINARY",
                   "dll_includes": "BINARY",
                   "data_files": "DATA"}

_pyInstallerOptions = [("v", "", "OPTION"), ("W ignore", "", "OPTION"), ("f", "", "OPTION"),
                       ("u", "", "OPTION"), ("s", "", "OPTION"), ("O", "", "OPTION")]


_comboImages = {"py2exe": {"bundle_files": ["bundle"]*3,
                           "optimize": ["optimize"]*3,
                           "compressed": ["compress"]*3,
                           "exekind": ["windows", "console"]
                           },
                "cx_Freeze": {"base": ["windows", "console"],
                              "optimize": ["optimize"]*3,
                              "compress": ["compress"]*2
                              },
                "py2app": {"extension": ["frameworks", "dylib"],
                           "optimize": ["optimize"]*3
                           },
                "PyInstaller": {"level": ["compress"]*10
                                },
                "bbfreeze": {"gui_only": ["windows", "console"],
                             "compress": ["compress"]*2,
                             "optimize": ["optimize"]*3
                             },
                "vendorid": {"optimize": ["optimize"]*3}
                }
                           
_bpPngs = [[_("New Child"), "new_child", _("Append a new tree item to the selected item")],
           [_("New Sibling"), "new_sibling", _("Add a new tree item below the selected item")],
           [_("Duplicate"), "duplicate", _("Duplicates the selected tree item")],
           [_("Delete"), "delete", _("Deletes the selected tree item (and everything below)")]]

if wx.Platform == '__WXMSW__':
    _faces = { 'times': 'Times New Roman',
               'mono' : 'Courier New',
               'helv' : 'Arial',
               'other': 'Comic Sans MS',
               'size' : 10,
               'size2': 8,
             }
elif wx.Platform == '__WXMAC__':
    _faces = { 'times': 'Times New Roman',
               'mono' : 'Courier New',
               'helv' : 'Arial',
               'other': 'Comic Sans MS',
               'size' : 12,
               'size2': 10,
             }
else:
    _faces = { 'times': 'Times',
               'mono' : 'Courier',
               'helv' : 'Helvetica',
               'other': 'new century schoolbook',
               'size' : 12,
               'size2': 10,
             }


def GetTooltips():

    _toolTips = {"py2exe": {"optimize": _("Optimization level for the compiled bytecode.\n\n0: No optimization on the compiled bytecode;\n1 (Python -O): Optimize the generated bytecode;\n2 (Python -OO): remove doc-strings in addition to the -O optimizations."),
                        "compressed": _("Creates a compressed zip archive (zipfile).\n\nIt can be either 0 or a positive number, the meaning of\nactivating/deactivating the compression is as follows:\n\n- No Compression: the zipfile will be created using the\n  zipfile.ZIP_STORED Python option;\n- With Compression: the zipfile will be created using the\n  zipfile.ZIP_DEFLATED Python option.<note>If you specify the Skip Archive option, compression can not\nbe activated (no zipfile to compress)."),
                        "bundle_files": _("Bundling options for the final dist directory.\n\n- Level 1: includes the .pyd and .dll files into the zip-archive\n  or the executable itself, and does the same for pythonXY.dll;\n- Level 2: includes the .pyd and .dll files into the zip-archive\n  or the executable;\n- Level 3: default for py2exe. No pyd or dll is bundled in the exe\n  or in the zip-archive.<note>The Bundle Files option is currently not available on 64\nbit machines."),
                        "zipfile_choice": _("By activating this option in GUI2Exe, you can specify a name\nfor the compressed zip file where py2exe will put all the\nbytecode-compiled Python modules. If you don't activate\nthis option, or the zipfile name is empty, the default in GUI2Exe\nis to use zipfile=None. This means the compiled bytecode will be\nattached to the executable itself and no zip file will be created.<note>If you specify the Skip Archive option, zipfile can not be\nNone."),
                        "dist_dir_choice": _("If you activate this switch, you will be able to\nspecify the name the directory to put final built\ndistributions in (the default is 'dist')."),
                        "skip_archive": _("By choosing this option, py2exe will copy\nthe Python bytecode files directly into the dist\ndirectory (or in the excutable itself). No zipfile\narchive is used."),
                        "manifest_file": _("Creates a file that instructs Windows on how to correctly\nrender the widgets in your user interface. This file lives\nunder 'other_resources' in py2exe."),
                        "xref": _("This command line switch instructs py2exe to create a Python\nmodule cross reference and display it in the webbrowser.\nThis allows to answer question why a certain module\nhas been included, or if you can exlude a certain module\nand its dependencies."),
                        "ascii": _("To prevent unicode encoding error, py2exe now by default\nincludes the codecs module and the encodings package.\nIf you are sure your program never implicitely or explicitely\nhas to convert between unicode and ascii strings this can be\nprevented by switching on this option in its associated\ncheck box in GUI2Exe."),
                        "custom_boot_script": _("By selecting a file for this option, your custom\nPython file can do things like installing a customized\nstdout blackhole. The custom boot script is executed\nduring startup of the executable immediately after\nboot_common.py is executed."),
                        "multipleexe": _("Add a new list item by hitting Ctrl+A and click on the\nthird list control column to select your Python Main\nScript.\n\nYou can change the executable kind (windows,\nconsole, com_server, service or ctypes_com_server)\nby clicking on the second list control column,\nand modify other property of your target class as well."),
                        "includes": _("Comma-separated list of Python modules to include.\n\nHit Ctrl+A to add a new item in the list and edit it.<note>The Includes option is stronger than the Excludes one.\nSo, if a module is present in both Includes and Excludes,\nit will be included in your final distribution."),
                        "excludes": _("Comma-separated list of Python modules to exclude.\n\nHit Ctrl+A to add a new item in the list and edit it.<note>The Includes option is stronger than the Excludes one.\nSo, if a module is present in both Includes and Excludes,\nit will be included in your final distribution."),
                        "packages": _("Comma-separated list of Python packages to include.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "ignores": _("Comma-separated list of Python modules to ignore\nif they are found during the building process.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "dll_excludes": _("Comma-separated list of DLLs to exclude.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "data_files": _("Py2exe allows you to include one (or more) series of files\nthat you are going to need to run your executable\n\nDepending on the choice in the menu 'Options' ==>\n'Recurse sub-dirs for DATA files option' there are\n2 possibilities:\n\n- Choose multiple files at once;\n- Choose one or more directories: every file in them\n  will be added recursively.\n\nHit Ctrl+A to add data files to the list."),
                        "icon_resources": _("Add a custom icon to your application.\nThe icon will be shown in Windows Explorer.\n\nHit Ctrl+A to add an item to the list and edit it."),
                        "bitmap_resources": _("Add one or more bitmaps as Windows resources,\nso that they get packaged in the executable.\n\nHit Ctrl+A to add an item to the list and edit it."),
                        "other_resources": _("Insert a custom named resource into the executable.\n\nHit Ctrl+A to add an item to the list and edit it."),
                        "create_exe": _("Force py2exe to create an executable file.<note>This option is only valid for services,\ncom_servers and ctypes_com_servers."),
                        "create_dll": _("Force py2exe to create a dll file.<note>This option is only valid for services,\ncom_servers and ctypes_com_servers."),                            
                        },
             "cx_Freeze": {"version": _("Your program version."),
                           "description": _("A short description of your application."),
                           "author": _("Information about the programmer."),
                           "name": _("The program name"),
                           "base": _("Depends on the kind of executable you wish to build:\n\n- windows: builds an executable for a GUI-based application;\n- console: creates an executable for a console program\n  (i.e., no graphical interface stuff involved)."),
                           "script": _("The Python main script you want to convert\nto an executable."),
                           "optimize": _("Optimization level for the compiled bytecode.\n\n0: No optimization on the compiled bytecode;\n1 (Python -O): Optimize the generated bytecode;\n2 (Python -OO): remove doc-strings in addition to the -O optimizations."),
                           "compress": _("Creates a compressed zip file."),
                           "target_name_choice": _("The name of the target executable; the default value is\nthe name of the script with the extension exchanged with\nthe extension for the base executable."),
                           "dist_dir_choice": _("The directory in which to place the target executable and\nany dependent files."),
                           "copy_dependent_files": _("Boolean value indicating if dependent files should be\ncopied to the target directory or not."),
                           "append_script_toexe": _("Boolean value indicating if the script module should be\nappended to the executable itself."),
                           "append_script_tolibrary": _("Boolean value indicating if the script module should\nbe appended to the shared library zipfile."),
                           "create_manifest_file": _("On Windows, it creates a manifest file that instructs\nWindows on how to correctly render the widgets in your\nuser interface."),
                           "icon": _("Name of icon which should be included in the executable\nitself on Windows or placed in the target directory for\nother platforms."),
                           "initScript": _("The name of the initialization script that will be executed\nbefore the actual script is executed; this script is used to\nset up the environment for the executable; if a name is given\nwithout an absolute path the names of files in the initscripts\nsubdirectory of the cx_Freeze package is searched."),
                           "includes": _("List of names of modules to include.\n\nHit Ctrl+A to add an item to the list and edit it."),
                           "excludes": _("List of names of modules to exclude.\n\nHit Ctrl+A to add an item to the list and edit it."),
                           "packages": _("List of names of packages to include, including all\nof the package's submodules.\n\nHit Ctrl+A to add an item to the list and edit it."),
                           "path": _("List of paths to search for modules.\n\nHit Ctrl+A to select one or more directories."),
                           "multipleexe": _("Add a new list item by hitting Ctrl+A and click on the\nthird list control column to select your Python Main\nScript.\n\nYou can change the executable kind (windows or\nconsole) by clicking on the second list control column,\nand modify other property of your target class as well.")
                           },
             "bbfreeze": {"script": _("The Python main script you want to convert\nto an executable."),
                          "optimize": _("Optimization level for the compiled bytecode.\n\n0: No optimization on the compiled bytecode;\n1 (Python -O): Optimize the generated bytecode;\n2 (Python -OO): remove doc-strings in addition to the -O optimizations."),
                          "compress": _("Creates a compressed zip file."),
                          "dist_dir_choice": _("The directory in which to place the target executable and\nany dependent files."),
                          "gui_only": _("The gui_only flag only has a meaning on Windows: If set, the\nexecutable created for this script will not open a console window."),
                          "include_py": _("Flag whether to create the included python interpreter."),
                          "create_manifest_file": _("On Windows, it creates a manifest file that instructs\nWindows on how to correctly render the widgets in your\nuser interface."),
                          "includes": _("List of names of modules to include.\n\nHit Ctrl+A to add an item to the list and edit it."),
                          "excludes": _("List of names of modules to exclude.\n\nHit Ctrl+A to add an item to the list and edit it."),
                          "multipleexe": _("Add a new list item by hitting Ctrl+A and click on the\nthird list control column to select your Python Main\nScript.\n\nYou can change the executable kind (windows or\nconsole) by clicking on the second list control column,\nand modify other property of your target class as well.")
                          },
             "PyInstaller": {"debug": _("Setting to 1 gives you progress messages from the executable\n(for a console=0, these will be annoying MessageBoxes)."),
                             "console": _("Always 1 on Linux/unix. On Windows, governs whether to use\nthe console executable, or the Windows subsystem executable."),
                             "strip": _("The executable and all shared libraries will be run through\nstrip.<note>Note that cygwin's strip tends to render normal Win32\ndlls unusable."),
                             "upx": _("If you have UPX installed (detected by Configure), this will use\nit to compress your executable (and, on Windows, your dlls)"),
                             "icon": _("Windows NT family only. icon='myicon.ico' to use an icon file."),
                             "version": _("Windows NT family only. version='myversion.txt'.<note>Use the PyInstaller Python file 'GrabVersion.py' to steal a\nversion resource from an executable, and then edit the output to create\nyour own. (The syntax of version resources is so arcane that I\nwouldn't attempt to write one from scratch)."),
                             "onefile": _("Produces a single file deployment."),
                             "onedir": _("Produces a single directory deployment (default)."),
                             "exename": _("The filename for the executable."),
                             "ascii": _("Ddo not include encodings.<note>The default (on Python versions with unicode support)\nis now to include all encodings."),
                             "dist_dir": _("The directory in which to place the target executable and\nany dependent files.<note>This is used only when 'onedir' is set to 1."),
                             "includetk": _("Include TCL/TK in the deployment."),
                             "level": _("The Zlib compression level to use.\n\nIf 0, the zlib module is not required."),
                             "create_manifest_file": _("On Windows, it creates a manifest file that instructs\nWindows on how to correctly render the widgets in your\nuser interface."),
                             "scripts": _("A list of scripts specified as file names.\n\nHit Ctrl+A to select one or more Python files."),
                             "includes": _("List of names of modules to include.\n\nHit Ctrl+A to select one or more Python modules."),
                             "excludes": _("List of names of modules to exclude.\n\nHit Ctrl+A to select one or more Python modules."),
                             "pathex": _("An optional list of paths to be searched before sys.path.\n\nHit Ctrl+A to select one or more directories."),
                             "hookspath": _("An optional list of paths used to extend the hooks package.\n\nHit Ctrl+A to select one or more directories."),
                             "dll_excludes": _("An optional list of binary files to exclude.\n\nHit Ctrl+A to select one or more binary files."),
                             "dll_includes": _("An optional list of binary files to include.\n\nHit Ctrl+A to select one or more binary files."),
                             "data_files": _("Arbitrary files to include in your distribution.\n\nDepending on the choice in the menu 'Options' ==>\n'Recurse sub-dirs for DATA files option' there are\n2 possibilities:\n\n- Choose multiple files at once;\n- Choose one or more directories: every file in them\n  will be added recursively.\n\nHit Ctrl+A to select one or more data files."),
                             "packages": _("List of names of packages to include.\n\nHit Ctrl+A to select one or more Python packages."),
                             "option1": _("Verbose imports (same as Python -v)."),
                             "option2": _("Warning option (Python 2.1+)."),
                             "option3": _("Force execpv (Linux/Unix only).\n\nEnsures that LD_LIBRARY_PATH is set properly."),
                             "option4": _("Unbuffered STDIO (same as Python -u)."),
                             "option5": _("Use site.py.\n\nThe opposite of Python -S.<note>Note that site.py must be in the executable's\ndirectory to be used."),
                             "option6": _("Build optimized.\n\nPyInstaller will gather *.pyo files\nif it is run optimized.")
                             },
             "py2app": {"script": _("The Python main script you want to convert\nto an executable."),
                        "dist_dir": _("Directory to put final built distributions in\n(default is dist)."),
                        "optimize": _("Optimization level for the compiled bytecode.\n\n0: No optimization on the compiled bytecode;\n1 (Python -O): Optimize the generated bytecode;\n2 (Python -OO): remove doc-strings in addition to the -O optimizations."),
                        "iconfile": _("Icon file to use for your application."),
                        "plist": _("Info.plist template file."),
                        "extension": _("Bundle extension (default: '.app' for app, '.plugin'\nfor plugins)."),
                        "graph": _("Output module dependency graph."),
                        "xref": _("This command line switch instructs py2app to create a Python\nmodule cross reference and display it in the webbrowser.\nThis allows to answer question why a certain module\nhas been included, or if you can exlude a certain module\nand its dependencies."),
                        "no_strip": _("Do not strip debug and local symbols from output."),
                        "no_chdir": _("Do not change to the data directory (Contents/Resources).<note> This is forced for plugins."),
                        "semi_standalone": _("Depend on an existing installation of Python 2.4+."),
                        "argv_emulation": _("Use argv emulation.<note> This is disabled for plugins."),
                        "use_pythonpath": _("Allow PYTHONPATH to effect the interpreter's environment."),
                        "site_packages": _("Include the system and user site-packages into sys.path."),
                        "prefer_ppc": _("Force application to run translated on i386."),
                        "debug_modulegraph": _("Drop to pdb console after the module finding phase is complete."),
                        "debug_skip_macholib": _("Skip macholib phase.<note>Your App will not be standalone."),
                        "resources": _("Py2app allows you to include one (or more) series of files\nthat you are going to need to run your executable\n\nDepending on the choice in the menu 'Options' ==>\n'Recurse sub-dirs for DATA files option' there are\n2 possibilities:\n\n- Choose multiple files at once;\n- Choose one or more directories: every file in them\n  will be added recursively.\n\nHit Ctrl+A to add data files to the list."),
                        "includes": _("Comma-separated list of Python modules to include.\n\nHit Ctrl+A to add a new item in the list and edit it.<note>The Includes option is stronger than the Excludes one.\nSo, if a module is present in both Includes and Excludes,\nit will be included in your final distribution."),
                        "excludes": _("Comma-separated list of Python modules to exclude.\n\nHit Ctrl+A to add a new item in the list and edit it.<note>The Includes option is stronger than the Excludes one.\nSo, if a module is present in both Includes and Excludes,\nit will be included in your final distribution."),
                        "packages": _("Comma-separated list of Python packages to include.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "dylib_excludes": _("Comma-separated list of frameworks or dylibs to\nexclude.\n\nHit Ctrl+A to select one or more dylibs or frameworks."),
                        "datamodels": _("xcdatamodels to be compiled and copied into\nResources.\n\nHit Ctrl+A to select one or more xcdatamodels."),
                        "frameworks": _("Comma-separated list of frameworks or dylibs to\ninclude in your distribution.\n\nHit Ctrl+A to select one or more dylibs or frameworks."),
                        "plistCode_choice": _("If activated, it allows you to add/edit PList\ndictionary key/value pairs, or to remove it altogether."),
                        "plistCode": _("Add Plist dictionary key/value pairs or edit\nan existing PList configuration."),
                        "plistRemove": _("Remove existing PList code.")
                        },
           "vendorid": {"script": _("The Python main script you want to convert\nto an executable."),
                        "build_dir": _("Directory to put final built distributions in\n(default is 'build_' + the base name of the python\nmain script without extension)."),
                        "optimize": _("Optimization level for the compiled bytecode.\n\n0: No optimization on the compiled bytecode;\n1 (Python -O): Optimize the generated bytecode;\n2 (Python -OO): remove doc-strings in addition to the -O optimizations."),
                        "exename": _("The filename for the executable."),
                        "build_dir_choice": _("If you activate this switch, you will be able to\nspecify the name the directory to put final built\ndistributions in (the default is 'build_' + the base name\nof the python main script without extension)."),
                        "includes": _("Comma-separated list of Python modules to include.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "packages": _("Comma-separated list of Python packages to include.\n\nHit Ctrl+A to add a new item in the list and edit it."),
                        "install_dir_choice": _("If you activate this switch, you will be able to\nspecify the name the directory to install the\nexecutable (using 'make install') in\n(the default is where Python lives)."),
                        "install_dir": _("Directory where to install the executable in\n(default is where Python lives, sys.exec_prefix)."),
                        "console": _("creates an executable for a console program\n(i.e., no graphical interface stuff involved).<note>This feature is Windows only."),
                        "iconfile": _("Windows NT family only. icon='myicon.ico' to use an icon file."),
                        "signed": _("Default is to create a signed interpreter\n(linked with the vendorid static library)"),
                        "verbose": _("Activates Python's verbose flag (same as Python -v)."),
                        "prefix": _("Use prefix as path prefix for compiled python code.\nDefault is the absolute path of the python source file.<note>This is normally not the path where the executable\nis installed on the target machines. You should use\nsomething like -p '' or -p 'application-name:'.\nSee the Python documentation of the filename argument\nof the builtin compile method for the meaning of prefix.")
                        }
    }
    
    _toolTips["py2exe"]["zipfile"] = _toolTips["py2exe"]["zipfile_choice"]
    _toolTips["py2exe"]["dist_dir"] = _toolTips["py2exe"]["dist_dir_choice"]
    _toolTips["py2app"]["dist_dir_choice"] = _toolTips["py2app"]["dist_dir"]

    _toolTips["cx_Freeze"]["target_name"] = _toolTips["cx_Freeze"]["target_name_choice"]
    _toolTips["cx_Freeze"]["dist_dir"] = _toolTips["cx_Freeze"]["dist_dir_choice"]

    _toolTips["bbfreeze"]["dist_dir"] = _toolTips["bbfreeze"]["dist_dir_choice"]    

    return _toolTips

    
# --------------------------------------------------------------
# PY2EXE SECTION
# --------------------------------------------------------------

_py2exe_imports = '''
# ======================================================== #
# File automagically generated by GUI2Exe version %(gui2exever)s
# Copyright: (c) 2007-2009 Andrea Gavana
# ======================================================== #

# Let's start with some default (for me) imports...

from distutils.core import setup
from py2exe.build_exe import py2exe

import glob
import os
import zlib
import shutil

%(remove_build)s
'''

_manifest_template = '''
manifest_template = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""
'''

_py2exe_class = '''
%s = Target(
    # what to build
    script = "%s",
    icon_resources = icon_resources,
    bitmap_resources = bitmap_resources,
    other_resources = other_resources,
    dest_base = "%s",    
    version = "%s",
    company_name = "%s",
    copyright = "%s",
    name = "%s",
    %s
    )'''

_upx_inno = '''
# Used to build a simple Inno Setup script (courtesy of the wxPython Wiki).

class InnoScript(object):
    """ Class that builds a simple InnoSetup script. """
    
    def __init__(self, name, lib_dir, dist_dir, windows_exe_files=[], console_exe_files=[],
                 lib_files=[], version="0.1"):
        """ Default class constructor. """
        
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir.endswith(os.sep):
            self.dist_dir += os.sep

        self.name = name
        self.version = version
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.console_exe_files = [self.chop(p) for p in console_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]


    def chop(self, pathname):
        """ Returns the path relative to `self.dist_dir`. """
        
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]


    def create(self, pathname=None):
        """ Creates the simple InnoSetup script. """
        
        if pathname is None:
            self.pathname = os.path.join(self.dist_dir, self.name + os.extsep + "iss")
        else:
            self.pathname = pathname

        self.file = open(self.pathname, "w")
        self.file.write("; WARNING: This script has been created by GUI2Exe. Changes to this script" + os.linesep)
        self.file.write("; will be overwritten the next time GUI2Exe is run!" + os.linesep)
        self.file.write(os.linesep)
        self.file.write(r"[Setup]" + os.linesep)
        self.file.write(r"AppName=" + self.name + os.linesep)
        self.file.write(r"AppVerName=" + self.name + " " + self.version + os.linesep)
        self.file.write(r"DefaultDirName={pf}/" + self.name + os.linesep)
        self.file.write(r"DefaultGroupName=" + self.name + os.linesep)
        self.file.write(r"OutputBaseFilename=" + self.name + "-" + self.version + "-setup" + os.linesep)
        self.file.write(os.linesep)
        self.file.write(r"[Files]" + os.linesep)
        for path in self.windows_exe_files + self.console_exe_files + self.lib_files:
            self.file.write(r'Source: "' + path + '"; DestDir: "{app}/' + os.path.dirname(path) + '"; Flags: ignoreversion' + os.linesep)
        self.file.write(os.linesep)
        self.file.write(r"[Icons]" + os.linesep)
        self.file.write(r";This section must be customized and edited as needed!" + os.linesep)
        for path in self.windows_exe_files:
            self.file.write(r';Name: "{group}/' + self.name + '"; Filename: "{app}/' + path + '"' + os.linesep)

        self.file.write(';Name: "{group}/Uninstall ' + self.name + '"; Filename: "{uninstallexe}"' + os.linesep)
        self.file.write(os.linesep)
        

    def compile(self, compilercmd="compile"):
        """ Compiles the script using InnoSetup. """

        import warnings
        
        try:
            import ctypes
        except ImportError:
            try:
                import win32api
            except ImportError:
                os.startfile(self.pathname)
            else:
                win32api.ShellExecute(0, compilercmd, self.pathname, None, None, 0)
        else:
            res = ctypes.windll.shell32.ShellExecuteA(0, compilercmd, self.pathname, None, None, 0)
            if res < 32:
                strs = "Unable to open Inno Setup script. Error code is " + repr(res) + "." + os.linesep
                strs += "Are you sure the `iss` extension is associated to an application?"
                warnings.warn(strs)

                
# Define our own command class based on py2exe so we can perform some
# customizations, and in particular support UPXing the binary files and
# creating simple Inno Setup scripts.

class Py2exe(py2exe):
    """
    Overridden class to handle UPX compression and the creation of simple Inno
    Setup scripts.
    """

    def initialize_options(self):
        """ Initialize the default options for py2exe. """
        
        # Add a new "upx" option for compression with upx
        py2exe.initialize_options(self)
        
        self.upx = %s
        self.inno = %s
        self.upx_checked = False


    def run(self):
        """ Actually run py2exe. """
        
        # First, let py2exe do it's work.
        py2exe.run(self)
        
        if not self.inno:
            return
            
        lib_dir = self.lib_dir
        dist_dir = self.dist_dir
        # create the Installer, using the files py2exe has created.
        script = InnoScript("%s", lib_dir, dist_dir,
                            self.windows_exe_files, self.console_exe_files,
                            self.lib_files, version="%s")
        print "*** creating the Inno Setup script***"
        script.create()
        print "*** compiling the Inno Setup script***"
        script.compile(None)
        # Note: By default the final setup.exe will be in an Output subdirectory.

        
    def has_upx(self):
        """ Returns whether UPX is installed and can be found on the PATH. """

        try:
            os.system('upx --help')
        except OSError, e:
            self.upx = False
            import warnings
            warnings.warn("Unable to find UPX. Are you sure UPX is in your PATH?")

        self.upx_checked = True            

    
    def copy_file(self, *args, **kwargs):
        """ Overridden to allow UPXing of binary files. """
        
        (fname, copied) = result = py2exe.copy_file(self, *args, **kwargs)

        if self.upx and not self.upx_checked:
            self.has_upx()

        if not self.upx:
            return result
            
        basename = os.path.basename(fname)
        if (copied and self.upx and
            (basename[:6]+basename[-4:]).lower() != 'python.dll' and
            fname[-4:].lower() in ('.pyd', '.dll')):
            os.system('upx --best "' + os.path.normpath(fname) + '"')
            
        return result


    def patch_python_dll_winver(self, dll_name, new_winver=None):
        """ Overridden to first check if the file is upx'd and skip if so. """
        
        if not self.dry_run and self.upx:
            if not os.system('upx -qt "' + dll_name + '" > nul'):
                if self.verbose:
                    print "Skipping setting sys.winver for " + dll_name + " (UPX'd)"
            else:
                py2exe.patch_python_dll_winver(self, dll_name, new_winver)
                basename = os.path.basename(dll_name)
                if (basename[:6]+basename[-4:]).lower() == 'python.dll':
                    return
                
                # We UPX this one file here rather than in copy_file so
                # the version adjustment can be successful
                if self.upx:
                    os.system('upx --best "' + os.path.normpath(dll_name) + '"')
'''

_py2exe_target = '''
class Target(object):
    """ A simple class that holds information on our executable file. """
    def __init__(self, **kw):
        """ Default class constructor. Update as you need. """
        self.__dict__.update(kw)
        

# Ok, let's explain why I am doing that.
# Often, data_files, excludes and dll_excludes (but also resources)
# can be very long list of things, and this will clutter too much
# the setup call at the end of this file. So, I put all the big lists
# here and I wrap them using the textwrap module.

data_files = %(data_files)s

includes = %(includes)s
excludes = %(excludes)s
packages = %(packages)s
dll_excludes = %(dll_excludes)s
icon_resources = %(icon_resources)s
bitmap_resources = %(bitmap_resources)s
other_resources = %(other_resources)s


# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

%(customcode)s


# Ok, now we are going to build our target class.
# I chose this building strategy as it works perfectly for me :-D
%(targetclasses)s

%(upx_inno)s

# That's serious now: we have all (or almost all) the options py2exe
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.
                    
setup(

    %(use_upx_inno)s

    data_files = data_files,

    options = {"py2exe": {"compressed": %(compressed)s, 
                          "optimize": %(optimize)s,
                          "includes": includes,
                          "excludes": excludes,
                          "packages": packages,
                          "dll_excludes": dll_excludes,
                          "bundle_files": %(bundle_files)s,
                          "dist_dir": "%(dist_dir)s",
                          "xref": %(xref)s,
                          "skip_archive": %(skip_archive)s,
                          "ascii": %(ascii)s,
                          "custom_boot_script": %(custom_boot_script)s,
                         }
              },

    zipfile = %(zipfile)s,
    %(console)s,
    %(windows)s,
    %(service)s,
    %(com_server)s,
    %(ctypes_com_server)s
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''

# --------------------------------------------------------------
# CX_FREEZE SECTION
# --------------------------------------------------------------

_cx_Freeze_imports = '''
# ======================================================#
# File automagically generated by GUI2Exe version %(gui2exever)s
# Andrea Gavana, 01 April 2007
# ======================================================#

# Let's start with some default (for me) imports...

from cx_Freeze import setup, Executable

'''

_cx_Freeze_class = '''
%s = Executable(
    # what to build
    script = "%s",
    initScript = %s,
    base = %s,
    targetDir = %s,
    targetName = "%s",
    compress = %s,
    copyDependentFiles = %s,
    appendScriptToExe = %s,
    appendScriptToLibrary = %s,
    icon = %s
    )
'''

_cx_Freeze_target = '''

# Process the includes, excludes and packages first

includes = %(includes)s
excludes = %(excludes)s
packages = %(packages)s
path = %(path)s

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

%(customcode)s

# The setup for cx_Freeze is different from py2exe. Here I am going to
# use the Python class Executable from cx_Freeze

%(targetclasses)s

# That's serious now: we have all (or almost all) the options cx_Freeze
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(
    
    version = %(version)s,
    description = %(description)s,
    author = %(author)s,
    name = %(name)s,
    
    options = {"build_exe": {"includes": includes,
                             "excludes": excludes,
                             "packages": packages,
                             "path": path
                             }
               },
                           
    executables = %(executables)s
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''

# --------------------------------------------------------------
# BBFREEZE SECTION
# --------------------------------------------------------------

_bbFreeze_imports = '''
# ======================================================#
# File automagically generated by GUI2Exe version %(gui2exever)s
# Andrea Gavana, 01 April 2007
# ======================================================#

# Let's start with some default (for me) imports...

from bbfreeze import Freezer
'''

_bbFreeze_class = '''
bbFreeze_Class.addScript(%(script)s, gui_only=%(gui_only)s)'''

_bbFreeze_target = '''

# Process the includes and excludes first

includes = %(includes)s
excludes = %(excludes)s

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

%(customcode)s

# The setup for bbFreeze is different from py2exe. Here I am going to
# use the Python class Freezer from bbFreeze

bbFreeze_Class = Freezer(%(dist_dir)s, includes=includes, excludes=excludes)
%(executables)s

bbFreeze_Class.use_compression = %(compress)s
bbFreeze_Class.include_py = %(include_py)s

# Call the actual class to do the freezing job
bbFreeze_Class()

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''

# --------------------------------------------------------------
# PYINSTALLER SECTION
# --------------------------------------------------------------

_pyInstaller_imports = '''
# ======================================================#
# File automagically generated by GUI2Exe version %(gui2exever)s
# Andrea Gavana, 01 April 2007
# ======================================================#
'''

_pyInstaller_target = '''

# Process the includes and excludes first

data_files = %(data_files)s

includes = %(includes)s
excludes = %(excludes)s
packages = %(packages)s
dll_excludes = %(dll_excludes)s
dll_includes = %(dll_includes)s

# Set up the more obscure PyInstaller runtime options

options = %(options)s

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

%(customcode)s

# The setup for PyInstaller is different from py2exe. Here I am going to
# use some common spec file declarations

analysis = Analysis(%(scripts)s,
                    pathex=%(pathex)s,
                    hookspath=%(hookspath)s,
                    excludes=excludes)
                    
pyz = PYZ(analysis.pure, level=%(level)s)

'''

_pyInstaller_target_onefile = _pyInstaller_target + \
'''
executable = EXE(%(TkPKG)s pyz,
                 analysis.scripts + includes + packages + options,
                 analysis.binaries - dll_excludes + dll_includes + data_files,
                 name=r"%(exename)s",
                 debug=%(debug)s,
                 console=%(console)s,
                 strip=%(strip)s,
                 upx=%(upx)s,
                 icon=%(icon)s,
                 version=%(version)s)

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''

_pyInstaller_target_onedir = _pyInstaller_target + \
'''
executable = EXE(pyz,
                 analysis.scripts + includes + packages + options,
                 exclude_binaries=1,
                 name=r"%(exename)s",
                 debug=%(debug)s,
                 console=%(console)s,
                 strip=%(strip)s,
                 upx=%(upx)s,
                 icon=%(icon)s,
                 version=%(version)s)
          
collect = COLLECT(%(TkPKG)s executable,
                  analysis.binaries - dll_excludes + dll_includes + data_files,
                  name=r"%(dist_dir)s",
                  strip=%(strip)s,
                  upx=%(upx)s)

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''

# --------------------------------------------------------------
# PY2APP SECTION
# --------------------------------------------------------------

_py2app_imports = '''
# ======================================================#
# File automagically generated by GUI2Exe version %(gui2exever)s
# Andrea Gavana, 01 April 2007
# ======================================================#

# Let's start with some default (for me) imports...

from setuptools import setup
'''

_py2app_target = '''

# Ok, let's explain why I am doing that.
# Often, data_files, excludes and friends (but also resources)
# can be very long list of things, and this will clutter too much
# the setup call at the end of this file. So, I put all the big lists
# here and I wrap them using the textwrap module.

resources = %(resources)s

includes = %(includes)s
excludes = %(excludes)s
packages = %(packages)s
frameworks = %(frameworks)s
dylib_excludes = %(dylib_excludes)s
datamodels = %(datamodels)s

# PList custom code (if any) goes here
%(plist_code)s

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

%(customcode)s


# That's serious now: we have all (or almost all) the options py2app
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(

    app = [%(script)s],
    setup_requires=['py2app'],
    
    options = {"py2app": {"optimize": %(optimize)s,
                          "includes": includes,
                          "excludes": excludes,
                          "packages": packages,
                          "dylib_excludes": dylib_excludes,
                          "frameworks": frameworks,
                          "datamodels": datamodels,
                          "resources": resources,
                          "iconfile": %(iconfile)s,
                          "plist": %(plist)s,
                          "extension": "%(extension)s",
                          "graph": %(graph)s,
                          "dist_dir": r"%(dist_dir)s",
                          "xref": %(xref)s,
                          "no_strip": %(no_strip)s,
                          "no_chdir": %(no_chdir)s,
                          "semi_standalone": %(semi_standalone)s,
                          "argv_emulation": %(argv_emulation)s,
                          "use_pythonpath": %(use_pythonpath)s,
                          "site_packages": %(site_packages)s,
                          "prefer_ppc": %(prefer_ppc)s,
                          "debug_modulegraph": %(debug_modulegraph)s,
                          "debug_skip_macholib": %(debug_skip_macholib)s
                         }
              },
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

%(postcompilecode)s


# And we are done. That's a setup script :-D

'''