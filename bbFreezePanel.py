# -*- coding: utf-8 -*-

########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

# Start the imports

import sys
import os
import wx

from BaseBuilderPanel import BaseBuilderPanel
from Widgets import BaseListCtrl, MultiComboBox
from Constants import _bbFreeze_imports, _bbFreeze_target, _bbFreeze_class, _pywild, ListType
from Utilities import setupString

# Get the I18N things
_ = wx.GetTranslation


class bbFreezePanel(BaseBuilderPanel):

    def __init__(self, parent, projectName, creationDate):
        """
        Default class constructor.

        
        **Parameters:**

        * projectName: the name of the project we are working on
        * creationDate: the date and time the project was created

        """
        
        BaseBuilderPanel.__init__(self, parent, projectName, creationDate, name="bbfreeze")

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False

        # A whole bunch of static box sizers
        self.commonSizer_staticbox = wx.StaticBox(self, -1, _("Common Options"))
        self.includesSizer_staticbox = wx.StaticBox(self, -1, _("Includes"))
        self.excludesSizer_staticbox = wx.StaticBox(self, -1, _("Excludes"))
        self.otherOptionsSizer_staticbox = wx.StaticBox(self, -1, _("Other Options"))
        self.targetSizer_staticbox = wx.StaticBox(self, -1, _("Target Classes"))

        transdict = dict(projectName=projectName, creationDate=creationDate)
        # A simple label that holds information about the project
        self.label = wx.StaticText(self, -1, _("bbFreeze options for: %(projectName)s (Created: %(creationDate)s)")%transdict)

        # A list control for the target classes, scripts
        self.multipleExe = BaseListCtrl(self, columnNames=[_("Exe Kind"), _("Python Main Script")],
                                        name="multipleexe")
        
        # Optimization level for bbFreeze 1 for "python -O", 2 for "python -OO",
        # 0 to disable
        self.optimizeCombo = MultiComboBox(self, ["0", "1", "2"], wx.CB_DROPDOWN|wx.CB_READONLY,
                                           self.GetName(), "optimize")
        # Compression level for the zipfile in bbFreeze
        self.compressCombo = MultiComboBox(self, ["0", "1"],
                                           wx.CB_DROPDOWN|wx.CB_READONLY, self.GetName(), "compress")

        # A checkbox that enables the user to choose a different name for the
        # distribution directory. Default is unchecked, that means dist_dir="dist"
        self.distChoice = wx.CheckBox(self, -1, _("Dist Directory"), name="dist_dir_choice")
        # The name of the distribution directory (if enabled)
        self.distTextCtrl = wx.TextCtrl(self, -1, "dist", name="dist_dir")

        # A list control for the "includes" option, a comma separated list of
        # modules to include
        self.includeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="includes")
        # A list control for the "excludes" option, a comma separated list of
        # modules to exclude
        self.excludeList = BaseListCtrl(self, columnNames=[_("Python Modules")], name="excludes")

        self.includeInterpreter = wx.CheckBox(self, -1, _("Include Python Interpreter"), name="include_py")
        self.addManifest = wx.CheckBox(self, -1, _("Create Manifest File (MSW)"), name="create_manifest_file")

        # Hold a reference to all the list controls, to speed up things later
        self.listCtrls = [self.includeList, self.excludeList]

        # Do the hard work... quite a few to layout :-D
        self.LayoutItems()
        self.SetProperties()
        self.BindEvents()
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets the properties fro bbFreezePanel and its children widgets. """

        # I use all the bbFreeze default values (where applicable), and my standard
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
        otherOptionsSizer = wx.StaticBoxSizer(self.otherOptionsSizer_staticbox, wx.HORIZONTAL)
        excludesSizer = wx.StaticBoxSizer(self.excludesSizer_staticbox, wx.HORIZONTAL)
        includesSizer = wx.StaticBoxSizer(self.includesSizer_staticbox, wx.HORIZONTAL)
        targetSizer = wx.StaticBoxSizer(self.targetSizer_staticbox, wx.HORIZONTAL)
        
        plusSizer = wx.BoxSizer(wx.HORIZONTAL)
        minusSizer = wx.BoxSizer(wx.HORIZONTAL)
        commonSizer = wx.StaticBoxSizer(self.commonSizer_staticbox, wx.VERTICAL)

        # This grid bag sizer will hold all the list controls and widgets
        # that display bbFreeze options
        commonGridSizer = wx.GridBagSizer(5, 5)

        commonSizer_7 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_6 = wx.BoxSizer(wx.VERTICAL)        
        commonSizer_5 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_4 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_3 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_2 = wx.BoxSizer(wx.VERTICAL)
        commonSizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        targetSizer = wx.StaticBoxSizer(self.targetSizer_staticbox, wx.HORIZONTAL)
        
        flag2 = wx.LEFT|wx.BOTTOM|wx.TOP|wx.EXPAND
        
        mainSizer.Add(self.label, 0, wx.ALL, 10)
        targetSizer.Add(self.multipleExe, 1, flag2, 5)
        targetSizer.Add(self.multipleExe.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        mainSizer.Add(targetSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        optimize = wx.StaticText(self, -1, _("Optimize"))
        commonSizer_1.Add(optimize, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_1.Add(self.optimizeCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_1, (1, 0), (1, 1), wx.ALL|wx.EXPAND, 5)
        compress = wx.StaticText(self, -1, _("Compressed"))
        commonSizer_2.Add(compress, 0, wx.RIGHT|wx.BOTTOM, 2)
        commonSizer_2.Add(self.compressCombo, 0, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_2, (1, 1), (1, 1), wx.ALL|wx.EXPAND, 5)

        commonGridSizer.Add((0, 0), (1, 3), (1, 1), wx.EXPAND)
        
        commonSizer_5.Add(self.distChoice, 0, wx.BOTTOM, 2)
        commonSizer_5.Add(self.distTextCtrl, 1, wx.EXPAND, 0)
        commonGridSizer.Add(commonSizer_5, (1, 5), (1, 1), wx.ALL|wx.EXPAND, 5)

        commonGridSizer.AddGrowableCol(3)
        commonGridSizer.AddGrowableCol(4)
        commonGridSizer.AddGrowableCol(5)
        commonGridSizer.AddGrowableCol(6)
        commonGridSizer.SetEmptyCellSize((0, 0))
        
        commonSizer.Add(commonGridSizer, 1, wx.EXPAND, 0)
        mainSizer.Add(commonSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        flag = wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND
        # Add the list controls
        includesSizer.Add(self.includeList, 1, flag, 5)
        includesSizer.Add(self.includeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        excludesSizer.Add(self.excludeList, 1, flag, 5)
        excludesSizer.Add(self.excludeList.MakeButtons(), 0, wx.EXPAND|wx.LEFT, 3)
        
        plusSizer.Add(includesSizer, 1, wx.EXPAND)
        plusSizer.Add(excludesSizer, 1, wx.EXPAND|wx.LEFT, 5)
        mainSizer.Add(plusSizer, 0, wx.ALL|wx.EXPAND, 5)
        
        otherOptionsSizer.Add(self.includeInterpreter, 0, wx.ALL|wx.EXPAND, 5)
        otherOptionsSizer.Add(self.addManifest, 0, wx.ALL|wx.EXPAND, 5)
        minusSizer.Add(otherOptionsSizer, 1, wx.EXPAND)
        mainSizer.Add(minusSizer, 0, wx.ALL|wx.EXPAND, 5)

        self.SetAutoLayout(True)
        self.SetSizer(mainSizer)

        self.SetupScrolling()
        self.label.SetFocus()

    
    def ValidateOptions(self):
        """ Validates the bbFreeze input options before compiling. """

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
        return self.BuildTargetClass(configuration, project, customCode, postCompile)


    def BuildTargetClass(self, configuration, project, customCode, postCompile):
        """ Builds the bbFreeze compilation script file, returning it as a string. """

        # A couple of dictionaries to populate the setup string        
        setupDict, importDict = {}, {}
        configuration = dict(configuration)
        # Delete the keys we don't need
        distChoice = self.distChoice.GetValue()
        del configuration["dist_dir_choice"]

        # Loop over all the keys, values of the configuration dictionary        
        for key, item in configuration.items():
            if isinstance(self.FindWindowByName(key), wx.CheckBox):
                item = bool(int(item))

            if key in ["create_manifest_file", "multipleexe"]:
                # Skip these 2 options, we'll take care of them later...
                continue

            if isinstance(item, basestring) and key != "compress":
                if key == "dist_dir" and (item == "" or not distChoice):
                    item = "'dist'"
                    if distChoice:
                        self.MainFrame.SendMessage(1, _('Empty dist_dir option. Using default value "dist"'))
                else:
                    item = "r'%s'"%item

            if type(item) == ListType:
                # Terrible hack to setup correctly the string to be included
                # in the setup file
                item = setupString(key, item)

            setupDict[key] = item

        targetclass = ""
        for indx in xrange(self.multipleExe.GetItemCount()):
            # Add the target classes
            gui_only = self.multipleExe.GetItem(indx, 1).GetText()
            scriptFile = self.multipleExe.GetItem(indx, 2).GetText()            
            gui = (gui_only == "windows" and [True] or [False])[0]

            targetclass += _bbFreeze_class%{"gui_only": gui, "script": 'r"%s"'%scriptFile}
            buildDir, scriptFile = os.path.split(scriptFile)
            
        # Add the custom code (if any)
        setupDict["customcode"] = (customCode and [customCode.strip()] or ["# No custom code added"])[0]

        # Add the post-compilation code (if any)
        setupDict["postcompilecode"] = (postCompile and [postCompile.strip()] or ["# No post-compilation code added"])[0]

        setupDict["executables"] = targetclass
        # Include the GUI2Exe version in the setup script
        importDict["gui2exever"] = self.MainFrame.GetVersion()

        # Populate the "import" section
        setupScript = _bbFreeze_imports % importDict

        # Populate the main section of the setup script            
        setupScript += _bbFreeze_target % setupDict
        
        # Send a message to out fancy bottom log window
        transdict = dict(projectName=project.GetName())
        self.MainFrame.SendMessage(0, _('Setup script for "%(projectName)s" succesfully created')%transdict)
        return setupScript, buildDir

