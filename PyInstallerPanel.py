# Start the imports

import os
import wx

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox
from Constants import _pyInstaller_imports, ListType
from Constants import _pyInstaller_target_onefile, _pyInstaller_target_onedir
from Constants import _pyInstallerTOC, _pyInstallerOptions
from Utilities import setupString

# Get the I18N things
_ = wx.GetTranslation


class PyInstallerPanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        @param projectName: the name of the project we are working on
        @param creationDate: the date and time the project was created

        """
        
        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="PyInstaller")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers

        self.pathSizer_staticbox = wx.StaticBox(self, -1, _("Path Extensions"))
        self.hookSizer_staticbox = wx.StaticBox(self, -1, _("Hooks Extensions"))
        self.commonSizer_staticbox = wx.StaticBox(self, -1, _("Common Options"))
        self.includesSizer_staticbox = wx.StaticBox(self, -1, _("Includes"))
        self.excludesSizer_staticbox = wx.StaticBox(self, -1, _("Excludes"))
        self.packagesSizer_staticbox = wx.StaticBox(self, -1, _("Packages (PKG)"))
        self.dllExcludesSizer_staticbox = wx.StaticBox(self, -1, _("DLL/Binary Excludes"))
        self.dllIncludesSizer_staticbox = wx.StaticBox(self, -1, _("DLL/Binary Includes"))
        self.datafileSizer_staticBox = wx.StaticBox(self, -1, _("Data Files"))
        self.otherOptionsSizer_staticbox = wx.StaticBox(self, -1, _("Other Options"))
        self.scriptSizer_staticbox = wx.StaticBox(self, -1, _("Scripts"))

        # A simple label that holds information about the project
        transdict = dict(projectName=projectName, creationDate=creationDate)
        self.label = wx.StaticText(self, -1, _("PyInstaller options for: %(projectName)s (Created: %(creationDate)s)")%transdict)

        # This list holds all the script files added by the user
        self.scriptsList = BaseListCtrl(self, columnNames=[_("Python Scripts")], name="scripts")
        # A list for the extension of the search path
        self.pathexList = BaseListCtrl(self, columnNames=[_("Paths")], name="pathex")
        # A list for the extension of the hooks package
        self.hookList = BaseListCtrl(self, columnNames=[_("Paths")], name="hookspath")
        # Do we want a debug build?
        self.debugCheck = wx.CheckBox(self, -1, _("Debug"), name="debug")
        # Radiobutton for the one-file build
        self.oneFileRadio = wx.RadioButton(self, -1, _("One File"), style=wx.RB_GROUP, name="onefile")
        # Name of the executable
        self.exeTextCtrl = wx.TextCtrl(self, -1, "", name="exename")
        # Whether it is a console or a windowed application
        self.consoleCheck = wx.CheckBox(self, -1, _("Console Application"), name="console")
        # Radiobutton for the one-dir build
        self.oneDirRadio = wx.RadioButton(self, -1, _("One Directory"), name="onedir")
        # A file picker for the executable icon
        self.iconPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL, name="icon")
        # Strip or no strip?
        self.stripCheck = wx.CheckBox(self, -1, _("Strip Executable"), name="strip")
        # Do we want to include encodings or not?
        self.asciiCheck = wx.CheckBox(self, -1, "Ascii", name="ascii")
        # Name of the distribution directory
        self.distTextCtrl = wx.TextCtrl(self, -1, "", name="dist_dir")
        # Compression level
        self.compressCombo = MultiComboBox(self, [str(i) for i in xrange(10)],
                                           wx.CB_DROPDOWN|wx.CB_READONLY, self.GetName(), "level")
        # Use UPX compression? 
        self.upxCheck = wx.CheckBox(self, -1, _("UPX Compression"), name="upx")
        # Include Tk in the distribution?
        self.includeTkCheck = wx.CheckBox(self, -1, _("Include Tk"), name="includetk")
        # A file picker for the version file
        self.versionPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL, name="version")
        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=[_("Python Modules"), _("Path")], name="includes")
        # A list control for the "excludes" option, a comma separated list of
        # modules to exclude
        self.excludeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="excludes")
        # A list control for the "packages" option, a comma separated list of
        # packages to include
        self.packagesList = BaseListCtrl(self, columnNames=[_("Python Packages"), _("Path")], name="packages")
        # A couple of listctrls to hold DLL/binary includes and excludes
        self.dllExcludeList = BaseListCtrl(self, columnNames=[_("File Name"), _("Path")], name="dll_excludes")
        self.dllIncludeList = BaseListCtrl(self, columnNames=[_("File Name"), _("Path")], name="dll_includes")
        # A list control for the "data_files" option. "data_files" should contain
        # a sequence of (target-dir, files) tuples, where files is a sequence of
        # files to be copied
        self.datafileList = BaseListCtrl(self, columnNames=[_("File Name"), _("Path")], name="data_files")
        # Less used options
        self.verboseCheck = wx.CheckBox(self, -1, _("Verbose Import"), name="option1")
        self.warningCheck = wx.CheckBox(self, -1, _("Warning Option"), name="option2")
        self.forceexecCheck = wx.CheckBox(self, -1, _("Force Execpv"), name="option3")
        self.unbufferedCheck = wx.CheckBox(self, -1, _("Unbuffered STDIO"), name="option4")
        self.useSiteCheck = wx.CheckBox(self, -1, _("Use Site.py"), name="option5")
        self.optimizeCheck = wx.CheckBox(self, -1, _("Build Optimized"), name="option6")
        self.addManifest = wx.CheckBox(self, -1, _("Create Manifest File (MSW)"), name="create_manifest_file")

        # Hold a reference to all the list controls, to speed up things later
        self.listCtrls = [self.includeList, self.packagesList, self.excludeList, self.dllExcludeList,
                          self.dllIncludeList, self.datafileList, self.scriptsList, self.pathexList,
                          self.hookList]
        # Hold a reference to the most obscure PyInstaller options
        self.optionsCheckBoxes = [self.verboseCheck, self.warningCheck, self.forceexecCheck,
                                  self.unbufferedCheck, self.useSiteCheck, self.optimizeCheck]
        
        # Do the hard work... quite a few to layout :-D
        self.LayoutItems()
        self.SetProperties()
        self.BindEvents()
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #

    def SetProperties(self):
        """ Set fonts and other default properties. """

        # Set a bold font for the static texts
        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        
        for child in self.GetChildren():
            if isinstance(child, wx.StaticText) or isinstance(child, wx.CheckBox) or \
               isinstance(child, wx.RadioButton):
                child.SetFont(font)

        
    def LayoutItems(self):

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        otherOptionsSizer = wx.StaticBoxSizer(self.otherOptionsSizer_staticbox, wx.HORIZONTAL)
        otherGridSizer = wx.FlexGridSizer(2, 4, 5, 5)
        dataFileSizer = wx.StaticBoxSizer(self.datafileSizer_staticBox, wx.HORIZONTAL)
        centerSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        dllIncludesSizer = wx.StaticBoxSizer(self.dllIncludesSizer_staticbox, wx.HORIZONTAL)
        dllExcludesSizer = wx.StaticBoxSizer(self.dllExcludesSizer_staticbox, wx.HORIZONTAL)
        packagesSizer = wx.StaticBoxSizer(self.packagesSizer_staticbox, wx.HORIZONTAL)
        centerSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        excludesSizer = wx.StaticBoxSizer(self.excludesSizer_staticbox, wx.HORIZONTAL)
        includesSizer = wx.StaticBoxSizer(self.includesSizer_staticbox, wx.HORIZONTAL)
        commonSizer = wx.StaticBoxSizer(self.commonSizer_staticbox, wx.HORIZONTAL)
        commonGridSizer = wx.FlexGridSizer(5, 5, 0, 5)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        hookSizer = wx.StaticBoxSizer(self.hookSizer_staticbox, wx.HORIZONTAL)
        pathSizer = wx.StaticBoxSizer(self.pathSizer_staticbox, wx.HORIZONTAL)
        scriptSizer = wx.StaticBoxSizer(self.scriptSizer_staticbox, wx.HORIZONTAL)
        mainSizer.Add(self.label, 0, wx.ALL, 10)
        
        flag = wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND
        scriptSizer.Add(self.scriptsList, 1, flag, 5)
        scriptSizer.Add(self.scriptsList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        topSizer.Add(scriptSizer, 2, wx.ALL|wx.EXPAND, 5)
        pathSizer.Add(self.pathexList, 1, flag, 5)
        pathSizer.Add(self.pathexList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        topSizer.Add(pathSizer, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        hookSizer.Add(self.hookList, 1, flag, 5)
        hookSizer.Add(self.hookList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        topSizer.Add(hookSizer, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        mainSizer.Add(topSizer, 0, wx.EXPAND, 0)
        exename = wx.StaticText(self, -1, _("Executable Name"))
        commonGridSizer.Add(exename, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        compress = wx.StaticText(self, -1, _("Compression Level"))
        commonGridSizer.Add(compress, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        commonGridSizer.Add(self.debugCheck, 0, wx.LEFT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.oneFileRadio, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM, 10)
        icon = wx.StaticText(self, -1, _("Icon File"))
        commonGridSizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        commonGridSizer.Add(self.exeTextCtrl, 0, wx.LEFT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.Add(self.compressCombo, 1, wx.EXPAND|wx.LEFT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.consoleCheck, 0, wx.LEFT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.oneDirRadio, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.iconPicker, 0, wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.Add((0, 15), 0, 0, 0)
        commonGridSizer.Add((0, 15), 0, 0, 0)
        commonGridSizer.Add((0, 5), 0, 0, 0)
        commonGridSizer.Add((0, 15), 0, 0, 0)
        commonGridSizer.Add((0, 15), 0, 0, 0)
        
        distname = wx.StaticText(self, -1, _("Dist Directory Name"))
        commonGridSizer.Add(distname, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.Add((0, 5), 1, 0, 0)
        commonGridSizer.Add(self.stripCheck, 0, wx.LEFT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.asciiCheck, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM, 10)
        version = wx.StaticText(self, -1, _("Version File"))
        commonGridSizer.Add(version, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.Add(self.distTextCtrl, 0, wx.LEFT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.Add((0, 5), 1, 0, 0)
        commonGridSizer.Add(self.upxCheck, 0, wx.LEFT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.includeTkCheck, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM, 10)
        commonGridSizer.Add(self.versionPicker, 0, wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        commonGridSizer.AddGrowableCol(0)
        commonGridSizer.AddGrowableCol(4)
        commonSizer.Add(commonGridSizer, 1, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(commonSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        # Add the list controls
        includesSizer.Add(self.includeList, 1, flag, 5)
        includesSizer.Add(self.includeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        centerSizer1.Add(includesSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        excludesSizer.Add(self.excludeList, 1, flag, 5)
        excludesSizer.Add(self.excludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        centerSizer1.Add(excludesSizer, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        mainSizer.Add(centerSizer1, 0, wx.EXPAND, 0)
        
        packagesSizer.Add(self.packagesList, 1, flag, 5)
        packagesSizer.Add(self.packagesList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        centerSizer2.Add(packagesSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        dllExcludesSizer.Add(self.dllExcludeList, 1, flag, 5)
        dllExcludesSizer.Add(self.dllExcludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        centerSizer2.Add(dllExcludesSizer, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        
        dllIncludesSizer.Add(self.dllIncludeList, 1, flag, 5)
        dllIncludesSizer.Add(self.dllIncludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        centerSizer2.Add(dllIncludesSizer, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        mainSizer.Add(centerSizer2, 0, wx.EXPAND, 0)
        
        dataFileSizer.Add(self.datafileList, 1, flag, 5)
        dataFileSizer.Add(self.datafileList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        mainSizer.Add(dataFileSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        otherGridSizer.Add(self.verboseCheck, 0, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.warningCheck, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.forceexecCheck, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.unbufferedCheck, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.useSiteCheck, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.optimizeCheck, 0, wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.Add(self.addManifest, 0, wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 5)
        otherGridSizer.AddGrowableCol(0)
        otherGridSizer.AddGrowableCol(1)
        otherGridSizer.AddGrowableCol(2)
        otherGridSizer.AddGrowableCol(3)
        otherOptionsSizer.Add(otherGridSizer, 1, wx.EXPAND, 0)
        mainSizer.Add(otherOptionsSizer, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        
        self.SetAutoLayout(True)
        self.SetSizer(mainSizer)

        self.SetupScrolling()
        self.label.SetFocus()


    def ValidateOptions(self):
        """ Validates the PyInstaller input options before compiling. """

        # check if the script files exist
        if self.scriptsList.GetItemCount() == 0:
            msg = _("No Python scripts have been added.")
            self.MainFrame.RunError(2, msg, True)
            return False

        for indx in xrange(self.scriptsList.GetItemCount()):
            script = self.scriptsList.GetItem(indx, 1)
            if not os.path.isfile(script.GetText()):
                transdict = dict(scriptName=script.GetText())
                msg = _("Python script:\n\n%(scriptName)s\n\nIs not a valid file.")%transdict
                self.MainFrame.RunError(2, msg, True)
                return False

        # check if the icon/version files are not empty and if they exist
        iconFile = self.iconPicker.GetPath()
        if iconFile and not os.path.isfile(iconFile):
            msg = _("Icon file is not a valid file.")
            self.MainFrame.RunError(2, msg, True)
            return False

        versionFile = self.versionPicker.GetPath()
        if versionFile and not os.path.isfile(versionFile):
            msg = _("Version file is not a valid file.")
            self.MainFrame.RunError(2, msg, True)
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
        transdict = dict(projectName=project.GetName())
        self.MainFrame.SendMessage(0, _('Generating "%(projectName)s" setup script...')%transdict)

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
        """ Builds the PyInstaller compilation script file, returning it as a string. """

        # A couple of dictionaries to populate the setup string        
        setupDict, importDict = {}, {}
        configuration = dict(configuration)

        pyFile = self.scriptsList.GetItem(0, 1).GetText()
        buildDir = os.path.split(pyFile)[0]

        includeTk = self.includeTkCheck.GetValue()
        oneDir = self.oneDirRadio.GetValue()
        ascii = self.asciiCheck.GetValue()
        normpath = os.path.normpath
        
        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if key.startswith("option"):
                continue
            if isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))

            if key == "create_manifest_file":
                continue
            
            if type(item) == ListType and item:
                # Terrible hack to setup correctly the string to be included
                # in the setup file
                if key not in ["hookspath", "scripts", "excludes", "pathex"]:
                    tmp = []
                    for data in item:
                        data = data + (_pyInstallerTOC[key],)
                        tmp.append(data)
                    item = tmp
                elif key == "pathex":
                    if buildDir not in item:
                        item.append(buildDir)
                elif key == "scripts":
                    continue
                
                item = setupString(key, item, True)

            if key == "exename" and not item.strip() and not oneDir:
                item = os.path.splitext(os.path.split(pyFile)[1])[0] + ".exe"
            if key == "dist_dir" and not item.strip() and oneDir:
                item = normpath(os.path.split(pyFile)[0] + "/dist")
            if key in ["icon", "version"]:
                if not item.strip():
                    item = None
                else:
                    item = "r'%s'"%item
            
            setupDict[key] = item

        # Set up the obscure options        
        otherOptions = []
        for indx, checks in enumerate(self.optionsCheckBoxes):
            if checks.GetValue():
                otherOptions.append(_pyInstallerOptions[indx])

        setupDict["options"] = otherOptions

        # Depending on the various choices in the interface, PyInstaller
        # includes/excludes some Python source file located in
        # PyInstaller_Path/support/

        pyInstallerPath = self.MainFrame.GetPyInstallerPath()
        if not pyInstallerPath or pyInstallerPath == "None":
            msg = _("PyInstaller path has not been set.\n\nPlease set the PyInstaller" \
                    "path using the menu Options ==> Set PyInstaller path.")
            self.MainFrame.RunError(2, msg)
            return

        items = configuration["scripts"][:]
        pyInstallerPath += "/support/"

        if setupDict["level"] != "0":
            # Include zlib as user wants compression
            items.append(normpath(pyInstallerPath + "_mountzlib.py").encode())
        
        if includeTk:
            # That's a bit of a mess, but PyInstaller is not exactly user-friendly...
            if oneDir:
                items.append(normpath(pyInstallerPath + "useTK.py").encode())
            else:
                items.extend([normpath(pyInstallerPath + "unpackTK.py").encode(),
                              normpath(pyInstallerPath + "useTK.py").encode(),
                              normpath(pyInstallerPath + "removeTK.py").encode()])

        if not ascii:
            # Using unicode
            items.append(normpath(pyInstallerPath + "useUnicode.py").encode())
            
        items.append(items[0])
        items.pop(0)
        
        setupDict["scripts"] = setupString("scripts", items, True)
        
        # Add the custom code (if any)
        setupDict["customcode"] = (customCode and [customCode.strip()] or ["# No custom code added"])[0]

        # Add the post-compilation code (if any)
        setupDict["postcompilecode"] = (postCompile and [postCompile.strip()] or ["# No post-compilation code added"])[0]
        
        # Include the GUI2Exe version in the setup script
        importDict["gui2exever"] = self.MainFrame.GetVersion()

        # Populate the "import" section
        setupScript = _pyInstaller_imports % importDict

        if oneDir:
            target = _pyInstaller_target_onedir
            if includeTk:
                setupDict["TkPKG"] = "TkTree(),"
            else:
                setupDict["TkPKG"] = ""
        else:
            target = _pyInstaller_target_onefile
            if includeTk:
                setupDict["TkPKG"] = "TkPKG(),"
            else:
                setupDict["TkPKG"] = ""
            
        # Populate the main section of the setup script            
        setupScript += target % setupDict

        # Send a message to out fancy bottom log window
        transdict = dict(projectName=project.GetName())
        self.MainFrame.SendMessage(0, _('Setup script for "%(projectName)s" succesfully created')%transdict)
        return setupScript, buildDir

