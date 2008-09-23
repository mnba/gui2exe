# Start the imports

import os
import wx
import pprint

import wx.lib.buttons as buttons

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox, PListEditor
from Constants import _py2app_target, _py2app_imports, _pywild, _iconwild, _plistwild, ListType
from Utilities import setupString


class Py2AppPanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        @param projectName: the name of the project we are working on
        @param creationDate: the date and time the project was created

        """
        
        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="py2app")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers
        self.commonSizer_staticbox = wx.StaticBox(self, -1, "Common Options")
        self.includesSizer_staticbox = wx.StaticBox(self, -1, "Includes")
        self.packagesSizer_staticbox = wx.StaticBox(self, -1, "Packages")
        self.excludesSizer_staticbox = wx.StaticBox(self, -1, "Excludes")
        self.dylibExcludesSizer_staticbox = wx.StaticBox(self, -1, "Dylib/Frameworks Excludes")
        self.datamodelsSizer_staticbox = wx.StaticBox(self, -1, "XC Data Models")
        self.frameworksSizer_staticbox = wx.StaticBox(self, -1, "Dylib/Frameworks Includes")
        self.datafile_staticbox = wx.StaticBox(self, -1, "Resources")

        self.otherSizer_staticbox = wx.StaticBox(self, -1, "Other Options")

        # A simple label that holds information about the project
        self.label = wx.StaticText(self, -1, "Py2app options for: %s (Created: %s)"%(projectName, creationDate))

        # A combobox to choose the application extension
        self.extensionCombo = MultiComboBox(self, [".app", ".plugin"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                            self.GetName(), "extension")
        # The file picker that allows us to pick the script to be compiled by py2app
        self.scriptPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL,
                                              wildcard=_pywild, name="script")

        # A checkbox that enables the user to choose a different name for the
        # distribution directory. Default is unchecked, that means dist_dir="dist"
        self.distChoice = wx.CheckBox(self, -1, "Dist Directory", name="dist_dir_choice")
        # The name of the distribution directory (if enabled)
        self.distTextCtrl = wx.TextCtrl(self, -1, "dist", name="dist_dir")
        
        # Optimization level for py2app  1 for "python -O", 2 for "python -OO",
        # 0 to disable
        self.optimizeCombo = MultiComboBox(self, ["0", "1", "2"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                           self.GetName(), "optimize")

        # The icon picker that allows us to pick the application icon
        self.iconPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL,
                                            wildcard=_iconwild, name="iconfile")
                
        # A picker for the PList file
        self.pListPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL,
                                             wildcard=_plistwild, name="plist")

        # To add/edit PList code
        self.pListChoice = wx.CheckBox(self, -1, "PList Code", name="plistCode_choice")
        editBmp = self.MainFrame.CreateBitmap("edit_add")
        removeBmp = self.MainFrame.CreateBitmap("remove")
        self.pListAddButton = buttons.ThemedGenBitmapTextButton(self, -1, editBmp, " Add/Edit",
                                                                size=(-1, 25), name="plistCode")
        self.pListRemoveButton = buttons.ThemedGenBitmapTextButton(self, -1, removeBmp, " Remove",
                                                                   size=(-1, 25), name="plistRemove")
        
        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=["Python Modules"], name="includes")
        # A list control for the "packages" option, a comma separated list of
        # packages to include
        self.packagesList = BaseListCtrl(self, columnNames=["Python Packages"], name="packages")
        # A list control for the "frameworks" option, a comma separated list of
        # frameworks/dylibs to include
        self.frameworksList = BaseListCtrl(self, columnNames=["Dylib/Frameworks Names"], name="frameworks")
        # A list control for the "excludes" option, a comma separated list of
        # modules to exclude   
        self.excludeList = BaseListCtrl(self, columnNames=["Python Modules"], name="excludes")
        # A list control for the "dylib_excludes" option, a comma separated list of
        # dylibs/frameworks to exclude
        self.dylibExcludeList = BaseListCtrl(self, columnNames=["Dylib/Frameworks Names"], name="dylib_excludes")
        # A list control for the "xcdatamodels" option, a comma separated list of
        # xcdatamodels to compile and include
        self.datamodelsList = BaseListCtrl(self, columnNames=["XC Data Models Names"], name="datamodels")
        # A list control for the "resources" option. "resources" should contain
        # a sequence of (target-dir, files) tuples, where files is a sequence of
        # files to be copied
        self.datafileList = BaseListCtrl(self, columnNames=["Files Path"], name="resources")

        # output module dependency graph
        self.graphCheck = wx.CheckBox(self, -1, "Graph", name="graph")
        # This command line switch instructs py2app to create a python module cross
        # reference and display it in the webbrowser.  This allows to answer question
        # why a certain module has been included, or if you can exclude a certain module
        # and it's dependencies. Also, the html page includes links which will even
        # allow to view the source code of a module in the browser, for easy inspection.
        self.crossRefCheck = wx.CheckBox(self, -1, "Cross-Reference", name="xref")
        # Do not strip debug and local symbols from output
        self.noStripCheck = wx.CheckBox(self, -1, "No Strip", name="no_strip")
        # Do not change to the data directory (Contents/Resources) [forced for plugins]
        self.noChdirCheck = wx.CheckBox(self, -1, "No Chdir", name="no_chdir")
        # Depend on an existing installation of Python 2.4
        self.semiStandaloneCheck = wx.CheckBox(self, -1, "Semi Standalone", name="semi_standalone")
        # Use argv emulation (disabled for plugins)
        self.argvEmulationCheck = wx.CheckBox(self, -1, "Argv Emulation", name="argv_emulation")
        # Allow PYTHONPATH to effect the interpreter's environment
        self.usePythonPathCheck = wx.CheckBox(self, -1, "Use PYTHONPATH", name="use_pythonpath")
        # Include the system and user site-packages into sys.path
        self.sitePackagesCheck= wx.CheckBox(self, -1, "Site Packages", name="site_packages")
        # Force application to run translated on i386 (LSPrefersPPC=True)
        self.preferPPCCheck= wx.CheckBox(self, -1, "Prefer PPC", name="prefer_ppc")
        # Drop to pdb console after the module finding phase is complete
        self.debugModuleGraphCheck= wx.CheckBox(self, -1, "Debug Modulegraph", name="debug_modulegraph")
        # Skip macholib phase (app will not be standalone!)
        self.skipMacholibCheck= wx.CheckBox(self, -1, "Debug Skip Macholib", name="debug_skip_macholib")

        # Hold a reference to all the list controls, to speed up things later
        self.listCtrls = [self.includeList, self.packagesList, self.frameworksList, self.excludeList,
                          self.dylibExcludeList, self.datamodelsList, self.datafileList]

        # Do the hard work... quite a few to layout :-D
        self.LayoutItems()
        self.SetProperties()
        self.BindEvents()

        self.Bind(wx.EVT_BUTTON, self.OnPListAdd, self.pListAddButton)
        self.Bind(wx.EVT_BUTTON, self.OnPListRemove, self.pListRemoveButton)

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets the properties fro Py2AppPanel and its children widgets. """

        # I use all the py2app default values (where applicable), and my standard
        # configuration or preferences otherwise. This can easily be changed later
        # with a user customizable default project options file (or wx.Config)
        
        self.distTextCtrl.Enable(False)

        # Set a bold font for the static texts
        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        
        for child in self.GetChildren():
            if isinstance(child, wx.StaticText) or isinstance(child, wx.CheckBox):
                child.SetFont(font)
        

    def LayoutItems(self):
        """ Layouts the widgets using sizers. """

        # Create a whole bunch of sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        otherSizer = wx.StaticBoxSizer(self.otherSizer_staticbox, wx.VERTICAL)
        otherSizer_1 = wx.FlexGridSizer(3, 4, 5, 5)
        plusSizer = wx.BoxSizer(wx.HORIZONTAL)
        minusSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        dylibExcludesSizer = wx.StaticBoxSizer(self.dylibExcludesSizer_staticbox, wx.HORIZONTAL)
        excludesSizer = wx.StaticBoxSizer(self.excludesSizer_staticbox, wx.HORIZONTAL)
        packagesSizer = wx.StaticBoxSizer(self.packagesSizer_staticbox, wx.HORIZONTAL)
        includesSizer = wx.StaticBoxSizer(self.includesSizer_staticbox, wx.HORIZONTAL)
        datamodelsSizer = wx.StaticBoxSizer(self.datamodelsSizer_staticbox, wx.HORIZONTAL)
        datafilesSizer = wx.StaticBoxSizer(self.datafile_staticbox, wx.HORIZONTAL)
        frameworksSizer = wx.StaticBoxSizer(self.frameworksSizer_staticbox, wx.HORIZONTAL)
        
        commonSizer = wx.StaticBoxSizer(self.commonSizer_staticbox, wx.VERTICAL)

        # This grid bag sizer will hold all the list controls and widgets
        # that display py2app options
        commonGridSizer = wx.GridBagSizer(5, 5)

        commonSizer_7 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_6 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_5 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_4 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_3 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_2 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_1 = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
                
        # Add the VersionInfo text controls
        mainSizer.Add(self.label, 0, wx.ALL, 10)

        flag = wx.LEFT|wx.RIGHT|wx.EXPAND

        extension = wx.StaticText(self, -1, "Extension")
        commonSizer_1.Add(extension, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_1.Add(self.extensionCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_1, (1, 0), (1, 1), flag, 5)
        script = wx.StaticText(self, -1, "Python Main Script")
        commonSizer_2.Add(script, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_2.Add(self.scriptPicker, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_2, (1, 1), (1, 4), flag, 5)
        commonSizer_3.Add(self.distChoice, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_3.Add(self.distTextCtrl, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_3, (1, 5), (1, 1), flag, 5)

        optimize = wx.StaticText(self, -1, "Optimize")
        commonSizer_4.Add(optimize, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_4.Add(self.optimizeCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_4, (2, 0), (1, 1), flag|wx.TOP, 5)
        icon = wx.StaticText(self, -1, "Icon File")
        commonSizer_5.Add(icon, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_5.Add(self.iconPicker, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_5, (2, 1), (1, 2), flag|wx.TOP, 5)
        plist = wx.StaticText(self, -1, "PList File")
        commonSizer_6.Add(plist, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_6.Add(self.pListPicker, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_6, (2, 3), (1, 2), flag|wx.TOP, 5)
        commonSizer_7.Add(self.pListChoice, 0, wx.RIGHT|wx.BOTTOM, 2)
        hSizer.Add(self.pListAddButton, 0, wx.RIGHT, 5)
        hSizer.Add(self.pListRemoveButton, 0)
        commonSizer_7.Add(hSizer, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_7, (2, 5), (1, 1), flag|wx.TOP, 5)
        
        commonGridSizer.AddGrowableCol(2)
        commonGridSizer.AddGrowableCol(3)
        commonGridSizer.AddGrowableCol(4)
        commonGridSizer.SetEmptyCellSize((0, 0))
        
        commonSizer.Add(commonGridSizer, 1, wx.EXPAND|wx.BOTTOM, 5)
        mainSizer.Add(commonSizer, 0, wx.ALL|wx.EXPAND, 5)

        flag = wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND
        # Add the list controls
        includesSizer.Add(self.includeList, 1, flag, 5)
        includesSizer.Add(self.includeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        packagesSizer.Add(self.packagesList, 1, flag, 5)
        packagesSizer.Add(self.packagesList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        frameworksSizer.Add(self.frameworksList, 1, flag, 5)
        frameworksSizer.Add(self.frameworksList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        plusSizer.Add(includesSizer, 1, wx.EXPAND)
        plusSizer.Add(packagesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        plusSizer.Add(frameworksSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(plusSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        excludesSizer.Add(self.excludeList, 1, flag, 5)
        excludesSizer.Add(self.excludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        dylibExcludesSizer.Add(self.dylibExcludeList, 1, flag, 5)
        dylibExcludesSizer.Add(self.dylibExcludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        datamodelsSizer.Add(self.datamodelsList, 1, flag, 5)
        datamodelsSizer.Add(self.datamodelsList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)

        minusSizer.Add(excludesSizer, 1, wx.EXPAND)
        minusSizer.Add(dylibExcludesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        minusSizer.Add(datamodelsSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(minusSizer, 1, wx.ALL|wx.EXPAND, 5)

        datafilesSizer.Add(self.datafileList, 1, flag, 5)
        datafilesSizer.Add(self.datafileList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        mainSizer.Add(datafilesSizer, 1, wx.ALL|wx.EXPAND, 5)

        # Add the other options at the bottom
        otherSizer_1.Add(self.graphCheck, 0)
        otherSizer_1.Add(self.crossRefCheck, 0)
        otherSizer_1.Add(self.noStripCheck, 0)
        otherSizer_1.Add(self.noChdirCheck, 0)
        otherSizer_1.Add(self.semiStandaloneCheck, 0)
        otherSizer_1.Add(self.argvEmulationCheck, 0)
        otherSizer_1.Add(self.usePythonPathCheck, 0)
        otherSizer_1.Add(self.sitePackagesCheck, 0)
        otherSizer_1.Add(self.preferPPCCheck, 0)
        otherSizer_1.Add(self.debugModuleGraphCheck, 0)
        otherSizer_1.Add(self.skipMacholibCheck, 0)

        otherSizer_1.AddGrowableCol(0)
        otherSizer_1.AddGrowableCol(1)
        otherSizer_1.AddGrowableCol(2)
        otherSizer_1.AddGrowableCol(3)
        otherSizer.Add(otherSizer_1, 1, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(otherSizer, 0, wx.ALL|wx.EXPAND, 5)

        self.SetAutoLayout(True)
        self.SetSizer(mainSizer)

        self.SetupScrolling()
        self.label.SetFocus()

    
    def ValidateOptions(self):
        """ Validates the py2app input options before compiling. """

        # check if the script file exists
        if not os.path.isfile(self.scriptPicker.GetPath()):
            msg = "Python main script is not a valid file."
            self.MainFrame.RunError("Error", msg, True)
            return False

        # check if the PList file is not empty and if it exists
        pListScript = self.pListPicker.GetPath()
        if pListScript and not os.path.isfile(pListScript):
            msg = "PList file is not a valid file."
            self.MainFrame.RunError("Error", msg, True)
            return False

        # check if the icon file is not empty and if it exists
        icon = self.iconPicker.GetPath()
        if icon and not os.path.isfile(icon):
            msg = "Icon file is not a valid file."
            self.MainFrame.RunError("Error", msg, True)
            return False

        # Everything is ok, let's go compiling...
        return True
    
        
    def PrepareForCompile(self):
        """ Retrieves all the data to prepare for compilation. """

        if not self.ValidateOptions():
            # No way, something went wrong with the options set by the user
            return None

        # Retrieve the project stored in the parent (LabelBook) properties
        project = self.GetParent().GetProject()
        # Send a message to out fancy bottom log window
        self.MainFrame.SendMessage("Message", 'Generating "%s" setup script...' % project.GetName())

        # Get the project configuration (all the options, basically)   
        configuration = project.GetConfiguration(self.GetName())
        # Get the custom code (if any) that the user added
        customCode = project.GetCustomCode(self.GetName())
        # Get the post-compilation code (if any) that the user added
        postCompile = project.GetPostCompileCode(self.GetName())

        for lists in self.listCtrls:
            # Last update for all the list controls
            lists.UpdateProject(False)

        # Build the target script file        
        return self.BuildTargetClass(configuration, project, None, customCode, postCompile)


    def BuildTargetClass(self, configuration, project, manifestFile, customCode, postCompile):
        """ Builds the py2app compilation script file, returning it as a string. """

        # A couple of dictionaries to populate the setup string        
        setupDict, importDict = {}, {}
        configuration = dict(configuration)
        distChoice = self.distChoice.GetValue()

        pListChoice = self.pListChoice.GetValue()
        usePListFile = True
        pListCode = {}
        
        if pListChoice:
            if "plist_code" in configuration:
                # Get the existing PList code (if any)
                pListCode = configuration["plist_code"]
                if pListCode:
                    usePListFile = False
                    plist_code = "plist_code = " + pprint.pformat(pListCode, width=100)

        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if key == "dist_dir_choice":
                continue
            if key == "script":
                buildDir, scriptFile = os.path.split(item)
                item = "r'%s'"%item
            elif key == "dist":
                if not item.strip() or not distChoice:
                    item = "dist"
                    if distChoice:
                        self.MainFrame.SendMessage("Warning", 'Empty dist_dir option. Using default value "dist" ')
            elif key in ["iconfile", "plist"]:
                if key == "plist" and not usePListFile:
                    item = "plist_code"
                else:
                    if not item.strip():
                        item = None
                    else:
                        item = "r'%s'"%item
                    
            if isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))

            if type(item) == ListType:
                # Terrible hack to setup correctly the string to be included
                # in the setup file
                item = setupString(key, item, True)
                
            setupDict[key] = item

        if not usePListFile:
            setupDict["plist_code"] = plist_code
        else:
            setupDict["plist_code"] = "# No code for PList"

        # Add the custom code (if any)
        setupDict["customcode"] = (customCode and [customCode.strip()] or ["# No custom code added"])[0]

        # Add the post-compilation code (if any)
        setupDict["postcompilecode"] = (postCompile and [postCompile.strip()] or ["# No post-compilation code added"])[0]
        
        # Include the GUI2Exe version in the setup script
        importDict["gui2exever"] = self.MainFrame.GetVersion()

        # Populate the "import" section
        setupScript = _py2app_imports % importDict

        # Populate the main section of the setup script            
        setupScript += _py2app_target % setupDict
        
        # Send a message to out fancy bottom log window
        self.MainFrame.SendMessage("Message", 'Setup script for "%s" succesfully created' % project.GetName())
        return setupScript, buildDir


    def OnPListAdd(self, event):
        """ Launches a custom PList editor. """

        if not self.ValidateOptions():
            # No way, something went wrong with the options set by the user
            return None

        programName = self.scriptPicker.GetPath()
        programName = os.path.split(os.path.splitext(programName)[0])[1]

        # Retrieve the project stored in the parent (LabelBook) properties
        project = self.GetParent().GetProject()
        if "plist_code" in project["py2app"]:
            # Get the existing PList code (if any)
            pListCode = project["py2app"]["plist_code"]
        else:
            pListCode = {}

        dlg = PListEditor(self.MainFrame, programName,
                          pListFile=self.pListPicker.GetPath().strip(),
                          pListCode=pListCode)
        
        if dlg.ShowModal() == wx.ID_CANCEL:
            # User cancelled the modifications
            dlg.Destroy()
            return

        PList = dlg.GetPList()
        project["py2app"]["plist_code"] = PList
        # Update the icon and the project name on the wx.aui.AuiNotebook tab
        self.MainFrame.UpdatePageBitmap(project.GetName() + "*", 1)
        

    def OnPListRemove(self, event):
        """ Deletes the PList code (if any) from the project. """

        # Retrieve the project stored in the parent (LabelBook) properties
        project = self.GetParent().GetProject()
        if "plist_code" in project["py2app"]:
            project["py2app"]["plist_code"] = {}
            # Update the icon and the project name on the wx.aui.AuiNotebook tab
            self.MainFrame.UpdatePageBitmap(project.GetName() + "*", 1)            
        