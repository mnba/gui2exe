import wx
from Resources import *

_defaultCompilers = ["py2exe", "py2app", "cx_Freeze", "PyInstaller", "bbfreeze"]

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
                              "message_skip", "message_filter"],
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
                 "resources": ["datafiles"]
                 }
_unWantedLists = ["messages", "missingmodules", "binarydependencies"]
_bookIcons = ["py2exe", "py2app", "cx_Freeze", "PyInstaller", "bbFreeze"]
_iconMapper = {"Message": 0, "Warning": 1, "Error": 2, "Find": 3, "Compile": 4, "Copy": 5}
_sizeIcons = ["py2exe_small", "py2app_small", "cx_Freeze_small", "PyInstaller_small",
              "bbFreeze_small", "file_size", "numfiles"]

_stcKeywords = ["includes", "excludes", "ignores", "packages", "dll_excludes", "data_files",
                "icon_resources", "bitmap_resources", "other_resources", "dest_base",
                "initScript", "base", "targetDir", "targetName", "compress", "script", 
                "copyDependentFiles", "appendScriptToExe", "appendScriptToLibrary", "icon",
                "dll_includes", "pathex", "hookspath", "exclude_binaries", "name", "debug",
                "console", "strip", "upx", "version", "options", "level", "path",
                "executables", "description", "author", "dylib_excludes", "frameworks",
                "datamodels", "resources", "iconfile", "plist", "extension", "graph",
                "no_chdir", "no_strip", "semi_standalone", "argv_emulation", "use_pythonpath",
                "site_packages", "prefer_ppc", "debug_modulegraph", "debug_skip_macholib"]

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
                             }
                }
                           

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


