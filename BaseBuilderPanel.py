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
import wx.lib.scrolledpanel as scrolled

from Constants import GetTooltips

# Import our fancy tooltips
if wx.Platform != "__WXMAC__":
    from Widgets import TransientPopup
else:
    from Widgets import MacTransientPopup as TransientPopup

# Get the I18N things
_ = wx.GetTranslation


class BaseBuilderPanel(scrolled.ScrolledPanel):
    """ Base ScrolledPanel class for all the compilers. """

    def __init__(self, parent, projectName, creationDate, name):
        """
        Default class constructor.
        
        
        **Parameters:**

        * parent: the widget parent;
        * projectName: the name of the project we are working on;
        * creationDate: the date and time the project was created;
        * name: the widget (compiler) name.

        """
        
        scrolled.ScrolledPanel.__init__(self, parent, name=name)
        self.MainFrame = wx.GetTopLevelParent(self)

        # I need this flag otherwise all the widgets start sending changed
        # events when I first populate the full panel
        
        self.created = False
        self.tipWindow = None
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #


    def BindEvents(self):
        """ Binds the event for almost all the widgets in PyInstallerPanel (except list controls). """

        isMac = wx.Platform == "__WXMAC__"

        for child in self.GetChildren():
            if isinstance(child, wx.TextCtrl):
                # That's a text control
                self.Bind(wx.EVT_TEXT, self.OnUserChange, child)
            elif isinstance(child, wx.combo.OwnerDrawnComboBox):
                # that's a combobox
                self.Bind(wx.EVT_COMBOBOX, self.OnUserChange, child)
            elif isinstance(child, wx.CheckBox):
                # That's a checkbox
                self.Bind(wx.EVT_CHECKBOX, self.OnUserChange, child)
            elif isinstance(child, wx.FilePickerCtrl):
                # and a file picker
                self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnUserChange, child)
            elif isinstance(child, wx.RadioButton):
                self.Bind(wx.EVT_RADIOBUTTON, self.OnUserChange, child)
                
            if isMac:
                # On the Mac we use smaller widgets
                child.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        

    def BindToolTips(self):
        """
        Binds the wx.EVT_ENTER_WINDOW and wx.EVT_LEAVE_WINDOW events for all
        the widgets in our panel.
        """

        for child in self.GetChildren():
            # For the Mac PList buttons
            childName = child.GetName()
            if isinstance(child, wx.TextCtrl) or isinstance(child, wx.combo.OwnerDrawnComboBox) \
               or isinstance(child, wx.CheckBox) or isinstance(child, wx.FilePickerCtrl) \
               or isinstance(child, wx.RadioButton) or isinstance(child, wx.ListCtrl) \
               or childName in ["plistCode", "plistRemove"]:
                child.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
                child.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
                
        
    # ============== #
    # Event handlers #
    # ============== #
    
    def OnChildFocus(self, event):
        """ Overridden method, to stop scrolledpanel from moving scrollbars. """

        pass


    def OnEnterWindow(self, event):
        """ Handles the wx.EVT_ENTER_WINDOW event for BaseBuilderPanel. """

        if not self.MainFrame.showTips:
            # User doesn't want tolltips...
            return
        
        if self.tipWindow:
            # A tooltip window already exists
            return

        # Get the hovered widget
        obj = event.GetEventObject()
        # Retrieve the main panel name and compiler name
        compiler = self.GetName()
        option = obj.GetName()

        _toolTips = GetTooltips()
        
        if compiler not in _toolTips:
            # This should not happen, but you never know...
            return

        if option not in _toolTips[compiler]:
            # Missing tooltip?
            return     

        # Retrieve the tooltip associated with the widget
        options = _toolTips[compiler]
        tip = options[option]

        tip = tip.split("<note>")
        if len(tip) > 1:
            # There is a note at the bottom of the tooltip
            tip, note = tip
        else:
            tip, note = tip[0], None

        # Launch the fancy tooltip viewer
        self.tipWindow = TransientPopup(self, compiler, option, tip, note)
        

    def OnLeaveWindow(self, event):
        """ Handles the wx.EVT_LEAVE_WINDOW event for BaseBuilderPanel. """

        if not self.tipWindow:
            # No tooltip window exists
            return

        window = event.GetEventObject()
        if window.GetScreenRect().Contains(wx.GetMousePosition()):
            # This stupid wx.EVT_LEAVE_WINDOW event gets fired for no reason...
            return
        
        # Destroy the existing tooltip window
        self.tipWindow.Destroy()
        self.tipWindow = None
        

    def OnMotion(self, event):
        """ Handles the wx.EVT_LEAVE_WINDOW event for BaseBuilderPanel. """

        if not self.tipWindow:
            # No tooltip window exists
            return

        # Destroy the existing tooltip window
        self.tipWindow.Destroy()
        self.tipWindow = None
                

    def OnUserChange(self, event):
        """ Handles all the events generated by the widgets (except list controls). """

        if not self.created:
            # No data yet, wait to be populated before whining
            return

        # Get the object that generated the event
        window = event.GetEventObject()
        # And retrieve its name
        windowName = window.GetName()

        # Get the value from the widget
        value = self.GetWindowValues(windowName, window)
        if isinstance(window, wx.CheckBox):
            # If it came from the xp manifest checkbox, update the
            # associated list control
            self.UpdateResourceList(windowName, value)

        # If it came from the zipfile or the dist checkbox, enable or
        # disable their associated text controls
        self.EnableAssociatedText(windowName, value)
        # Give visual feedback to the user that the model has changed
        if windowName in ["onedir", "onefile"]:
            # Hack for PyInstaller options
            otherName = (windowName == "onedir" and ["onefile"] or ["onedir"])[0]
            self.GiveScreenFeedback(otherName, not value)

        self.GiveScreenFeedback(windowName, value)
        
        event.Skip()


    def OnLeftDown(self, event):
        """ Handles the wx.EVT_LEFT_DOWN event for the scrolledpanel. """

        self.SetFocusIgnoringChildren()

            
    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def GetWindowValues(self, windowName, window=None):
        """
        Retrieve the current value(s) displayed in a widget.

        
        **Parameters:**

        * windowName: the widget name;
        * window: the widget itsefl (if any).
        """

        if window is None:
            # No window, find it by name
            window = self.FindWindowByName(windowName)
            
        if isinstance(window, wx.FilePickerCtrl):
            # It's a file path
            value = window.GetPath()
        elif isinstance(window, wx.ListCtrl):
            # It's a bit more complicated... translate it to something that
            # the project can actually understand
            value = window.TranslateToProject(window)
        else:
            if not isinstance(window, wx.lib.buttons.ThemedGenBitmapTextButton):
                # It's a text control or a checkbox
                value = window.GetValue()

        return value

    
    def GiveScreenFeedback(self, windowName, value, changeIcon=True):
        """
        Gives visual feedback to the user that the model has changed.

        
        **Parameters:**

        * windowName: the widget name;
        * value: the new widget value;
        * changeIcon: whether to change the tab icon in the AuiNotebook.
        """

        # Retrieve the project stored in the parent (LabelBook) properties
        project = self.GetParent().GetProject()
        # Update the project, without saving it to the database
        project.Update(self.GetName(), windowName, value)

        if changeIcon:
            # Update the icon and the project name on the wx.aui.AuiNotebook tab
            self.MainFrame.UpdatePageBitmap(project.GetName() + "*", 1)


    def UpdateResourceList(self, windowName, value):
        """
        Updates the "other_resources" list when the user checks/unchecks the
        xp manifest checkbox.

        
        **Parameters:**

        * windowName: the widget name;
        * value: the new widget value;
        """

        if windowName != "manifest_file":
            # No, it wasn't him...
            return

        if value == 1:
            # Check if the "other_resources" list has a manifest item
            if self.otherResourceList.HasManifest():
                # Yes, it has, go back
                return
            # Add the manifest item to the "other_resources" list
            self.otherResourceList.AddManifest()
        else:
            # Unchecked, remove the manifest item
            self.otherResourceList.DeleteManifest()

        # Translate the change made to something understandable by the project
        values = self.otherResourceList.TranslateToProject()
        # Give visual feedback to the user that the model has changed
        self.GiveScreenFeedback(self.otherResourceList.GetName(), values)


    def UpdateLabel(self, projectName, creationDate):
        """
        Updates the project name and creation date when the user rename a project.

        
        **Parameters:**

        * projectName: the name of the current project;
        * creationDate: the creation data of the project (as it is in the database).
        """

        transdict = dict(compiler=self.GetName(), projectName=projectName,
                         creationDate=creationDate)
        self.label.SetLabel(_("%(compiler)s options for: %(projectName)s (Created: %(creationDate)s)")%transdict)
        self.label.Refresh()


    def SetConfiguration(self, configuration, delete=False):
        """
        Populates all the widgets with the values coming from the project.

        
        **Parameters:**

        * configuration: the project configuration coming from the database;
        * delete: whether to delete the current configuration or not.
        """

        onedir = ("onedir" in configuration and [configuration["onedir"]] or [None])[0]
        onefile = ("onefile" in configuration and [configuration["onefile"]] or [None])[0]

        # Remove the old keys from cx_Freeze and bbFreeze
        configuration = self.RemoveOldKeys(configuration)

        # Loop over all the keys, values in the dictionary
        for key, value in configuration.items():
            if isinstance(value, list):
                if value:
                    if key == "options":
                        # It's one of the obscure check boxes options
                        continue
                    else:
                        # It's surely a list control, call its method
                        lst = self.FindWindowByName(key)
                        if delete:
                            lst.DeleteAllItems()

                        lst.PopulateList(value)
            else:
                # Hack for PyInstaller
                if key == "onedir":
                    if onefile:
                        continue
                elif key in ["plistCode", "plist_code", "plistRemove"]:
                    # Mac py2app things, used later
                    continue
                
                # It's something we can easily handle here
                self.SetProjectOptions(key, value)

        # Just re-affirm that we are created and ready to receive events
        self.created = True
        if self.GetName() == "py2exe":
            # Hack for services, com_servers and ctypes_com_servers
            self.EnableDllAndExe()
        

    def SetProjectOptions(self, key, value):
        """
        Populates all the widgets (except list controls).

        
        **Parameters:**

        * key: the configuration option name (which is also a window name);
        * value: the configuration option value.
        """

        # Find the window given its name (that is a key in the project dictionary)        
        window = self.FindWindowByName(key)

        if isinstance(window, wx.TextCtrl) or isinstance(window, wx.combo.OwnerDrawnComboBox):
            # That's easy
            window.SetValue(str(value))
        elif isinstance(window, wx.RadioButton):
            # Radiobuttons are not very user friendly...
            window.SetValue(bool(value))
        elif isinstance(window, wx.CheckBox):
            # comboboxes needs integer values
            window.SetValue(int(value))
            # If it came from the zipfile or the dist checkbox, enable or
            # disable their associated text controls
            self.EnableAssociatedText(key, value)
        else:
            # It's a file picker control
            window.SetPath(value)
                

    def EnableAssociatedText(self, windowName, value):
        """
        Enables/disables the text controls associated with the zipfile checkbox
        or the dist checkbox.
        
        
        **Parameters:**

        * windowName: the widget name;
        * value: the new widget value.
        """

        if windowName.find("_choice") < 0:
            # No, it wasn't him
            return

        # Check if a text control with this name can exist...        
        possibleTextName = windowName.replace("_choice", "")
        possibleTextCtrl = self.FindWindowByName(possibleTextName)
        if possibleTextCtrl:
            # Found it: enable or disable it accordingly
            possibleTextCtrl.Enable(int(value))
            if possibleTextName == "plistCode":
                # It may be the PList buttons
                sibling = self.FindWindowByName("plistRemove")
                sibling.Enable(int(value))


    def RemoveOldKeys(self, configuration):
        """
        Removes the old configuration keys from cx_Freeze and bbFreeze.
        
        
        **Parameters:**

        * configuration: the configuration to be checked.
        """

        # Check if we are dealing with older project for cx_Freeze or bbFreeze
        name = self.GetName()

        if name == "cx_Freeze":
            # Hack the old projects
            if "version" not in configuration:
                return configuration

            # We need to remove the old keys in cx_Freeze
            cxFreeze = []
            cxFreezeOld = ["base", "script", "target_name", "version", \
                           "description", "author", "name"]

            target, script = configuration["target_name"], configuration["script"]
            if not target.strip() and script.strip():
                # Default the executable name to the Python scripts name
                configuration["target_name"] = os.path.split(os.path.splitext(script)[0])[1]
                
            for items in cxFreezeOld:
                # The new configuration style is similar to py2exe
                cxFreeze.append(configuration[items])

            configuration["multipleexe"] = [cxFreeze]
            for items in cxFreezeOld + ["target_name_choice"]:
                # Delete the old keys
                del configuration[items]

        elif name == "bbfreeze":
            if "gui_only" in configuration:
                configuration["multipleexe"] = [[configuration["gui_only"], configuration["script"]]]
                del configuration["gui_only"], configuration["script"]

        elif name == "py2exe":
            if "version" not in configuration:
                return configuration

            py2exe = [""]*7
            py2exeOld = ["kind", "script", "version", \
                         "company", "copyright", "name"]

            script = configuration["script"]
            counter = 0
            for item in py2exeOld:
                py2exe[counter] = configuration[item]
                if item == "script":
                    counter += 1
                    if script.strip():
                        py2exe[counter] = os.path.split(os.path.splitext(script)[0])[1]
                        
                counter += 1
                
            configuration["multipleexe"] = [py2exe]
            for items in py2exeOld:
                # Delete the old keys
                del configuration[items]
                        
        return configuration
    