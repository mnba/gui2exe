__author__  = "Andrea Gavana <andrea.gavana@gmail.com>, <gavana@kpo.kz>"
__date__    = "01 Apr 2007, 13:15 GMT"
__version__ = "0.2alpha"
__docformat__ = "epytext"

# Start the imports
import os
import wx
import time

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())
del sys.setdefaultencoding

# Used to start the compiled executable
if sys.version[0:3] >= "(2,4)":
    # subprocess is new in 2.4
    import subprocess

import wx.aui
import wx.lib.dialogs

# This is somehow needed by distutils, otherwise it bombs on Windows
# when you have py2App installed (!)
if wx.Platform == "__WXMAC__":
    try:
        import setuptools
    except ImportError:
        pass

# I need webbrowser for the help and tips and tricks
import webbrowser

# Used to clean up the distribution folder
import shutil

# Get the translation module
import locale

# Let's import few modules I have written for GUI2Exe
from ProjectTreeCtrl import ProjectTreeCtrl
from MessageWindow import MessageWindow
from ExecutableProperties import ExecutableProperties
from AUINotebookPage import AUINotebookPage
from DataBase import DataBase
from Project import Project
from Process import Process
from Widgets import CustomCodeViewer, Py2ExeMissing, PyBusyInfo, BuildDialog, PreferencesDialog
from Widgets import ExceptionHook
from Utilities import GetLangId, GetAvailLocales, now, CreateBitmap
from Utilities import opj, odict, PrintTree, ConnectionThread
from Constants import _auiImageList, _pywildspec, _defaultCompilers, _manifest_template
from Constants import _standaloneString
from AllIcons import catalog

# And import the fancy AdvancedSplash
import AdvancedSplash as AS

# I need this for restorable perspectives:
ID_FirstPerspective = wx.ID_HIGHEST + 10000
# Some ids to avoid using FindMenu...
ID_CleanDist = ID_FirstPerspective + 2000
ID_DeleteBuild = ID_CleanDist + 1
ID_ShowTip = ID_CleanDist + 2
ID_Recurse = ID_CleanDist + 3

# Define a translation string
_ = wx.GetTranslation

# It looks like that, while py2exe and py2app are installed on site-packages
# (or at least you can actually __import__ them), for the other 2 beasts
# is far more complicated, at least on Windows

def ImportCompilers():
    """ Simple function that imports the available compilers (if any). """
    
    compilers = odict()
    for compiler in _defaultCompilers:
        try:
            module = __import__(compiler)
            compilers[compiler] = module.__version__
            
        except ImportError:
            # No compiler, no party
            pass
        
        except AttributeError:
            try:
                compilers[compiler] = module.version
            except:
                # cx_Freeze has no version number in its installation
                # Hey developer, what about adding a __version__
                # attribute to cx_Freeze? It's not rocket science...
                compilers[compiler] = "(No version)"
        except:  # any other error
            pass

    return compilers

# Ok, now get the compilers...
_compilers = ImportCompilers()



