# Start the imports

import os
import wx
import wx.lib.scrolledpanel as scrolled

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox
from Constants import _py2exe_target, _py2exe_imports, _manifest_template, _pywild, ListType
from Constants import _py2exe_class
from Utilities import setupString


class Py2ExePanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        @param projectName: the name of the project we are working on
        @param creationDate: the date and time the project was created

        """
        
        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="py2exe")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers
        self.commonSizer_staticbox = wx.StaticBox(self, -1, "Common Options")
        self.includesSizer_staticbox = wx.StaticBox(self, -1, "Includes")
        self.packagesSizer_staticbox = wx.StaticBox(self, -1, "Packages")
        self.excludesSizer_staticbox = wx.StaticBox(self, -1, "Excludes")
        self.dllExcludesSizer_staticbox = wx.StaticBox(self, -1, "DLL Excludes")
        self.ignoreSizer_staticbox = wx.StaticBox(self, -1, "Ignores")
        self.datafile_staticbox = wx.StaticBox(self, -1, "Data Files")
        self.icon_staticbox = wx.StaticBox(self, -1, "Icon Resources")
        self.bitmap_staticbox = wx.StaticBox(self, -1, "Bitmap Resources")
        self.other_staticbox = wx.StaticBox(self, -1, "Other Resources")
        self.otherSizer_staticbox = wx.StaticBox(self, -1, "Other Options")
        self.targetSizer_staticbox = wx.StaticBox(self, -1, "Target Classes")

        # A simple label that holds information about the project
        self.label = wx.StaticText(self, -1, "Py2exe options for: %s (Created: %s)"%(projectName, creationDate))

        # These text controls hold data used by VersionInfo in py2exe

        # A list control for the target classes, scripts
        self.multipleExe = BaseListCtrl(self, columnNames=["Exe Kind", "Python Main Script",
                                                           "Executable Name", "Version",
                                                           "Company Name", "Copyrights",
                                                           "Program Name"], name="multipleexe")
        
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
        self.distChoice = wx.CheckBox(self, -1, "Dist Directory", name="dist_dir_choice")
        # The name of the distribution directory (if enabled)
        self.distTextCtrl = wx.TextCtrl(self, -1, "dist", name="dist_dir")
        # Allows to skip the archive. If checked, this copies the Python bytecode files
        # directly into the dist directory and subdirectories - no archive is used.
        self.skiparchiveChoice = wx.CheckBox(self, -1, "Skip Archive", name="skip_archive")
        # If checked, embed the XP manifest file directly in the executable
        self.xpmanifestChoice = wx.CheckBox(self, -1, "XP Manifest File", name="manifest_file")

        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=["Python Modules"], name="includes")
        # A list control for the "packages" option, a comma separated list of
        # packages to include
        self.packagesList = BaseListCtrl(self, columnNames=["Python Packages"], name="packages")
        # A list control for the "excludes" option, a comma separated list of
        # modules to exclude
        self.excludeList = BaseListCtrl(self, columnNames=["Python Modules"], name="excludes")
        # A list control for the "dll_excludes" option, a comma separated list of
        # Windows dlls to include
        self.dllExcludeList = BaseListCtrl(self, columnNames=["DLL Names"], name="dll_excludes")
        # A list control for the "ignores" option, a comma separated list of
        # modules to ignores
        self.ignoreList = BaseListCtrl(self, columnNames=["Python Modules"], name="ignores")
        # A list control for the "data_files" option. "data_files" should contain
        # a sequence of (target-dir, files) tuples, where files is a sequence of
        # files to be copied
        self.datafileList = BaseListCtrl(self, columnNames=["Directory"+" "*15, "Files Path"], name="data_files")
        # A list control for the "icon_resources" option
        self.iconResourceList = BaseListCtrl(self, columnNames=["Id  ", "Icon Path"], name="icon_resources")
        # A list control for the "bitmap_resources" option
        self.bitmapResourceList = BaseListCtrl(self, columnNames=["Id  ", "Bitmap Path"], name="bitmap_resources")
        # A list control for the "other_resources" option
        self.otherResourceList = BaseListCtrl(self, columnNames=["Type", "Id  ", "Icon Path"], name="other_resources")

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
        
        targetSizer = wx.StaticBoxSizer(self.targetSizer_staticbox, wx.VERTICAL)
        topGridSizer = wx.FlexGridSizer(1, 4, 5, 5)
        topSizer_4 = wx.BoxSizer(wx.VERTICAL)
        topSizer_3 = wx.BoxSizer(wx.VERTICAL)
        topSizer_2 = wx.BoxSizer(wx.VERTICAL)
        topSizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        # Add the VersionInfo text controls
        mainSizer.Add(self.label, 0, wx.ALL, 10)
        targetSizer.Add(self.multipleExe, 1, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(targetSizer, 0, wx.ALL|wx.EXPAND, 5)

        flag = wx.LEFT|wx.RIGHT|wx.EXPAND
        
        optimize = wx.StaticText(self, -1, "Optimize")
        commonSizer_1.Add(optimize, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_1.Add(self.optimizeCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_1, (1, 0), (1, 1), flag, 5)
        compress = wx.StaticText(self, -1, "Compressed")
        commonSizer_2.Add(compress, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_2.Add(self.compressCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_2, (1, 1), (1, 1), flag, 5)
        bundle = wx.StaticText(self, -1, "Bundle Files")
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

        # Add the list controls
        includesSizer.Add(self.includeList, 1, wx.ALL|wx.EXPAND, 5)
        packagesSizer.Add(self.packagesList, 1, wx.ALL|wx.EXPAND, 5)
        
        plusSizer.Add(includesSizer, 1, wx.EXPAND)
        plusSizer.Add(packagesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(plusSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        excludesSizer.Add(self.excludeList, 1, wx.ALL|wx.EXPAND, 5)
        dllExcludesSizer.Add(self.dllExcludeList, 1, wx.ALL|wx.EXPAND, 5)
        ignoreSizer.Add(self.ignoreList, 1, wx.ALL|wx.EXPAND, 5)

        minusSizer.Add(excludesSizer, 1, wx.EXPAND)
        minusSizer.Add(dllExcludesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        minusSizer.Add(ignoreSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(minusSizer, 1, wx.ALL|wx.EXPAND, 5)

        datafilesSizer.Add(self.datafileList, 1, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(datafilesSizer, 1, wx.ALL|wx.EXPAND, 5)

        iconSizer.Add(self.iconResourceList, 1, wx.EXPAND|wx.ALL, 5)
        bitmapSizer.Add(self.bitmapResourceList, 1, wx.EXPAND|wx.ALL, 5)
        otherResSizer.Add(self.otherResourceList, 1, wx.EXPAND|wx.ALL, 5)
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
        customboot = wx.StaticText(self, -1, "Custom Boot Script")
        otherSizer_2.Add(customboot, 0, wx.BOTTOM, 2)
        otherSizer_2.Add(self.customBootPicker, 0, wx.EXPAND)
        otherSizer.Add(otherSizer_1, 0, wx.EXPAND)
        otherSizer.Add(otherSizer_2, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(otherSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        self.SetAutoLayout(True)
        self.SetSizer(mainSizer)

        self.SetupScrolling()
        self.label.SetFocus()
    

    def ValidateOptions(self):
        """ Validates the py2exe input options before compiling. """

        # check if the script files exist
        if self.multipleExe.GetItemCount() == 0:
            msg = "No Python scripts have been added."
            self.MainFrame.RunError("Error", msg, True)
            return False

        for indx in xrange(self.multipleExe.GetItemCount()):
            script = self.multipleExe.GetItem(indx, 2)
            if not os.path.isfile(script.GetText()):
                msg = "Python main script is not a valid file."
                self.MainFrame.RunError("Error", msg, True)
                return False

        # check if the custom boot file is not empty and if it exists
        customBoot = self.customBootPicker.GetPath()
        if customBoot and not os.path.isfile(customBoot):
            msg = "Custom boot file is not a valid file"
            self.MainFrame.RunError("Error", msg+".", True)
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
        del configuration["zipfile_choice"], configuration["dist_dir_choice"]

        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if key == "custom_boot_script" and not item:
                # I don't know how often this option is used
                item = "''"
            elif isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))

            if type(item) == ListType and key != "multipleexe":
                # Terrible hack to setup correctly the string to be included
                # in the setup file
                item = setupString(key, item)

            if key == "zipfile":
                if item and item.strip() and zipChoice:
                    if (os.path.splitext(item)[1]).lower() != ".zip":
                        self.MainFrame.SendMessage("Warning", 'zipfile does not have ".zip" extension')
                    item = "r'%s'"%item
                else:
                    item = None
            elif key == "dist_dir":
                if item and item.strip() and distChoice:
                    item = r'%s'%item
                else:
                    item = "dist"
                    if distChoice:
                        self.MainFrame.SendMessage("Warning", 'Empty dist_dir option. Using default value "dist" ')
                
            setupDict[key] = item

        targetclass = ""
        baseName = "GUI2Exe_Target_%d"
        console, windows = "console = [", "windows = ["

        for indx in xrange(self.multipleExe.GetItemCount()):

            tupleMultiple = (baseName%(indx+1), )
            consoleOrWindows = self.multipleExe.GetItem(indx, 1).GetText()
            scriptFile = self.multipleExe.GetItem(indx, 2).GetText()
            buildDir, scriptFile = os.path.split(scriptFile)

            if consoleOrWindows == "console":
                console += tupleMultiple[0] + ", "
            else:
                windows += tupleMultiple[0] + ", "

            tupleMultiple += (scriptFile, )
            
            for col in xrange(3, self.multipleExe.GetColumnCount()):
                item = self.multipleExe.GetItem(indx, col)
                text = item.GetText()
                if not text.strip():
                    text = os.path.splitext(scriptFile)[0]
                if col == 3:
                    programName = text.strip()
                    
                tupleMultiple += (text, )

            targetclass += _py2exe_class%tupleMultiple                

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

        # Populate the main section of the setup script            
        setupScript += _py2exe_target % setupDict
        
        if manifestFile:
            # Substitute a dummy line with the real one
            setupScript = setupScript.replace("'manifest_template'", "manifest_template")

        # Send a message to out fancy bottom log window
        self.MainFrame.SendMessage("Message", 'Setup script for "%s" succesfully created' % project.GetName())
        return setupScript, buildDir