_toolTips = {"py2exe": {"optimize": "Optimization level for the compiled bytecode.\n\n" \
                        "0: No optimization on the compiled bytecode;\n" \
                        "1 (Python -O): Optimize the generated bytecode;\n" \
                        "2 (Python -OO): remove doc-strings in addition to the -O optimizations.",
                        "compressed": "Creates a compressed zip archive (zipfile).\n\n" \
                        "It can be either 0 or a positive number, the meaning of\n" \
                        "activating/deactivating the compression is as follows:\n\n" \
                        "- No Compression: the zipfile will be created using the\n" \
                        "  zipfile.ZIP_STORED Python option;\n" \
                        "- With Compression: the zipfile will be created using the\n"\
                        "  zipfile.ZIP_DEFLATED Python option." \
                        "<note>If you specify the Skip Archive option, compression can not\n" \
                        "be activated (no zipfile to compress).",
                        "bundle_files": "Bundling options for the final dist directory.\n\n" \
                        "- Level 3: default for py2exe. No pyd or dll is bundled in the exe\n" \
                        "  or in the zip-archive;\n" \
                        "- Level 2: includes the .pyd and .dll files into the zip-archive\n" \
                        "  or the executable;\n" \
                        "- Level 1: includes the .pyd and .dll files into the zip-archive\n"\
                        "  or the executable itself, and does the same for pythonXY.dll."\
                        "<note>The Bundle Files option is currently not available on 64\n"\
                        "bit machines.",
                        "zipfile_choice": "By activating this option in GUI2Exe, you can specify a name\n" \
                        "for the compressed zip file where py2exe will put all the\n" \
                        "bytecode-compiled Python modules. If you don't activate\n" \
                        "this option, or the zipfile name is empty, the default in GUI2Exe\n" \
                        "is to use zipfile=None. This means the compiled bytecode will be\n" \
                        "attached to the executable itself and no zip file will be created." \
                        "<note>If you specify the Skip Archive option, zipfile can not be\n"\
                        "None.",
                        "dist_dir_choice": "If you activate this switch, you will be able to\n"
                        "specify the name the directory to put final built\n" \
                        "distributions in (the default is 'dist').",
                        "skip_archive": "By choosing this option, py2exe will copy\n" \
                        "the Python bytecode files directly into the dist\n" \
                        "directory (or in the excutable itself). No zipfile\n" \
                        "archive is used.",
                        "manifest_file": "Creates a file that instructs Windows on how to correctly\n" \
                        "render the widgets in your user interface. This file lives\n" \
                        "under 'other_resources' in py2exe.",
                        "xref": "This command line switch instructs py2exe to create a Python\n" \
                        "module cross reference and display it in the webbrowser.\n" \
                        "This allows to answer question why a certain module\n" \
                        "has been included, or if you can exlude a certain module\n" \
                        "and its dependencies.",
                        "ascii": "To prevent unicode encoding error, py2exe now by default\n" \
                        "includes the codecs module and the encodings package.\n" \
                        "If you are sure your program never implicitely or explicitely\n" \
                        "has to convert between unicode and ascii strings this can be\n" \
                        "prevented by switching on this option in its associated\n" \
                        "check box in GUI2Exe.",
                        "custom_boot_script": "By selecting a file for this option, your custom\n" \
                        "Python file can do things like installing a customized\n" \
                        "stdout blackhole. The custom boot script is executed\n" \
                        "during startup of the executable immediately after\n" \
                        "boot_common.py is executed.",
                        "multipleexe": "Add a new list item by hitting Ctrl+A and click on the\n" \
                        "third list control column to select your Python Main\n" \
                        "Script. You can change the executable kind (windows or\n" \
                        "(console) by clicking on the second list control column,\n" \
                        "and modify other property of your target class as well." \
                        "<note>The other options currently available in py2exe, namely\n" \
                        "service, com_server and ctypes_com_server are currently\n" \
                        "not implemented in GUI2Exe.",
                        "includes": "comma-separated list of Python modules to include.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it." \
                        "<note>The Includes option is stronger than the Excludes one.\n" \
                        "So, if a module is present in both Includes and Excludes,\n" \
                        "it will be included in your final distribution.",
                        "excludes": "comma-separated list of Python modules to exclude.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it." \
                        "<note>The Includes option is stronger than the Excludes one.\n" \
                        "So, if a module is present in both Includes and Excludes,\n" \
                        "it will be included in your final distribution.",
                        "packages": "comma-separated list of Python packages to include.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it.",
                        "ignores": "comma-separated list of Python modules to ignore\n" \
                        "if they are found during the building process.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it.",
                        "dll_excludes": "comma-separated list of DLLs to exclude.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it.",
                        "data_files": "Py2exe allows you to include one (or more) series of files\n" \
                        "that you are going to need to run your executable\n\n" \
                        "Depending on the choice ine the menu 'Options' ==>\n" \
                        "'Recurse sub-dirs for DATA files option' there are\n" \
                        "2 possibilities:\n\n" \
                        "- Choose multiple files at once;\n" \
                        "- Choose one or more directories: every file in them\n" \
                        "  will be added recursively.\n\n" \
                        "Hit Ctrl+A to add data files to the list.",
                        "icon_resources": "Add a custom icon to your application.\n" \
                        "The icon will be shown in Windows Explorer.\n\n"\
                        "Hit Ctrl+A to add an item to the list and edit it.",
                        "bitmap_resources": "Add one or more bitmaps as Windows resources,\n" \
                        "so that they get packaged in the executable.\n\n"
                        "Hit Ctrl+A to add an item to the list and edit it.",
                        "other_resources": "Insert a custom named resource into the executable.\n\n" \
                        "Hit Ctrl+A to add an item to the list and edit it."
                        },
             "cx_Freeze": {"version": "Your program version.",
                           "description": "A short description of your application.",
                           "author": "Information about the programmer.",
                           "name": "The program name",
                           "base": "Depends on the kind of executable you wish to build:\n\n" \
                           "- windows: builds an executable for a GUI-based application;\n"
                           "- console: creates an executable for a console program\n" \
                           "  (i.e., no graphical interface stuff involved).",
                           "script": "The Python main script you want to convert\n" \
                           "to an executable.",
                           "optimize": "Optimization level for the compiled bytecode.\n\n" \
                           "0: No optimization on the compiled bytecode;\n" \
                           "1 (Python -O): Optimize the generated bytecode;\n" \
                           "2 (Python -OO): remove doc-strings in addition to the -O optimizations.",
                           "compress": "Creates a compressed zip file.",
                           "target_name_choice": "the name of the target executable; the default value is\n"
                           "the name of the script with the extension exchanged with\n" \
                           "the extension for the base executable.",
                           "dist_dir_choice": "the directory in which to place the target executable and\n" \
                           "any dependent files.",
                           "copy_dependent_files": "boolean value indicating if dependent files should be\n" \
                           "copied to the target directory or not.",
                           "append_script_toexe": "boolean value indicating if the script module should be\n" \
                           "appended to the executable itself.",
                           "append_script_tolibrary": "boolean value indicating if the script module should\n" \
                           "be appended to the shared library zipfile.",
                           "create_manifest_file": "On Windows, it creates a manifest file that instructs\n" \
                           "Windows on how to correctly render the widgets in your\n" \
                           "user interface.",
                           "icon": "name of icon which should be included in the executable\n" \
                           "itself on Windows or placed in the target directory for\n" \
                           "other platforms.",
                           "initScript": "the name of the initialization script that will be executed\n" \
                           "before the actual script is executed; this script is used to\n" \
                           "set up the environment for the executable; if a name is given\n" \
                           "without an absolute path the names of files in the initscripts\n" \
                           "subdirectory of the cx_Freeze package is searched.",
                           "includes": "list of names of modules to include.\n\n" \
                           "Hit Ctrl+A to add an item to the list and edit it.",
                           "excludes": "list of names of modules to exclude.\n\n" \
                           "Hit Ctrl+A to add an item to the list and edit it.",
                           "packages": "list of names of packages to include, including all\n" \
                           "of the package's submodules.\n\n" \
                           "Hit Ctrl+A to add an item to the list and edit it.",
                           "path": "list of paths to search for modules.\n\n" \
                           "Hit Ctrl+A to select one or more directories."
                           },
             "bbfreeze": {"script": "The Python main script you want to convert\n" \
                          "to an executable.",
                          "optimize": "Optimization level for the compiled bytecode.\n\n" \
                          "0: No optimization on the compiled bytecode;\n" \
                          "1 (Python -O): Optimize the generated bytecode;\n" \
                          "2 (Python -OO): remove doc-strings in addition to the -O optimizations.",
                          "compress": "Creates a compressed zip file.",
                          "dist_dir_choice": "the directory in which to place the target executable and\n" \
                          "any dependent files.",
                          "gui_only": "The gui_only flag only has a meaning on Windows: If set, the\n" \
                          "executable created for this script will not open a console window.",
                          "include_py": "flag whether to create the included python interpreter.",
                          "create_manifest_file": "On Windows, it creates a manifest file that instructs\n" \
                          "Windows on how to correctly render the widgets in your\n" \
                          "user interface.",
                          "includes": "list of names of modules to include.\n\n" \
                          "Hit Ctrl+A to add an item to the list and edit it.",
                          "excludes": "list of names of modules to exclude.\n\n" \
                          "Hit Ctrl+A to add an item to the list and edit it."
                          },
             "PyInstaller": {"debug": "Setting to 1 gives you progress messages from the executable\n" \
                             "(for a console=0, these will be annoying MessageBoxes)." ,
                             "console": "Always 1 on Linux/unix. On Windows, governs whether to use\n" \
                             "the console executable, or the Windows subsystem executable.",
                             "strip": "the executable and all shared libraries will be run through\n" \
                             "strip. Note that cygwin's strip tends to render normal Win32\n" \
                             "dlls unusable.",
                             "upx": "if you have UPX installed (detected by Configure), this will use\n" \
                             "it to compress your executable (and, on Windows, your dlls)",
                             "icon": "Windows NT family only. icon='myicon.ico' to use an icon file.",
                             "version": "Windows NT family only. version='myversion.txt'."
                             "<note>Use the PyInstaller Python file 'GrabVersion.py' to steal a \n" \
                             "version resource from an executable, and then edit the output to create\n" \
                             "your own. (The syntax of version resources is so arcane that I\n" \
                             "wouldn't attempt to write one from scratch).",
                             "onefile": "produces a single file deployment.",
                             "onedir": "produces a single directory deployment (default).",
                             "exename": "The filename for the executable.",
                             "ascii": "do not include encodings." \
                             "<note>The default (on Python versions with unicode support)\n" \
                             "is now to include all encodings.",
                             "dist_dir": "the directory in which to place the target executable and\n" \
                             "any dependent files." \
                             "<note>This is used only when 'onedir' is set to 1.",
                             "includetk": "include TCL/TK in the deployment.",
                             "level": "The Zlib compression level to use.\n\n" \
                             "If 0, the zlib module is not required.",
                             "create_manifest_file": "On Windows, it creates a manifest file that instructs\n" \
                             "Windows on how to correctly render the widgets in your\n" \
                             "user interface.",
                             "scripts": "a list of scripts specified as file names.\n\n" \
                             "Hit Ctrl+A to select one or more Python files.",
                             "includes": "list of names of modules to include.\n\n" \
                             "Hit Ctrl+A to select one or more Python modules.",
                             "excludes": "list of names of modules to exclude.\n\n" \
                             "Hit Ctrl+A to select one or more Python modules.",
                             "pathex": "an optional list of paths to be searched before sys.path.\n\n" \
                             "Hit Ctrl+A to select one or more directories.",
                             "hookspath": "an optional list of paths used to extend the hooks package.\n\n" \
                             "Hit Ctrl+A to select one or more directories.",
                             "dll_excludes": "an optional list of binary files to exclude.\n\n" \
                             "Hit Ctrl+A to select one or more binary files.",
                             "dll_includes": "an optional list of binary files to include.\n\n" \
                             "Hit Ctrl+A to select one or more binary files.",
                             "data_files": "Arbitrary files to include in your distribution.\n\n" \
                             "Depending on the choice ine the menu 'Options' ==>\n" \
                             "'Recurse sub-dirs for DATA files option' there are\n" \
                             "2 possibilities:\n\n" \
                             "- Choose multiple files at once;\n" \
                             "- Choose one or more directories: every file in them\n" \
                             "  will be added recursively.\n\n" \
                             "Hit Ctrl+A to select one or more data files.",
                             "packages": "list of names of packages to include.\n\n" \
                             "Hit Ctrl+A to select one or more Python packages.",
                             "option1": "Verbose imports (same as Python -v).",
                             "option2": "Warning option (Python 2.1+).",
                             "option3": "Force execpv (Linux/Unix only).\n\n" \
                             "Ensures that LD_LIBRARY_PATH is set properly.",
                             "option4": "Unbuffered STDIO (same as Python -u).",
                             "option5": "Use site.py.\n\nThe opposite of Python -S." \
                             "<note>Note that site.py must be in the executable's \n" \
                             "directory to be used.",
                             "option6": "Build optimized.\n\nPyInstaller will gather *.pyo files\n" \
                             "if it is run optimized."
                             },
             "py2app": {"script": "The Python main script you want to convert\n" \
                        "to an executable.",
                        "dist_dir": "directory to put final built distributions in \n" \
                        "(default is dist).",
                        "optimize": "Optimization level for the compiled bytecode.\n\n" \
                        "0: No optimization on the compiled bytecode;\n" \
                        "1 (Python -O): Optimize the generated bytecode;\n" \
                        "2 (Python -OO): remove doc-strings in addition to the -O optimizations.",
                        "iconfile": "Icon file to use for your application.",
                        "plist": "Info.plist template file.",
                        "extension": "Bundle extension (default: '.app' for app, '.plugin' \n" \
                        "for plugins).",
                        "graph": "output module dependency graph.",
                        "xref": "This command line switch instructs py2app to create a Python\n" \
                        "module cross reference and display it in the webbrowser.\n" \
                        "This allows to answer question why a certain module\n" \
                        "has been included, or if you can exlude a certain module\n" \
                        "and its dependencies.",
                        "no_strip": "do not strip debug and local symbols from output.",
                        "no_chdir": "do not change to the data directory (Contents/Resources)." \
                        "<note> This is forced for plugins.",
                        "semi_standalone": "depend on an existing installation of Python 2.4+.",
                        "argv_emulation": "Use argv emulation." \
                        "<note> This is disabled for plugins.",
                        "use_pythonpath": "Allow PYTHONPATH to effect the interpreter's environment.",
                        "site_packages": "include the system and user site-packages into sys.path.",
                        "prefer_ppc": "Force application to run translated on i386.",
                        "debug_modulegraph": "Drop to pdb console after the module finding phase is complete.",
                        "debug_skip_macholib": "skip macholib phase.<note>Your App will not be standalone.",
                        "resources": "Py2app allows you to include one (or more) series of files\n" \
                        "that you are going to need to run your executable\n\n" \
                        "Depending on the choice ine the menu 'Options' ==>\n" \
                        "'Recurse sub-dirs for DATA files option' there are\n" \
                        "2 possibilities:\n\n" \
                        "- Choose multiple files at once;\n" \
                        "- Choose one or more directories: every file in them\n" \
                        "  will be added recursively.\n\n" \
                        "Hit Ctrl+A to add data files to the list.",
                        "includes": "comma-separated list of Python modules to include.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it." \
                        "<note>The Includes option is stronger than the Excludes one.\n" \
                        "So, if a module is present in both Includes and Excludes,\n" \
                        "it will be included in your final distribution.",
                        "excludes": "comma-separated list of Python modules to exclude.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it." \
                        "<note>The Includes option is stronger than the Excludes one.\n" \
                        "So, if a module is present in both Includes and Excludes,\n" \
                        "it will be included in your final distribution.",
                        "packages": "comma-separated list of Python packages to include.\n\n" \
                        "Hit Ctrl+A to add a new item in the list and edit it.",
                        "dylib_excludes": "comma-separated list of frameworks or dylibs to\n" \
                        "exclude.\n\n" \
                        "Hit Ctrl+A to select one or more dylibs or frameworks.",
                        "datamodels": "xcdatamodels to be compiled and copied into\n" \
                        "Resources." \
                        "Hit Ctrl+A to select one or more xcdatamodels.",
                        "frameworks": "comma-separated list of frameworks or dylibs to\n" \
                        "include in your distribution.\n\n" \
                        "Hit Ctrl+A to select one or more dylibs or frameworks."
                        }
             }