class GUI2Exe(wx.Frame):
    """ Main wx.Frame class for our application. """
    
    def __init__(self, parent, id=-1, title="", pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE):
        """ Default wx.Frame class constructor. """
        
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # Yes, I know, I am obsessively addicted to wxAUI
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        # Some default starting values for our class
        # where are we
        self.installDir = wx.GetApp().GetInstallDir()

        self.autoSave = False                # use autoSave? (not implemented yet...)
        self.deleteBuild = True              # delete the "build" directory (recommended)
        self.cleanDist = False               # Clean up the "dist" directory
        self.process = None                  # keeps track of the compilation subprocess
        self.exeTimer = wx.Timer(self)       # I use that to monitor exe failures
        self.timerCount = 0                  # same as above
        self.processTimer = wx.Timer(self)   # used to monitor the external process
        self.pythonVersion = sys.executable  # Default Python executable
        self.pyInstallerPath = None          # Where PyInstaller lives
        self.recurseSubDirs = False          # Recurse sub-directories for the data_files option
        self.showTips = True                 # Show tooltips for various compiler options
        
        self.perspectives = []

        # Create the status bar
        self.CreateBar()
        # Set frame properties (title, icon...)
        self.SetProperties()
        # Create the menu bar (lots of code, mostly always the same)
        self.CreateMenuBar()
        # Build the wx.aui.AuiNotebook image list
        # But why in the world is so different from wx.Notebook???
        self.BuildNBImageList()

        # Look if there already exists a database for GUI2Exe
        dbName = self.CheckForDatabase()

        # This is the left CustomTreeCtrl that holds all our projects
        self.projectTree = ProjectTreeCtrl(self)
        # This is the main window, the central pane
        self.mainPanel = wx.aui.AuiNotebook(self, -1, style=wx.aui.AUI_NB_DEFAULT_STYLE|
                                            wx.aui.AUI_NB_WINDOWLIST_BUTTON)
        # Let's be fancy and add a special logging window
        self.messageWindow = MessageWindow(self)
        # Add a small panel to show the executable properties
        self.executablePanel = ExecutableProperties(self)
        # Call the database. This actually populates the project tree control
        self.dataBase = DataBase(self, dbName)

        # Check if we had a very hard crash (irreversible)
        if self.dataBase.hasError:
            strs = _("The database file and its backup seem to be broken.\n\n" \
                     "Please go to the /USER/Application Data/.GUI2Exe/ folder\n" \
                     "and delete the GUI2Exe database file.")
            self.RunError(2, strs)
            self.Destroy()
            return

        # Add the panes to the wxAUI manager
        # Very nice the bug introduced in wxPython 2.8.3 about wxAUI Maximize buttons...
        self._mgr.AddPane(self.projectTree, wx.aui.AuiPaneInfo().Left().
                          Caption(_("GUI2Exe Projects")).MinSize(wx.Size(250, -1)).
                          FloatingSize(wx.Size(200, 300)).Layer(1).MaximizeButton().
                          Name("GUI2ExeProjects"))
        self._mgr.AddPane(self.executablePanel, wx.aui.AuiPaneInfo().Left().
                          Caption(_("Executable Properties")).MinSize(wx.Size(200, 100)).
                          BestSize(wx.Size(200, size[1]/6)).MaxSize(wx.Size(200, 100)).
                          FloatingSize(wx.Size(200, 200)).Layer(1).Position(1).MaximizeButton().
                          Name("ExecutableProperties"))
        self._mgr.GetPane(self.executablePanel).dock_proportion = 100000/4
        self._mgr.AddPane(self.mainPanel, wx.aui.AuiPaneInfo().CenterPane().Name("MainPanel"))
        self._mgr.AddPane(self.messageWindow, wx.aui.AuiPaneInfo().Bottom().
                          Caption(_("Messages And Actions")).MinSize(wx.Size(200, 100)).
                          FloatingSize(wx.Size(500, 300)).BestSize(wx.Size(200, size[1]/6)).
                          MaximizeButton().Name("MessagesAction"))
        
        # Set all the flags for wxAUI
        self.SetAllFlags()
        # Bind the main frame events
        self.BindEvents()

        # Save the current perspective to be reloaded later if requested
        self.perspectives.append(self._mgr.SavePerspective())
        # Update the wxAUI manager
        self._mgr.Update()
        # Sort the tree children
        self.projectTree.SortItems()
        # Read the default configuration file.
        self.ReadConfigurationFile()
        # Disable the Run and Dry-Run buttons
        self.messageWindow.NoPagesLeft(False)

        # Apply the user preferences
        wx.CallAfter(self.ApplyPreferences)
        transdict = dict(dateAndTime=now())
        self.SendMessage(0, _("GUI2Exe succesfully started at %(dateAndTime)s")%transdict)


    # ================================== #
    # GUI2Exe methods called in __init__ #
    # ================================== #
    
    def CreateBar(self):
        """ Creates the GUI2Exe status bar. """

        # Come on, let's see how fast the menubar is able to delete the text
        # I have in the status bar...
        self.statusBar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusBar.SetStatusWidths([-1, -2])
        self.FillStatusBar()


    def MenuData(self):
        """ Handles all the information used to build the menu bar. """

        # That's really a bunch of data...
        
        return ((_("&File"),
                    (_("&New project...")+"\tCtrl+N", _("Add a new project to the project tree"), "project", -1, self.OnNewProject, ""),
                    (_("Switch project &database...")+"\tCtrl+D", _("Load another GUI2Exe database file"), "switch_db", -1, self.OnSwitchDB, ""),
                    ("", "", "", "", "", ""),
                    (_("&Save project") + "\tCtrl+S", _("Save the current project to database"), "save_project", -1, self.OnSaveProject, ""),
                    (_("&Save project as...")+"\tCtrl+Shift+S", _("Save the current project to a file"), "save_to_file", -1, self.OnExportProject, ""),
                    ("", "", "", "", "", ""),
                    (_("&Export setup file...")+"\tCtrl+E", _("Export the Setup.py file"), "export_setup", -1, self.OnExportSetup, ""),
                    ("", "", "", "", "", ""),
                    (_("&Quit") + "\tCtrl+Q", _("Exit GUI2Exe"), "exit", wx.ID_EXIT, self.OnClose, "")),
                (_("&Options"),
                    (_("Use &AutoSave"), _("AutoSaves your work every minute"), "", -1, self.OnAutoSave, wx.ITEM_CHECK),
                    ("", "", "", "", "", ""),
                    (_('De&lete "build" directory'), _("Delete the build folder at every compilation"), "", ID_DeleteBuild, self.OnDeleteBuild, wx.ITEM_CHECK),
                    (_('Clea&n "dist" directory'), _("Clean the distribution folder at every compilation"), "", ID_CleanDist, self.OnCleanDist, wx.ITEM_CHECK),
                    ("", "", "", "", "", ""),
                    (_("&Recurse sub-dirs for data_files option"), _("Recurse sub-directories for data_files option if checked"), "", ID_Recurse, self.OnRecurseSubDir, wx.ITEM_CHECK),
                    (_("Show t&ooltips"), _("show tooltips for the various compiler options"), "", ID_ShowTip, self.OnShowTip, wx.ITEM_CHECK),
                    ("", "", "", "", "", ""),
                    (_("Change &Python version...") + "\tCtrl+H", _("Temporarily changes the Python version"), "python_version", -1, self.OnChangePython, ""),
                    (_("Set P&yInstaller path...") + "\tCtrl+Y", _("Sets the PyInstaller installation path"), "PyInstaller_small", -1, self.OnSetPyInstaller, ""),
                    ("", "", "", "", "", ""),
                    (_("Add &custom code...")+"\tCtrl+U", _("Add custom code to the setup script"), "custom_code", -1, self.OnCustomCode, ""),
                    (_("&Insert post compilation code...")+"\tCtrl+I", _("Add custom code to be executed after the building process"), "post_compile", -1, self.OnPostCompilationCode, ""),
                    ("", "", "", "", "", ""),
                    (_("Preferences..."), _("Edit preferences/settings"), "preferences", wx.ID_PREFERENCES, self.OnPreferences, "")),
                (_("&Builds"),
                    (_("&Test executable") + "\tCtrl+R", _("Test the compiled file (if it exists)"), "runexe", -1, self.OnTestExecutable, ""),
                    ("", "", "", "", "", ""),
                    (_("View &setup script") + "\tCtrl+P", _("View the auto-generated setup script"), "view_setup", -1, self.OnViewSetup, ""),
                    (_("&Check setup script syntax") + "\tCtrl+X", _("Check the syntax of the auto-generated setup script"), "spellcheck", -1, self.OnCheckSyntax, ""),
                    ("", "", "", "", "", ""),
                    (_("Show &full build output")+"\tCtrl+F", _("View the full build output for the current compiler"), "full_build", -1, self.OnViewFullBuild, ""),
                    ("", "", "", "", "", ""),
                    (_("&Missing modules") + "\tCtrl+M", _("What the compiler thinks are the missing modules (py2exe only)"), "missingmodules", -1, self.OnViewMissing, ""),
                    (_("&Binary dependencies") + "\tCtrl+B", _("What the compiler says are the binary dependencies (py2exe only)"), "binarydependencies", -1, self.OnViewMissing, "")),
                (_("&View"),
                    (_("Save &panes configuration..."), _("Save the current GUI panes configuration"), "save_aui_config", -1, self.OnSaveConfig, ""),
                    (_("Restore original &GUI") + "\tCtrl+G", _("Restore the original GUI appearance"), "restore_aui", ID_FirstPerspective, self.OnRestorePerspective, "")),
                (_("&Help"),
                    (_("GUI2Exe &help") + "\tF1", _("Opens the GUI2Exe help"), "help", -1, self.OnHelp, ""),
                    (_("GUI2Exe &API") + "\tF2", _("Opens the GUI2Exe API reference"), "api_reference", -1, self.OnAPI, ""),
                    ("", "", "", "", "", ""),
                    (_("Compiler s&witches") + "\tF3", _("Show compilers switches and common options"), "compiler_switches", -1, self.OnCompilerSwitches, ""),
                    (_("&Tips and tricks") + "\tF4", _("Show compilation tips and tricks"), "tips_and_tricks", -1, self.OnTipsAndTricks, ""),
                    ("", "", "", "", "", ""),
                    (_("Check for &upgrade") + "\tF9", _("Check for a GUI2Exe upgrade"), "upgrade", -1, self.OnCheckUpgrade, ""),
                    ("", "", "", "", "", ""),
                    (_("&Contact the Author..."), _("Contact Andrea Gavana by e-mail"), "contact", -1, self.OnContact, ""),
                    (_("&About GUI2Exe..."), _("About GUI2Exe and the Creator..."), "about", wx.ID_ABOUT, self.OnAbout, "")))
                    
                    
    def CreateMenu(self, menuData):
        """
        Creates a menu based on input menu data.

        @param menuData: the menu item label, bitmap, longtip etc...        
        """
        
        menu = wx.Menu()

        # Here is a bit trickier than what presented in Robin and Noel book,
        # but not that much.
        for eachLabel, eachStatus, eachIcon, eachId, eachHandler, eachKind in menuData:

            if not eachLabel:
                menu.AppendSeparator()
                continue

            # There are also few check menu items around...
            kind = (eachKind and [eachKind] or [wx.ITEM_NORMAL])[0]

            menuItem = wx.MenuItem(menu, eachId, eachLabel, eachStatus, kind=kind)
            if eachIcon:
                # Check menu items usually don't have associated icons
                menuItem.SetBitmap(self.CreateBitmap(eachIcon))

            menu.AppendItem(menuItem)
            if eachId == ID_DeleteBuild:
                # By default the "remove build directory" is on
                menuItem.Check(True)

            if eachId == ID_ShowTip:
                # By default we activate the tooltips, unless in the wx.Config
                # it's set to False
                menuItem.Check(True)

            # Only store the meanningful menus...
            if eachId == ID_FirstPerspective:
                self.configMenu = menu

            # Bind the event
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
            
        return menu


    def CreateMenuBar(self):
        """ Creates the main frame menu bar. """

        menuBar = wx.MenuBar()

        # loop over the bunch of data above
        for eachMenuData in self.MenuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1:]
            menuBar.Append(self.CreateMenu(menuItems), menuLabel)
    
        # Bind the special "restore perspective" menu item
        self.Bind(wx.EVT_MENU_RANGE, self.OnRestorePerspective, id=ID_FirstPerspective,
                  id2=ID_FirstPerspective+1000)

        # We're done with the menubar
        self.SetMenuBar(menuBar)

        # Add accelerators for the Ctrl+W and F5 switches
        idClose, idRun = wx.NewId(), wx.NewId()
        self.Bind(wx.EVT_MENU, self.AccelClosing, id=idClose)
        self.Bind(wx.EVT_MENU, self.AccelRun, id=idRun)
        self.accelTable = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("w"), idClose),
                                               (wx.ACCEL_NORMAL, wx.WXK_F5, idRun)])
        # Set the accelerator table
        self.SetAcceleratorTable(self.accelTable)
        

    def BuildNBImageList(self):
        """ Builds a fake image list for wx.aui.AuiNotebook. """

        # One day someone will explain why it doesn't handle wx.ImageList
        # like every other Book.
        self.nbImageList = []
        for png in _auiImageList:
            bmp = self.CreateBitmap(png)
            self.nbImageList.append(bmp)
            

    def SetProperties(self):
        """ Sets the main frame properties (title, icon...). """

        self.SetIcon(wx.IconFromBitmap(self.CreateBitmap("GUI2Exe")))
        self.SetTitle("GUI2Exe v" + __version__)


    def SetAllFlags(self):
        """ Sets all the fancy flags for wxAUI and friends. """

        # Allow to have active panes and transparent dragging
        self._mgr.SetFlags(self._mgr.GetFlags() ^ wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE)
        self._mgr.SetFlags(self._mgr.GetFlags() ^ wx.aui.AUI_MGR_TRANSPARENT_DRAG)

        # Try to give a decent look to the gradients
        self._mgr.GetArtProvider().SetColor(wx.aui.AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR,
                                            wx.Colour(128, 128, 128))
        self._mgr.GetArtProvider().SetColor(wx.aui.AUI_DOCKART_ACTIVE_CAPTION_GRADIENT_COLOUR,
                                            wx.WHITE)

        # Very useful method
        self.mainPanel.SetUniformBitmapSize((16, 16))


    def CheckForDatabase(self):
        """ Checks if a database exists. If it doesn't, creates one anew. """

        # We build the database inside the user config folder, where we
        # also create a sub-directory called /.GUI2Exe
        standardPath = wx.StandardPaths.Get()
        configDir = opj(standardPath.GetUserConfigDir() + "/.GUI2Exe")
        configDb = opj(configDir + "/GUI2Exe_Database.db")
        
        if not os.path.isfile(configDb):
            # No database
            if not os.path.isdir(configDir):
                # And no directory. Create a new one.
                os.mkdir(configDir)

        return configDb.encode()
    

    def BindEvents(self):
        """ Binds all the events related to GUI2Exe. """

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # This one won't work in any case, I think
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnClose)
        # We monitor the external compilation process, when started
        self.Bind(wx.EVT_END_PROCESS, self.OnProcessEnded)
        self.Bind(wx.EVT_TIMER, self.OnExeTimer, self.exeTimer)
        # Bind the timer event. This allows us to monitor either the dry-run or
        # the real compilation using an external process which sends back to
        # us its output and error streams, and we monitor them in this event.
        self.Bind(wx.EVT_TIMER, self.OnProcessTimer, self.processTimer)

        # Let's do some fancy checking and painting during the page changing
        # an page closing event for wx.aui.AuiNotebook
        self.mainPanel.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnPageClosing)
        self.mainPanel.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.OnPageClosed)
        self.mainPanel.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.mainPanel.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


    def ReadConfigurationFile(self):
        """ Reads the default configuration file (default project initialization). """

        # This should really be moved in wx.Config
        self.defaultConfig = {"py2exe": {}, "cx_Freeze": {}, "bbfreeze": {},
                              "PyInstaller": {}, "py2app": {}}
        fid = open(opj(self.installDir + "/defaultConfig.txt"), "rt")

        while 1:

            tline = fid.readline().encode()
            
            if not tline:
                fid.close()
                break

            if tline.find("%%") >= 0:
                section = 0
                # Ok, we found a compiler
                current = self.defaultConfig[tline.replace("%%", "").strip()]
                continue

            # I need the "--" separator to differentiate between string input
            # and other things
            if tline.find("--") >= 0:
                section += 1
                continue

            config, projectSwitches = tline.strip().split(":")

            if section:
                # it's not a string. I know eval is evil.
                projectSwitches = eval(projectSwitches)
            else:
                # it's a string, strip it
                projectSwitches = projectSwitches.strip()
                
            current[config] = projectSwitches

        # Read the data from the config file
        options = wx.GetApp().GetConfig()
        menuBar = self.GetMenuBar()

        val = options.Read('PythonVersion')
        if val:
            self.pythonVersion = val.encode()
        val = options.Read('PyInstaller_Path')
        if val:
            self.pyInstallerPath = val.encode()
        val = options.Read('Recurse_Subdirs')
        if val:
            self.recurseSubDirs = eval(val)
            menuBar.Check(ID_Recurse, self.recurseSubDirs)

        val = options.Read('Show_Tooltips')
        if val:
            self.showTips = eval(val)
            menuBar.Check(ID_ShowTip, self.showTips)

        val = options.Read('Delete_Build')
        if val:
            self.deleteBuild = eval(val)
            menuBar.Check(ID_DeleteBuild, self.deleteBuild)
            
        val = options.Read('Clean_Dist')
        if val:
            self.cleanDist = eval(val)
            menuBar.Check(ID_CleanDist, self.cleanDist)

        preferences = {}
        val = options.Read('Preferences')
        if val:
            preferences = eval(val)
        else:
            preferences["Transparency"] = 255
            preferences["Reload_Projects"] = [0, []]
            preferences["Remember_Compiler"] = [0, {}]
            preferences["Window_Size"] = [0, (-1, -1)]
            preferences["Window_Position"] = [0, (-1, -1)]
            preferences["Language"] = "Default"
            preferences["Perspective"] = [0, ""]

        self.preferences = preferences
        wx.GetApp().SetPreferences(preferences)


    def ApplyPreferences(self):
        """ Applies user preferences. """

        # Alpha transparency
        self.SetTransparent(self.preferences["Transparency"])

        # AUI GUI perspective
        choice, perspective = self.preferences["Perspective"]
        if choice:
            self._mgr.LoadPerspective(perspective)
            self._mgr.Update()

        # GUI2Exe Window size
        choice, size = self.preferences["Window_Size"]
        if choice and size > (20, 20):
            self.SetSize(size)
        # GUI2Exe Window position
        choice, position = self.preferences["Window_Position"]
        if choice:
            self.SetPosition(position)
        else:
            self.CenterOnScreen()

        # Reload the projects?
        choice, projects = self.preferences["Reload_Projects"]
        if choice:
            for prj in projects:
                self.projectTree.LoadFromPreferences(prj)


    def GetPreferences(self, key):
        """
        Returns the user preferences for a particular setting.

        @param key: the preferences option name.
        """

        return wx.GetApp().GetPreferences(key)


    def SetPreferences(self, key, value):
        """
        Sets the user preferences for a particular setting.

        @param key: the preferences option name;
        @param value: the preferences option value.
        """

        app = wx.GetApp()
        preferences = app.GetPreferences()
        preferences[key] = value
        app.SetPreferences(preferences)
        
        
    def GetDefaultConfiguration(self, compiler):
        """
        Returns the default configuration for a given compiler.

        @param compiler: the compiler we are using now.
        """

        return self.defaultConfig[compiler]


    # ============================== #
    # Event handlers for GUI2Exe     #
    # ============================== #
    
    def OnNewProject(self, event):
        """ A new project is being created. """

        # Send it to the project tree control
        wx.BeginBusyCursor()
        self.projectTree.NewProject()
        wx.EndBusyCursor()
        if self.mainPanel.GetPageCount() == 1:
            # Only one page, enable the compile buttons!
            self.messageWindow.NoPagesLeft(True)


    def OnSwitchDB(self, event):
        """ Switch to another project database. """

        # Not implemented yet...
        self.RunError(0, _("This option has not been implemented yet."))
        event.Skip()


    def OnSaveProject(self, event):
        """ Saves the current project. """
        
        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        # Use an accessor function, as I need it also somewhere else below        
        self.SaveProject(project)

        
    def OnExportSetup(self, event):
        """ Exports the Setup.py file. """

        page = self.GetCurrentPage()
        
        if not page:
            # No page opened, you can't fool me
            return
        
        outputs = page.PrepareForCompile()
        if not outputs:
            # Setup.py file creation went wrong.
            # Have you set all the required variables?
            return

        # Compilation returns a big string containing the setup script and
        # the directory where the main script lives.
        setupScript, buildDir = outputs

        # Launch the save dialog        
        dlg = wx.FileDialog(self, message=_("Save file as ..."), defaultDir=buildDir,
                            defaultFile="setup.py", wildcard=_pywildspec,
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you.
            fp = file(path, 'w') # Create file anew
            text = setupScript + _standaloneString
            if os.name != "nt":
                text = text.replace("\r\n", "\n").replace("\n", "\r\n")
            else:
                text = text.replace('\r\n', '\n').replace('\r', '\n')

            fp.write(text)
            fp.close()
            transdict = dict(filePath=path)
            self.SendMessage(0, _("File %(filePath)s successfully saved")%transdict)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


    def OnExportProject(self, event):
        """
        Exports a project to a file. Useful for version control systems (svn or cvs)
        in which the project can be saved and reloaded as a file.
        """

        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        # Build the project as a human readable text        
        strs = "# GUI2Exe Generated Project Output\n\n"
        strs += "projectDict = {\n\n"
        strs = PrintTree(strs, project)
        strs += "\n}"

        # Launch the save dialog        
        dlg = wx.FileDialog(self, message=_("Save file as ..."), 
                            defaultFile="%s.g2e"%project.GetName(),
                            wildcard="All files (*.*)|*.*",
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you.
            fp = file(path, 'w') # Create file anew
            fp.write(strs)
            fp.close()
            transdict = dict(projectName=project.GetName(), filePath=path)
            self.SendMessage(0, _("Project %(projectName)s successfully exported to file %(filePath)s")%transdict)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()        

        
    def OnClose(self, event):
        """ Handles the wx.EVT_CLOSE event for the main frame. """

        if self.exeTimer.IsRunning():
            # Kill the monitoring timer
            self.exeTimer.Stop()

        if self.process is not None:
            # Try to kill the process. Doesn't work very well
            self.process.Kill()
            self.processTimer.Stop()

        preferences = wx.GetApp().GetPreferences()

        reload_projects = preferences["Reload_Projects"][0]
        toReload = []
        # Loop over all the opened wx.aui.AuiNotebook pages to see if
        # there are unsaved projects
        for pageNumber in xrange(self.mainPanel.GetPageCount()-1, -1, -1):
            toReload.append(self.mainPanel.GetPageText(pageNumber))
            if not self.HandlePageClosing(pageNumber, event):
                # User pressed cancel
                return

        # Check the user preferences
        if reload_projects:
            # The user wants to reload the opened projects at startup
            toReload.reverse()
            preferences["Reload_Projects"] = [1, toReload]

        if preferences["Window_Size"][0]:
            # The user wants to remeber GUI2Exe window size at startup
            size = self.GetSize()
            if size.x > 20 and size.y > 20:
                vector = (size.x, size.y)
            else:
                # Window size too small (?)
                size = wx.GetDisplaySize()
                # We run at 5/6 of that size
                xvideo, yvideo = 5*size.x/6, 5*size.y/6
                vector = (xvideo, yvideo)
                
            preferences["Window_Size"] = [1, vector]
            
        if preferences["Window_Position"][0]:
            # The user wants to remeber GUI2Exe window positions at startup
            pos = self.GetPosition()
            preferences["Window_Position"] =  [1, (pos.x, pos.y)]

        if preferences["Perspective"][0]:
            # The user wants to remember the AUI perspective
            preferences["Perspective"] =  [1, self._mgr.SavePerspective()]

        # Save back the configuration items
        config = wx.GetApp().GetConfig()
        config.Write('PythonVersion', str(self.pythonVersion))
        config.Write('PyInstaller_Path', str(self.pyInstallerPath))
        config.Write('Recurse_Subdirs', str(self.recurseSubDirs))
        config.Write('Show_Tooltips', str(self.showTips))
        config.Write('Delete_Build', str(self.deleteBuild))
        config.Write('Clean_Dist', str(self.cleanDist))
        config.Write('Preferences', str(preferences))
        config.Flush()

        # Close down the database...
        self.dataBase.CloseSession()

        # Destroy it
        wx.CallAfter(self.Destroy)


    def AccelClosing(self, event):
        """ Handles the Ctrl+W accelerator key (close a page in the central notebook. """

        if self.mainPanel.GetPageCount() == 0:
            # No pages left
            return

        self.HandlePageClosing(self.mainPanel.GetSelection(), event)
        

    def OnPageClosing(self, event):
        """ Handles the wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE event. """

        # Get the selected page
        selection = event.GetSelection()
        # Use the auxiliary method to handle this (is needed also in OnClose)
        self.HandlePageClosing(selection, event)
        

    def OnPageClosed(self, event):
        """ Handles the wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED event. """

        if self.mainPanel.GetPageCount() == 0:
            # Clear the ExecutableProperties list at the bottom left
            self.executablePanel.PopulateList(True, None)
            # Disable the Run and Dry-Run buttons
            self.messageWindow.NoPagesLeft(False)


    def OnPageChanging(self, event):
        """ Handles the wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING event. """

        # Highlight the new item with a bold font
        newBook = self.mainPanel.GetPage(event.GetSelection())
        self.projectTree.HighlightItem(newBook.GetTreeItem(), True)
        
        if event.GetOldSelection() >= 0:
            # Restore the original font for the old item
            oldBook = self.mainPanel.GetPage(event.GetOldSelection())
            self.projectTree.HighlightItem(oldBook.GetTreeItem(), False)

        event.Skip()
        

    def OnPageChanged(self, event):
        """ Handles the wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED event. """

        newBook = self.mainPanel.GetPage(event.GetSelection())
        newProject = newBook.GetProject()
        wx.CallLater(100, self.executablePanel.PopulateList, False, newProject)
        if self.process:
            return
        
        # Disable the dry-run button if not using py2exe
        book = self.GetCurrentBook()
        self.messageWindow.EnableDryRun(book)


    def OnAutoSave(self, event):
        """ Enables/Disables the AutoSave feature. """

        # Not implemented yet...
        self.autoSave = event.IsChecked()


    def OnDeleteBuild(self, event):
        """ Enables/Disables the automatic removal of the "build" folder. """

        # That's easy, we use it later
        self.deleteBuild = event.IsChecked()


    def OnCleanDist(self, event):
        """ Enables/Disables the automatic cleaning of the "dist" folder. """

        # That's easy, we use it later        
        self.cleanDist = event.IsChecked()


    def OnShowTip(self, event):
        """ Enables/Disables the showing of tooltips. """

        self.showTips = event.IsChecked()        
            

    def OnChangePython(self, event):
        """ Changes the Python version. """

        default = os.path.split(self.pythonVersion)[0]
        if wx.Platform == "__WXMSW__":
            wildcard = "Python executable (*.exe)|*.exe"
            fileName = "python.exe"
        else:
            wildcard = "All files (*.*)|*.*"
            fileName = "python"
            
        dlg = wx.FileDialog(self, message=_("Please select the new Python executable ..."), defaultDir=default,
                            defaultFile=fileName, wildcard=wildcard,
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        dlg.CenterOnParent()
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            # Let's see if it is a real python.exe file...
            directory, fileName = os.path.split(path)
            if wx.Platform == "__WXMSW__":
                if fileName.lower() != "python.exe":
                    self.RunError(2, _("The selected file is not a Python executable."))
                    return

            transdict = dict(oldVersion=self.pythonVersion, newVersion=path)
            self.SendMessage(0, _("Python executable changed from %(oldVersion)s to %(newVersion)s")%transdict)
            self.pythonVersion = path
            
        else:
            # Destroy the dialog. Don't do this until you are done with it!
            # BAD things can happen otherwise!
            dlg.Destroy()        


    def OnRecurseSubDir(self, event):
        """
        Switches between directory recursion to simple files adding for the
        data_files option.
        """

        self.recurseSubDirs = event.IsChecked()


    def OnSetPyInstaller(self, event):
        """ Sets the PyInstaller installation path. """

        dlg = wx.DirDialog(self, _("Choose the PyInstaller location:"),
                          style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if os.path.isfile(os.path.normpath(path + "/Build.py")):
                self.pyInstallerPath = path
            else:
                dlg.Destroy()
                self.RunError(2, _("Invalid PyInstaller path: no file named 'Build.py' has been found."))
                return
                
        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        

    def OnTestExecutable(self, event):
        """ Test the compiled executable. """
        
        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        if not project.HasBeenCompiled():
            # The project hasn't been compiled yet
            msg = _("This project has not been compiled yet.")
            self.RunError(2, msg)
            return

        page = self.GetCurrentPage()
        # Try to run the successful compilation accessor method        
        self.SuccessfulCompilation(project, page.GetName(), False)
        

    def OnCustomCode(self, event):
        """ Allows the user to add custom code to the Setup.py file. """

        self.HandleUserCode(post=False)


    def OnPostCompilationCode(self, event):
        """ Allows the user to execute custom code after the building process. """
        
        self.HandleUserCode(post=True)        


    def OnPreferences(self, event):
        """ Edit/view pereferences and settings for GUI2Exe. """

        dlg = PreferencesDialog(None)
        dlg.ShowModal()
        dlg.Destroy()
        
        
    def OnViewSetup(self, event):
        """ Allows the user to see the Setup.py file. """

        wx.BeginBusyCursor()
        # I simply recreate the Setup.py script in memory
        self.RunCompile(view=True, run=False)
        wx.EndBusyCursor()


    def OnCheckSyntax(self, event):
        """
        Checks the Python syntax (for SyntaxError) of the automatically
        generated Setup.py file.
        """

        page = self.GetCurrentPage()
        if not page:
            # No page opened, you can't fool me
            return

        outputs = page.PrepareForCompile()
        if not outputs:
            # Setup.py file creation went wrong.
            # Have you set all the required variables?
            return

        setupScript, buildDir = outputs
        
        # Try to compile the code
        try:
            compile(setupScript, 'test', 'exec')
            self.RunError(0, _("No SyntaxError detected in the automatically generated Setup.py file."))
        except:
            # What can be wrong?
            exception_instance = sys.exc_info()[1]
            msg = _("SyntaxError at line %d, column %d")%(exception_instance.lineno,
                                                          exception_instance.offset)
            self.RunError(2, msg)
            

    def OnViewFullBuild(self, event):
        """
        Allows the user to see the full build process output for the selected
        compiler.
        """

        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        # Get the current LabelBook and compiler name
        book = self.GetCurrentBook()
        page = book.GetPage(book.GetSelection())
        compiler = page.GetName()

        # Retrieve the build output (if any)
        outputText = project.GetBuildOutput(compiler)
        if not outputText:
            # No compilatin has been done
            transdict = dict(compiler=compiler)
            msg = _("This project has not been compiled with %(compiler)s yet.")%transdict
            self.RunError(2, msg)
            return

        # Show the result in a nice dialog
        wx.BeginBusyCursor()
        dlg = BuildDialog(self, project.GetName(), compiler, outputText)
        wx.EndBusyCursor()
        dlg.ShowModal()

        dlg.Destroy()
        wx.SafeYield()
        

    def OnViewMissing(self, event):
        """ Shows the missing modules and dlls. """

        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        book = self.GetCurrentBook()
        page = book.GetPage(book.GetSelection()).GetName()
        if page != "py2exe":
            msg = _("This option is available only for Py2Exe.")
            self.RunError(2, msg)
            return

        if not project.HasBeenCompiled():
            # The project hasn't been compiled yet
            msg = _("This project has not been compiled yet.")
            self.RunError(2, msg)
            return

        wx.BeginBusyCursor()

        # Switch between the "show missing modules" and "show binary dependencies"        
        label = self.GetMenuBar().GetLabel(event.GetId())
        dll = (label.find(_("Binary")) >= 0 and [True] or [False])[0]
        # Run the appropriate frame
        frame = Py2ExeMissing(self, project, dll)
        
        wx.EndBusyCursor()
        

    def OnCompilerSwitches(self, event):
        """ Shows the different compiler switches/options. """

        webbrowser.open_new(opj(self.installDir + "/docs/switches.html"))
        

    def OnTipsAndTricks(self, event):
        """ Shows the compilation tips and tricks. """

        webbrowser.open_new("http://www.py2exe.org/index.cgi/WorkingWithVariousPackagesAndModules")

        
    def OnSaveConfig(self, event):
        """ Saves the current GUI configuration, in terms of panes positions. """

        # Ask the user to enter a configuration name
        dlg = wx.TextEntryDialog(self, _("Enter a name for the new configuration:"),
                                 _("Saving panels configuration"))
        dlg.SetValue((_("Perspective %d"))%len(self.perspectives))
        
        if dlg.ShowModal() != wx.ID_OK:
            # No choice made, go back
            return

        value = dlg.GetValue()
        dlg.Destroy()

        if not value.strip():
            # Empty configuration name?
            self.RunError(2, _("Invalid perspective name!"))
            return
        
        if len(self.perspectives) == 1:
            # Append a separator on the Configuration menu
            self.configMenu.AppendSeparator()

        # Append a new item in the Configuration menu
        item = wx.MenuItem(self.configMenu, ID_FirstPerspective + len(self.perspectives), value,
                           _("Restore GUI configuration: %s")%value)
        item.SetBitmap(self.CreateBitmap("aui_config"))
        self.configMenu.AppendItem(item)

        # Save the current perspective        
        self.perspectives.append(self._mgr.SavePerspective())


    def OnRestorePerspective(self, event):
        """ Restore the selected GUI perspective. """

        self._mgr.LoadPerspective(self.perspectives[event.GetId() - ID_FirstPerspective])
        self._mgr.Update()


    def OnHelp(self, event):
        """ Shows the GUI2Exe help file. """

        # Not implemented yet...
        self.RunError(0, _("This option has not been implemented yet."))


    def OnAPI(self, event):
        """ Shows the GUI2Exe API help file. """

        webbrowser.open_new(opj(self.installDir + "/docs/api/index.html"))

        
    def OnCheckUpgrade(self, event):
        """ Checks for a possible upgrade of GUI2Exe. """

        dlg = wx.ProgressDialog(_("GUI2Exe: Check for upgrade"),
                                _("Attempting to connect to the internet..."), parent=self,
                                style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
        dlg.Pulse()
        # Run in a separate thread
        thread = ConnectionThread(self)
        while thread.isAlive():
            time.sleep(0.3)
            dlg.Pulse()

        dlg.Destroy()
        wx.SafeYield()
        

    def CheckVersion(self, text):
        """
        Called by a worker thread which check my web page on the internet.

        @param text: my web page raw text (if internet connection was successful).
        """
        
        if text is None:
            # We can't get to the internet?
            self.RunError(2, _("Unable to connect to the internet."))
            return

        # A bit shaky, but it seems to work...
        indx = text.find("<small><strong>GUI2Exe")
        version = text[indx:indx+40].split(";")[1]
        version = version[0:version.find("<")]
        if version > __version__:
            # Time to upgrade maybe? :-D
            strs = _("A new version of GUI2Exe is available!\n\nPlease go to " \
                   "http://xoomer.alice.it/infinity77/main/GUI2Exe.html\nif you wish to upgrade.")
            self.RunError(0, strs)
            return

        # No upgrade required
        self.RunError(0, _("At present you have the latest version of GUI2Exe."))        


    def OnContact(self, event):
        """ Launch the mail program to contact the GUI2Exe author. """

        wx.BeginBusyCursor()
        webbrowser.open_new("mailto:andrea.gavana@gmail.com?subject=Comments On GUI2Exe&cc=gavana@kpo.kz")
        wx.CallAfter(wx.EndBusyCursor)


    def OnAbout(self, event):
        """ Shows the about dialog for GUI2Exe. """

        msg = _("This is the about dialog of GUI2Exe.\n\n" + \
              "Version %s \n" + \
              "Author: Andrea Gavana @ 01 Apr 2007\n\n" + \
              "Please report any bug/request of improvements\n" + \
              "to me at the following addresses:\n\n" + \
              "andrea.gavana@gmail.com\ngavana@kpo.kz\n\n" + \
              "Thanks to Cody Precord and the wxPython mailing list\n" + \
              "for the help, ideas and useful suggestions.")%__version__
              
        self.RunError(0, msg)


    def OnProcessTimer(self, event):
        """ Handles the wx.EVT_TIMER event for the main frame. """

        # This event runs only when a compilation process is alive
        # When the process finishes (or dies), we simply stop the timer
        if self.process is not None:
            # Defer to the Process class the message scanning
            self.process.HandleProcessMessages()
        

    def OnProcessEnded(self, event):
        """ Handles the wx.EVT_END_PROCESS for the main frame. """

        # We stop the timer that look for the compilation steps
        self.processTimer.Stop()

        # Handle the (eventual) remaning process messages
        self.process.HandleProcessMessages(True)
        # Destroy the process
        wx.CallAfter(self.process.Destroy)
        # Re-enable the buttons at the bottom
        self.messageWindow.EnableButtons(True)
        # Disable the dry-run button if not using py2exe
        book = self.GetCurrentBook()
        self.messageWindow.EnableDryRun(book)
        # Hide the throbber
        self.messageWindow.ShowThrobber(False)

        # Show the executable data size in the bottom-left list        
        newBook = self.mainPanel.GetPage(self.mainPanel.GetSelection())
        newProject = newBook.GetProject()
        wx.CallLater(100, self.executablePanel.PopulateList, False, newProject)

        self.process = None

        
    def OnExeTimer(self, event):
        """ Handles the wx.EVT_TIMER event for the main frame. """

        # Look if the log file exists
        self.timerCount += 1
        logFile = self.currentExe + ".log"
        if os.path.isfile(logFile):
            # log file is there. The executable crashed for some reason
            self.exeTimer.Stop()
            # Examine the log file
            self.ExamineLogFile(logFile)

        if self.timerCount > 200:
            # More than 20 seconds elapsed... the exe works or the machine
            # is fantastically slow. Reset everything
            self.exeTimer.Stop()
            self.currentExe = None
            self.timerCount = 0


    # ============================== #
    # Auxiliary methods for GUI2Exe  #
    # ============================== #

    def HandleUserCode(self, post):
        """
        Handles the custom and post-compilation code the user may add.

        @param post: whether the code will be pre- or post-compilation.
        """

        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        currentPage = self.mainPanel.GetSelection()
        compiler = self.GetCurrentPage().GetName()
        
        # Retrieve the existing custom code (if any)
        if post:
            customCode = project.GetPostCompileCode(compiler)
        else:
            customCode = project.GetCustomCode(compiler)
            
        # Run the styled text control with the Python code in it, and
        # allow the user to edit it.
        frame = CustomCodeViewer(self, readOnly=False, text=customCode, project=project,
                                 page=currentPage, compiler=compiler, postBuild=post)
        

    def HandlePageClosing(self, selection, event):
        """
        Checks whether a page needs saving before closing.

        @param selection: the current selected tab in the AuiNotebook;
        @param event: the event that has been triggered.
        """

        isAUI = isinstance(event, wx.aui.AuiNotebookEvent)
        # Let's see if the project has been saved or not
        unSaved = self.mainPanel.GetPageBitmap(selection) == self.nbImageList[1]

        # Retrieve all the information we need before closing
        page = self.mainPanel.GetPage(selection)
        project = page.GetProject()
        projectName = project.GetName()
        treeItem = page.GetTreeItem()
        # Check if it is a close event or a wx.aui.AuiNotebookEvent
        isCloseEvent = (event.GetId() == wx.ID_EXIT)

        # Get the preferences for the compiler
        remember_compiler = self.GetPreferences("Remember_Compiler")
        
        if not unSaved:
            # Mark the item as non-edited anymore (if it exists)
            self.projectTree.SetItemEditing(treeItem, False)
            # Save the preferences (if needed)
            remember_compiler[1].update({projectName: page.GetSelection()})
            self.SetPreferences("Remember_Compiler", remember_compiler)
            if not isCloseEvent:
                event.Skip()
                if not isAUI:
                    self.mainPanel.DeletePage(selection)
            return True

        # Not saved. If it wasn't ever saved before, not saving will delete
        # the item from the project tree
        msg = _("Warning: the selected page contains unsaved data.\n\nDo you wish to save this project?")
        answer = self.RunError(3, msg)

        if answer == wx.ID_CANCEL:
            # You want to think about it, eh?
            if isAUI or isCloseEvent:
                event.Veto()
            return False
        elif answer == wx.ID_YES:
            # Save the project, defer to the database
            self.dataBase.SaveProject(project)
            remember_compiler[1].update({projectName: page.GetSelection()})
            self.SetPreferences("Remember_Compiler", remember_compiler)
            if not isCloseEvent:
                # We are handling wx.aui.AuiNotebook close event
                event.Skip()
                if not isAUI:
                    self.mainPanel.DeletePage(selection)
        else:
            # Don't save changes ID_NO
            # Check if the project exists
            projectExists = self.dataBase.IsProjectExisting(project)
            if projectExists:
                remember_compiler[1].update({projectName: page.GetSelection()})
                self.SetPreferences("Remember_Compiler", remember_compiler)

            if not isCloseEvent:
                event.Skip()
                if not isAUI:
                    self.mainPanel.DeletePage(selection)

            if not projectExists:
                # Project is not in the database, so delete the tree item
                self.projectTree.DeleteProject([treeItem])
            else:
                # Mark the item as non-edited anymore (if it exists)
                self.projectTree.SetItemEditing(treeItem, False)       

        return True
            
        
    def SaveProject(self, project):
        """
        Saves the current project.

        @param project: the current project.
        """

        # Send the data to the database        
        self.dataBase.SaveProject(project)
        # Visually indicates that the project has been saved
        self.UpdatePageBitmap(project.GetName(), 0, self.mainPanel.GetSelection())


    def UpdatePageBitmap(self, pageName, pageIcon, selection=None):
        """
        Updates the wx.aui.AuiNotebook page image and text, to reflect the
        current project state (saved/unsaved).

        @param pageName: the name of the tab in the AuiNotebook;
        @param pageIcon: the icon index to set to the tab;
        @param selection: if any, the current selected tab in the AuiNotebook.
        """

        if selection is None:
            # Get the selection ourselves
            selection = self.mainPanel.GetSelection()

        if self.mainPanel.GetPageBitmap(selection) == self.nbImageList[pageIcon]:
            # No way, the page bitmap is the same
            return

        # Change the bitmap and the text        
        self.mainPanel.SetPageBitmap(selection, self.nbImageList[pageIcon])
        self.mainPanel.SetPageText(selection, pageName)
        

    def RunError(self, kind, msg, sendMessage=False):
        """
        An utility method that shows a message dialog with different functionalities
        depending on the input.

        @param kind: the kind of message (error, warning, question, message);
        @param msg: the actual message to display;
        @param sendMessage: Whether to display the message in the bottom log window too.
        """

        if sendMessage:
            # Send a message also to the log window at the bottom
            self.SendMessage(kind, msg.strip("."))

        kindDict = {0: _("Message"), 1: _("Warning"), 2: _("Error"), 3: _("Question")}
        kind = kindDict[kind]
        
        if kind == _("Message"):    # is a simple message
            style = wx.OK | wx.ICON_INFORMATION
        elif kind == _("Warning"):  # is a warning
            style = wx.OK | wx.ICON_EXCLAMATION
        elif kind == _("Question"): # is a question
            style = wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        else:                    # is an error
            style = wx.OK | wx.ICON_ERROR

        # Create the message dialog
        dlg = wx.MessageDialog(None, msg, "GUI2Exe %s"%kind, style|wx.STAY_ON_TOP)
        answer = dlg.ShowModal()
        dlg.Destroy()

        if kind == _("Question"):
            # return the answer, it was a question
            return answer


    def AddNewProject(self, treeItem, projectName):
        """
        Adds a new project to the current center pane.

        @param treeItem: the item in the left TreeCtrl;
        @param projectName: the new project name.
        """

        # Freeze all. It speeds up a bit the drawing
        busy = PyBusyInfo(_("Creating new project..."), self)
        wx.SafeYield()
        
        self.Freeze()

        # Create a new project, dictionary-based
        project = Project(self.defaultConfig, projectName)
        # The Project method adds a page to the center pane
        # I need it in another method as I use it also elsewhere below
        self.Project(project, treeItem, True)
        
        # Send a message to the log window at the bottom
        transdict = dict(projectName=projectName)
        self.SendMessage(0, _('New project "%(projectName)s" added')%transdict)

        # Time to warm up...        
        self.Thaw()
        del busy


    def LoadProject(self, treeItem, projectName):
        """
        Loads a project in the center pane.

        @param treeItem: the item in the left TreeCtrl;
        @param projectName: the existing project name.
        """

        # Check if there already is a page with the same name
        page = self.IsAlreadyOpened(treeItem)
        if page is not None:
            # There is, bring the page into focus
            self.mainPanel.SetSelection(page)
            return

        wx.BeginBusyCursor()
        
        # Load the project from the database
        project = self.dataBase.LoadProject(projectName)
        # The Project method adds a page to the center pane
        self.Project(project, treeItem, False)
        projectName = project.GetName()
        if self.mainPanel.GetPageCount() == 1:
            # Disable the Run and Dry-Run buttons
            self.messageWindow.NoPagesLeft(True)

        book = self.GetCurrentBook()
        remember, projects = self.GetPreferences("Remember_Compiler")
        if projectName in projects and remember:
            # Get the current LabelBook
            book.SetSelection(projects[projectName])
            page = book.GetPage(projects[projectName])
            wx.CallAfter(page.SetFocusIgnoringChildren)
            
        # Send a message to the log window at the bottom
        transdict = dict(projectName=projectName)
        self.SendMessage(0, _('Project "%(projectName)s" successfully loaded')%transdict)

        book.UpdatePageImages()
        wx.EndBusyCursor()
        

    def RenameProject(self, treeItem, oldName, newName):
        """
        The user has renamed the project in the project tree control.

        @param treeItem: the item in the left TreeCtrl;
        @param oldName: the old project name;
        @param newName: the new project name.
        """

        # Rename the project in the database
        project = self.dataBase.RenameProject(oldName, newName)
        # Update information on screen (if needed)
        page = self.WalkAUIPages(treeItem)
        if page is None:
            # This page is not opened, go back
            return

        # Set the new name in the wx.aui.AuiNotebook tab
        self.mainPanel.SetPageText(page, newName)
        book = self.mainPanel.GetPage(page)
        if project is None:
            # Never saved in the database
            project = book.GetProject()
            project.SetName(newName)
            
        book.SetProject(project)
        # Update the label in the central panel
        for indx in xrange(book.GetPageCount()):
            book.GetPage(indx).UpdateLabel(project.GetName(), project.GetCreationDate())
        
        
    def Project(self, project, treeItem, isNew):
        """
        Auxiliary method used to actually add a page to the center pane.

        @param project: the project we are creating/loading;
        @param treeItem: the item in the left TreeCtrl;
        @param isNew: whether the project is a new one or we are loading an existing one.
        """

        # Get the project name        
        projectName = project.GetName()
        # Add a page to the wx.aui.AuiNotebook
        page = AUINotebookPage(self.mainPanel, project, _compilers)
        # Check project name and bitmap depending on the isNew state
        pageName = (isNew and [projectName+"*"] or [projectName])[0]
        bmp = (isNew and [1] or [0])[0]

        # Assing project and treeItem to the added page
        page.SetProject(project)
        page.SetTreeItem(treeItem)

        # Add the page to the wx.aui.AuiNotebook        
        self.mainPanel.AddPage(page, pageName, True, bitmap=self.nbImageList[bmp])
                

    def WalkAUIPages(self, treeItem):
        """
        Walks over all the opened page in the center pane.

        @param treeItem: the item in the left TreeCtrl.
        """

        # Loop over all the wx.aui.AuiNotebook pages
        for indx in xrange(self.mainPanel.GetPageCount()):
            page = self.mainPanel.GetPage(indx)
            if page.GetTreeItem() == treeItem:
                # Yes, the page is already opened
                return indx

        # No page like that is there
        return None            
        

    def IsAlreadyOpened(self, treeItem):
        """
        Looks if a page is already opened.

        @param treeItem: the item in the left TreeCtrl.
        """

        return self.WalkAUIPages(treeItem)
    
    
    def CloseAssociatedPage(self, treeItem):
        """
        A method used to close a wx.aui.AuiNotebook page when an item in the
        project tree is deleted.

        @param treeItem: the item in the left TreeCtrl.        
        """

        page = self.WalkAUIPages(treeItem)
        if page is not None:
            self.mainPanel.DeletePage(page)


    def ReassignPageItem(self, oldItem, newItem):
        """
        Reassigns an item to an opened page after a drag and drop operation.

        @param oldItem: the old item in the left TreeCtrl;
        @param newItem: the new item in the left TreeCtrl.
        """

        page = self.WalkAUIPages(oldItem)
        if page is not None:
            # We found an opened page
            page = self.mainPanel.GetPage(page)
            page.SetTreeItem(newItem)


    def FillStatusBar(self):
        """ Fills the statusbar fields with different information. """

        # Get the wxPython version information
        wxPythonVersion = wx.version()
        statusText = "wxPython %s"%wxPythonVersion

        for compiler, version in _compilers.items():
            # adds the compilers information found
            statusText += ", %s %s"%(compiler, version)

        # Ah, by the way, thank you menu bar for deleting my status bar messages...            
        self.statusBar.SetStatusText(statusText, 1)
        self.statusBar.SetStatusText(_("Welcome to GUI2Exe"), 0)


    def CreateBitmap(self, bmpName):
        """
        Utility function to create bitmap passing a filename.

        @param bmpName: the bitmap name (without extension).
        """

        return CreateBitmap(bmpName)
    

    def GetCurrentPage(self):
        """ Returns the current LabelBook page. """

        book = self.GetCurrentBook()
        if not book:
            # No page opened, you can't fool me
            return
        
        return book.GetPage(book.GetSelection())


    def GetCurrentBook(self):
        """ Returns the current wx.aui.AuiNotebook page (a LabelBook). """

        if self.mainPanel.GetPageCount() == 0:
            # No page opened, fire an error
            msg = "No project has been loaded."
            self.RunError(2, msg, True)
            return None

        # Return the current page (is a LabelBook)
        selection = self.mainPanel.GetSelection()
        return self.mainPanel.GetPage(selection)
        

    def GetCurrentProject(self):
        """ Returns the current project associated to a LabelBook. """

        book = self.GetCurrentBook()
        if not book:
            # No page opened, you can't fool me
            return
        
        return book.GetProject()
    

    def CleanDistDir(self):
        """ Cleans up the distribution folder. """

        self.SendMessage(0, _("Cleaning the distribution folder..."))
        
        page = self.GetCurrentPage()
        # Get all the information we need about this project        
        compiler = page.GetName()
        project = self.GetCurrentProject()

        # Retrieve the distribution directory for the selected compiler
        dist_dir = project.GetDistDir(compiler)
        # Remove the dist directory altogether
        shutil.rmtree(dist_dir, ignore_errors=True)


    def AccelRun(self, event):
        """ Handles the F5 key to run the compilation process. """

        if self.process:
            # Compilation already running
            self.RunError(2, _("One instance of the building process is already running."))
            return

        # Run the compilation process        
        self.RunCompile(view=False, run=True)


    def RunCompile(self, view, run):
        """
        Auxiliary method. Depending on the input, it does different things.

        @param view: whether the user wants to view the Setup.py file or run it;
        @param run: whether the user wants a normal build or a Dry-Run (py2exe only).

        Possible combinations:        
        - view=True ==> Get the Setup.py script and displays it (run is discarded);
        - run=False ==> Start a dry-run (a compilation that does nothing);
        - run=True  ==> Start the real compilation process.
        """
    
        page = self.GetCurrentPage()
        if not page:
            # No page opened, you can't fool me
            return

        if not view and not run and page.GetName() != "py2exe":
            msg = _("The Dry-Run option is available only for Py2Exe.")
            self.RunError(2, msg)
            return
        
        outputs = page.PrepareForCompile()
        if not outputs:
            # Setup.py file creation went wrong.
            # Have you set all the required variables?
            return

        setupScript, buildDir = outputs
    
        if view:    # we just want to view the code
            frame = CustomCodeViewer(self, readOnly=True, text=setupScript+_standaloneString)
            return

        # Show the throbber
        self.messageWindow.ShowThrobber(True)

        if self.cleanDist:
            # Clean up the distribution folder
            self.CleanDistDir()
        
        # Disable the run buttons
        self.messageWindow.EnableButtons(False)

        # Get all the information we need about this project        
        compiler = page.GetName()
        project = self.GetCurrentProject()
        currentPage = self.mainPanel.GetSelection()

        transdict = dict(pythonExecutable=self.pythonVersion)
        self.SendMessage(0, _("Starting compilation with Python executable: %(pythonExecutable)s")%transdict)
        transdict = dict(compiler=compiler.upper())
        self.SendMessage(0, _("The compiler selected is ==> %(compiler)s <==")%transdict)
        
        # Start the external process, which is actually subclassed in
        # The Process class
        self.process = Process(self, buildDir, setupScript, run, compiler,
                               project, currentPage, self.pythonVersion)

        # Start the monitoring timer
        self.processTimer.Start(1000)
        # Start the process
        self.process.Start()


    def KillCompile(self):
        """ Kills (or tries to) the compilation process. """

        if not self.process:
            # Nothing is running yet
            return
        
        # Stop the process timer
        self.processTimer.Stop()
        # This doesn't work, at least on Windows.
        # The process is still there and there is no os.kill on Windows
        self.process.Kill()
        # Send a failure message to the log window at the bottom
        self.SendMessage(1, _("Compilation killed by user"))
        # Re-enable the run buttons
        self.messageWindow.EnableButtons(True)

        # Disable the dry-run button if not using py2exe
        book = self.GetCurrentBook()
        self.messageWindow.EnableDryRun(book)
            

    def SuccessfulCompilation(self, project, compiler, ask=True):
        """
        Assumes that the compilation process was successful and tries to test
        the new exe file.

        @param project: the current project;
        @param compiler: the compiler used to build the current project;
        @param ask: whether to ask the user to test the executable or not.        
        """

        if ask:
            # We came from an wx.EVT_END_PROCESS event
            msg = _("The compiler has successfully built your executable.\n" \
                    "Do you wish to test your application?")
            answer = self.RunError(3, msg)
            if answer != wx.ID_YES:
                return

        msg = _("This project has never been compiled or its executable has been deleted.")
        # Get the executable name from the Project class
        try:
            exeName = project.GetExecutableName(compiler)
        except:
            self.RunError(2, msg)
            return

        if wx.Platform != '__WXMAC__':
            if not os.path.isfile(exeName):
                # No such file, have you compiled it?
                self.RunError(2, msg)
                return
        else:
            # On OSX .app files are directories so just check that it exists
            if not os.path.exists(exeName):
                self.RunError(2, msg)
                return

        # Starts the compiled exe file
        msg = _("Starting compiled executable...")
        busy = PyBusyInfo(msg, self)
        wx.SafeYield()
        self.SendMessage(0, msg) 

        logFile = exeName + ".log"
        # Remove the log file or it will fool us later
        if os.path.isfile(logFile):
            try:
                os.remove(logFile)
            except:
                pass
            
        self.currentExe = exeName
        pwd = os.getcwd()
        directory, exe = os.path.split(exeName)
        os.chdir(directory)

        if compiler == "py2exe":
            # Start the monitoring timer to check if a log file is created
            self.exeTimer.Start(100)

        if wx.Platform == "__WXGTK__":
            exe = "./" + exe
        elif wx.Platform == "__WXMAC__":
            exe = "open %s" % exe

        if sys.version[0:3] > "(2,4)":
            # subprocess is new in 2.4
            subprocess.Popen(exe, shell=(not subprocess.mswindows))
        else:
            if wx.Platform == "__WXGTK__":
                # GTK doesn't like os.spawnl...
                os.system(exe + " &")
            else:
                os.spawnl(os.P_NOWAIT, exe)
        
        del busy
        wx.SafeYield()
        os.chdir(pwd)


    def ExamineLogFile(self, logFile):
        """
        Examine a log file, created by an executable that crashed for some reason.

        @param logFile: the log file name created when errors happens (py2exe only).
        """

        # Reset few variables, we don't need them anymore
        self.currentExe = None
        self.timerCount = 0

        # Send the error message to the log window at the bottom
        self.SendMessage(2, _("Executable terminated with errors or warnings"))
        
        # Ask the user if he/she wants to examine the tracebacks in the log file
        transdict = dict(logFile=logFile)
        msg = _("It appears that the executable generated errors in file:\n\n%(logFile)s\n\nDo you want to examine the tracebacks?")%transdict
        answer = self.RunError(3, msg)
        if answer != wx.ID_YES:
            return

        wx.BeginBusyCursor()

        # Read the log file        
        fid = open(logFile, "rt")
        msg = fid.read()
        fid.close()
        # And displays it in a scrolled message dialog
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, _("Tracebacks in log file"))
        wx.EndBusyCursor()
        dlg.ShowModal()
        dlg.Destroy()

        
    def SendMessage(self, kind, message, copy=False):
        """
        Sends a message to the log window at the bottom.

        @param kind: the kind of message (error, warning, message);
        @param message: the actual message to display;
        @param copy: whether to save this message in the log window stack.
        """

        self.messageWindow.SendMessage(kind, message, copy)
        

    def CopyLastMessage(self):
        """ Re-sends the previous message to the log window (for long processes). """

        self.messageWindow.CopyLastMessage()
        

    def GetVersion(self):
        """ Return the current GUI2Exe version. """

        return wx.GetApp().GetVersion()
    

    def GetPyInstallerPath(self):
        """ Returns the path where PyInstaller is installed. """
        
        return self.pyInstallerPath
        

    def CreateManifestFile(self, project, compiler):
        """
        Create a XP-style manifest file if requested.

        @param project: the current project;
        @param compiler: the compiler used to build this project.
        """

        if wx.Platform != "__WXMSW__":
            # Wrong platform
            return

        try:
            outputs = project.GetManifestFileName(compiler)
        except AttributeError:
            # The current project has not manifest file name
            return

        if not outputs:
            # No manifest file created
            return
        
        manifestFile, programName = outputs
        # Save the manifest file to the user distribution directory
        fid = open(manifestFile, "wt")
        fid.write((_manifest_template % dict(prog=programName))[25:-4])
        fid.close()


    def ResetConfigurations(self, selectedItem, project):
        """
        Updates a project from an external file.

        @param selectedItem: the selected item in the left TreeCtrl;
        @param project: the current project.
        """

        # Update information on screen (if needed)
        page = self.WalkAUIPages(selectedItem)
        if page is None:
            self.SendMessage(0, _("Project successfully updated from file."))
            # This page is not opened, go back
            return        

        page = self.mainPanel.GetPage(page)
        self.mainPanel.Freeze()
        # Loop over all the pages in the LabelBook
        for indx in xrange(page.GetPageCount()):
            book = page.GetPage(indx)
            name = book.GetName()
            # Erase the old configuration, add the new one
            book.SetConfiguration(project[name], delete=True)

        self.mainPanel.Thaw()
        self.SendMessage(0, _("Project successfully updated from file."))
        

class GUI2ExeSplashScreen(AS.AdvancedSplash):
    """ A fancy splash screen class, with a shaped frame. """

    def __init__(self, app):
        """
        A fancy splash screen :-D

        @param app: the current wxPython app.
        """

        # Retrieve the bitmap used for the splash screen
        bmp = catalog["gui2exe_splash"].GetBitmap()
        # Create the splash screen
        AS.AdvancedSplash.__init__(self, None, bitmap=bmp, timeout=5000,
                                   extrastyle=AS.AS_TIMEOUT|AS.AS_CENTER_ON_SCREEN)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # Show the main application after 2 seconds
        self.fc = wx.FutureCall(2000, self.ShowMain)
        self.app = app


    def OnClose(self, event):
        """ Handles the wx.EVT_CLOSE event for GUI2ExeSplashScreen. """
        
        # Make sure the default handler runs too so this window gets
        # destroyed
        event.Skip()
        self.Hide()
        
        # if the timer is still running then go ahead and show the
        # main frame now
        if self.fc.IsRunning():
            # Stop the wx.FutureCall timer
            self.fc.Stop()
            self.ShowMain()


    def ShowMain(self):
        """ Shows the main application (GUI2Exe). """

        # Get the size of the display
        size = wx.GetDisplaySize()
        # We run at 5/6 of that size
        xvideo, yvideo = 5*size.x/6, 5*size.y/6
        frame = GUI2Exe(None, -1, "", size=(xvideo, yvideo))

        self.app.SetTopWindow(frame)
        frame.Show()

        if self.fc.IsRunning():
            # Stop the splash screen timer and close it
            self.Raise()
            
            
class GUI2ExeApp(wx.App):
    """ The main application class. """
    
    def OnInit(self):
        """ Default wx.App initialization. """

        # Set the default python encoding (not that it helps...)
        wx.SetDefaultPyEncoding("utf-8")
        self.SetAppName("GUI2Exe")

        try:
            installDir = os.path.dirname(os.path.abspath(__file__))
        except:
            installDir = os.path.dirname(os.path.abspath(sys.argv[0]))

        self.installDir = installDir.decode(sys.getfilesystemencoding())

        # Retrieve the user configuration directory (if any)
        language = self.GetPreferences("Language")
        if not language:
            # Missing preferences...
            language = "Default"
                
        # Setup Locale
        locale.setlocale(locale.LC_ALL, '')
        self.locale = wx.Locale(GetLangId(installDir, language))
        if self.locale.GetCanonicalName() in GetAvailLocales(installDir):
            self.locale.AddCatalogLookupPathPrefix(os.path.join(installDir, "locale"))
            self.locale.AddCatalog("GUI2Exe")
        else:
            del self.locale
            self.locale = None

        # Set up the exception handler...
        sys.excepthook = ExceptionHook

        # Start our application
        splash = GUI2ExeSplashScreen(self)
        splash.Show()

        return True
        

    def OnExit(self, evt=None, force=False):
        """
        Handle application exit request

        @param evt: event that called this handler
        """

        self.Exit()


    def GetVersion(self):
        """ Return the current GUI2Exe version. """

        return __version__


    def GetInstallDir(self):
        """ Returns the installation directory for GUI2Exe. """

        return self.installDir        


    def GetDataDir(self):
        """ Returns the option directory for GUI2Exe. """
        
        sp = wx.StandardPaths.Get()
        return sp.GetUserDataDir()


    def GetConfig(self):
        """ Returns the configuration for GUI2Exe. """
        
        if not os.path.exists(self.GetDataDir()):
            # Create the data folder, it still doesn't exist
            os.makedirs(self.GetDataDir())

        config = wx.FileConfig(localFilename=os.path.join(self.GetDataDir(), "options"))
        return config


    def LoadConfig(self):
        """ Checks for the option file in wx.Config. """

        userDir = self.GetDataDir()
        fileName = os.path.join(userDir, "options")
        preferences = {}
        
        # Check for the option configuration file
        if os.path.isfile(fileName):
            options = wx.FileConfig(localFilename=fileName)
            # Check for preferences if they exist
            val = options.Read('Preferences')
            if val:
                # Evaluate preferences
                preferences = eval(val)
        
        return preferences
    

    def GetPreferences(self, preferenceKey=None):
        """
        Returns the user preferences as stored in wx.Config.

        @param preferenceKey: the preference to load
        """

        preferences = self.LoadConfig()
        if preferenceKey is None:
            return preferences

        optionVal = None        
        if preferenceKey in preferences:            
            optionVal = preferences[preferenceKey]

        return optionVal        


    def SetPreferences(self, newPreferences):
        """ Save the user preferences in wx.Config. """

        preferences = self.LoadConfig()
        config = self.GetConfig()
        for key in newPreferences:
            preferences[key] = newPreferences[key]
            
        config.Write("Preferences", str(preferences))
                    
        config.Flush()


#----------------------------------------------------------------------------#
                
if __name__ == "__main__":
    # Start the whole thing
    app = GUI2ExeApp(0)
    app.MainLoop()

