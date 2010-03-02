# -*- coding: utf-8 -*-

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

import wx.lib.buttons as buttons

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox
from Constants import _pywild, _iconwild, ListType
from Utilities import setupString

# Get the I18N things
_ = wx.GetTranslation


class VendorIDPanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        
        **Parameters:**

        * projectName: the name of the project we are working on
        * creationDate: the date and time the project was created

        """

        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="vendorid")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers
        self.commonSizer_staticbox = wx.StaticBox(self, -1, _("Common Options"))
        self.includesSizer_staticbox = wx.StaticBox(self, -1, _("Includes"))
        self.packagesSizer_staticbox = wx.StaticBox(self, -1, _("Packages"))
        self.otherSizer_staticbox = wx.StaticBox(self, -1, _("Other Options"))

        # A simple label that holds information about the project
        transdict = dict(projectName=projectName, creationDate=creationDate)
        self.label = wx.StaticText(self, -1, _("VendorID options for: %(projectName)s (Created: %(creationDate)s)")%transdict)

        # The file picker that allows us to pick the script to be compiled by py2app
        self.scriptPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL,
                                              wildcard=_pywild, name="script")

        # Name of the executable
        self.exeTextCtrl = wx.TextCtrl(self, -1, "", name="exename")

        # Optimization level for vendorid  1 for "python -O", 2 for "python -OO",
        # 0 to disable
        self.optimizeCombo = MultiComboBox(self, ["0", "1", "2"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                           self.GetName(), "optimize")

        # A checkbox that enables the user to choose a different name for the
        # distribution directory. Default is unchecked, that means build_dir="build_ + python main script name"
        self.distChoice = wx.CheckBox(self, -1, _("Build Directory"), name="build_dir_choice")
        # The name of the distribution directory (if enabled)
        self.distTextCtrl = wx.TextCtrl(self, -1, "", name="build_dir")
        
        # A checkbox that enables the user to choose a different name for the
        # installation directory. Default is unchecked, that means sys.exec_prefix
        self.instChoice = wx.CheckBox(self, -1, _("Installation Directory"), name="install_dir_choice")
        # The name of the installation directory (if enabled)
        self.instTextCtrl = wx.TextCtrl(self, -1, "", name="install_dir")
        # Prefix for compiled Python code
        self.prefixTextCtrl = wx.TextCtrl(self, -1, "", name="prefix")
        # The icon picker that allows us to pick the application icon (Windows only)
        self.iconPicker = wx.FilePickerCtrl(self, style=wx.FLP_USE_TEXTCTRL,
                                            wildcard="Icon files (*.ico)|*.ico", name="iconfile")
                
        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="includes")
        # A list control for the "packages" option, a comma separated list of
        # packages to include
        self.packagesList = BaseListCtrl(self, columnNames=[_("Python Packages")], name="packages")

        # Create a signed interpreter (default is True)
        self.signCheck = wx.CheckBox(self, -1, "Sign Interpreter", name="signed")

        # Create console application (Windows only)
        self.consoleCheck = wx.CheckBox(self, -1, "Console App", name="console")

        # Add support for Python's verbose flag (default is False)
        self.verboseCheck = wx.CheckBox(self, -1, "Verbose Flag", name="verbose")

        # Run make install after compilation
        self.runmakeCheck = wx.CheckBox(self, -1, "Run Make Install", name="runmake")
        
        # Hold a reference to all the list controls, to speed up things later
        self.listCtrls = [self.includeList, self.packagesList]

        # Do the hard work... quite a few to layout :-D
        self.LayoutItems()
        self.SetProperties()
        self.BindEvents()


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets the properties fro Py2AppPanel and its children widgets. """

        # I use all the py2app default values (where applicable), and my standard
        # configuration or preferences otherwise. This can easily be changed later
        # with a user customizable default project options file (or wx.Config)
        
        self.distTextCtrl.Enable(False)
        self.instTextCtrl.Enable(False)

        # Set a bold font for the static texts
        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        
        for child in self.GetChildren():
            if isinstance(child, wx.StaticText) or isinstance(child, wx.CheckBox):
                child.SetFont(font)

        if wx.Platform != "__WXMSW__":
            # Disable non-Windows options
            self.iconPicker.SetPath("")
            self.iconPicker.Enable(False)
            self.consoleCheck.SetValue(0)
            self.consoleCheck.Enable(False)
            

    def LayoutItems(self):
        """ Layouts the widgets using sizers. """

        # Create a whole bunch of sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        otherSizer = wx.StaticBoxSizer(self.otherSizer_staticbox, wx.VERTICAL)
        otherSizer_1 = wx.FlexGridSizer(1, 4, 5, 5)
        plusSizer = wx.BoxSizer(wx.HORIZONTAL)
        minusSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        packagesSizer = wx.StaticBoxSizer(self.packagesSizer_staticbox, wx.HORIZONTAL)
        includesSizer = wx.StaticBoxSizer(self.includesSizer_staticbox, wx.HORIZONTAL)        
        commonSizer = wx.StaticBoxSizer(self.commonSizer_staticbox, wx.VERTICAL)

        # This grid bag sizer will hold all the list controls and widgets
        # that display py2app options
        commonGridSizer = wx.GridBagSizer(5, 5)

        commonSizer_8 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_7 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_6 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_5 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_4 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_3 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_2 = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
                
        # Add the VersionInfo text controls
        mainSizer.Add(self.label, 0, wx.ALL, 10)

        flag = wx.LEFT|wx.RIGHT|wx.EXPAND

        script = wx.StaticText(self, -1, _("Python Main Script"))
        commonSizer_2.Add(script, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_2.Add(self.scriptPicker, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_2, (1, 0), (1, 4), flag, 5)

        exename = wx.StaticText(self, -1, _("Executable Name"))        
        commonSizer_3.Add(exename, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_3.Add(self.exeTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_3, (1, 4), (1, 2), flag, 5)

        optimize = wx.StaticText(self, -1, _("Optimize"))
        commonSizer_4.Add(optimize, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_4.Add(self.optimizeCombo, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_4, (3, 0), (1, 1), flag|wx.TOP, 5)

        commonSizer_5.Add(self.distChoice, 0, wx.BOTTOM, 2)
        commonSizer_5.Add(self.distTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_5, (3, 1), (1, 1), flag|wx.TOP, 5)
        
        commonSizer_6.Add(self.instChoice, 0, wx.BOTTOM, 2)
        commonSizer_6.Add(self.instTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_6, (3, 2), (1, 1), flag|wx.TOP, 5)

        prefix = wx.StaticText(self, -1, _("Prefix"))
        commonSizer_8.Add(prefix, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_8.Add(self.prefixTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_8, (3, 3), (1, 1), flag|wx.TOP, 5)

        icon = wx.StaticText(self, -1, _("Icon File"))
        commonSizer_7.Add(icon, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_7.Add(self.iconPicker, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_7, (3, 4), (1, 2), flag|wx.TOP, 5)
        
        commonGridSizer.AddGrowableCol(1)
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

        plusSizer.Add(includesSizer, 1, wx.EXPAND)
        plusSizer.Add(packagesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(plusSizer, 1, wx.ALL|wx.EXPAND, 5)
        
        # Add the other options at the bottom
        otherSizer_1.Add(self.signCheck, 0)
        otherSizer_1.Add(self.consoleCheck, 0)
        otherSizer_1.Add(self.verboseCheck, 0)
        otherSizer_1.Add(self.runmakeCheck, 0)
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
        """ Validates the VendorID input options before compiling. """

        # check if the script file exists
        if not os.path.isfile(self.scriptPicker.GetPath()):
            msg = _("Python main script is not a valid file.")
            self.MainFrame.RunError(2, msg, True)
            return False

        # check if the icon file is not empty and if it exists
        icon = self.iconPicker.GetPath()
        if icon and not os.path.isfile(icon):
            msg = _("Icon file is not a valid file.")
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

        for lists in self.listCtrls:
            # Last update for all the list controls
            lists.UpdateProject(False)

        # Build the target script file        
        return self.BuildTargetClass(configuration, project, None)


    def BuildTargetClass(self, configuration, project, manifestFile):
        """ Builds the VendorID compilation options, returning it as a string. """

        # A couple of dictionaries to populate the setup string
        configuration = dict(configuration)
        distChoice = self.distChoice.GetValue()
        instChoice = self.instChoice.GetValue()

        pythonName = os.path.split(os.path.splitext(self.scriptPicker.GetPath())[0])[1]
        optionString = ""

        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if key in ["build_dir_choice", "install_dir_choice"]:
                continue
            if key == "script":
                buildDir, scriptFile = os.path.split(item)
            elif key == "build_dir":
                if not item.strip() or not distChoice:
                    outputDir = os.path.normpath(buildDir + "/build_%s"%pythonName)
                    if distChoice:
                        self.MainFrame.SendMessage(1, _('Empty build_dir option. Using default value "build_%s"'%pythonName))
                else:
                    optionString += " -d %s "%item.strip()
                    outputDir = os.path.normpath(buildDir + "/" + item.strip())
                                    
            elif key == "install":
                if not item.strip() or not instChoice:
                    if instChoice:
                        self.MainFrame.SendMessage(1, _('Empty install_dir option. Using default value "sys.exec_prefix"'))
                else:
                    optionString += " -t %s "%item.strip()

            elif key == "iconfile":
                if item.strip():
                    optionString += " -i %s "%item.strip()

            elif key == "exename":
                if item.strip():
                    optionString += " -n %s "%item.strip()

            elif key == "prefix":
                if item.strip():
                    optionString += " -p %s "%item.strip()
                    
            if isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))
                if key == "verbose" and item:
                    optionString += " -v "
                elif key == "signed" and not item:
                    optionString += " -u "
                elif key == "console" and item:
                    optionString += " -c "
                elif key == "runmake":
                    runMakeInstall = item

            if type(item) == ListType:
                # Loop over all the included packages and modules
                for pkg in item:
                    optionString += " -m %s "%pkg
                
        # Send a message to out fancy bottom log window
        transdict = dict(projectName=project.GetName())

        if wx.Platform == "__WXMSW__":
            separator = "&"
        else:
            separator = ";"

        # Get the user preference for GNU make or MS nmake
        vendorIDPath = self.MainFrame.GetVendorIDPath()
        if not vendorIDPath:
            makeOrNmake = "make"
        else:
            sibPath, makeOrNmake = vendorIDPath
        
        optionString = optionString + " " + self.scriptPicker.GetPath().strip()
        optionString += " " + separator + "cd %s "%outputDir + separator + "%s "%makeOrNmake
        if runMakeInstall:
            optionString += separator + "cd %s "%outputDir + separator + "%s install"%makeOrNmake
        
        self.MainFrame.SendMessage(0, _('Setup script for "%(projectName)s" succesfully created')%transdict)
        return optionString, buildDir

    