_toolTips["py2exe"]["zipfile"] = _toolTips["py2exe"]["zipfile_choice"]
_toolTips["py2exe"]["dist_dir"] = _toolTips["py2exe"]["dist_dir_choice"]

_toolTips["cx_Freeze"]["target_name"] = _toolTips["cx_Freeze"]["target_name_choice"]
_toolTips["cx_Freeze"]["dist_dir"] = _toolTips["cx_Freeze"]["dist_dir_choice"]

_toolTips["bbfreeze"]["dist_dir"] = _toolTips["bbfreeze"]["dist_dir_choice"]


# --------------------------------------------------------------
# PY2EXE SECTION
# --------------------------------------------------------------

_py2exe_imports = '''
# ======================================================#
# File automagically generated by GUI2Exe version %(gui2exever)s
# Andrea Gavana, 01 April 2007
# ======================================================#

# Let's start with some default (for me) imports...

from distutils.core import setup
import py2exe
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
    name = "%s"
    )

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

# That's serious now: we have all (or almost all) the options py2exe
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(

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
    %(windows)s
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

exeClass = Executable(script=%(script)s, initScript=%(initScript)s,
                      base=%(base)s, targetDir=%(dist_dir)s,
                      targetName=%(target_name)s, compress=%(compress)s,
                      copyDependentFiles=%(copy_dependent_files)s,
                      appendScriptToExe=%(append_script_toexe)s,
                      appendScriptToLibrary=%(append_script_tolibrary)s,
                      icon=%(icon)s, path=path)

# That's serious now: we have all (or almost all) the options cx_Freeze
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(
    
    name = %(name)s,
    version = %(version)s,
    description = %(description)s,
    author = %(author)s,
    
    options = {"build_exe": {"includes": includes,
                             "excludes": excludes,
                             "packages": packages,
                             }
               },
                           
    executables = [exeClass])


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
bbFreeze_Class.addScript(%(script)s, gui_only=%(gui_only)s)

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