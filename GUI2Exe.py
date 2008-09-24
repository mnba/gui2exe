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
sys.setdefaultencoding('utf-8')
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

# Let's import few modules I have written for GUI2Exe
from ProjectTreeCtrl import ProjectTreeCtrl
from MessageWindow import MessageWindow
from ExecutableProperties import ExecutableProperties
from AUINotebookPage import AUINotebookPage
from DataBase import DataBase
from Project import Project
from Process import Process
from Widgets import CustomCodeViewer, Py2ExeMissing, PyBusyInfo, BuildDialog
from Utilities import opj, odict, PrintTree, ConnectionThread
from Constants import _auiImageList, _pywildspec, _defaultCompilers, _manifest_template
from AllIcons import catalog

# And import the fancy AdvancedSplash
import AdvancedSplash as AS

# I need that to have restorable perspectives
ID_FirstPerspective = wx.ID_HIGHEST + 10001

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
    
    def __init__(self, parent, id=-1, title="", pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE):
        """ Default wx.Frame class constructor. """
        
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # Yes, I know, I am obsessively addicted to wxAUI
        self._mgr = wx.aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        # Some default starting values for our class
        # where are we
        try:
            self.installDir = os.path.dirname(os.path.abspath(__file__))
        except:
            self.installDir = os.path.dirname(os.path.abspath(sys.argv[0]))

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
        self.showTips = False                # Show tooltips for various compiler options
        self.openingPages = {}               # Used to remember the last used compiler for every project
        
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
            strs = "The database file and its backup seem to be broken.\n\n" \
                   "Please go to the /USER/Application Data/.GUI2Exe/ folder\n" \
                   "and delete the GUI2Exe database file."
            self.RunError("Error", strs)
            self.Destroy()
            return

        # Add the panes to the wxAUI manager
        # Very nice the bug introduced in wxPython 2.8.3 about wxAUI Maximize buttons...
        self._mgr.AddPane(self.projectTree, wx.aui.AuiPaneInfo().Left().
                          Caption("GUI2Exe Projects").MinSize(wx.Size(250, -1)).
                          FloatingSize(wx.Size(200, 300)).Layer(1).MaximizeButton())
        self._mgr.AddPane(self.executablePanel, wx.aui.AuiPaneInfo().Left().
                          Caption("Executable Properties").MinSize(wx.Size(200, 100)).
                          BestSize(wx.Size(200, size[1]/6)).MaxSize(wx.Size(200, 100)).
                          FloatingSize(wx.Size(200, 200)).Layer(1).Position(1).MaximizeButton())
        self._mgr.GetPane(self.executablePanel).dock_proportion = 100000/4
        self._mgr.AddPane(self.mainPanel, wx.aui.AuiPaneInfo().CenterPane())
        self._mgr.AddPane(self.messageWindow, wx.aui.AuiPaneInfo().Bottom().
                          Caption("Messages And Actions").MinSize(wx.Size(200, 100)).
                          FloatingSize(wx.Size(500, 300)).BestSize(wx.Size(200, size[1]/6)).
                          MaximizeButton())
        
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
        # Read the default configuration file. At the moment it contains data
        # only for py2exe, and it might be moved to wx.Config
        self.ReadConfigurationFile()


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
        
        return (("&File",
                    ("&New project...\tCtrl+N", "Add a new project to the project tree", "project", self.OnNewProject, ""),
                    ("Switch project &database...\tCtrl+D", "Load another GUI2Exe database file", "switch_db", self.OnSwitchDB, ""),
                    ("", "", "", "", ""),
                    ("&Save project\tCtrl+S", "Save the current project to database", "save_project", self.OnSaveProject, ""),
                    ("&Save project as...\tCtrl+Shift+S", "Save the current project to a file", "save_to_file", self.OnExportProject, ""),
                    ("", "", "", "", ""),
                    ("&Export setup file...\tCtrl+E", "Export the Setup.py file", "export_setup", self.OnExportSetup, ""),
                    ("", "", "", "", ""),
                    ("&Quit\tCtrl+Q", "Exit GUI2Exe", "exit", self.OnClose, "")),
                ("&Options",
                    ("Use &AutoSave", "AutoSaves your work every minute", "", self.OnAutoSave, wx.ITEM_CHECK),
                    ("", "", "", "", ""),
                    ('De&lete "build" directory', "Delete the build folder at every compilation", "", self.OnDeleteBuild, wx.ITEM_CHECK),
                    ('Clea&n "dist" directory', "Clean the distribution folder at every compilation", "", self.OnCleanDist, wx.ITEM_CHECK),
                    ("", "", "", "", ""),
                    ("&Recurse sub-dirs for data_files option", "Recurse sub-directories for data_files option if checked", "", self.OnRecurseSubDir, wx.ITEM_CHECK),
                    ("Show t&ooltips", "show tooltips for the various compiler options", "", self.OnShowTip, wx.ITEM_CHECK),
                    ("", "", "", "", ""),
                    ("Change &Python version...\tCtrl+H", "Temporarily changes the Python version", "python_version", self.OnChangePython, ""),
                    ("Set P&yInstaller path...\tCtrl+Y", "Sets the PyInstaller installation path", "PyInstaller_small", self.OnSetPyInstaller, ""),
                    ("", "", "", "", ""),
                    ("Add &custom code...\tCtrl+U", "Add custom code to the setup script", "custom_code", self.OnCustomCode, ""),
                    ("&Insert post compilation code...\tCtrl+I", "Add custom code to be executed after the building process", "post_compile", self.OnPostCompilationCode, "")),                    
                ("&Builds",
                    ("&Test executable\tCtrl+R", "Test the compiled file (if it exists)", "runexe", self.OnTestExecutable, ""),
                    ("", "", "", "", ""),
                    ("View &setup script\tCtrl+P", "View the auto-generated setup script", "view_setup", self.OnViewSetup, ""),
                    ("&Check setup script syntax\tCtrl+X", "Check the syntax of the auto-generated setup script", "spellcheck", self.OnCheckSyntax, ""),
                    ("", "", "", "", ""),
                    ("Show &full build output\tCtrl+F", "View the full build output for the current compiler", "full_build", self.OnViewFullBuild, ""),
                    ("", "", "", "", ""),                 
                    ("&Missing modules\tCtrl+M", "What the compiler thinks are the missing modules (py2exe only)", "missingmodules", self.OnViewMissing, ""),
                    ("&Binary dependencies\tCtrl+B", "What the compiler says are the binary dependencies (py2exe only)", "binarydependencies", self.OnViewMissing, "")),
                ("&View",
                    ("Save &panes configuration...", "Save the current GUI panes configuration", "save_aui_config", self.OnSaveConfig, ""),
                    ("Restore original &GUI\tCtrl+G", "Restore the original GUI appearance", "restore_aui", self.OnRestorePerspective, "")),
                ("&Help",
                    ("GUI2Exe &help\tF1", "Opens the GUI2Exe help", "help", self.OnHelp, ""),
                    ("GUI2Exe &API\tF2", "Opens the GUI2Exe API reference", "api_reference", self.OnAPI, ""),
                    ("", "", "", "", ""),
                    ("Compiler s&witches\tF3", "Show compilers switches and common options", "compiler_switches", self.OnCompilerSwitches, ""),
                    ("&Tips and tricks\tF4", "Show compilation tips and tricks", "tips_and_tricks", self.OnTipsAndTricks, ""),
                    ("", "", "", "", ""),
                    ("Check for &upgrade\tF9", "Check for a GUI2Exe upgrade", "upgrade", self.OnCheckUpgrade, ""),
                    ("", "", "", "", ""),
                    ("&Contact the Author...", "Contact Andrea Gavana by e-mail", "contact", self.OnContact, ""),
                    ("&About GUI2Exe...", "About GUI2Exe and the Creator...", "about", self.OnAbout, "")))
                    
                    
    def CreateMenu(self, menuData):
        """ Creates a menu based on input menu data. """
        
        menu = wx.Menu()

        # Here is a bit trickier than what presented in Robin and Noel book,
        # but not that much.
        for eachLabel, eachStatus, eachIcon, eachHandler, eachKind in menuData:

            if not eachLabel:
                menu.AppendSeparator()
                continue

            # I need to find which menu holds the wxAUI-based "restore perspective"
            # as I have to bind on wx.EVT_MENU_RANGE with a specific start id 
            id = (eachLabel.find("Restore") >= 0 and [ID_FirstPerspective] or [-1])[0]
            # The about menu on Mac should go on the application menu
            id = (eachLabel.find("About") >= 0 and [wx.ID_ABOUT] or [-1])[0]
            # The exit menu is more special
            id = (eachLabel.find("Quit") >= 0 and [wx.ID_EXIT] or [-1])[0]
            # There are also few check menu items around...
            kind = (eachKind and [eachKind] or [wx.ITEM_NORMAL])[0]

            menuItem = wx.MenuItem(menu, id, eachLabel, eachStatus, kind=kind)
            if eachIcon:
                # Check menu items usually don't have associated icons
                menuItem.SetBitmap(self.CreateBitmap(eachIcon))

            menu.AppendItem(menuItem)
            if eachLabel.find('"build"') >= 0:
                # By default the "remove build directory" is on
                menuItem.Check(True)

            if eachLabel.find("tooltips") >= 0:
                # By default we activate the tooltips, unless in the wx.Config
                # it's set to False
                menuItem.Check(True)
                
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

        # I need to keep track of this menu
        id = menuBar.FindMenu("View")
        self.configMenu = menuBar.GetMenu(id)

        # We're done with the menubar
        self.SetMenuBar(menuBar)

        # Add an accelerator for the Ctrl+W switch
        idClose, idRun = wx.NewId(), wx.NewId()
        self.Bind(wx.EVT_MENU, self.AccelClosing, id=idClose)
        self.Bind(wx.EVT_MENU, self.AccelRun, id=idRun)
        self.accelTable = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("w"), idClose),
                                               (wx.ACCEL_NORMAL, wx.WXK_F5, idRun)])
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

        options = self.GetConfig()
        menuBar = self.GetMenuBar()

        val = options.Read('PythonVersion')
        if val:
            self.pythonVersion = val
        val = options.Read('PyInstaller_Path')
        if val:
            self.pyInstallerPath = val
        val = options.Read('Recurse_Subdirs')
        if val:
            self.recurseSubDirs = eval(val)
            item = menuBar.FindMenuItem("Options", "Recurse sub-dirs for data_files option")
            menuBar.Check(item, self.recurseSubDirs)

        val = options.Read('Show_Tooltips')
        if val:
            self.showTips = eval(val)
            item = menuBar.FindMenuItem("Options", "Show tooltips")
            menuBar.Check(item, self.showTips)

        val = options.Read('Delete_Build')
        if val:
            self.deleteBuild = eval(val)
            item = menuBar.FindMenuItem("Options", 'Delete "build" directory')
            menuBar.Check(item, self.deleteBuild)
            
        val = options.Read('Clean_Dist')
        if val:
            self.cleanDist = eval(val)
            item = menuBar.FindMenuItem("Options", 'Clean "dist" directory')
            menuBar.Check(item, self.cleanDist)

        val = options.Read('Opened_Pages')
        if val:
            self.openingPages = eval(val)


    def GetDefaultConfiguration(self, compiler):
        """ Returns the default configuration for a given compiler. """

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


    def OnSwitchDB(self, event):
        """ Switch to another project database. """

        # Not implemented yet...
        self.RunError("Message", "This option has not been implemented yet.")
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
        dlg = wx.FileDialog(self, message="Save file as ...", defaultDir=buildDir,
                            defaultFile="Setup.py", wildcard=_pywildspec,
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you.
            fp = file(path, 'w') # Create file anew
            fp.write(setupScript)
            fp.close()
            self.SendMessage("Message", "File %s successfully saved"%path)

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
        dlg = wx.FileDialog(self, message="Save file as ...", 
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
            self.SendMessage("Message", "Project %s successfully exported to file %s"% \
                             (project.GetName(), path))

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

        # Loop over all the opened wx.aui.AuiNotebook pages to see if
        # there are unsaved projects
        for pageNumber in xrange(self.mainPanel.GetPageCount()-1, -1, -1):
            if not self.HandlePageClosing(pageNumber, event):
                # User pressed cancel
                return

        # Save back the configuration items
        config = self.GetConfig()
        config.Write('PythonVersion', str(self.pythonVersion))
        config.Write('PyInstaller_Path', str(self.pyInstallerPath))
        config.Write('Recurse_Subdirs', str(self.recurseSubDirs))
        config.Write('Show_Tooltips', str(self.showTips))
        config.Write('Delete_Build', str(self.deleteBuild))
        config.Write('Clean_Dist', str(self.cleanDist))
        config.Write('Opened_Pages', str(self.openingPages))
        config.Flush()

        # Close down the database...
        self.dataBase.CloseSession()

        # Destoy it
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
            
        dlg = wx.FileDialog(self, message="Please select the new Python executable ...", defaultDir=default,
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
                    self.RunError("Error", "The selected file is not a Python executable.")
                    return
            
            self.SendMessage("Message", "Python executable changed from %s to %s"%(self.pythonVersion, path))
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

        dlg = wx.DirDialog(self, "Choose the PyInstaller location:",
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
                self.RunError("Error", "Invalid PyInstaller path: no file named Build.py has been found.")
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
            msg = "This project has not been compiled yet."
            self.RunError("Error", msg)
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
            self.RunError("Message", "No SyntaxError detected in the automatically generated Setup.py file. ")
        except:
            # What can be wrong?
            exception_instance = sys.exc_info()[1]
            msg = "SyntaxError at line %d, column %d"%(exception_instance.lineno,
                                                       exception_instance.offset)
            self.RunError("Error", msg)
            

    def OnViewFullBuild(self, event):
        """
        Allows the user to see the full build process output for the selected
        compiler.
        """

        project = self.GetCurrentProject()
        if not project:
            # No page opened, you can't fool me
            return

        book = self.GetCurrentBook()
        page = book.GetPage(book.GetSelection())
        compiler = page.GetName()

        outputText = project.GetBuildOutput(compiler)
        if not outputText:            
            msg = "This project has not been compiled with %s yet."%compiler
            self.RunError("Error", msg)
            return

        dlg = BuildDialog(self, project.GetName(), compiler, outputText)
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
            msg = "This option is available only for Py2Exe."
            self.RunError("Error", msg)
            return

        if not project.HasBeenCompiled():
            # The project hasn't been compiled yet
            msg = "This project has not been compiled yet."
            self.RunError("Error", msg)
            return

        wx.BeginBusyCursor()

        # Switch between the "show missing modules" and "show binary dependencies"        
        label = self.GetMenuBar().GetLabel(event.GetId())
        dll = (label.find("Binary") >= 0 and [True] or [False])[0]
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
        dlg = wx.TextEntryDialog(self, "Enter A Name For The New Configuration:",
                                 "Saving Panels Configuration")
        dlg.SetValue(("Perspective %d")%(len(self.perspectives)))
        
        if dlg.ShowModal() != wx.ID_OK:
            # No choice made, go back
            return

        value = dlg.GetValue()
        dlg.Destroy()

        if not value.strip():
            # Empty configuration name?
            self.RunError("Error", "Invalid perspective name!")
            return
        
        if len(self.perspectives) == 1:
            # Append a separator on the Configuration menu
            self.configMenu.AppendSeparator()

        # Append a new item in the Configuration menu
        item = wx.MenuItem(self.configMenu, ID_FirstPerspective + len(self.perspectives), value,
                           "Restore GUI configuration: %s"%value)
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
        self.RunError("Message", "This option has not been implemented yet.")


    def OnAPI(self, event):
        """ Shows the GUI2Exe API help file. """

        webbrowser.open_new(opj(self.installDir + "/docs/api/index.html"))

        
    def OnCheckUpgrade(self, event):
        """ Checks for a possible upgrade of GUI2Exe. """

        dlg = wx.ProgressDialog("GUI2Exe: Check for upgrade",
                                "Attempting to connect to the internet...", parent=self,
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
        """ Called by a worker thread which check my web page on the internet. """
        
        if text is None:
            self.RunError("Error", "Unable to connect to the internet.")
            return

        # A bit shaky, but it seems to work...
        indx = text.find("<small><strong>GUI2Exe")
        version = text[indx:indx+40].split(";")[1]
        version = version[0:version.find("<")]
        if version > __version__:
            # Time to upgrade maybe? :-D
            strs = "A new version of GUI2Exe is available!\n\nPlease go to " \
                   "http://xoomer.alice.it/infinity77/main/GUI2Exe.html\nif you wish to upgrade."
            self.RunError("Message", strs)
            return

        # No upgrade required
        self.RunError("Message", "At present you have the latest version of GUI2Exe.")        


    def OnContact(self, event):
        """ Launch the mail program to contact the GUI2Exe author. """

        wx.BeginBusyCursor()
        webbrowser.open_new("mailto:andrea.gavana@gmail.com?subject=Comments On GUI2Exe&cc=gavana@kpo.kz")
        wx.CallAfter(wx.EndBusyCursor)


    def OnAbout(self, event):
        """ Shows the about dialog for GUI2Exe. """

        msg = "This is the about dialog of GUI2Exe.\n\n" + \
              "Version %s"%__version__ + "\n"+ \
              "Author: Andrea Gavana @ 01 Apr 2007\n\n" + \
              "Please report any bug/request of improvements\n" + \
              "to me at the following addresses:\n\n" + \
              "andrea.gavana@gmail.com\ngavana@kpo.kz\n\n" + \
              "Thanks to Robin Dunn and the wxPython mailing list\n" + \
              "for the ideas and useful suggestions."
              
        self.RunError("Message", msg)


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
        """ Handles the custom and post-compilation code the user may add. """

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
        """ Checks whether a page needs saving before closing. """

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
            
        if not unSaved:
            # Mark the item as non-edited anymore (if it exists)
            self.projectTree.SetItemEditing(treeItem, False)
            self.openingPages[projectName] = page.GetSelection()
            if not isCloseEvent:
                event.Skip()
                if not isAUI:
                    self.mainPanel.DeletePage(selection)
            return True

        # Not saved. If it wasn't ever saved before, not saving will delete
        # the item from the project tree
        msg = "Warning: the selected page contains unsaved data.\n\nDo you wish to save this project?"
        answer = self.RunError("Question", msg)

        if answer == wx.ID_CANCEL:
            # You want to think about it, eh?
            if isAUI or isCloseEvent:
                event.Veto()
            return False
        elif answer == wx.ID_YES:
            # Save the project, defer to the database
            self.dataBase.SaveProject(project)
            self.openingPages[projectName] = page.GetSelection()
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
                self.openingPages[projectName] = page.GetSelection()

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
        """ Saves the current project. """

        # Send the data to the database        
        self.dataBase.SaveProject(project)
        # Visually indicates that the project has been saved
        self.UpdatePageBitmap(project.GetName(), 0, self.mainPanel.GetSelection())


    def UpdatePageBitmap(self, pageName, pageIcon, selection=None):
        """
        Updates the wx.aui.AuiNotebook page image and text, to reflect the
        current project state (saved/unsaved).
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
        """

        if sendMessage:
            # Send a message also to the log window at the bottom
            self.SendMessage(kind, msg.strip("."))
            
        if kind == "Message":    # is a simple message
            style = wx.OK | wx.ICON_INFORMATION
        elif kind == "Warning":  # is a warning
            style = wx.OK | wx.ICON_EXCLAMATION
        elif kind == "Question": # is a question
            style = wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        else:                    # is an error
            style = wx.OK | wx.ICON_ERROR

        # Create the message dialog
        dlg = wx.MessageDialog(None, msg, "GUI2Exe %s"%kind, style|wx.STAY_ON_TOP)
        answer = dlg.ShowModal()
        dlg.Destroy()

        if kind == "Question":
            # return the answer, it was a question
            return answer


    def AddNewProject(self, treeItem, projectName):
        """ Adds a new project to the current center pane. """

        # Freeze all. It speeds up a bit the drawing
        busy = PyBusyInfo("Creating new project...")
        wx.SafeYield()
        
        self.Freeze()

        # Create a new project, dictionary-based
        project = Project(self.defaultConfig, projectName)
        # The Project method adds a page to the center pane
        # I need it in another method as I use it also elsewhere below
        self.Project(project, treeItem, True)
        self.openingPages[projectName] = 0
        # Send a message to the log window at the bottom    
        self.SendMessage("Message", 'New project "%s" added'%projectName)

        # Time to warm up...        
        self.Thaw()
        del busy


    def LoadProject(self, treeItem, projectName):
        """ Loads a project in the center pane. """

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
        if projectName in self.openingPages:
            # Get the current LabelBook
            book = self.GetCurrentBook()
            book.SetSelection(self.openingPages[projectName])
            
        # Send a message to the log window at the bottom
        self.SendMessage("Message", 'Project "%s" successfully loaded'%projectName)

        wx.EndBusyCursor()
        

    def RenameProject(self, treeItem, oldName, newName):
        """ The user has renamed the project in the project tree control. """

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
        """ Auxiliary method used to actually add a page to the center pane. """

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
        """ Walks over all the opened page in the center pane. """

        # Loop over all the wx.aui.AuiNotebook pages
        for indx in xrange(self.mainPanel.GetPageCount()):
            page = self.mainPanel.GetPage(indx)
            if page.GetTreeItem() == treeItem:
                # Yes, the page is already opened
                return indx

        # No page like that is there
        return None            
        

    def IsAlreadyOpened(self, treeItem):
        """ Looks if a page is already opened. """

        return self.WalkAUIPages(treeItem)
    
    
    def CloseAssociatedPage(self, treeItem):
        """
        A method used to close a wx.aui.AuiNotebook page when an item in the
        project tree is deleted.
        """

        page = self.WalkAUIPages(treeItem)
        if page is not None:
            self.mainPanel.DeletePage(page)


    def ReassignPageItem(self, oldItem, newItem):
        """ Reassigns an item to an opened page after a drag and drop operation. """

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
        self.statusBar.SetStatusText("Welcome to GUI2Exe", 0)


    def CreateBitmap(self, bmpName):
        """ Utility function to create bitmap passing a filename. """
        
        return catalog[bmpName].GetBitmap()
    

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
            msg = "No project has been loaded"
            self.RunError("Error", msg +".", True)
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

        self.SendMessage("Message", "Cleaning the distribution folder...")
        
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
            self.RunError("Error", "One instance of the building process is already running.")
            return

        # Run the compilation process        
        self.RunCompile(view=False, run=True)


    def RunCompile(self, view, run):
        """
        Auxiliary method. Depending on the input, it does different things:
        - view=True ==> Get the Setup.py script and displays it (run is discarded);
        - run=False ==> Start a dry-run (a compilation that does nothing);
        - run=True  ==> Start the real compilation process.
        """
    
        page = self.GetCurrentPage()
        if not page:
            # No page opened, you can't fool me
            return

        if not view and not run and page.GetName() != "py2exe":
            msg = "The Dry-Run option is available only for Py2Exe."
            self.RunError("Error", msg)
            return
        
        outputs = page.PrepareForCompile()
        if not outputs:
            # Setup.py file creation went wrong.
            # Have you set all the required variables?
            return

        setupScript, buildDir = outputs
    
        if view:    # we just want to view the code
            frame = CustomCodeViewer(self, readOnly=True, text=setupScript)
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

        self.SendMessage("Message", "Starting compilation with Python executable: %s"%self.pythonVersion)
        self.SendMessage("Message", "The compiler selected is ==> %s <=="%compiler.upper())
        
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
            return
        
        # Stop the process timer
        self.processTimer.Stop()
        # This doesn't work, at least on Windows.
        # The process is still there and there is no os.kill on Windows
        self.process.Kill()
        # Send a failure message to the log window at the bottom
        self.SendMessage("Warning", "Compilation killed by user")
        # Re-enable the run buttons
        self.messageWindow.EnableButtons(True)

        # Disable the dry-run button if not using py2exe
        book = self.GetCurrentBook()
        self.messageWindow.EnableDryRun(book)
            

    def SuccessfulCompilation(self, project, compiler, ask=True):
        """
        Assumes that the compilation process was successful and tries to test
        the new exe file.
        """

        if ask:
            # We came from an wx.EVT_END_PROCESS event
            msg = "The compiler has successfully built your executable.\n" \
                  "Do you wish to test your application?"
            answer = self.RunError("Question", msg)
            if answer != wx.ID_YES:
                return

        # Get the executable name from the Project class
        exeName = project.GetExecutableName(compiler)
        if not os.path.isfile(exeName):
            # No such file, have you compiled it?
            msg = "This project has never been compiled or its executable has been deleted."
            self.RunError("Error", msg)
            return

        # Starts the compiled exe file
        msg = "Starting compiled executable..."
        busy = PyBusyInfo(msg)
        wx.SafeYield()
        self.SendMessage("Message", msg) 

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

        if sys.version[0:3] > "(2,4)":
            # subprocess is new in 2.4
            subprocess.Popen(exe)
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
        """ Examine a log file, created by an executable that crashed for some reason. """

        # Reset few variables, we don't need them anymore
        self.currentExe = None
        self.timerCount = 0

        # Send the error message to the log window at the bottom
        self.SendMessage("Error", "Executable terminated with errors or warnings")
        
        # Ask the user if he/she wants to examine the tracebacks in the log file
        msg = "It appears that the executable generated errors in file:\n\n%s" % logFile
        msg += "\n\nDo you want to examine the tracebacks?"
        answer = self.RunError("Question", msg)
        if answer != wx.ID_YES:
            return

        wx.BeginBusyCursor()

        # Read the log file        
        fid = open(logFile, "rt")
        msg = fid.read()
        fid.close()
        # And displays it in a scrolled message dialog
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, "Tracebacks in log file")
        wx.EndBusyCursor()
        dlg.ShowModal()
        dlg.Destroy()

        
    def SendMessage(self, kind, message, copy=False):
        """ Sends a message to the log window at the bottom. """

        self.messageWindow.SendMessage(kind, message, copy)
        

    def CopyLastMessage(self):
        """ Re-sends the previous message to the log window (for long processes). """

        self.messageWindow.CopyLastMessage()
        

    def GetVersion(self):
        """ Return the current GUI2Exe version. """

        return __version__
    

    def GetPyInstallerPath(self):
        """ Returns the path where PyInstaller is installed. """
        
        return self.pyInstallerPath
        

    def GetDataDir(self):
        """ Return the standard location on this platform for application data. """
        
        sp = wx.StandardPaths.Get()
        return sp.GetUserDataDir()


    def GetConfig(self):
        """ Returns the configuration for GUI2Exe. """
        
        if not os.path.exists(self.GetDataDir()):
            os.makedirs(self.GetDataDir())

        config = wx.FileConfig(localFilename=os.path.join(self.GetDataDir(), "options"))
        return config


    def CreateManifestFile(self, project, compiler):
        """ Create a XP-style manifest file if requested. """

        if wx.Platform != "__WXMSW__":
            # Wrong platform
            return

        try:
            outputs = project.GetManifestFileName(compiler)
        except AttributeError:
            return

        if not outputs:
            return
        
        manifestFile, programName = outputs
        fid = open(manifestFile, "wt")
        fid.write((_manifest_template % dict(prog=programName))[25:-4])
        fid.close()


    def ResetConfigurations(self, selectedItem, project):
        """ Updates a project from an external file. """

        # Update information on screen (if needed)
        page = self.WalkAUIPages(selectedItem)
        if page is None:
            self.SendMessage("Message", "Project successfully updated from file.")
            # This page is not opened, go back
            return        

        page = self.mainPanel.GetPage(page)
        self.mainPanel.Freeze()
        
        for indx in xrange(page.GetPageCount()):
            book = page.GetPage(indx)
            name = book.GetName()
            book.SetConfiguration(project[name], delete=True)

        self.mainPanel.Thaw()
        self.SendMessage("Message", "Project successfully updated from file.")
        

class GUI2ExeSplashScreen(AS.AdvancedSplash):
    """ A fancy splash screen class, with a shaped frame. """

    def __init__(self, app):
        """ A fancy splash screen :-D """

        bmp = catalog["gui2exe_splash"].GetBitmap()
        AS.AdvancedSplash.__init__(self, None, bitmap=bmp, timeout=5000,
                                   extrastyle=AS.AS_TIMEOUT|AS.AS_CENTER_ON_SCREEN)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.fc = wx.FutureCall(2000, self.ShowMain)
        self.app = app


    def OnClose(self, evt):
        """ Handles the wx.EVT_CLOSE event for GUI2ExeSplashScreen. """
        
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
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
        frame.CenterOnScreen()
        frame.Show()

        if self.fc.IsRunning():
            self.Raise()
            
            
class GUI2ExeApp(wx.App):
    """ The main application class. """
    
    def OnInit(self):
        """ Default wx.App initialization. """

        wx.SetDefaultPyEncoding("utf-8")
        
        splash = GUI2ExeSplashScreen(self)
        splash.Show()

        self.SetAppName("GUI2Exe")

        return True
        

if __name__ == "__main__":
    app = GUI2ExeApp(0)
    app.MainLoop()

