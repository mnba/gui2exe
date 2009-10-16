########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

# Start the imports

import os
import wx

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox
from Constants import _py2exe_target, _py2exe_imports, _manifest_template, ListType
from Constants import _py2exe_class, _upx_inno
from Utilities import setupString

# Get the I18N things
_ = wx.GetTranslation


class Py2ExePanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        
        **Parameters:**

        * projectName: the name of the project we are working on
        * creationDate: the date and time the project was created

        """
        
        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="py2exe")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers
        self.commonSizer_staticbox = wx.StaticBox(self, -1, _("Common Options"))
        self.includesSizer_staticbox = wx.StaticBox(self, -1, _("Includes"))
        self.packagesSizer_staticbox = wx.StaticBox(self, -1, _("Packages"))
        self.excludesSizer_staticbox = wx.StaticBox(self, -1, _("Excludes"))
        self.dllExcludesSizer_staticbox = wx.StaticBox(self, -1, _("DLL Excludes"))
        self.ignoreSizer_staticbox = wx.StaticBox(self, -1, _("Ignores"))
        self.datafile_staticbox = wx.StaticBox(self, -1, _("Data Files"))
        self.icon_staticbox = wx.StaticBox(self, -1, _("Icon Resources"))
        self.bitmap_staticbox = wx.StaticBox(self, -1, _("Bitmap Resources"))
        self.other_staticbox = wx.StaticBox(self, -1, _("Other Resources"))
        self.otherSizer_staticbox = wx.StaticBox(self, -1, _("Other Options"))
        self.targetSizer_staticbox = wx.StaticBox(self, -1, _("Target Classes"))

        # A simple label that holds information about the project
        transdict = dict(projectName=projectName, creationDate=creationDate)
        self.label = wx.StaticText(self, -1, _("Py2exe options for: %(projectName)s (Created: %(creationDate)s)")%transdict)

        # These text controls hold data used by VersionInfo in py2exe

        # A list control for the target classes, scripts
        self.multipleExe = BaseListCtrl(self, columnNames=[_("Exe Kind"), _("Python Main Script"),
                                                           _("Executable Name"), _("Version"),
                                                           _("Company Name"), _("Copyrights"),
                                                           _("Program Name")], name="multipleexe")
        
        # Optimization level for py2exe  1 for "python -O", 2 for "python -OO",
        # 0 to disable
        self.optimizeCombo = MultiComboBox(self, ["0", "1", "2"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                           self.GetName(), "optimize")
        # Compression level for the zipfile (if any) in py2exe
        self.compressCombo = MultiComboBox(self, ["0", "1", "2"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                           self.GetName(), "compressed")
        # Bundle files option for py2exe. Specifying a level of 2 includes
        # the .pyd and .dll files into the zip-archive or the executable. Thus,
        # the dist directory will contain your exe file(s), the library.zip file
        # (if you haven't specified 'zipfile=None'), and the python dll. The
        # advantage of this scheme is that the application can still load extension
        # modules from the file system if you extend sys.path at runtime.
        # Using a level of 1 includes the .pyd and .dll files into the zip-archive
        # or the executable itself, and does the same for pythonXY.dll. The advantage
        # is that you only need to distribute one file per exe, which will however
        # be quite large. Another advantage is that inproc COM servers will run
        # completely isolated from other Python interpreters in the same exe. The
        # disadvantage of this scheme is that it is impossible to load other
        # extensions from the file system, the application will crash with a fatal
        # Python error if you try this.
        self.bundleCombo = MultiComboBox(self, ["1", "2", "3"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                         self.GetName(), "bundle_files")
        # A checkbox that enables the user to choose a different name for the zipfile
        # Default is unchecked, that means zipfile=None
        self.zipfileChoice = wx.CheckBox(self, -1, "Zipfile", name="zipfile_choice")
        # The name of the zipfile (if enabled by the user)
        self.zipfileTextCtrl = wx.TextCtrl(self, -1, "None", name="zipfile")
        # A checkbox that enables the user to choose a different name for the
        # distribution directory. Default is unchecked, that means dist_dir="dist"
        self.distChoice = wx.CheckBox(self, -1, _("Dist Directory"), name="dist_dir_choice")
        # The name of the distribution directory (if enabled)
        self.distTextCtrl = wx.TextCtrl(self, -1, "dist", name="dist_dir")
        # Allows to skip the archive. If checked, this copies the Python bytecode files
        # directly into the dist directory and subdirectories - no archive is used.
        self.skiparchiveChoice = wx.CheckBox(self, -1, "Skip Archive", name="skip_archive")
        # If checked, embed the XP manifest file directly in the executable
        self.xpmanifestChoice = wx.CheckBox(self, -1, "XP Manifest File", name="manifest_file")

        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="includes")
        # A list control for the "packages" option, a comma separated list of
        # packages to include
        self.packagesList = BaseListCtrl(self, columnNames=[_("Python Packages")], name="packages")
        # A list control for the "excludes" option, a comma separated list of
        # modules to exclude
        self.excludeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="excludes")
        # A list control for the "dll_excludes" option, a comma separated list of
        # Windows dlls to include
        self.dllExcludeList = BaseListCtrl(self, columnNames=[_("DLL Names")], name="dll_excludes")
        # A list control for the "ignores" option, a comma separated list of
        # modules to ignores
        self.ignoreList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="ignores")
        # A list control for the "data_files" option. "data_files" should contain
        # a sequence of (target-dir, files) tuples, where files is a sequence of
        # files to be copied
        self.datafileList = BaseListCtrl(self, columnNames=[_("Directory")+" "*15, _("Files Path")], name="data_files")
        # A list control for the "icon_resources" option
        self.iconResourceList = BaseListCtrl(self, columnNames=[_("Id  "), _("Icon Path")], name="icon_resources")
        # A list control for the "bitmap_resources" option
        self.bitmapResourceList = BaseListCtrl(self, columnNames=[_("Id  "), _("Bitmap Path")], name="bitmap_resources")
        # A list control for the "other_resources" option
        self.otherResourceList = BaseListCtrl(self, columnNames=[_("Type"), _("Id  "), _("Path/Value")], name="other_resources")

        # This command line switch instructs py2exe to create a python module cross
        # reference and display it in the webbrowser.  This allows to answer question
        # why a certain module has been included, or if you can exclude a certain module
        # and it's dependencies. Also, the html page includes links which will even
        # allow to view the source code of a module in the browser, for easy inspection.
        self.crossRefCheck = wx.CheckBox(self, -1, "Cross-Reference", name="xref")
        # To prevent unicode encoding error, py2exe now by default includes the codecs
        # module and the encodings package. If you are sure your program never
        # implicitely or explicitely has to convert between unicode and ascii strings
        # this can be prevented by checking this checkbox 
        self.asciiCheck = wx.CheckBox(self, -1, "Ascii", name="ascii")

        # The following 2 are only for service, com_server and ctypes_com_server
        self.createExeCheck = wx.CheckBox(self, -1, "Create EXE", name="create_exe")
        self.createDllCheck = wx.CheckBox(self, -1, "Create DLL", name="create_dll")

        # By picking a Python script here, this script can do things like installing
        # a customized stdout blackhole. See py2exe's boot_common.py for examples of
        # what can be done. The custom boot script is executed during startup of
        # the executable immediately after boot_common.py is executed
        self.customBootPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL, name="custom_boot_script")

        # Hold a reference to all the list controls, to speed up things later
        self.listCtrls = [self.includeList, self.packagesList, self.excludeList, self.dllExcludeList,
                          self.ignoreList, self.datafileList, self.iconResourceList, self.bitmapResourceList,
                          self.otherResourceList]

        # Do the hard work... quite a few to layout :-D
        self.LayoutItems()
        self.SetProperties()
        self.BindEvents()
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets the properties fro Py2ExePanel and its children widgets. """

        # I use all the py2exe default values (where applicable), and my standard
        # configuration or preferences otherwise. This can easily be changed later
        # with a user customizable default project options file (or wx.Config)
        
        # Defaults (for me) zipfile=None
        self.zipfileTextCtrl.Enable(False)
        self.distTextCtrl.Enable(False)

        self.createExeCheck.SetValue(1)
        self.createDllCheck.SetValue(1)
        
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
        otherSizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        otherSizer_2 = wx.BoxSizer(wx.VERTICAL)
        ignoreSizer = wx.StaticBoxSizer(self.ignoreSizer_staticbox, wx.HORIZONTAL)
        dllExcludesSizer = wx.StaticBoxSizer(self.dllExcludesSizer_staticbox, wx.HORIZONTAL)
        excludesSizer = wx.StaticBoxSizer(self.excludesSizer_staticbox, wx.HORIZONTAL)
        packagesSizer = wx.StaticBoxSizer(self.packagesSizer_staticbox, wx.HORIZONTAL)
        includesSizer = wx.StaticBoxSizer(self.includesSizer_staticbox, wx.HORIZONTAL)
        datafilesSizer = wx.StaticBoxSizer(self.datafile_staticbox, wx.HORIZONTAL)
        iconSizer = wx.StaticBoxSizer(self.icon_staticbox, wx.HORIZONTAL)
        bitmapSizer = wx.StaticBoxSizer(self.bitmap_staticbox, wx.HORIZONTAL)
        otherResSizer = wx.StaticBoxSizer(self.other_staticbox, wx.HORIZONTAL)
        
        plusSizer = wx.BoxSizer(wx.HORIZONTAL)
        minusSizer = wx.BoxSizer(wx.HORIZONTAL)
        resourceSizer = wx.BoxSizer(wx.HORIZONTAL)
        commonSizer = wx.StaticBoxSizer(self.commonSizer_staticbox, wx.VERTICAL)

        # This grid bag sizer will hold all the list controls and widgets
        # that display py2exe options
        commonGridSizer = wx.GridBagSizer(5, 5)

        commonSizer_7 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_6 = wx.BoxSizer(wx.VERTICAL)        
        commonSizer_5 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_4 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_3 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_2 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        targetSizer = wx.StaticBoxSizer(self.targetSizer_staticbox, wx.HORIZONTAL)
        topGridSizer = wx.FlexGridSizer(1, 4, 5, 5)
        topSizer_4 = wx.BoxSizer(wx.VERTICAL)
        topSizer_3 = wx.BoxSizer(wx.VERTICAL)
        topSizer_2 = wx.BoxSizer(wx.VERTICAL)
        topSizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        flag = wx.LEFT|wx.RIGHT|wx.EXPAND
        flag2 = wx.LEFT|wx.BOTTOM|wx.TOP|wx.EXPAND
        
        mainSizer.Add(self.label, 0, wx.ALL, 10)
        targetSizer.Add(self.multipleExe, 1, flag2, 5)
        targetSizer.Add(self.multipleExe.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        mainSizer.Add(targetSizer, 0, wx.ALL|wx.EXPAND, 5)

        optimize = wx.StaticText(self, -1, _("Optimize"))
        commonSizer_1.Add(optimize, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_1.Add(self.optimizeCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_1, (1, 0), (1, 1), flag, 5)
        compress = wx.StaticText(self, -1, _("Compressed"))
        commonSizer_2.Add(compress, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_2.Add(self.compressCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_2, (1, 1), (1, 1), flag, 5)
        bundle = wx.StaticText(self, -1, _("Bundle Files"))
        commonSizer_3.Add(bundle, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_3.Add(self.bundleCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_3, (1, 2), (1, 1), flag, 5)

        commonGridSizer.Add((0, 0), (1, 3), (1, 1), wx.EXPAND)
        
        commonSizer_4.Add(self.zipfileChoice, 0, wx.BOTTOM, 2)
        commonSizer_4.Add(self.zipfileTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_4, (1, 4), (1, 1), flag, 5)
        commonSizer_5.Add(self.distChoice, 0, wx.BOTTOM, 2)
        commonSizer_5.Add(self.distTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_5, (1, 5), (1, 1), flag, 5)

        commonGridSizer.AddGrowableCol(3)
        commonGridSizer.AddGrowableCol(4)
        commonGridSizer.AddGrowableCol(5)
        commonGridSizer.AddGrowableCol(6)
        commonGridSizer.SetEmptyCellSize((0, 0))
        
        commonSizer.Add(commonGridSizer, 1, wx.EXPAND|wx.BOTTOM, 5)
        mainSizer.Add(commonSizer, 0, wx.ALL|wx.EXPAND, 5)

        flag = wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND
        # Add the list controls
        includesSizer.Add(self.includeList, 1, flag, 5)
        includesSizer.Add(self.includeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        packagesSizer.Add(self.packagesList, 1, flag, 5)
        packagesSizer.Add(self.packagesList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        
        plusSizer.Add(includesSizer, 1, wx.EXPAND)
        plusSizer.Add(packagesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(plusSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        excludesSizer.Add(self.excludeList, 1, flag, 5)
        excludesSizer.Add(self.excludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        dllExcludesSizer.Add(self.dllExcludeList, 1, flag, 5)
        dllExcludesSizer.Add(self.dllExcludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        ignoreSizer.Add(self.ignoreList, 1, flag, 5)
        ignoreSizer.Add(self.ignoreList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)

        minusSizer.Add(excludesSizer, 1, wx.EXPAND)
        minusSizer.Add(dllExcludesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        minusSizer.Add(ignoreSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(minusSizer, 1, wx.ALL|wx.EXPAND, 5)

        datafilesSizer.Add(self.datafileList, 1, flag, 5)
        datafilesSizer.Add(self.datafileList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        mainSizer.Add(datafilesSizer, 1, flag, 5)

        iconSizer.Add(self.iconResourceList, 1, flag, 5)
        iconSizer.Add(self.iconResourceList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        bitmapSizer.Add(self.bitmapResourceList, 1, flag, 5)
        bitmapSizer.Add(self.bitmapResourceList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        otherResSizer.Add(self.otherResourceList, 1, flag, 5)
        otherResSizer.Add(self.otherResourceList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        resourceSizer.Add(iconSizer, 1, wx.EXPAND)
        resourceSizer.Add(bitmapSizer, 1, wx.EXPAND|wx.LEFT, 5)
        resourceSizer.Add(otherResSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(resourceSizer, 0, wx.ALL|wx.EXPAND, 5)

        # Add the other options at the bottom
        otherSizer_1.Add(self.xpmanifestChoice, 0, wx.ALL, 5)
        otherSizer_1.Add((0, 0), 1)
        otherSizer_1.Add(self.crossRefCheck, 0, wx.ALL, 5)
        otherSizer_1.Add((0, 0), 1)
        otherSizer_1.Add(self.asciiCheck, 0, wx.ALL, 5)
        otherSizer_1.Add((0, 0), 1)        
        otherSizer_1.Add(self.skiparchiveChoice, 0, wx.ALL, 5)
        otherSizer_1.Add((0, 0), 1)
        otherSizer_1.Add(self.createExeCheck, 0, wx.ALL, 5)
        otherSizer_1.Add((0, 0), 1)
        otherSizer_1.Add(self.createDllCheck, 0, wx.ALL, 5)

        customboot = wx.StaticText(self, -1, _("Custom Boot Script"))
        otherSizer_2.Add(customboot, 0, wx.BOTTOM, 2)
        otherSizer_2.Add(self.customBootPicker, 0, wx.EXPAND)
        otherSizer.Add(otherSizer_1, 0, wx.EXPAND)
        otherSizer.Add(otherSizer_2, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(otherSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        self.SetAutoLayout(True)
        self.SetSizer(mainSizer)

        self.SetupScrolling()
        self.label.SetFocus()
    

    def EnableDllAndExe(self):
        """
        Enables or disables the create_exe and create_dll option for py2exe.
        These options are only available for services, com_servers and ctypes_com_servers.
        """

        # Disable the create_exe and create_dll
        self.createDllCheck.Enable(False)
        self.createExeCheck.Enable(False)

        # Enable the create_exe/create_dll if a service, com_server or ctypes_com_server are there
        for indx in xrange(self.multipleExe.GetItemCount()):
            consoleOrWindows = self.multipleExe.GetItem(indx, 1).GetText()
            if consoleOrWindows in ["service", "com_server", "ctypes_com_server"]:
                # These things accept module *names*, not file names...
                self.createDllCheck.Enable(True)
                self.createExeCheck.Enable(True)
                break
        

    def ValidateOptions(self):
        """ Validates the py2exe input options before compiling. """

        # check if the script files exist
        if self.multipleExe.GetItemCount() == 0:
            msg = _("No Python scripts have been added.")
            self.MainFrame.RunError(2, msg, True)
            return False

        for indx in xrange(self.multipleExe.GetItemCount()):
            script = self.multipleExe.GetItem(indx, 2)
            if not os.path.isfile(script.GetText()):
                msg = _("Python main script is not a valid file.")
                self.MainFrame.RunError(2, msg, True)
                return False

        # check if the custom boot file is not empty and if it exists
        customBoot = self.customBootPicker.GetPath()
        if customBoot and not os.path.isfile(customBoot):
            msg = _("Custom boot file is not a valid file.")
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
        # See if the user wants the manifest file embedded in the executable
        manifestFile = self.xpmanifestChoice.GetValue()
        # Get the post-compilation code (if any) that the user added
        postCompile = project.GetPostCompileCode(self.GetName())

        for lists in self.listCtrls:
            # Last update for all the list controls
            lists.UpdateProject(False)

        # Build the target script file        
        return self.BuildTargetClass(configuration, project, manifestFile, customCode, postCompile)


    def BuildTargetClass(self, configuration, project, manifestFile, customCode, postCompile):
        """ Builds the py2exe compilation script file, returning it as a string. """

        # A couple of dictionaries to populate the setup string        
        setupDict, importDict = {}, {}
        configuration = dict(configuration)
        # Delete the keys we don't need
        zipChoice, distChoice = self.zipfileChoice.GetValue(), self.distChoice.GetValue()
        createExe, createDll = self.createExeCheck.GetValue(), self.createDllCheck.GetValue()
        
        del configuration["zipfile_choice"], configuration["dist_dir_choice"]
        if "create_exe" in configuration:
            del configuration["create_exe"]
        if "create_dll" in configuration:
            del configuration["create_dll"]
        
        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if key == "custom_boot_script":
                # I don't know how often this option is used
                if not item:
                    item = "''"
                else:
                    item = "r'%s'"%item
            elif isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))

            if type(item) == ListType and key != "multipleexe":
                # Terrible hack to setup correctly the string to be included
                # in the setup file
                item = setupString(key, item)

            if key == "zipfile":
                if item and item.strip() and zipChoice:
                    if (os.path.splitext(item)[1]).lower() != ".zip":
                        self.MainFrame.SendMessage(1, _('zipfile does not have ".zip" extension'))
                    item = "r'%s'"%item
                else:
                    item = None
            elif key == "dist_dir":
                if item and item.strip() and distChoice:
                    item = r'%s'%item
                else:
                    item = "dist"
                    if distChoice:
                        self.MainFrame.SendMessage(1, _('Empty dist_dir option. Using default value "dist"'))
            
            setupDict[key] = item

        targetclass = ""
        baseName = "GUI2Exe_Target_%d"
        console, windows, service, com_server, ctypes_com_server = "console = [", "windows = [", \
                                                                   "service = [", "com_server = [", \
                                                                   "ctypes_com_server = ["

        for indx in xrange(self.multipleExe.GetItemCount()):

            tupleMultiple = (baseName%(indx+1), )
            consoleOrWindows = self.multipleExe.GetItem(indx, 1).GetText()
            scriptFile = self.multipleExe.GetItem(indx, 2).GetText()
            buildDir, scriptFile = os.path.split(scriptFile)

            isSpecial = False
            realScript = scriptFile

            if consoleOrWindows in ["service", "com_server", "ctypes_com_server"]:
                # These things accept module *names*, not file names...
                realScript = os.path.splitext(scriptFile)[0]
                isSpecial = True
                
            if consoleOrWindows == "console":
                console += tupleMultiple[0] + ", "
            elif consoleOrWindows == "windows":
                windows += tupleMultiple[0] + ", "
            elif consoleOrWindows == "service":
                service += tupleMultiple[0] + ", "
            elif consoleOrWindows == "com_server":
                com_server += tupleMultiple[0] + ", "
            else:
                ctypes_com_server += tupleMultiple[0] + ", "

            tupleMultiple += (realScript, )
            
            for col in xrange(3, self.multipleExe.GetColumnCount()):
                item = self.multipleExe.GetItem(indx, col)
                text = item.GetText()
                if not text.strip():
                    text = os.path.splitext(scriptFile)[0]
                    self.MainFrame.SendMessage(1, _('Empty targetName option. Using Python script name'))
                if col == 3:
                    programName = text.strip()
                elif col == 4:
                    versionNumber = text.strip()
                    
                tupleMultiple += (text, )

            extraKeywords = self.multipleExe.GetExtraKeywords(indx)
            if isSpecial:
                tupleMultiple += (extraKeywords + "\n    create_exe = %s, create_dll = %s"%(bool(createExe), bool(createDll)), )
            else:
                tupleMultiple += (extraKeywords, )

            if isSpecial:
                # services, com_servers and ctypes_com_server require a "modules" keyword
                py2exe_class = _py2exe_class.replace("    script = ", "    modules = ")
            else:
                py2exe_class = _py2exe_class
                
            targetclass += py2exe_class%tupleMultiple
                

        # Add the custom code (if any)
        setupDict["customcode"] = (customCode and [customCode.strip()] or ["# No custom code added"])[0]
        # Look if the user wants to remove the "build" directory
        removeBuild = (self.MainFrame.deleteBuild and \
                       ['# Remove the build folder\nshutil.rmtree("build", ignore_errors=True)\n'] or [""])[0]
        
        importDict["remove_build"] = removeBuild
        # Include the GUI2Exe version in the setup script
        importDict["gui2exever"] = self.MainFrame.GetVersion()

        # Add the post-compilation code (if any)
        setupDict["postcompilecode"] = (postCompile and [postCompile.strip()] or ["# No post-compilation code added"])[0]
        
        # Populate the "import" section
        setupScript = _py2exe_imports % importDict

        if manifestFile:
            # Embed the manifest file                
            setupDict["other_resources"] = setupDict["other_resources"]%""
            setupScript += _manifest_template % dict(prog=programName)

        setupDict["targetclasses"] = targetclass
        setupDict["console"] = console.rstrip(", ") + "]"
        setupDict["windows"] = windows.rstrip(", ") + "]"
        setupDict["service"] = service.rstrip(", ") + "]"
        setupDict["com_server"] = com_server.rstrip(", ") + "]"
        setupDict["ctypes_com_server"] = ctypes_com_server.rstrip(", ") + "]"

        upx, inno = project.GetUseUPX("py2exe"), project.GetBuildInno("py2exe")

        if upx or inno:
            upxinno = _upx_inno%(upx, inno, programName, versionNumber)
            setupDict["upx_inno"] = upxinno
            setupDict["use_upx_inno"] = 'cmdclass = {"py2exe": Py2exe},'
        else:
            setupDict["upx_inno"] = "# No custom class for UPX compression or Inno Setup script"
            setupDict["use_upx_inno"] = "# No UPX or Inno Setup"
        
        # Populate the main section of the setup script            
        setupScript += _py2exe_target % setupDict
        
        if manifestFile:
            # Substitute a dummy line with the real one
            setupScript = setupScript.replace("'manifest_template'", "manifest_template")

        # Send a message to out fancy bottom log window
        transdict = dict(projectName=project.GetName())
        self.MainFrame.SendMessage(0, _('Setup script for "%(projectName)s" succesfully created')% transdict)
        return setupScript, buildDir
