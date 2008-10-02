# Start the imports
import os
import sys
import wx
import glob
import webbrowser

import wx.lib.mixins.listctrl as listmix
import wx.stc as stc
import wx.combo
import wx.lib.buttons as buttons
import wx.lib.langlistctrl as langlist
import wx.lib.buttonpanel as bp

_hasMacThings = True
try:
    # For the PList editor
    from py2app.apptemplate import plist_template    
    import plistlib
    import wx.gizmos as gizmos
except ImportError:
    _hasMacThings = False
    
# This is needed by BaseListCtrl
from bisect import bisect
# This is needed by the StyledTextCtrl
import keyword

from Utilities import flatten, unique, RecurseSubDirs, GetLocaleDict, GetAvailLocales
from Utilities import FormatTrace, EnvironmentInfo
from Constants import _iconFromName, _unWantedLists, _faces
from Constants import _stcKeywords, _pywild, _pypackages, _dllbinaries
from Constants import _xcdatawild, _dylibwild, _comboImages, _bpPngs

# Let's see if we can add few nice shadows to our tooltips (Windows only)
_libimported = None

_ = wx.GetTranslation

if wx.Platform == "__WXMSW__":
    osVersion = wx.GetOsVersion()
    # Shadows behind menus are supported only in XP
    if osVersion[1] == 5 and osVersion[2] == 1:
        try:
            # Try Mark Hammond's win32all extensions
            import win32api
            import win32con
            import win32gui
            _libimported = "MH"
        except ImportError:
            _libimported = None
    else:
        _libimported = None
        
                 
class BaseListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.TextEditMixin,
                   listmix.ColumnSorterMixin):
    """ Base class for all the list controls in our application. """

    def __init__(self, parent, columnNames, name="", mainFrame=None):
        """
        Default class constructor.

        @param parent: the parent widget
        @param columnNames: the list control column names
        @param name: the list control name
        @param mainFrame: the application main frame (GUI2Exe)
        """

        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.SUNKEN_BORDER,
                             name=name)

        # Initialize the auto width mixin. We always need it        
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        if name not in _unWantedLists:
            # But we don't always want text edit mixin
            listmix.TextEditMixin.__init__(self)
            self._defaultb, self._color = None, None

        if name == "multipleexe":
            self.setResizeColumn(3)
            # That's a hack for multiple executables in py2exe
            self.dummyCombo = wx.ComboBox(self, value= "windows", style=wx.CB_DROPDOWN,
                                          choices= ["windows", "console"])
            self.dummyCombo.Hide()
            self.dummyButton = wx.Button(self, -1, "...")
            self.dummyButton.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
            self.dummyButton.Hide()
            if wx.Platform == "__WXMAC__":
                # Use smaller widgets on Mac
                self.dummyCombo.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
                self.dummyButton.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        # If we are on a secondary frame, we pass the main frame reference
        if not mainFrame:
            # That's  secondary frame
            self.MainFrame = wx.GetTopLevelParent(self)
        else:
            # We are a descendant of GUI2Exe main frame
            self.MainFrame = mainFrame

        # The column sorter mixin will be initialized later
        self.columnSorter = False
        self.itemDataMap = {}
        self.isBeingEdited = False

        # Do the hard work        
        self.BuildImageList()
        self.InsertColumns(columnNames)
        self.BindEvents()

        # Usually the "resources" lists for py2exe do not contain many items
        # so we allow them to be smaller than other lists
        if name.find("resources") < 0:
            self.SetMinSize((-1, 150))        


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def InsertColumns(self, columnNames):
        """
        Inserts the columns in the list control.

        @param columnNames: the list control column names.        
        """

        # The first column is always empty text, as I use it to display
        # an informative/fancy icon
        self.InsertColumn(0, "")

        # Loop over all the column names        
        for indx, column in enumerate(columnNames):
            self.InsertColumn(indx+1, column)
            self.SetColumnWidth(indx+1, wx.LIST_AUTOSIZE_USEHEADER)

        # The first column only displays an icon, 24 is perfect on Windows
        self.SetColumnWidth(0, 24)


    def BuildImageList(self):
        """ Build the image list for the list control. """

        # Ok, here it gets tricky as I am trying to re-use the same base class
        # for 6 or more different list control
        name = self.GetName()
        imgList = wx.ImageList(16, 16)
        # Get the icons from the list control name
        pngs = _iconFromName[name]

        # Loop over all the images in the list
        for png in pngs:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        if name not in ["messages", "multipleexe"]:
            # The other list can be sorted, but not the one at the bottom
            # that is our log message window
            self.sm_up = imgList.Add(self.MainFrame.CreateBitmap("sort_up"))
            self.sm_dn = imgList.Add(self.MainFrame.CreateBitmap("sort_down"))

        # Assign the image list, I don't want to store it            
        self.AssignImageList(imgList, wx.IMAGE_LIST_SMALL)            
        

    def BindEvents(self):
        """ Binds the event handler for the list. """

        self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColumnDrag)
        
        if self.GetName() not in _unWantedLists:
            # For most of the list we really do hard work
            self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit)
            self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndEdit)
            self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
            self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnRightClick)
            self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
            # for wxMSW
            self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightUp)
            # for wxGTK
            self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            # Fix a bug
            self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, lambda event: None)
            # Handle the scrolling of lists
            self.popupId1, self.popupId2, self.popupId3 = wx.NewId(), wx.NewId(), wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnDeleteSelected, id=self.popupId1)
            self.Bind(wx.EVT_MENU, self.OnClearAll, id=self.popupId2)
            self.Bind(wx.EVT_MENU, self.OnAdd, id=self.popupId3)

        if self.GetName() == "multipleexe":
            self.dummyCombo.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
            self.dummyButton.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
            self.dummyButton.Bind(wx.EVT_BUTTON, self.OnChooseScript)
            self.Bind(wx.EVT_LEFT_DOWN, self.OnItemActivated)


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnColumnDrag(self, event):
        """ Handles the wx.EVT_LIST_COL_BEGIN_DRAG event for the list control. """

        if event.GetColumn() == 0:
            # Veto the event for the first column, it holds the icon
            event.Veto()
            return

        event.Skip()


    def OnBeginEdit(self, event):
        """ Handles the wx.EVT_LIST_BEGIN_LABEL_EDIT event for the list control. """

        if event.GetColumn() == 0:
            # Veto the event for the first column, it holds the icon
            event.Veto()
            return

        if self.GetName() == "other_resources":
            if event.GetItem().GetId() == 0 and self.HasManifest():
                # You can't edit the manifest item (if present)
                event.Veto()
                return

        elif self.GetName() == "multipleexe" and event.GetColumn() in [1, 2]:
            event.Veto()
            return

        self.Select(event.m_itemIndex)
        self.isBeingEdited = True
        event.Skip()


    def OnEndEdit(self, event):
        """ Handles the wx.EVT_LIST_END_LABEL_EDIT event for the list control. """

        if event.IsEditCancelled():
            # Nothing to do, the user cancelled the editing
            self.isBeingEdited = False
            event.Skip()
            return

        col = event.GetColumn()
        indx = event.GetItem().GetId()
        # Check if the user has really modified the item text
        oldLabel = self.GetItem(indx, col).GetText().encode().strip()
        newLabel = event.GetLabel().strip()
        if newLabel == oldLabel:
            # they seems the same, go back...
            event.Skip()
            return
        
        event.Skip()

        # Adjust the data for the column sorter mixin
        tuple = ()
        # Loop over all the columns, populating a tuple
        for col in xrange(self.GetColumnCount()):
            item = self.GetItem(indx, col)
            tuple += (item.GetText().encode(),)

        # Store the data
        self.SetItemData(indx, indx)
        self.itemDataMap[indx] = tuple
        # Initialize the column sorter mixin (if needed)
        self.InizializeSorter()

        # Update the project, as something changed
        wx.CallAfter(self.UpdateProject)
        self.isBeingEdited = False
        

    def OnKeyDown(self, event):
        """ Handles the wx.EVT_KEY_DOWN event for the list control. """

        if event.GetModifiers() == wx.MOD_CONTROL and event.GetKeyCode() == ord("A"):
            # User pressed Ctrl+A, so he/she can add items to the list
            # The behavior is different depending on the list name and compiler type
            self.OnAdd(event)

        elif event.GetKeyCode() == wx.WXK_DELETE:
            # We are deleting something from the list control
            selections = self.GetSelectedIndices()
            # Reverse them, to delete them safely
            selections.reverse()
            # Loop over all the indices
            self.Freeze()
            for ind in selections:
                # Pop the data from the column sorter mixin dictionary
                indx = self.GetItemData(ind)
                self.itemDataMap.pop(indx)
                # Delete the item from the list
                self.DeleteItem(ind)
            self.Thaw()
            wx.CallAfter(self.UpdateProject)
            wx.CallAfter(self.Recolor)
        # Otherwise skip the event
        event.Skip()


    def OnRightClick(self, event):
        """ Handles the wx.EVT_LIST_ITEM_RIGHT_CLICK event for the list control. """

        x = event.GetX()
        y = event.GetY()

        item, flags = self.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            if not self.GetSelectedIndices():
                self.Select(item)
        
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.popupId3, _("Add Item(s)"))
        bmp = self.MainFrame.CreateBitmap("add")
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        menu.AppendSeparator()        
        # Well, we can either delete the selected item(s)...
        item = wx.MenuItem(menu, self.popupId1, _("Delete selected"))
        bmp = self.MainFrame.CreateBitmap("delete_selected")
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        # Or clear completely the list
        item = wx.MenuItem(menu, self.popupId2, _("Clear all"))
        bmp = self.MainFrame.CreateBitmap("clear_all")
        item.SetBitmap(bmp)
        menu.AppendItem(item)

        # Popup the menu on ourselves
        self.PopupMenu(menu)
        menu.Destroy()


    def OnRightUp(self, event):
        """ Handles the wx.EVT_RIGHT_UP event for the list control. """

        menu = wx.Menu()
        item = wx.MenuItem(menu, self.popupId3, _("Add Item(s)"))
        bmp = self.MainFrame.CreateBitmap("add")
        item.SetBitmap(bmp)
        menu.AppendItem(item)

        # Popup the menu on ourselves
        self.PopupMenu(menu)
        menu.Destroy()


    def OnDeleteSelected(self, event):
        """ Handles the wx.EVT_MENU event for the list control. """

        # Freeze everything... it helps with flicker
        self.Freeze()
        wx.BeginBusyCursor()
        
        if self.isBeingEdited:
            # We may be in editing mode...
            self.isBeingEdited = False
            self.editor.Hide()
            self.SetFocus()
            
        # Get all the selected items
        indices = self.GetSelectedIndices()
        # Reverse them, to delete them safely
        indices.reverse()

        # Multiple exe list does not use ColumnSorterMixin
        isMultipleExe = self.GetName() == "multipleexe"
        # Loop over all the indices
        for ind in indices:
            # Pop the data from the column sorter mixin dictionary
            indx = self.GetItemData(ind)
            if not isMultipleExe:
                self.itemDataMap.pop(indx)
            # Delete the item from the list
            self.DeleteItem(ind)

        # Time to warm up...
        self.Thaw()
        wx.EndBusyCursor()

        if indices:
            # Update the project, something changed
            wx.CallAfter(self.UpdateProject)
            wx.CallAfter(self.Recolor)


    def OnClearAll(self, event):
        """ Handles the wx.EVT_MENU event for the list control. """

        wx.BeginBusyCursor()
        # Freeze everything... it helps with flicker
        self.Freeze()
        # Clear all the list
        self.DeleteAllItems()
        # Time to warm up...
        self.Thaw()

        # Update the project, something changed
        self.itemDataMap = {}
        self.UpdateProject()
        wx.EndBusyCursor()
        

    def OnAdd(self, event):
        """ Handles the wx.EVT_MENU event when adding items to the list. """

        # Get our name and the compiler name
        name = self.GetName()
        compiler = self.GetParent().GetName()

        # This is a bit of a mess, but it works :-D        
        if compiler == "PyInstaller":
            self.HandleOtherInputs()
        elif compiler == "cx_Freeze" and name == "path":
            self.HandleOtherInputs()
        elif compiler == "py2app" and name in ["datamodels", "dylib_excludes", "frameworks"]:
            self.HandleMacImports(name)
        else:            
            if name.find("resources") >= 0:
                if compiler == "py2exe":
                    # New resource files, use a file dialog to pick them
                    self.HandleNewResource(name)
                else:
                    # py2app calls resources the data_files option...
                    self.HandleDataFiles()
            elif name == "data_files":
                # New data files, use a file dialog to pick them
                self.HandleDataFiles()
            elif name == "multipleexe":
                # Another executable to build
                self.HandleMutlipleExe()
            else:
                # New modules, simply enter one item and start editing
                self.HandleNewModule()

        self.Recolor()

        
    def OnItemActivated(self, event):
        """ Handles the wx.EVT_LEFT_DOWN event for the list control. """

        if self.GetName() != "multipleexe":
            # Wrong list control
            event.Skip()
            return

        # Where did the user click?
        x, y = event.GetPosition()
        row, flags = self.HitTest((x, y))

        if row < 0:
            # It seems that the click was not on an item
            event.Skip()
            return

        # Calculate the columns location (in pixels)            
        col_locs = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            col_locs.append(loc)

        # Get the selected column and row for this item
        column = bisect(col_locs, x+self.GetScrollPos(wx.HORIZONTAL)) - 1
        self.selectedItem = row
        rect = self.GetItemRect(self.selectedItem)

        if column == 1:
            # Choosing between Windows and Console program            
            rect.x += self.GetColumnWidth(0)
                
            if not self.GetRect().ContainsRect(rect):
                # simplified scrollbar compensate
                rect.SetWidth(max(self.GetColumnWidth(1), self.dummyCombo.GetBestSize().x))

            # Show the combobox
            wx.CallAfter(self.ShowDummyControl, self.dummyCombo, rect)
            
        elif column == 2:
            # Choosing the Python script
            for indx in xrange(3):
                rect.x += self.GetColumnWidth(indx)
            rect.x -= 26

            if not self.GetRect().ContainsRect(rect):
                rect.SetWidth(25)

            # Show the import button            
            wx.CallAfter(self.ShowDummyControl, self.dummyButton, rect)
            
        else:
            # Some other column, we are not interested
            event.Skip()

            
    def ShowDummyControl(self, control, rect):
        """
        Shows a hidden widgets in the list control (py2exe only, top list control).

        @param control: which control to show (a button or a combobox);
        @param rect: the wx.Rect rectangle where to place the widget to be shown.
        """
        
        control.SetRect(rect)
        control.SetFocus()
        control.Show()
        control.Raise()


    def OnKillFocus(self, event):
        """ Handles the wx.EVT_KILL_FOCUS event for the list control. """

        obj = event.GetEventObject()
        if obj == self.dummyButton:
            # Hide the py2exe import button in the top list control
            self.dummyButton.Hide()
            return
        
        shown = self.dummyCombo.IsShown()
        self.dummyCombo.Hide()
        if shown:
            # Hide the py2exe combobox in the top list control
            value = self.dummyCombo.GetValue()
            self.SetStringItem(self.selectedItem, 1, value)
            self.UpdateProject()


    def OnChooseScript(self, event):
        """
        Handles the wx.EVT_BUTTON for the hidden button in the top list control
        (py2exe only).
        """

        # Launch the file dialog        
        dlg = wx.FileDialog(self.MainFrame, message=_("Add Python Script..."),
                            wildcard=_pywild,
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you.
            self.SetStringItem(self.selectedItem, 2, path)
            exeName = os.path.split(os.path.splitext(path)[0])[1]
            self.SetStringItem(self.selectedItem, 3, exeName)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()
        self.Recolor()
        self.UpdateProject()

            
    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def PopulateList(self, configuration):
        """
        Populates the list control based on the input configuration.

        @param configuration: the project configuration.
        """

        if not configuration or not configuration[0]:
            # Nothing in here, go back
            return

        colCount = self.GetColumnCount()
        # This gets very tricky        
        for value in configuration:
            # The first item is always an empty string with the informative icon
            indx = self.InsertImageStringItem(sys.maxint, "", 0)
            # Initialize the tuple for the column sorter mixin
            tupleMap = ("",)
            if isinstance(value, basestring):
                # So, this must be one of "includes", "excludes", "modules",
                # "packages", "ignores", they are a list of strings
                self.SetStringItem(indx, 1, value.strip())
                tupleMap += (value.strip(),)
                self.itemDataMap[indx] = tupleMap
                self.SetItemData(indx, indx)
            else:
                # This is a list of lists
                if self.GetName() == "data_files":
                    # We have data files, a bit trickier
                    # Everything here is done to comply with the format in which
                    # the data is stored in the database
                    for index, tup in enumerate(value[1]):
                        if index > 0:
                            indx = self.InsertImageStringItem(sys.maxint, "", 0)
                            tupleMap = ("",)
                        self.SetStringItem(indx, 1, value[0])
                        self.SetStringItem(indx, 2, tup)
                        tupleMap += (value[0], tup)
                        self.itemDataMap[indx] = tupleMap
                        self.SetItemData(indx, indx)
                        
                else:
                    # Otherwise is a "resources" list
                    for col in xrange(colCount-1):
                        item = (col < len(value) and [value[col]] or [""])[0]
                        item = ("%s"%item).strip()
                        self.SetStringItem(indx, col+1, item)
                        tupleMap += (item,)

                    self.itemDataMap[indx] = tupleMap
                    self.SetItemData(indx, indx)

        # Initialize the column sorter mixin (if needed)
        self.InizializeSorter()
        self.Recolor()


    def InizializeSorter(self):
        """
        Initializes the column sorter mixin.
        Not used by the "message" list.
        """

        # We don't want to sort our log window at the bottom        
        if not self.columnSorter and self.GetName() not in ["messages", "multipleexe"]:
            # Not initialized yet
            colCount = self.GetColumnCount()
            listmix.ColumnSorterMixin.__init__(self, colCount)
            sortedColumn = (wx.GetTopLevelParent(self)==self.MainFrame and [colCount-1] or [1])[0]
            self.SortListItems(sortedColumn, True)
            self.columnSorter = True
            

    def GetListCtrl(self):
        """
        Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py.
        Not used by the "message" list.
        """
        
        return self


    def GetSortImages(self):
        """
        Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py.
        Not used by the "message" list.
        """

        # Returns the images used to display the sorting order
        return (self.sm_dn, self.sm_up)
    

    def HasManifest(self):
        """
        Returns whether the manifest file has been added to "other resources" or not.
        Used only for the "other_resources" list control. 
        """

        if self.GetItemCount() == 0:
            # No manifest file added, list is empty
            return False

        # If it exists, its text is in the 3rd column
        item = self.GetItem(0, 3)
        if item.GetText().find("manifest_template") >= 0:
            # Got it, is there
            return True

        # Shouldn't never reach this point, but who knows...
        return False
    

    def AddManifest(self):
        """
        Adds the manifest file to the list control.
        Used only for the "other_resources" list control. 
        """

        # The first item is always empty text with an informative icon
        indx = self.InsertImageStringItem(0, "", 0)
        # This is the format we need for the Setup.py file
        items = ["24", "1", "manifest_template%s"]
        for col, item in enumerate(items):
            self.SetStringItem(indx, col+1, item)

        # Update the data for the column sorter mixins
        self.SetItemData(indx, indx)
        self.itemDataMap[indx] = tuple(items)
        self.Recolor()
        

    def DeleteManifest(self):
        """
        Deletes the manifest file from the list control.
        Used only for the "other_resources" list control. 
        """

        if not self.HasManifest():
            # How did we get here?!?
            return

        # Just as simple as it gets
        self.itemDataMap.pop(0)
        self.DeleteItem(0)
        self.Recolor()


    def HandleNewResource(self, name):
        """
        Handles the user request to add new resources.

        @param name: the resource name (bitmap, icon).
        """

        if name.find("bitmap") >= 0:   # bitmap resources
            wildcard = "Bitmap files (*.bmp)|*.bmp"
        elif name.find("icon") >= 0:   # icon resources
            wildcard = "Icon files (*.ico)|*.ico"
        else:                          # whatever other resource
            wildcard = "All files (*.*)|*.*"

        # Run a file dialog with multiple selection            
        dlg = wx.FileDialog(self.MainFrame, message=_("New resources"),
                            wildcard=wildcard,
                            style=wx.FD_OPEN|wx.FD_MULTIPLE)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        
        paths = dlg.GetPaths()
        dlg.Destroy()

        wx.BeginBusyCursor()

        # Get how many items we have in the current list control        
        numItems = self.GetItemCount()
        # Default value for the other_resources list control
        resourceType = 24
        # Get the number of columns in the current list control
        cols = self.GetColumnCount()

        config = []
        # loop over all the selected files
        for path in paths:
            values = []
            numItems += 1
            values.append(numItems)
            if cols == 4:
                # This is the other_resources list control
                values.append(resourceType)
            values.append(path)
            config.append(values)

        # Populate the list control
        self.PopulateList(config)
        # Update the project, something changed
        self.UpdateProject()

        wx.EndBusyCursor()
        

    def HandleNewModule(self):
        """ Handles the user request to add a new module. """

        # The first item is always empty text with an informative icon
        indx = self.InsertImageStringItem(sys.maxint, "", 0)
        # Insert an item with some visual indicator that should be edited...
        self.SetStringItem(indx, 1, "==> Edit Me! <==")
        # Update the column sorter mixin
        self.SetItemData(indx, indx)
        self.itemDataMap[indx] = ("", "==> Edit Me! <==")
        # Start editing the new label
        self.EnsureVisible(indx)
        

    def HandleDataFiles(self):
        """ Handles the user request to add new data files. """

        compiler = self.GetParent().GetName()
        
        if self.MainFrame.recurseSubDirs:

            # Here we recurse and add all the files in a particular folder
            # and its subfolder

            # Use our fancy directory selector (which allows multiple
            # folder selection at the same time
            dlg = GUI2ExeDirSelector(self.MainFrame,
                                     title=_("Please select one directory..."),
                                     showExtensions=True)

            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
        
            folder, extensions = dlg.GetSelectedFolders()
            if not folder:
                # No folders selected
                return

            if not extensions or (len(extensions) == 1 and extensions[0].strip() == ""):
                # Empty extensions, use default one (all files)
                extensions = ["*.*"]

            extensions = [ext.strip() for ext in extensions]                
            defaultDir = os.path.basename(folder)
            
        else:            
            # Run a file dialog with multiple selection        
            wildcard = "All files (*.*)|*.*"
            dlg = wx.FileDialog(self.MainFrame, message=_("New data files"), wildcard=wildcard,
                                style=wx.FD_OPEN|wx.FD_MULTIPLE)

            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            
            paths = dlg.GetPaths()
            # Try to suggest a possible folder name to the user
            defaultDir = os.path.basename(dlg.GetDirectory())
            
        dlg.Destroy()

        if compiler == "py2exe":
            # Ask the user which name the directory in the py2exe distribution
            # should have, suggesting the above defaultDir
            dlg = wx.TextEntryDialog(self.MainFrame,
                                     _("Please enter the name of the folder for py2exe:"),
                                     _("Directory Name"))
            dlg.SetValue(defaultDir)
            
            if dlg.ShowModal() != wx.ID_OK:
                # No choice made, no items added
                return

            # Get the user choice
            defaultDir = dlg.GetValue().strip()
            dlg.Destroy()

            if not defaultDir.strip():
                # Empty folder name?
                self.MainFrame.RunError(2, _("Invalid folder name."))
                return

        wx.BeginBusyCursor()
        if self.MainFrame.recurseSubDirs:
            # We are to include all the files in the selected folder
            if compiler == "py2exe":
                config = RecurseSubDirs(folder, defaultDir, extensions)
            else:
                config = []
                # Loop over all the selected extensions
                for ext in extensions:
                    config += glob.glob(folder + "/" + ext)
        else:
            # The user selected a bunch of files all together
            if compiler == "py2exe":
                config = [(defaultDir, paths)]
            else:
                config = paths

        # Populate the list control
        self.PopulateList(config)
        # Update the project, something changed
        self.UpdateProject()
        wx.EndBusyCursor()
        

    def HandleMutlipleExe(self):
        """ Handles the user request to add new executable to build. """

        # The first item is always empty text with an informative icon
        indx = self.InsertImageStringItem(sys.maxint, "", 0)
        # Insert the "Windows" option, which is the default...
        multipleOptions = ["windows", "", "", "0.1", _("No Company"),
                           _("No Copyrights"),
                           _("Py2Exe Sample File")]
        for i in xrange(1, self.GetColumnCount()):            
            self.SetStringItem(indx, i, multipleOptions[i-1])

        self.EnsureVisible(indx)
        

    def HandleOtherInputs(self):
        """ Handles the various PyInstaller/cx_Freeze options. """

        # PyInstaller is very different from all the other executable builders.
        # Treating it separately it's more convenient
        
        name = self.GetName()
        if name in ["scripts", "includes", "packages", "dll_excludes",
                    "dll_includes", "data_files"]:
            self.AddFilesWithPath(name)
        else:
            self.AddDirectories()


    def HandleMacImports(self, name):
        """
        Handles the Dylib/Frameworks/XCDataModels options for Mac.

        @param name: the option name (dylib, frameworks, xcdatamodels).
        """

        if name.find("dylib") >= 0 or name.find("frameworks") >= 0:
            message = _("Add Dylib/Frameworks")
            wildcard = _dylibwild
        else:
            message = _("Add XC Data Models")
            wildcard = _xcdatawild
            
        dlg = wx.FileDialog(self.MainFrame, message=message, wildcard=wildcard,
                            style=wx.FD_OPEN|wx.FD_MULTIPLE)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
            
        paths = dlg.GetPaths()
        for path in paths:
            indx = self.InsertImageStringItem(sys.maxint, "", 0)
            self.SetStringItem(indx, 1, path)


    def AddFilesWithPath(self, name):
        """
        Processes all the list controls option for PyInstaller except the Path
        and Hooks extensions.

        @param name: the list control name.        
        """

        # A bunch of if switches to handle all the possibility offered
        # by PyInstaller
        if name == "scripts":
            message = _("Add Python Scripts")
            wildcard = _pywild
        elif name == "includes":
            message = _("Add Python Modules")
            wildcard = _pywild
        elif name == "packages":
            message = _("Add Python Packages")
            wildcard = _pypackages
        elif name[0:3] == "dll":
            message = _("Add Dll/Binary Files")
            wildcard = _dllbinaries
        else:
            if self.MainFrame.recurseSubDirs:
                self.AddDataFiles()
                return                
            message = _("Add Data Files")
            wildcard = "All files (*.*)|*.*"
        
        columns = self.GetColumnCount()

        # Launch the file dialog            
        dlg = wx.FileDialog(self.MainFrame, message=message,
                            wildcard=wildcard,
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR|wx.FD_MULTIPLE)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.AddFiles(paths, columns)
        else:
            dlg.Destroy()
            return
        
        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


    def AddFiles(self, paths, columns):
        """
        Utility function to handle properly the PyInstaller options.

        @param paths: the file name paths;
        @param columns: the number of items in every path (2 or 3).
        """

        for path in paths:
            directory, filename = os.path.split(path)
            indx = self.InsertImageStringItem(sys.maxint, "", 0)
            # Initialize the tuple for the column sorter mixin
            tupleMap = ("",)
            item = (columns == 2 and [path] or [filename])[0]
            self.SetStringItem(indx, 1, item)
            tupleMap += (item,)
            
            if columns > 2:
                # The Scripts list control has only 2 columns
                self.SetStringItem(indx, 2, path)
                tupleMap += (path,)

            self.itemDataMap[indx] = tupleMap
            self.SetItemData(indx, indx)

        self.UpdateProject()
        

    def AddDataFiles(self):
        """ Utility function to handle properly the PyInstaller data_files option. """
        
        # Here we recurse and add all the files in a particular folder
        # and its subfolder
        dlg = wx.DirDialog(self, _("Choose a data files directory:"),
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        # Retrieve the selected directory
        path = dlg.GetPath()
        fileNames = []
        # Loop ove all the files in that directory
        for root, dirs, files in os.walk(path):
            for name in files:
                fileNames.append(os.path.normpath(os.path.join(root, name)))

        self.AddFiles(fileNames, 3)            
            

    def AddDirectories(self):
        """ Handles the Path and Hooks extensions for PyInstaller. """

        # Use our fancy directory selector (which allows multiple
        # folder selection at the same time
        dlg = GUI2ExeDirSelector(self.MainFrame,
                                 title=_("Browse For Folders..."),
                                 showExtensions=False)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        
        folders = dlg.GetSelectedFolders()

        for dirs in folders:
            indx = self.InsertImageStringItem(sys.maxint, "", 0)
            # Initialize the tuple for the column sorter mixin
            self.SetStringItem(indx, 1, dirs)
            tupleMap = ("", dirs)
            self.itemDataMap[indx] = tupleMap
            self.SetItemData(indx, indx)
        
        dlg.Destroy()
        self.UpdateProject()
        

    def GetSelectedIndices(self, state=wx.LIST_STATE_SELECTED):
        """
        Returns the indices of the selected items in the list control.

        @param state: the list control item state.
        """

        indices = []
        lastFound = -1

        # Loop until told to stop        
        while 1:
            index = self.GetNextItem(lastFound, wx.LIST_NEXT_ALL, state)
            if index == -1:
                # No item selected
                break
            else:
                # Found one item, append to the list of condemned
                lastFound = index
                indices.append(index)

        return indices


    def TranslateToProject(self):
        """
        Translate all the list control item values to something understandable
        by the model stored in the database.
        """

        # Get all the information we need
        columns = self.GetColumnCount()
        windowName = self.GetName()
        values = []

        # Loop over all the items in the list control
        for row in xrange(self.GetItemCount()):
            temp = []
            # Loop over all the columns in the list control
            for col in xrange(1, columns):
                # Get the item text
                text = self.GetItem(row, col).GetText()
                if windowName.find("resources") >= 0 and col < columns-1:
                    # These are all integers, as py2exe requires
                    text = int(text)
                else:
                    text = text.encode("utf-8")
                temp.append(text)

            # depending on the list name, different output are requested            
            values.append((columns > 2 and [tuple(temp)] or [temp])[0])

        if columns == 2:
            # Transform the list of list in a flat 1D list of strings
            return flatten(values)

        if windowName == "data_files":
            # Throw away duplicated folder names
            return unique(values)
        
        return values


    def MakeButtons(self):
        """ Creates the +/- buttons for the list controls. """
        
        # Call our parent
        parent = self.GetParent()

        # NOTE: the borderless bitmap button control on OSX requires the bitmaps
        #       to be native size else they loose their transparency. These
        #       should probably be changed to 16x16 so they can work properly
        #       on all platforms.
        
        if wx.Platform == '__WXMAC__':
            bsize = (16, 16)
            plusBmp = "list_plus_mac"
            minusBmp = "list_minus_mac"
        else:
            bsize = (13, 13)
            plusBmp = "list_plus"
            minusBmp = "list_minus"

        # Create the bitmaps for the button
        plusBmp = self.MainFrame.CreateBitmap(plusBmp)
        minusBmp = self.MainFrame.CreateBitmap(minusBmp)
        
        # Create a couple of themed buttons for the +/- actions
        plusButton = wx.BitmapButton(parent, bitmap=plusBmp, size=bsize, style=wx.NO_BORDER)
        minusButton = wx.BitmapButton(parent, bitmap=minusBmp, size=bsize, style=wx.NO_BORDER)
        # Add some explanation...
        plusButton.SetToolTipString(_("Add items to the list"))
        minusButton.SetToolTipString(_("Remove items from the list"))
        # Put everything in a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0, 0), 1, wx.EXPAND)
        sizer.Add(plusButton, 0, wx.BOTTOM, 3)
        sizer.Add(minusButton, 0, wx.BOTTOM, 5)
        # Bind the events
        plusButton.Bind(wx.EVT_BUTTON, self.OnAdd)
        minusButton.Bind(wx.EVT_BUTTON, self.OnDeleteSelected)
        
        return sizer


    def UpdateProject(self, changeIcon=True):
        """
        Updates the project in the database, as something changed.

        @param changeIcon: whether to change the icon in the AuiNotebook tab.
        """

        # Translate the list control values to something understandable
        # by the model stored in the database
        values = self.TranslateToProject()
        # Give feedback to the user if something changed (different icon)
        self.GetParent().GiveScreenFeedback(self.GetName(), values, changeIcon)
        

    def Recolor(self):
        """ Re-color all the rows. """

        containingSizer = self.GetContainingSizer().GetStaticBox()
        oldLabelText = containingSizer.GetLabelText()
        if "(" in oldLabelText:
            oldLabelText = oldLabelText[0:oldLabelText.rindex("(")-1]
            
        newLabelText = oldLabelText + " (%d)"%self.GetItemCount()
        containingSizer.SetLabel(newLabelText)
        
        for row in xrange(self.GetItemCount()):
            if self._defaultb is None:
                self._defaultb = wx.WHITE

            dohlight = row % 2

            if dohlight:
                if self._color is None:
                    if wx.Platform in ['__WXGTK__', '__WXMSW__']:
                        color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT)
                    else:
                        color = wx.Colour(237, 243, 254)
                else:
                    color = self._color
            else:
                color = self._defaultb

            self.SetItemBackgroundColour(row, color)


class CustomCodeViewer(wx.Frame):
    """ A custom frame class to view the Setup.py code or to add code. """

    def __init__(self, parent, readOnly=False, text="", project=None, page=None,
                 compiler=None, postBuild=False):
        """
        Default class constructor.

        @param parent: the parent widget
        @param readOnly: indicates if the children StyledTextCtrl should be
                         read only or not
        @param text: the text to add to the StyledTextCtrl
        @param project: the project as it is stored in the database
        @param page: the page number of our main wx.aui.AuiNotebook
        @param compiler: the compiler to which the custom code refers
        @param postBuild: whether it is a post-compilation code or not

        """        

        wx.Frame.__init__(self, parent, title=_("GUI2Exe Code Viewer"), size=(700, 550))

        # Store few objects, we are going to need them later        
        self.MainFrame = parent
        self.modified = False
        self.project = project
        self.page = page
        self.compiler = compiler
        self.postBuild = postBuild
        
        self.mainPanel = wx.Panel(self)
        # Add the StyledTextCtrl with Python syntax
        self.pythonStc = PythonSTC(self.mainPanel, readOnly)

        if not readOnly:
            # We are not read only, that means the user is going to add
            # some custom Python code in the py2exe Setup.py file
            saveBmp = self.MainFrame.CreateBitmap("code_save")
            discardBmp = self.MainFrame.CreateBitmap("code_discard")
            # Create a couple of themed buttons to save or discard changes
            self.saveButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, -1, saveBmp, _("Save"))
            self.discardButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, -1, discardBmp, _("Discard"))
            self.saveButton.SetDefault()
            # If it is custom code, add the compiler name to the frame title
            self.SetTitle("%s - %s"%(self.GetTitle(), compiler))

        # Do the hard work
        self.SetProperties(readOnly, text)
        self.LayoutItems(readOnly)
        self.BindEvents(readOnly)

        # Center ourselves in the main frame (GUI2Exe)
        self.CenterOnParent()
        self.Show()


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self, readOnly, text):
        """
        Sets few properties for the frame and the StyledTextCtrl.

        @param readOnly: whether the StyledTextCtrl will be read-only or not
        @param text: the text displayed in the StyledTextCtrl
        """

        self.SetIcon(self.MainFrame.GetIcon())
        # Set the input text for the StyledTextCtrl
        self.pythonStc.SetText(text)
        self.pythonStc.EmptyUndoBuffer()
        # Colourise the Python code
        self.pythonStc.Colourise(0, -1)

        # line numbers in the margin
        self.pythonStc.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.pythonStc.SetMarginWidth(1, 25)

        if readOnly:
            # No way, you can't change the text now
            self.pythonStc.SetReadOnly(True)

        self.SetTransparent(self.MainFrame.GetPreferences("Transparency"))
        

    def LayoutItems(self, readOnly):
        """
        Layout the widgets with sizers.

        @param readOnly: whether the StyledTextCtrl will be read-only or not
        """
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        stcSizer = wx.BoxSizer(wx.HORIZONTAL)
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        if readOnly:
            topLabel = _("This is the Setup file as it comes out after the pre-processing\n" \
                         "work done by GUI2Exe.")
        else:
            topLabel = _("Enter your custom code below and it will be inserted inside the\n" \
                         "Setup script. Note that you can use as 'keywords' also the compiler\n" \
                         "options like data_files, ignores and icon_resources.")

        # The top label text is different depending on the choice of the user
        # If he/she chose to view the Setup.py file, it is read only
        topLabel = wx.StaticText(self.mainPanel, -1, topLabel)
        topLabel.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        panelSizer.Add(topLabel, 0, wx.ALL, 10)
        stcSizer.Add(self.pythonStc, 1, wx.ALL|wx.EXPAND, 5)

        if not readOnly:
            # Add the save/discard buttons
            rightSizer.Add((20, 20), 1, wx.EXPAND, 0)
            rightSizer.Add(self.saveButton, 0, wx.BOTTOM|wx.EXPAND, 5)
            rightSizer.Add(self.discardButton, 0, wx.BOTTOM|wx.EXPAND, 5)
            stcSizer.Add(rightSizer, 0, wx.ALL|wx.EXPAND, 5)

        # Layout everything
        panelSizer.Add(stcSizer, 1, wx.EXPAND, 0)
        self.mainPanel.SetSizer(panelSizer)
        panelSizer.Layout()
        # Add everything to the main sizer
        mainSizer.Add(self.mainPanel, 1, wx.EXPAND, 0)
        self.SetSizer(mainSizer)
        mainSizer.Layout()


    def BindEvents(self, readOnly):
        """
        Binds the events for our CustomCodeViewer.

        @param readOnly: whether the StyledTextCtrl will be read-only or not
        """

        if not readOnly:
            self.Bind(wx.EVT_BUTTON, self.OnSave, self.saveButton)
            self.Bind(wx.EVT_BUTTON, self.OnDiscard, self.discardButton)
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            # The user is going to add some custom code, so look for
            # possible modifications of it
            self.Bind(stc.EVT_STC_MODIFIED, self.OnModified, self.pythonStc)


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnSave(self, event):
        """ Handles the wx.EVT_BUTTON event for CustomCodeViewer. """

        # Save the custom code added by the user in the project
        if self.postBuild:
            # is a post-compilation code
            self.project.SetPostCompileCode(self.compiler, self.pythonStc.GetText())
        else:
            # is a standard custom code that goes in Setup.py
            self.project.SetCustomCode(self.compiler, self.pythonStc.GetText())
            
        # Update the page itmap for our main wx.aui.AuiNotebook
        self.MainFrame.UpdatePageBitmap(self.project.GetName()+ "*", 1, self.page)
        # Change the modified flag, we are saved now
        self.modified = False
        
        event.Skip()


    def OnDiscard(self, event):
        """ Handles the wx.EVT_BUTTON event for CustomCodeViewer. """

        # No changes made or changes discarded. Destroy ourselves
        self.Destroy()
        event.Skip()


    def OnModified(self, event):
        """ Handles the stc.EVT_STC_MODIFIED event for CustomCodeViewer. """

        self.modified = True


    def OnClose(self, event):
        """ Handles the wx.EVT_CLOSE event for CustomCodeViewer. """

        if not self.modified:
            # No modifications or modifications saved. Destroy ourselves
            self.Destroy()
            return

        # Something changed. Ask for saving
        question = _("The current code has changed.\nDo you want to save changes?")
        answer = self.MainFrame.RunError(3, question)
        
        if answer == wx.ID_CANCEL:
            # Do you want to think about it, eh?
            return
        elif answer == wx.ID_YES:
            # Save the code in the project class
            if self.postBuild:
                # is a post-compilation code
                self.project.SetPostCompileCode(self.compiler, self.pythonStc.GetText())
            else:
                # is a standard custom code that goes in Setup.py
                self.project.SetCustomCode(self.compiler, self.pythonStc.GetText())

            self.MainFrame.SaveProject(self.project)

        event.Skip()



class PythonSTC(stc.StyledTextCtrl):
    """ A simple Python editor based on StyledTextCtrl. """
    
    def __init__(self, parent, readOnly):
        """
        Default class constructor.

        @param parent: the StyledTextCtrl parent;
        @param readOnly: indicates if the StyledTextCtrl should be in read-only mode.

        """        

        stc.StyledTextCtrl.__init__(self, parent)

        # Add the Python keywords to the list        
        keys = keyword.kwlist + _stcKeywords

        # Allow zooming (StyledTextCtrl is quite cool)        
        self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        # Set the Python lexer and the keywords
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keys))

        self.SetProperty("fold", "1")
        # What the hell means this tab timmy???
        self.SetProperty("tab.timmy.whinge.level", "1")
        self.SetMargins(0,0)

        self.SetViewWhiteSpace(False)        
        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        if not readOnly:
            # Is the user enters custom code, it is good to remember him not
            # to exceed 80 characters per line :-D
            self.SetEdgeColumn(78)
        else:
            # We are seeing the automagically generated Setup.py file, which
            # can contain quite long strings...
            self.SetEdgeColumn(300)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # Like a flattened tree control using square headers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,           "white", "#808080")

        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        
        # Make some styles,  The lexer defines what each style is used for, we
        # just have to define what each style looks like.  This set is adapted from
        # Scintilla sample property files.

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(mono)s,size:%(size)d" % _faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % _faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % _faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % _faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default 
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(mono)s,size:%(size)d" % _faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(mono)s,size:%(size)d" % _faces)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % _faces)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(mono)s,size:%(size)d" % _faces)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(mono)s,size:%(size)d" % _faces)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % _faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % _faces)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % _faces)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % _faces)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % _faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % _faces)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(mono)s,size:%(size)d" % _faces)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % _faces)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % _faces)

        self.SetCaretForeground("BLUE")


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnUpdateUI(self, event):
        """ Handles the stc.EVT_STC_UPDATEUI event for PythonSTC. """
        
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)


    def OnMarginClick(self, event):
        """ Handles the stc.EVT_STC_MARGINCLICK event for PythonSTC. """
        
        # fold and unfold as needed
        if event.GetMargin() == 2:
            if event.GetShift() and event.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(event.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if event.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif event.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)


    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def FoldAll(self):
        """ Folds/unfolds everything in the code. """
        
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1



    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        """ Expands/contracts lines after a folding event. """
        
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

        
class Py2ExeMissing(wx.Frame):
    """
    A handy frame which can show the modules py2exe thinks are missing
    or the dlls your executable relies on.
    """

    def __init__(self, parent, project, dll=False):
        """
        Default class constructor.

        @param parent: the parent widget;
        @param project: the project as stored in the database;
        @param dll: indicates whether we are going to show the missing binary
                    dependencies (dll) or the missing modules (py).

        """
        
        wx.Frame.__init__(self, parent, size=(500, 400))
        
        self.MainFrame = parent
        self.mainPanel = wx.Panel(self)

        # Build column names dinamically depending on the dll value
        name = (dll and ["binarydependencies"] or ["missingmodules"])[0]
        if dll:
            columnNames = [_("DLL Name"), _("DLL Path")]
        else:
            # There might be some strange sub-sub-sub module imported...
            columnNames = [_("Main Module"), _("Sub-Module 1"),
                           _("Sub-Module 2"), _("Sub-Module 3")]

        # Build the base list control            
        self.list = BaseListCtrl(self.mainPanel, columnNames, name, self.MainFrame)

        # Build a couple of fancy and useless buttons        
        okBmp = self.MainFrame.CreateBitmap("project_ok")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
        self.okButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, wx.ID_OK, okBmp, _("Ok"))
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, wx.ID_CANCEL, cancelBmp, _("Cancel"))

        # Do the hard work        
        self.SetProperties(dll)
        self.LayoutItems(dll)
        self.BindEvents()

        # Populate the list, retrieving the data directly from the project
        missingModules, binaryDependencies = project.GetCompilationData()
        self.list.PopulateList((dll and [binaryDependencies] or [missingModules])[0])

        for col in xrange(2, self.list.GetColumnCount()):
            self.list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
            
        self.CenterOnParent()
        self.Show()
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self, dll):
        """
        Sets few properties for the Py2ExeMissing frame.

        @param dll: whether this frame is showing dlls or missing modules.
        """

        if dll:
            # We are showing binary dependencies
            title = _("Py2Exe Binary Dependencies")
        else:
            # These are what py2exe thinks are the missing modules
            title = _("Py2Exe Missing Modules")
            
        self.SetTitle(title)
        self.SetIcon(self.MainFrame.GetIcon())

        # We want the second column to fill all the available space
        self.list.setResizeColumn(2)    
        self.okButton.SetDefault()
        self.SetTransparent(self.MainFrame.GetPreferences("Transparency"))


    def LayoutItems(self, dll):
        """
        Layouts the widgets with sizers.

        @param dll: whether this frame is showing dlls or missing modules.
        """

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        if dll:
            # We are showing binary dependencies
            label = _("Make sure you have the license if you distribute any of them, and\n"  \
                      "make sure you don't distribute files belonging to the operating system.")
        else:
            # These are what py2exe thinks are the missing modules
            label = _("Py2Exe thinks that these modules (and sub-modules) are missing.\n" \
                      "Inclusion of one or more of them may allow your compiled application to run.")

        label = wx.StaticText(self.mainPanel, -1, label)
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

        panelSizer.Add(label, 0, wx.ALL, 10)
        panelSizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)

        # Add the fancy and useless buttons
        bottomSizer.Add(self.okButton, 0, wx.ALL, 15)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 15)

        panelSizer.Add(bottomSizer, 0, wx.EXPAND)
        self.mainPanel.SetSizer(panelSizer)
        panelSizer.Layout()

        # Add everything to the main sizer        
        mainSizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Layout()


    def BindEvents(self):
        """ Binds the events for Py2ExeMissing. """

        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.cancelButton)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUp)
        

    # ============== #
    # Event handlers #
    # ============== #
    
    def OnOk(self, event):
        """ Handles the wx.EVT_BUTTON event for Py2ExeMissing. """

        # Very useful these buttons, eh?
        self.Destroy()
        event.Skip()


    def OnKeyUp(self, event):
        """ Handles the wx.EVT_CHAR_HOOK event for Py2ExeMissing. """

        if event.GetKeyCode() in [wx.WXK_ESCAPE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # Close this window
            self.OnOk(event)

        event.Skip()
        

class BaseDialog(wx.Dialog):
    """ A wx.Dialog base class for all the other GUI2Exe dialogs. """

    def __init__(self, parent):
        """
        Default class constructor.

        @param parent: the dialog parent;
        """
            
        wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.MainFrame = parent
        
        # Set the user transparency
        self.SetTransparent(self.MainFrame.GetPreferences("Transparency"))
        

    def CreateButtons(self):
        """ Creates the Ok and cancel bitmap buttons. """
        
        # Build a couple of fancy and useless buttons        
        okBmp = self.MainFrame.CreateBitmap("project_ok")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
        self.okButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_OK, okBmp, _("Ok"))
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CANCEL, cancelBmp, _("Cancel"))        


    def SetProperties(self, title):
        """ Sets few properties for the dialog. """        

        self.SetTitle(title)
        self.SetIcon(self.MainFrame.GetIcon())
        self.okButton.SetDefault()        


    def BindEvents(self):
        """ Binds the events to specific methods. """
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUp)


    def OnOk(self, event):
        """ Handles the Ok wx.EVT_BUTTON event for the dialog. """

        self.EndModal(wx.ID_OK)


    def OnCancel(self, event):
        """ Handles the Cancel wx.EVT_BUTTON event for the dialog. """

        self.OnClose(event)


    def OnClose(self, event):
        """ User canceled the dialog. """

        self.EndModal(wx.ID_CANCEL)


    def OnKeyUp(self, event):
        """ Handles the wx.EVT_CHAR_HOOK event for the dialog. """
        
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            # Close the dialog, no action
            self.OnClose(event)
        elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # Close the dialog, the user wants to continue
            self.OnOk(event)

        event.Skip()


class GUI2ExeDirSelector(BaseDialog):
    """
    A different implementation of wx.DirDialog which allows multiple
    folders to be selected at once.
    """

    def __init__(self, parent, title, showExtensions=False):
        """
        Default BaseDialog class constructor.

        @param parent: the dialog parent widget;
        @param title: the dialog title;
        @param showExtensions: whether to show a text control to filter extensions.
        """
        
        BaseDialog.__init__(self, parent)

        self.showExtensions = showExtensions
        
        self.dirCtrl = wx.GenericDirCtrl(self, size=(300, 200), style=wx.DIRCTRL_3D_INTERNAL|wx.DIRCTRL_DIR_ONLY)
        self.CreateButtons()
        
        if showExtensions:
            # Create a text control to filter extensions
            self.extensionText = wx.TextCtrl(self, -1, "*.*")

        self.SetProperties(title)           
        # Setup the layout and frame properties        
        self.SetupDirCtrl()
        self.LayoutItems()
        self.BindEvents()
    

    def SetupDirCtrl(self):
        """ Setup the wx.GenericDirCtrl (icons, labels, etc...). """

        il = wx.ImageList(16, 16)

        # Add images to list. You need to keep the same order in order for
        # this to work!

        # closed folder:
        il.Add(self.MainFrame.CreateBitmap("folder_close"))

        # open folder:
        il.Add(self.MainFrame.CreateBitmap("folder_open"))

        # root of filesystem (linux):
        il.Add(self.MainFrame.CreateBitmap("computer"))

        # drive letter (windows):
        il.Add(self.MainFrame.CreateBitmap("hd"))

        # cdrom drive:
        il.Add(self.MainFrame.CreateBitmap("cdrom"))

        # removable drive on win98:
        il.Add(self.MainFrame.CreateBitmap("removable"))

        # removable drive (floppy, flash, etc):
        il.Add(self.MainFrame.CreateBitmap("removable"))

        # assign image list:
        treeCtrl = self.dirCtrl.GetTreeCtrl()
        treeCtrl.AssignImageList(il)

        if not self.showExtensions:
            treeCtrl.SetWindowStyle(treeCtrl.GetWindowStyle() | wx.TR_MULTIPLE)

        # Set the wx.GenericDirCtrl defult path
        executable = os.path.split(sys.executable)[0]
        self.dirCtrl.ExpandPath(executable)
        self.dirCtrl.SetDefaultPath(executable)
        self.dirCtrl.SetPath(executable)
        

    def LayoutItems(self):
        """ Layout the widgets using sizers. """

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        staticText = wx.StaticText(self, -1, _("Choose one or more folders:"))
        staticText.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))

        # Add the main wx.GenericDirCtrl        
        mainSizer.Add(staticText, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(self.dirCtrl, 1, wx.EXPAND|wx.ALL, 10)

        if self.showExtensions:
            # Show the extension filter
            label = wx.StaticText(self, -1, _("Filter file extensions using wildcard separated by a comma:"))
            label.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
            # Add the extension text control
            mainSizer.Add(label, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
            mainSizer.Add((0, 2))
            mainSizer.Add(self.extensionText, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
            
        # Add the fancy buttons
        bottomSizer.Add(self.okButton, 0, wx.ALL, 10)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 10)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND)

        # Layout the dialog
        self.SetSizer(mainSizer)
        mainSizer.Layout()
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)


    def GetSelectedFolders(self):
        """ Returns the folders selected by the user. """

        # Retrieve the tree control and the selections the
        # user has made
        treeCtrl = self.dirCtrl.GetTreeCtrl()
        selections = treeCtrl.GetSelections()

        folders = []

        # Loop recursively over the selected folder and its sub-direcories
        for select in selections:
            itemText = treeCtrl.GetItemText(select)
            # Recurse on it.
            folder = self.RecurseTopDir(treeCtrl, select, itemText)
            folders.append(os.path.normpath(folder))

        if not self.showExtensions:
            return folders

        extensions = self.extensionText.GetValue().strip()
        return folders[0], extensions.split(",")
    

    def RecurseTopDir(self, treeCtrl, item, itemText):
        """
        Recurse a directory tree to include all the sub-folders.

        @param treeCtrl: the tree control associated with wx.GenericDirCtrl;
        @param item: the selected tree control item;
        @param itemText: the selected tree control item text.
        """

        # Get the item parent        
        parent = treeCtrl.GetItemParent(item)
        if parent != treeCtrl.GetRootItem():
            # Not the root item, recurse again on it
            itemText = treeCtrl.GetItemText(parent) + "/" + itemText
            itemText = self.RecurseTopDir(treeCtrl, parent, itemText)

        return itemText


    def BindEvents(self):
        """ Binds the events to specific methods. """

        BaseDialog.BindEvents(self)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)
        

class PyInfoFrame(wx.Frame):
    """ Base class for PyBusyInfo. """

    def __init__(self, parent, message, useCustom):
        """ Defaults class constructor.

        @param parent: the frame parent;
        @param message: the message to display in the PyBusyInfo;
        @param useCustom: if True, it will custom-draw the content in an OnPaint handler.
        """
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, _("Busy"), wx.DefaultPosition,
                          wx.DefaultSize, wx.NO_BORDER | wx.FRAME_TOOL_WINDOW | wx.FRAME_SHAPED | wx.STAY_ON_TOP)

        panel = wx.Panel(self)
        panel.SetCursor(wx.HOURGLASS_CURSOR)

        if not useCustom:

            text = wx.StaticText(panel, wx.ID_ANY, message)
            text.SetCursor(wx.HOURGLASS_CURSOR)

            # make the frame of at least the standard size (400*80) but big enough
            # for the text we show
            sizeText = text.GetBestSize()

        else:

            # We will take care of drawing the text and not using wx.StaticText
            self._message = message
            dc = wx.ClientDC(self)
            textWidth, textHeight, dummy = dc.GetMultiLineTextExtent(self._message)
            sizeText = wx.Size(textWidth, textHeight)

        self.SetClientSize((max(sizeText.x, 340) + 60, max(sizeText.y, 40) + 60))
        # need to size the panel correctly first so that text.Centre() works
        panel.SetSize(self.GetClientSize())

        if useCustom:
            # Bind the events to draw ourselves
            panel.Bind(wx.EVT_PAINT, self.OnPaint)
            panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
            
        else:
            text.Centre(wx.BOTH)
            
        self.Centre(wx.BOTH)

        # Create a non-rectangular region to set the frame shape
        size = self.GetSize()
        bmp = wx.EmptyBitmap(size.x, size.y)
        dc = wx.BufferedDC(None, bmp)
        dc.SetBackground(wx.Brush(wx.Color(0, 0, 0), wx.SOLID))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Color(0, 0, 0), 1))
        dc.DrawRoundedRectangle(0, 0, size.x, size.y, 12)                
        r = wx.RegionFromBitmapColour(bmp, wx.Color(0, 0, 0))
        # Store the non-rectangular region
        self.reg = r

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetBusyShape)
        else:
            self.SetBusyShape()

        # Add a custom bitmap at the top                    
        gui2exe = wx.GetApp().GetTopWindow()
        self._icon = gui2exe.CreateBitmap("GUI2Exe_small")


    def SetBusyShape(self, event=None):
        """ Sets the PyBusyInfo shape. """

        self.SetShape(self.reg)
        if event:
            # GTK only
            event.Skip()
            

    def OnPaint(self, event):
        """ Custom OnPaint event handler to draw nice backgrounds. """

        panel = event.GetEventObject()
        
        dc = wx.BufferedPaintDC(panel)
        dc.Clear()

        # Fill the background with a gradient shading
        startColour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        endColour = wx.WHITE

        rect = panel.GetRect()
        dc.GradientFillLinear(rect, startColour, endColour, wx.SOUTH)

        # Draw the label
        font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        dc.SetFont(font)

        # Draw the message
        rect2 = wx.Rect(*rect)
        rect2.height += 20
        dc.DrawLabel(self._message, rect2, alignment=wx.ALIGN_CENTER|wx.ALIGN_CENTER)

        # Draw the top title
        font.SetWeight(wx.BOLD)
        dc.SetFont(font)
        dc.SetPen(wx.Pen(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT)))
        dc.SetTextForeground(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT))
        dc.DrawBitmap(self._icon, 5, 5)
        dc.DrawText(_("GUI2Exe Busy Message"), 26, 5)
        dc.DrawLine(5, 25, rect.width-5, 25)

        size = self.GetSize()
        dc.SetPen(wx.Pen(startColour, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRoundedRectangle(0, 0, size.x, size.y-1, 12)
        

    def OnErase(self, event):
        """
        Erase background event is intentionally empty to avoid flicker during
        custom drawing.
        """

        # This is empty on purpose, to avoid flickering
        pass

                
# -------------------------------------------------------------------- #
# The actual PyBusyInfo implementation
# -------------------------------------------------------------------- #

if wx.Platform == "__WXMAC__":
    
    # wxMac doesn't like the custom PyBusyInfo

    class PyBusyInfo(wx.BusyInfo):
        """ Standard wx.BusyInfo class in wxWidgets. """

        def __init__(self, message, parent=None):
            """
            Default class constructor.

            @param message: the message to display in wx.BusyInfo;
            @param parent: the wx.BusyInfo parent (if any).
            """

            wx.BusyInfo.__init__(self, message, parent)

else:
            
    class PyBusyInfo(object):
        """
        Constructs a busy info window as child of parent and displays msg in it.
        NB: If parent is not None you must ensure that it is not closed while the busy info is shown.
        """

        def __init__(self, message, parent=None, useCustom=True):
            """
            Default class constructor.

            @param message: the message to display;
            @param parent: the PyBusyInfo parent (can be None);
            @parent useCustom: if True, custom drawing/shading can be implemented.
            """

            self._infoFrame = PyInfoFrame(parent, message, useCustom)

            if parent and parent.HasFlag(wx.STAY_ON_TOP):
                # we must have this flag to be in front of our parent if it has it
                self._infoFrame.SetWindowStyleFlag(wx.STAY_ON_TOP)
                
            self._infoFrame.Show(True)
            self._infoFrame.Refresh()
            self._infoFrame.Update()
            

        def __del__(self):
            """ Overloaded method, for compatibility with wxWidgets. """

            self._infoFrame.Show(False)
            self._infoFrame.Destroy()
        

class MultiComboBox(wx.combo.OwnerDrawnComboBox):
    """ A multi-purpose combobox. """

    def __init__(self, parent, choices, style, compiler, name):
        """
        Default class constructor.

        @param parent: the combobox parent;
        @param choices: a list of strings which represents the combobox choices;
        @param style: the combobox style;
        @param compiler: the compiler to which the combobox's parent belongs;
        @param name: the option name associated to this combobox.
        """

        wx.combo.OwnerDrawnComboBox.__init__(self, parent, choices=choices,
                                             style=style, name=name)

        self.MainFrame = wx.GetTopLevelParent(self)
        self.compiler = compiler
        self.option = name

        # Find out the longest element
        lengths = [len(choice) for choice in choices]
        index = lengths.index(max(lengths))
        longestChoice = choices[index]

        # This seems to do nothing on Mac, while it works
        # pretty well on Windows and GTK
        choiceWidth, dummy = self.GetTextExtent(longestChoice)
        nameWidth, dummy = self.GetTextExtent(name)
        width = max(choiceWidth, nameWidth) + self.GetButtonSize().x + 35
        self.SetMinSize((width, 22))

        # Create the image list for our choices
        self.BuildImageList()


    def BuildImageList(self):
        """ Builds an image list for our list of choices. """

        # Retrieve the images from Constants
        images = _comboImages[self.compiler][self.option]
        self.imageList = []
        # Build the image list
        for png in images:
            self.imageList.append(self.MainFrame.CreateBitmap(png))

        
    def OnDrawItem(self, dc, rect, item, flags):
        """
        Overridden from OwnerDrawnComboBox, called to draw each item in the list.

        @param dc: the device context used to draw text, icons etc... ;
        @param rect: the bounding rectangle for the item being drawn
                     (DC clipping region is set to this rectangle before
                     calling this function);
        @param item: the index of the item to be drawn;
        @param flags: flags to draw the item.
        """
        
        if item == wx.NOT_FOUND:
            # painting the control, but there is no valid item selected yet
            return

        r = wx.Rect(*rect)  # make a copy
        r.Deflate(3, 5)

        pen = wx.Pen(dc.GetTextForeground(), 1)
        dc.SetPen(pen)

        # Get the item string and bitmap
        string = self.GetString(item)
        indx = self.GetItems().index(string)
        bmp = self.imageList[indx]
        y = (r.y+r.height/2-8)
        # Draw the bitmap and the text
        dc.DrawBitmap(bmp, r.x+3, y, True)
        dc.DrawText(string, r.x + 25, r.y + (r.height/2 - dc.GetCharHeight()/2)-1)
            

    def OnDrawBackground(self, dc, rect, item, flags):
        """
        Overridden from OwnerDrawnComboBox, called for drawing the background area of each item.

        @param dc: the device context used to draw text, icons etc... ;
        @param rect: the bounding rectangle for the item being drawn
                     (DC clipping region is set to this rectangle before
                     calling this function);
        @param item: the index of the item to be drawn;
        @param flags: flags to draw the item.
        """
        
        # If the item is selected, or we are painting the
        # combo control itself, then use the default rendering.

        if flags & (wx.combo.ODCB_PAINTING_CONTROL | wx.combo.ODCB_PAINTING_SELECTED):
            wx.combo.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return
        
        string = self.GetString(item)
        # Otherwise, draw every item background
        bgCol = wx.WHITE
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        dc.DrawRectangleRect(rect)

        
    def OnMeasureItem(self, item):
        """
        Overridden from OwnerDrawnComboBox, should return the height needed to display
        an item in the popup, or -1 for default.

        @param item: the index of the item to be drawn.
        """

        # Return a sensible value for item height on all platforms
        return 19


    def OnMeasureItemWidth(self, item):
        """
        Overridden from OwnerDrawnComboBox.  Callback for item width, or -1
        for default/undetermined.

        @param item: the index of the item to be drawn.
        """

        dc = wx.ClientDC(self)
        string = self.GetString(item)

        # Return the text width + the bitmap width + some white space
        return dc.GetTextExtent(string)[0] + 25


class BuildDialog(BaseDialog):
    """
    A dialog used to show the full build output for a specific compiler.
    It allows to save the build output text to a file or to export it to
    the clipboard.
    """
    
    def __init__(self, parent, projectName, compiler, outputText):

        """
        Default class constructor.

        @param parent: the dialog's parent;
        @param projectName: the current project name;
        @param compiler: the compiler used to build the executable;
        @param outputText: the full build output text.
        """

        BaseDialog.__init__(self, parent)

        # Split the text to look for compiler info/build text
        header, text = outputText.split("/-/-/")
        self.outputTextCtrl = wx.TextCtrl(self, -1, text.strip(), style=wx.TE_MULTILINE|wx.TE_READONLY)

        # Create few bitmaps for the fancy buttons
        saveBmp = self.MainFrame.CreateBitmap("save_to_file")
        clipboardBmp = self.MainFrame.CreateBitmap("copy_to_clipboard")
        cancelBmp = self.MainFrame.CreateBitmap("exit")

        # Create the fancy buttons to export to a file, copy to the clipboard
        # or close the dialog
        self.exportButton = buttons.ThemedGenBitmapTextButton(self, -1, saveBmp, _("Save to file..."))
        self.clipboardButton = buttons.ThemedGenBitmapTextButton(self, -1, clipboardBmp, _("Export to clipboard"))
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CANCEL, cancelBmp, _("Cancel"))

        # Do the hard work, layout items and set dialog properties
        self.SetProperties()
        self.DoLayout(header, projectName, compiler)

        self.BindEvents()
        self.CenterOnParent()


    def SetProperties(self):
        """ Sets few properties for the dialog. """

        self.SetTitle(_("Full Build Output Dialog"))
        self.SetIcon(self.GetParent().GetIcon())

        size = self.MainFrame.GetSize()
        self.SetSize((2*size.x/3, 2*size.y/3))


    def DoLayout(self, header, projectName, compiler):
        """
        Layouts the widgets with sizers.

        @param header: the header text (containing compiler information;
        @param projectName: the name of the project the build output refers to;
        @param compiler: the compiler used to build the project.
        """

        # Create the sizer structure        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        transdict = dict(projectName=projectName, compiler=compiler, header=header)
        label = wx.StaticText(self, -1,
                              _("Build output text for %(projectName)s (%(compiler)s):\nBuilt on %(header)s") % \
                              transdict)
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        mainSizer.Add(label, 0, wx.ALL, 10)
        
        # Add the main text control
        mainSizer.Add(self.outputTextCtrl, 1, wx.ALL|wx.EXPAND, 10)

        # Add the fancy buttons        
        bottomSizer.Add(self.exportButton, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        bottomSizer.Add((5, 0), 0, 0, 0)
        bottomSizer.Add(self.clipboardButton, 0, wx.TOP|wx.BOTTOM, 10)
        bottomSizer.Add((0, 0), 1, 0, 0)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 10)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND, 0)

        # Layout the sizers
        self.SetSizer(mainSizer)
        self.Layout()


    def BindEvents(self):
        """ Binds the events to specific methods. """

        BaseDialog.BindEvents(self)
        
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.exportButton)
        self.Bind(wx.EVT_BUTTON, self.OnClipboard, self.clipboardButton)
        

    def OnSave(self, event):
        """ Handles the wx.EVT_BUTTON event for the 'Save' action. """

        # Launch the save dialog        
        dlg = wx.FileDialog(self, message=_("Save file as..."),
                            defaultFile="BuildOutput.txt", wildcard="All files (*.*)|*.*",
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you.
            fp = file(path, 'w') # Create file anew
            fp.write(self.outputTextCtrl.GetValue())
            fp.close()
            transdict = dict(filePath=path)
            self.MainFrame.SendMessage(0, _("Build output file %(filePath)s successfully saved") % transdict)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()
        

    def OnClipboard(self, event):
        """ Handles the wx.EVT_BUTTON event for the 'Copy' action. """

        # Create a text objct in memory
        self.do = wx.TextDataObject()
        self.do.SetText(self.outputTextCtrl.GetValue())

        # Open the clipboard        
        if wx.TheClipboard.Open():
            # Copy the data to the clipboard
            wx.TheClipboard.SetData(self.do)
            wx.TheClipboard.Close()
            self.MainFrame.SendMessage(0, _("Build output text successfully copied to the clipboard"))
        else:
            # Some problem with the clipboard...
            self.MainFrame.RunError(2, _("Unable to open the clipboard."))
        
        
#-----------------------------------------------------------------------------#       

class TransientBase(object):
    """
    Base class for the TransientPopup class defined later.
    Allows our custom tooltip to work on all platforms.
    """
    
    def __init__(self, parent, compiler, option, tip, note=None):
        """
        Default class constructor.

        @param parent: the TransientPopup parent;
        @param compiler: the compiler currently selected;
        @param option: the option currently hovered by the mouse;
        @param tip: the help tip;
        @param note: a note on the current option.
        """
        
        self.panel = wx.Panel(self, -1)

        self.MainFrame = parent.MainFrame
        self.bmp = self.MainFrame.CreateBitmap("GUI2Exe_small")

        # Store the input data        
        self.option = option
        self.tip = tip
        self.note = note
        self.compiler = compiler

        if note:
            # A bottom note is present
            self.warnbmp = self.MainFrame.CreateBitmap("note")
            self.note.capitalize()

        # Measure the correct width and height for ourselves        
        dc = wx.ClientDC(self)
        self.bigfont = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        self.boldfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, True)
        self.normalfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False)
        self.slantfont = wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL, False)
        dc.SetFont(self.bigfont)
        transdict = dict(compiler=compiler)
        width1, height1 = dc.GetTextExtent(_("GUI2Exe Help Tip (%(compiler)s)") % transdict)
        width1 += 25 
        height1 = max(height1, 16)
        dc.SetFont(self.boldfont)
        width2, height2, dummy = dc.GetMultiLineTextExtent(self.option)
        dc.SetFont(self.normalfont)
        width3, height3, dummy = dc.GetMultiLineTextExtent(self.tip)

        width4 = height4 = 0
        if self.note:
            dc.SetFont(self.slantfont)
            width4, height4, dummy = dc.GetMultiLineTextExtent(self.note)
            width4 += 26

        fullheight = height1 + height2 + height3 + height4 + 40
        fullwidth = max(max(max(width1, width2), width3), width4) + 20

        # Set size and position
        size = wx.Size(fullwidth, fullheight)
        self.panel.SetSize(size)
        self.SetSize(size)
        # Bind the events to the panel
        self.panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        # Drop a shadow underneath (Windows XP only)
        self.DropShadow()

        self.AdjustPosition(size)
        self.Show()
        

    def OnPaint(self, event):
        """ Draw the full TransientPopup. """

        dc = wx.BufferedPaintDC(self.panel)
        rect = self.panel.GetClientRect()

        # Fill the background with a gradient shading
        startColour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        endColour = wx.WHITE

        dc.GradientFillLinear(rect, startColour, endColour, wx.SOUTH)

        # Draw the bitmap in the title
        dc.SetFont(self.bigfont)
        dc.SetTextForeground(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT))

        width, height = dc.GetTextExtent(_("GUI2Exe Help Tip"))
        ypos = 13 - height/2
        dc.DrawBitmap(self.bmp, 5, ypos)
        # Draw the title text
        transdict = dict(compiler=self.compiler)
        dc.DrawText(_("GUI2Exe Help Tip (%(compiler)s)") % transdict, 26, ypos)

        # Draw a line separator between the title and the message
        newYpos = ypos + height + 6
        dc.SetPen(wx.GREY_PEN)
        dc.DrawLine(rect.x+5, newYpos, rect.width-5, newYpos)

        newYpos += 5        

        # Draw the option name, in bold font
        dc.SetFont(self.boldfont)
        dc.SetTextForeground(wx.BLACK)
        
        width2, height2, dummy = dc.GetMultiLineTextExtent(self.option)
        textRect = wx.Rect(10, newYpos, width2, height2)
        dc.DrawLabel(self.option, textRect)

        newYpos += height2 + 6

        # Draw the option tooltip        
        dc.SetFont(self.normalfont)
        width3, height3, dummy = dc.GetMultiLineTextExtent(self.tip)
        textRect = wx.Rect(10, newYpos, width3, height3)
        dc.DrawLabel(self.tip, textRect)

        newYpos += height3 + 6
        if not self.note:
            # Draw a separator line
            dc.DrawLine(rect.x+10, newYpos, rect.width-10, newYpos)
            return

        # Draw the note below, with a warning sign
        dc.SetFont(self.slantfont)        
        width4, height4, dummy = dc.GetMultiLineTextExtent(self.note)
        textRect = wx.Rect(26, newYpos, width4, height4)
        dc.DrawBitmap(self.warnbmp, 5, newYpos+height4/2-8)
        dc.DrawLabel(self.note, textRect)
        newYpos += height4 + 6
        # Draw a separator line
        dc.DrawLine(rect.x+5, newYpos, rect.width-5, newYpos)
        

    def AdjustPosition(self, size):
        """
        Adjust the position of TransientPopup accordingly to the TransientPopup
        size, mouse position and screen geometry.

        @param size: our size.        
        """

        # Retrieve mouse position and screen geometry
        XMousePos, YMousePos = wx.GetMousePosition()
        XScreen, YScreen = wx.GetDisplaySize()

        # Position the tooltip window in order not to crash against
        # the screen borders
        if XMousePos + size.x > XScreen:
            if YMousePos + size.y > YScreen:
                # This is bottom right corner
                xPos, yPos = XMousePos - size.x, YMousePos - size.y
            else:
                # This is top right corner
                xPos, yPos = XMousePos - size.x, YMousePos
        else:
            if YMousePos + size.y > YScreen:
                # This is bottom left corner
                xPos, yPos = XMousePos, YMousePos - size.y
            else:
                # This is top left corner
                xPos, yPos = XMousePos, YMousePos
            
        self.SetPosition((xPos, yPos))


    def OnEraseBackground(self, event):
        """ Handles the wx.EVT_ERASE_BACKGROUND event for TransientPopup class. """

        # Empty handler on purpose, it avoids flickering        
        pass
    

    def OnMouseLeftDown(self, event):
        """ Handles the wx.EVT_LEFT_DOWN event for TransientPopup. """        

        # We destroy ourselves when the user click on us
        self.Show(False)
        self.Destroy()


    def DropShadow(self, drop=True):
        """ Adds a shadow under the window (Windows Only). """

        if not _libimported:
            # No Mark Hammond's win32all extension
            return
        
        if wx.Platform != "__WXMSW__":
            # This works only on Windows XP
            return

        hwnd = self.GetHandle()

        # Create a rounded rectangle region
        size = self.GetSize()
        rgn = win32gui.CreateRoundRectRgn(0, 0, size.x, size.y, 9, 9)
        win32gui.SetWindowRgn(hwnd, rgn, True)
        
        CS_DROPSHADOW = 0x00020000
        # Load the user32 library
        if not hasattr(self, "_winlib"):
            self._winlib = win32api.LoadLibrary("user32")
        
        csstyle = win32api.GetWindowLong(hwnd, win32con.GCL_STYLE)
        if csstyle & CS_DROPSHADOW:
            return
        else:
            csstyle |= CS_DROPSHADOW     #Nothing to be done

        # Drop the shadow underneath the window                
        GCL_STYLE= -26
        cstyle= win32gui.GetClassLong(hwnd, GCL_STYLE)
        if cstyle & CS_DROPSHADOW == 0:
            win32api.SetClassLong(hwnd, GCL_STYLE, cstyle | CS_DROPSHADOW)


class MacTransientPopup(wx.Frame, TransientBase):
    """ Popup window that works on wxMac """

    def __init__(self, parent, compiler, option, tip, note=None):
        """
        Default class constructor.

        @param parent: the TransientPopup parent;
        @param compiler: the compiler currently selected;
        @param option: the option currently hovered by the mouse;
        @param tip: the help tip;
        @param note: a note on the current option.
        """
        
        wx.Frame.__init__(self, parent, style=wx.NO_BORDER|wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR|wx.POPUP_WINDOW)
        # Call the base class
        TransientBase.__init__(self, parent, compiler, option, tip, note)


class TransientPopup(TransientBase, wx.PopupWindow):
    """
    A simple wx.PopupWindow that holds fancy tooltips.
    Not available on Mac as wx.PopupWindow is not implemented.
    """
    
    def __init__(self, parent, compiler, option, tip, note=None):
        """
        Default class constructor.

        @param parent: the TransientPopup parent;
        @param compiler: the compiler currently selected;
        @param option: the option currently hovered by the mouse;
        @param tip: the help tip;
        @param note: a note on the current option.
        """

        wx.PopupWindow.__init__(self, parent)
        # Call the base class
        TransientBase.__init__(self, parent, compiler, option, tip, note)


class PListEditor(BaseDialog):
    """ A simple PList editor for GUI2Exe (py2app only). """

    def __init__(self, parent, CFBundleExecutable, pListFile=None, pListCode={}):
        """
        Default class constructor.

        @param parent: the dialog parent;
        @param CFBundleExecutable: the program name;
        @param pListFile: a PList file, if any, to be merged with pListCode;
        @param pListCode: the existing PList code (if any).
        """

        BaseDialog.__init__(self, parent)
        
        PFile = {}
        if pListFile:
            # We got a file from the user
            PFile = plistlib.readPlist(pListFile)

        if not pListCode:
            # No existing PList code
            PTemplate = plist_template.infoPlistDict(CFBundleExecutable, pListCode)
            for key in PFile.keys():
                if key not in PTemplate:
                    PTemplate[key] = PFile[key]
        else:
            # If the user already has some PList code in the project,
            # we do no update it reading the plist_template from py2app
            PTemplate = pListCode

        self.vSplitter = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_LIVE_UPDATE|wx.SP_HORIZONTAL)
        
        self.topPanel = wx.Panel(self.vSplitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        self.bottomPanel = wx.Panel(self.vSplitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        self.titleBar = bp.ButtonPanel(self.topPanel, -1, "PList Actions",
                                       style=bp.BP_USE_GRADIENT, alignment=bp.BP_ALIGN_LEFT)  
        
        boldFont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        self.codeCheck = wx.CheckBox(self.bottomPanel, -1, _("Add by Python code"))
        self.codeCheck.SetFont(boldFont)
        self.staticText_1 = wx.StaticText(self.bottomPanel, -1, _("Double-click on one item in the tree control above:"))
        self.staticText_1.SetFont(boldFont)
        self.itemParentText = wx.TextCtrl(self.bottomPanel, -1, "")
        self.staticText_2 = wx.StaticText(self.bottomPanel, -1, _("Add your key/value dictionary in Python code:"))
        self.staticText_2.SetFont(boldFont)
        self.pythonStc = PythonSTC(self.bottomPanel, readOnly=True)

        addBmp = self.MainFrame.CreateBitmap("add")
        self.addButton = buttons.ThemedGenBitmapTextButton(self.bottomPanel, -1, addBmp, _("Append"), size=(-1, 22))

        self.enablingItems = [self.staticText_1, self.staticText_2, self.itemParentText,
                              self.pythonStc, self.addButton]

        # Create a tree list control to handle the Plist dictionary
        self.treeList = gizmos.TreeListCtrl(self.topPanel, -1, style=wx.TR_DEFAULT_STYLE | wx.TR_ROW_LINES |
                                            wx.TR_COLUMN_LINES | wx.TR_FULL_ROW_HIGHLIGHT)
   
        # Build a couple of fancy and useless buttons
        self.CreateButtons()
        self.UpdateTitleBar()

        size = self.MainFrame.GetSize()
        self.SetSize((size.x/2, 4*size.y/5))
        
        # Do the hard work
        self.SetProperties()
        self.LayoutItems()
        self.BuildImageList()
        self.PopulateTree(PTemplate)
        self.BindEvents()
        
        self.CenterOnParent()
        self.Show()

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets few properties for the dialog. """        

        BaseDialog.SetProperties(self, _("Simple PList editor for py2app"))
        self.EnableCode(False)

        bpArt = self.titleBar.GetBPArt()
        bpArt.SetColor(bp.BP_TEXT_COLOR, wx.WHITE)

        # These default to white and whatever is set in the system
        # settings for the wx.SYS_COLOUR_ACTIVECAPTION.  We'll use
        # some specific settings to ensure a consistent look for the
        # demo.
        activeCaption = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        bpArt.SetColor(bp.BP_BORDER_COLOR, activeCaption)
        bpArt.SetColor(bp.BP_GRADIENT_COLOR_TO, bp.BrightenColour(activeCaption, 0.4))
        bpArt.SetColor(bp.BP_GRADIENT_COLOR_FROM, activeCaption)
        bpArt.SetColor(bp.BP_BUTTONTEXT_COLOR, wx.WHITE)
        bpArt.SetColor(bp.BP_SEPARATOR_COLOR,
                       bp.BrightenColour(wx.Colour(60, 11, 112), 0.85))
        bpArt.SetColor(bp.BP_SELECTION_BRUSH_COLOR, bp.BrightenColour(activeCaption, 0.4))
        bpArt.SetColor(bp.BP_SELECTION_PEN_COLOR, activeCaption)

        self.titleBar.SetUseHelp(self.MainFrame.showTips)
        

    def UpdateTitleBar(self):
        """ Actually builds the ButtonPanel. """

        self.indices = []

        # Populate the ButtonPanel
        count = 0
        for name, png, tip in _bpPngs:

            btn = bp.ButtonInfo(self.titleBar, wx.NewId(),
                                self.MainFrame.CreateBitmap(png), kind=wx.ITEM_NORMAL,
                                shortHelp=tip)
            
            self.titleBar.AddButton(btn)
            self.Bind(wx.EVT_BUTTON, self.OnManipulateTree, id=btn.GetId())
            
            self.indices.append(btn.GetId())
            # Set the button text
            btn.SetText(name)

            if count > 0:
                # Append a separator after the second button
                self.titleBar.AddSeparator()
                if count == 2:
                    self.titleBar.AddSpacer()
                    
                btn.SetBitmap(self.MainFrame.CreateBitmap(png+"_grey"), "Disabled")
                btn.SetStatus("Disabled")

            count += 1                


    def LayoutItems(self):
        """ Layouts the widgets with sizers. """        

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        label = _("You can edit the properties below or add new ones:")

        label = wx.StaticText(self.topPanel, -1, label)
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

        topSizer.Add((0, 5))
        topSizer.Add(label, 0, wx.ALL, 5)
        topSizer.Add(self.titleBar, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        topSizer.Add(self.treeList, 1, wx.EXPAND|wx.ALL, 5)

        bottomSizer.Add((0, 5))        
        bottomSizer.Add(self.codeCheck, 0, wx.ALL, 5)
        bottomSizer.Add(self.staticText_1, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        bottomSizer.Add((0, 2))
        bottomSizer.Add(self.itemParentText, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        bottomSizer.Add(self.staticText_2, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        bottomSizer.Add((0, 2))
        bottomSizer.Add(self.pythonStc, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        bottomSizer.Add((0, 2))
        bottomSizer.Add(self.addButton, 0, wx.RIGHT|wx.BOTTOM|wx.ALIGN_RIGHT, 5)
        
        # Add the fancy and useless buttons
        buttonSizer.Add(self.okButton, 0, wx.ALL, 15)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 15)

        self.vSplitter.SplitHorizontally(self.topPanel, self.bottomPanel)
        self.vSplitter.SetMinimumPaneSize(100)

        self.titleBar.DoLayout()
        
        self.topPanel.SetSizer(topSizer)
        self.bottomPanel.SetSizer(bottomSizer)
        mainSizer.Add(self.vSplitter, 1, wx.EXPAND)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        mainSizer.Layout()

        wx.CallAfter(self.vSplitter.SetSashPosition, self.GetSize()[1]/2)
        

    def BindEvents(self):
        """ Binds the events to specific methods. """

        BaseDialog.BindEvents(self)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)
        self.Bind(wx.EVT_BUTTON, self.OnAddCode, self.addButton)
        self.treeList.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnLabelEdit)
        self.treeList.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self.treeList.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.codeCheck.Bind(wx.EVT_CHECKBOX, self.OnEnableCode)


    def BuildImageList(self):
        """ Builds the image list for the tree list control. """
        
        images = ["home"] + [str(i) for i in xrange(1, 6)] + ["mac"]
        imgList = wx.ImageList(16, 16)
        
        for png in images:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        self.treeList.AssignImageList(imgList)            


    def EnableCode(self, enable):
        """
        Enables/disables the top portion of the dialog, the one which contains
        the Python code editor.

        @param enable: whether to enable or disable the top portion of the dialog.
        """

        for item in self.enablingItems:
            item.Enable(enable)

        self.enableCode = enable
        

    def PopulateTree(self, PTemplate):
        """
        Populates the tree list control using the PList dictionary.

        @param PTemplate: a PList dictionary.
        """

        # Add three columns for property name, class and value
        self.treeList.AddColumn(_("Property List "), edit=True)
        self.treeList.AddColumn(_("Class          "), flag=wx.ALIGN_CENTER)
        self.treeList.AddColumn(_("Value"), edit=True)
        
        self.treeList.SetMainColumn(0) # the one with the tree in it...
        self.root = self.treeList.AddRoot("Root", 0)

        # Recursively add children
        self.AutoAddChildren(self.root, PTemplate, 0)
        # Sort the root's children
        self.treeList.SortChildren(self.root)
        self.treeList.SetItemText(self.root, "Dictionary", 1)
        transdict = dict(dictionaryItems=len(PTemplate.keys()))
        self.treeList.SetItemText(self.root, _("%(dictionaryItems)d key/value pairs") % transdict, 2)
        self.treeList.SetPyData(self.root, ["Dictionary", 0])

        self.Recolor()

        # Make the root item more visible
        boldFont = self.GetFont()
        pointSize = boldFont.GetPointSize()
        boldFont.SetWeight(wx.BOLD)
        boldFont.SetPointSize(pointSize+2)
        self.treeList.SetItemFont(self.root, boldFont)

        # Expand all items below the root, recursively        
        self.treeList.ExpandAll(self.root)
        colWidth, dummy = self.CalculateColumnWidth(self.root, 0)
        self.treeList.SetColumnWidth(0, colWidth)
        self.treeList.SetColumnWidth(2, 300)
        

    def AutoAddChildren(self, itemParent, PTemplate, level):
        """
        Recursively adds children to a tree item.

        @param itemParent: the item to which we will add children (if any);
        @param PTemplate: a PList dictionary or a list/string;
        @param level: the hierarchy level (root=0)
        """

        treeList = self.treeList

        # Loop around the key/value pairs
        keys = PTemplate.keys()
        keys.sort()
        for item in keys:
            child = treeList.AppendItem(itemParent, item, level+1)
            if isinstance(PTemplate[item], dict):
                # Is a dictionary, recurse on it
                treeList.SetItemText(child, "Dictionary", 1)
                transdict = dict(dictionaryItems=len(PTemplate[item].keys()))
                treeList.SetItemText(child, _("%(dictionaryItems)d key/value pairs") % transdict, 2)
                treeList.SetPyData(child, ["Dictionary", level])
                level = self.AutoAddChildren(child, PTemplate[item], level+1)
            else:
                # It is either a list, or a string
                # NOTE: array should be treated differently, as
                # they may be array of dictionaries, for which we
                # need to recurse on them
                treeList.SetItemImage(child, level+1)
                value = PTemplate[item]
                if isinstance(value, list):
                    kind = "Array"
                else:
                    kind = "String"

                treeList.SetItemText(child, kind, 1)
                
                treeList.SetItemText(child, str(value), 2)
                treeList.SetItemImage(child, 6, 2)
                # Store the item kind in the item PyData
                treeList.SetPyData(child, [kind, level])
                toSet = False
                if kind == "Array":
                    # Arrays can contain dictionaries...
                    for indx, val in enumerate(value):
                        if isinstance(val, dict):
                            toSet = True
                            grandChild = treeList.AppendItem(child, "%d"%indx, level+2)
                            treeList.SetItemText(grandChild, "Dictionary", 1)
                            transdict = dict(dictionaryItems=len(val.keys()))
                            treeList.SetItemText(grandChild, _("%(dictionaryItems)d key/value pairs") % transdict, 2)
                            treeList.SetPyData(grandChild, ["Dictionary", level+2])
                            level = self.AutoAddChildren(grandChild, val, level+2)

                if toSet:
                    transdict = dict(numberOfObjects=len(value))
                    treeList.SetItemText(child, _("%(numberOfObjects)d ordered objects")%transdict, 2)
                    treeList.SetItemImage(child, -1, 2)
                    
        return level
    

    def CalculateColumnWidth(self, item, colWidth, level=1):
        """
        Calculates the correct column widths for the tree list control columns.

        @param item: the item to be measured;
        @param colWidth: the maximum column width up to now;
        @param level: the hierarchy level (root=0).
        """

        treeList = self.treeList
        child, cookie = treeList.GetFirstChild(self.root)
        # Loop over all the item's children
        while child.IsOk():
            if treeList.HasChildren(child):
                # Recurse on this item, it has children
                colWidths, level = self.CalculateColumnWidth(child, colWidth, level+1)

            # Get the bounding rectangle of the item
            rect = treeList.GetBoundingRect(child)
            # Calculate the column width based on the bounding rectangle
            colWidth = max(colWidth, rect.width + 40*level+16)
            # Get the next item
            child, cookie = treeList.GetNextChild(item, cookie)
            
        return colWidth, level
            
                
    # ============== #
    # Event handlers #
    # ============== #


    def OnLabelEdit(self, event):
        """ Handles the wx.EVT_TREE_BEGIN_LABEL_EDIT event for the tree list control. """

        item = event.GetItem()
        self.treeList.SelectItem(item)
        
        if self.treeList.HasChildren(item):
            # No no, you can't edit items with children
            event.Veto()
            return

        event.Skip()


    def OnItemActivated(self, event):
        """ Handles the wx.EVT_TREE_ITEM_ACTIVATED event for the tree list control. """

        if not self.enableCode:
            # We are not adding PList dicts by code
            return

        # Store the item text in the upper text control
        itemText = self.treeList.GetItemText(event.GetItem())
        self.itemParentText.SetValue(itemText)
        self.itemParentText.Refresh()
        # Store the tree item in the text control
        self.itemParentText.treeItem = event.GetItem()
        

    def OnSelChanged(self, event):
        """ Handles the wx.EVT_TREE_SEL_CHANGED event for the tree list control. """
        
        buttons = self.titleBar._vButtons
        item = event.GetItem()

        # User can't delete or duplicate the root item
        for btn in buttons[1:]:
            btn.Enable(item != self.root)

        self.titleBar.Refresh()
            
        event.Skip()
        

    def OnEnableCode(self, event):
        """ Handles the wx.EVT_CHECKBOX event for the dialog. """

        self.EnableCode(event.IsChecked())
        

    def OnAddCode(self, event):
        """ Handles the wx.EVT_BUTTON event when adding Python code. """

        if not hasattr(self.itemParentText, "treeItem"):
            msg = _("Please double-click on one of the tree items, to which the\n" \
                    "new property will be appended.")
            self.MainFrame.RunError(2, msg)
            return
        
        # Get the Python code the user entered
        code = self.pythonStc.GetText()
        if not code.strip():
            # Code is empty?
            self.MainFrame.RunError(2, _("No Python code has been entered."))
            return

        code2 = code.strip().split("=")
        if len(code2) < 2:
            # The code should be in the form property = value
            msg = _("Invalid Python code entered.\n\n" \
                    "You should enter code in the form 'property = value',\n" \
                    "where 'value' can be any Python dictionary, string or list.")
            self.MainFrame.RunError(2, msg)
            return

        dummy = code.split("\n")
        dummy = dummy[-1].split("=")
        
        property, value = dummy[0].strip(), "=".join(dummy[1:])
        exc = False
        newCode = ";".join(self.pythonStc.GetText().split("\r"))
        try:
            # Try to eval it
            newValue = {}
            exec newCode in newValue
            value = newValue[property]
        except NameError:
            exc = True
            trb = sys.exc_info()[1]
            error, line, msg = "NameError", 1, trb.message
        except KeyError:
            exc = True
            trb = sys.exc_info()[1]
            error, line, msg = "KeyError", 1, trb.message
        except:
            exc = True
            trb = sys.exc_info()[1]
            error, line, msg = trb.msg, trb.lineno, trb.text

        if exc:
            transdict = dict(errorKind=error, errorAtLine=line, errorMessage=msg)
            msg = _("Invalid Python code entered.\n\n" \
                    "The error returned by 'eval' is:\n\n%(errorKind)s\nLine: %(errorAtLine)d, %(errorMessage)s")%transdict
            self.MainFrame.RunError(2, msg)
            return

        treeItem = self.itemParentText.treeItem
        level = self.treeList.GetPyData(treeItem)[1]

        self.AutoAddChildren(treeItem, {property: value}, level)
        self.treeList.ExpandAll(self.root)
        self.codeCheck.SetValue(0)
        self.EnableCode(False)
        self.Recolor()


    def OnKeyUp(self, event):
        """ Handles the wx.EVT_CHAR_HOOK event for the dialog. """
        
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            # Close the dialog, no action
            self.OnClose(event)
        elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            if wx.Window.FindFocus() == self.pythonStc:
                # Don't kill the dialog if the user presses enter
                event.Skip()
                return
            # Close the dialog, the user wants to continue
            self.OnOk(event)

        event.Skip()


    def OnManipulateTree(self, event):
        """ Handles all the toolbar button actions. """

        selection = self.treeList.GetSelection()
        if not selection or not selection.IsOk():
            # Is this possible?
            self.MainFrame.RunError(2, _("Please select one item in the tree."))
            return
        
        btn = event.GetId()
        indx = self.indices.index(btn)
        self.treeList.Freeze()

        if indx in [0, 1]:
            if indx == 1:
                # siblings are just brothers...
                selection = self.treeList.GetItemParent(selection)
            # We add new child or a new sibling to the selected item
            dlg = PListHelperDialog(self)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return

            name, kind, value = dlg.GetValues()
            level = self.treeList.GetPyData(selection)[1]
            item = self.treeList.AppendItem(selection, name, level+1)
            self.treeList.SetItemText(item, kind, 1)
            # Try to be clever, but not too much...
            if kind == "Dictionary":
                if value:
                    self.treeList.SetItemText(item, value, 2)
                else:
                    self.treeList.SetItemText(item, _("0 key/value pairs"), 2)
            else:
                self.treeList.SetItemText(item, value, 2)
                self.treeList.SetItemImage(item, 6, 2)

            self.treeList.SetItemImage(item, level+1)            
            self.treeList.SetPyData(item, [kind, level+1])
            self.treeList.EnsureVisible(item)

        elif indx == 2:
            # Duplicate an item...
            oldItem = selection
            parent = self.treeList.GetItemParent(oldItem)
            self.Duplicate(parent, oldItem)

        else:
            # Delete the item
            self.treeList.Delete(selection)
            
        # Recolor the tree list control
        self.Recolor()
        self.treeList.Thaw()


    def Duplicate(self, parent, oldItem):

        text, img = self.treeList.GetItemText(oldItem), self.treeList.GetItemImage(oldItem)
        newItem = self.treeList.AppendItem(parent, text, img)
        for col in xrange(1, 3):
            text, img = self.treeList.GetItemText(oldItem, col), self.treeList.GetItemImage(oldItem, col)
            self.treeList.SetItemImage(newItem, img, col)
            self.treeList.SetItemText(newItem, text, col)
        
        child, cookie = self.treeList.GetFirstChild(oldItem)
        while child.IsOk():
            self.Duplicate(newItem, child)
            child, cookie = self.treeList.GetNextChild(oldItem, cookie)

        self.treeList.ExpandAll(newItem)
        self.treeList.EnsureVisible(newItem)
        

    def Recolor(self, item=None, itemCounter=0):
        """
        Uses alternate colours for the tree list rows and sets the font.

        @param item: the item to be checked;
        @param itemCounter: the number of items already checked.
        """

        if item is None:
            item = self.root
            
        # Define the colours for alternate row colouring
        white, blue = wx.WHITE, wx.Colour(234, 242, 255)
        # Define some bold font for items with children
        boldFont = self.GetFont()
        boldFont.SetWeight(wx.BOLD)

        child, cookie = self.treeList.GetFirstChild(item)
        while child.IsOk():
            # Loop over all the items
            colour = (itemCounter%2 == 0 and [blue] or [white])[0]
            self.treeList.SetItemBackgroundColour(child, colour)
            itemCounter += 1
            if self.treeList.HasChildren(child):
                # Call ourselves recursively
                self.treeList.SetItemFont(child, boldFont)
                itemCounter = self.Recolor(child, itemCounter)

            child, cookie = self.treeList.GetNextChild(item, cookie)

        return itemCounter            


    def GetPList(self, item=None, PList={}):
        """ Returns the newly edited PList as a dictionary. """

        if item is None:
            # We have just started...
            item = self.root
            PList = dict()

        treeList = self.treeList        
        child, cookie = treeList.GetFirstChild(item)
        itemKind = treeList.GetPyData(item)[0]
        itemKey = treeList.GetItemText(item).encode()
        
        # Loop over all the item's children
        while child.IsOk():
            
            key = treeList.GetItemText(child).encode()
            value = treeList.GetItemText(child, 2)
            kind = treeList.GetPyData(child)[0]

            if kind == "Array":
                if treeList.HasChildren(child):
                    # Is an array of dictionaries, or something similar
                    grandChild, cookie2 = treeList.GetFirstChild(child)
                    counter = 0
                    PList[key] = []
                    while grandChild.IsOk():
                        PList[key].append(self.GetPList(grandChild, {}))
                        grandChild, cookie2 = treeList.GetNextChild(child, cookie2)
                else:
                    # A simple array of strings
                    PList[key] = eval(value)
            else:
                if treeList.HasChildren(child):
                    # Recurse on the child, it has children
                    PList[key] = self.GetPList(child, {})
                else:
                    if kind == "String":
                        PList[key] = value.encode()
                    else:
                        # NOTE: array should be treated differently, as
                        # they may be array of dictionaries, for which we
                        # need to recurse on them
                        PList[key] = eval(value)

            # Get the next child
            child, cookie = treeList.GetNextChild(item, cookie)        

        return PList
        

class PListHelperDialog(BaseDialog):
    """ A helper class for the PListEditor. """
    
    def __init__(self, parent):
        """
        Default class constructor.

        @param parent: the widget parent.
        """        

        BaseDialog.__init__(self, parent.MainFrame)
        
        self.propertyText = wx.TextCtrl(self, -1, "")
        self.typeCombo = wx.ComboBox(self, -1, choices=["String", "List", "Dictionary"],
                                     style=wx.CB_DROPDOWN|wx.CB_DROPDOWN|wx.CB_READONLY)
        self.valueText = wx.TextCtrl(self, -1, "")

        self.CreateButtons()
        self.SetProperties(_("New property dialog"))
        self.DoLayout()
        self.BindEvents()


    def SetProperties(self, title):
        """
        Sets few properties for the dialog.

        @param title: the dialog title.
        """

        BaseDialog.SetProperties(self, title)
        self.typeCombo.SetValue("String")


    def DoLayout(self):
        """ Layout the widgets using sizers. """

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.FlexGridSizer(2, 2, 2, 5)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self, -1, _("Please insert the property name and select its type below:"))
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        mainSizer.Add(label, 0, wx.ALL, 10)
        label1 = wx.StaticText(self, -1, _("Property Name:"))
        gridSizer.Add(label1, 0, 0, 0)
        label2 = wx.StaticText(self, -1, _("Property Type:"))
        gridSizer.Add(label2, 0, 0, 0)
        gridSizer.Add(self.propertyText, 1, wx.EXPAND, 0)
        gridSizer.Add(self.typeCombo, 0, 0, 0)
        gridSizer.AddGrowableCol(0)
        mainSizer.Add(gridSizer, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        mainSizer.Add((0, 10), 0, 0, 0)
        label3 = wx.StaticText(self, -1, _("Property Value (optional)"))
        sizer_1.Add(label3, 0, 0, 0)
        sizer_1.Add((0, 2), 0, 0, 0)
        sizer_1.Add(self.valueText, 0, wx.EXPAND, 0)
        mainSizer.Add(sizer_1, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        # Add the fancy buttons
        buttonSizer.Add(self.okButton, 0, wx.ALL, 15)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 15)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.Layout()


    def OnOk(self, event):
        """ Handles the Ok event generated by a button. """

        name, kind, value = self.GetValues()
        if len(name) == 0:
            # No way we can allow an empty name...
            self.MainFrame.RunError(2, _("Invalid or empty property name."))
            return

        self.EndModal(wx.ID_OK)


    def GetValues(self):
        """ Returns the property name, type and value (if any). """

        name = self.propertyText.GetValue().strip()
        kind = self.typeCombo.GetValue()
        value = self.valueText.GetValue().strip()

        return name, kind, value

        
class PreferencesDialog(BaseDialog):
    """ A dialog to show/edit preferences for GUI2Exe. """

    def __init__(self, parent):
        """
        Default class constructor.

        @param parent: the dialog parent.
        """

        BaseDialog.__init__(self, parent)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() & ~wx.RESIZE_BORDER)

        self.interfaceSizer_staticbox = wx.StaticBox(self, -1, _("User Interface"))
        self.languagesSizer_staticbox = wx.StaticBox(self, -1, _("Locale Settings"))
        self.projectSizer_staticbox = wx.StaticBox(self, -1, _("Projects"))
        self.loadProjects = wx.CheckBox(self, -1, _("Reload opened projects at start-up"),
                                        name="Reload_Projects")
        self.openedCompilers = wx.CheckBox(self, -1, _("Remember last used compiler for all projects"),
                                           name="Remember_Compiler")
        self.gui2exeSize = wx.CheckBox(self, -1, _("Remember GUI2Exe window size on exit"),
                                       name="Window_Size")
        self.gui2exePosition = wx.CheckBox(self, -1, _("Remember GUI2Exe window position on exit"),
                                           name="Window_Position")
        self.perspective = wx.CheckBox(self, -1, _("Use last UI perspective at start-up"),
                                       name="Perspective")
        self.transparency = wx.Slider(self, -1, 255, 100, 255, style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.languages = LangListCombo(self, self.MainFrame.GetPreferences("Language"))

        # Store the widgets for later use        
        self.preferencesWidgets = [self.loadProjects, self.openedCompilers, self.gui2exeSize,
                                   self.gui2exePosition, self.perspective]
        
        # Do the hard work
        self.CreateButtons()
        self.SetProperties()
        self.LayoutItems()
        self.BindEvents()
        
        self.CenterOnParent()
        
    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    

    def SetProperties(self):
        """ Sets few properties for the dialog. """        

        BaseDialog.SetProperties(self, _("GUI2Exe Preferences dialog"))

        for widget in self.preferencesWidgets:
            # Get all the user preferences
            name = widget.GetName()
            widget.SetValue(self.MainFrame.GetPreferences(name)[0])

        transparency = self.MainFrame.GetPreferences("Transparency")
        self.transparency.SetValue(transparency)
        
        
    def LayoutItems(self):
        """ Layouts the widgets with sizers. """        

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        languagesSizer = wx.StaticBoxSizer(self.languagesSizer_staticbox, wx.VERTICAL)
        interfaceSizer = wx.StaticBoxSizer(self.interfaceSizer_staticbox, wx.VERTICAL)
        projectSizer = wx.StaticBoxSizer(self.projectSizer_staticbox, wx.VERTICAL)
        label = wx.StaticText(self, -1, _("Your GUI2Exe preferences can be edited below:"))
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        mainSizer.Add(label, 0, wx.ALL, 10)
        projectSizer.Add(self.loadProjects, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        projectSizer.Add((0, 2), 0, 0, 0)
        projectSizer.Add(self.openedCompilers, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        mainSizer.Add(projectSizer, 0, wx.ALL|wx.EXPAND, 5)
        interfaceSizer.Add(self.gui2exeSize, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        interfaceSizer.Add((0, 2), 0, 0, 0)
        interfaceSizer.Add(self.gui2exePosition, 0, wx.LEFT|wx.RIGHT, 5)
        interfaceSizer.Add((0, 2), 0, 0, 0)
        interfaceSizer.Add(self.perspective, 0, wx.LEFT|wx.RIGHT, 5)
        interfaceSizer.Add((0, 20), 0, 0, 0)
        label2 = wx.StaticText(self, -1, _("Window Transparency:"))
        interfaceSizer.Add(label2, 0, wx.LEFT|wx.RIGHT, 5)
        interfaceSizer.Add((0, 5), 0, 0, 0)
        interfaceSizer.Add(self.transparency, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        mainSizer.Add(interfaceSizer, 0, wx.ALL|wx.EXPAND, 5)
        label3 = wx.StaticText(self, -1, _("Language:"))
        languagesSizer.Add(label3, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        languagesSizer.Add((0, 2), 0, 0, 0)
        languagesSizer.Add(self.languages, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        mainSizer.Add(languagesSizer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)

        # Add the fancy and useless buttons
        bottomSizer.Add(self.okButton, 0, wx.ALL, 15)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 15)

        mainSizer.Add(bottomSizer, 0, wx.EXPAND)
        
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        mainSizer.Layout()
        

    def BindEvents(self):
        """ Binds the events to specific methods. """

        BaseDialog.BindEvents(self)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancelButton)
        self.Bind(wx.EVT_COMMAND_SCROLL, self.OnTransparency, self.transparency)
        

    def OnTransparency(self, event):
        """ Handles the wx.EVT_COMMAND_SCROLL event for the dialog. """
        
        for win in wx.GetTopLevelWindows():
            win.SetTransparent(self.transparency.GetValue())


    def OnCancel(self, event):
        """ Handles the Cancel wx.EVT_BUTTON event for the dialog. """

        for win in wx.GetTopLevelWindows():
            win.SetTransparent(self.MainFrame.GetPreferences("Transparency"))

        self.EndModal(wx.ID_CANCEL)
        

    def OnOk(self, event):
        """ Applies the user choices and saves them to wx.Config. """

        for widget in self.preferencesWidgets:
            # Get all the user preferences
            name = widget.GetName()
            value = widget.GetValue()
            preference = self.MainFrame.GetPreferences(name)
            # Sets them back with the user choices
            preference[0] = value
            self.MainFrame.SetPreferences(name, preference)

        self.MainFrame.SetPreferences("Language", self.languages.GetValue())
        self.MainFrame.SetPreferences("Transparency", self.transparency.GetValue())
        self.EndModal(wx.ID_OK)


    def OnClose(self, event):
        """ User canceled the dialog. """

        self.OnCancel(event)


#---- Language List Combo Box----#
class LangListCombo(wx.combo.BitmapComboBox):
    """
    Combines a langlist and a BitmapComboBox.
    @note: from Editra.dev_tool
    """
    
    def __init__(self, parent, default=None):
        """
        Creates a combobox with a list of all translations for GUI2Exe
        as well as displaying the countries flag next to the item
        in the list.

        @param default: The default item to show in the combo box
        """

        self.MainFrame = parent.MainFrame
        
        lang_ids = GetLocaleDict(GetAvailLocales(self.MainFrame.installDir)).values()
        lang_items = langlist.CreateLanguagesResourceLists(langlist.LC_ONLY, \
                                                           lang_ids)
        wx.combo.BitmapComboBox.__init__(self, parent,
                                         size=wx.Size(250, 26),
                                         style=wx.CB_READONLY)
        for lang_d in lang_items[1]:
            bit_m = lang_items[0].GetBitmap(lang_items[1].index(lang_d))
            self.Append(lang_d, bit_m)

        if default:
            self.SetValue(default)


def ExceptionHook(exctype, value, trace):
    """
    Handler for all unhandled exceptions.

    @param exctype: Exception Type
    @param value: Error Value
    @param trace: Trace back info
    @note: from Editra.dev_tool
    """
    ftrace = FormatTrace(exctype, value, trace)

    # Ensure that error gets raised to console as well
    print ftrace

    if not ErrorDialog.REPORTER_ACTIVE:
        ErrorDialog(ftrace)


class ErrorReporter(object):
    """Crash/Error Reporter Service
    @summary: Stores all errors caught during the current session and
              is implemented as a singleton so that all errors pushed
              onto it are kept in one central location no matter where
              the object is called from.
    @note: from Editra.dev_tool

    """
    instance = None
    _first = True
    def __init__(self):
        """Initialize the reporter
        @note: The ErrorReporter is a singleton.

        """
        # Ensure init only happens once
        if self._first:
            object.__init__(self)
            self._first = False
            self._sessionerr = list()
        else:
            pass

    def __new__(cls, *args, **kargs):
        """Maintain only a single instance of this object
        @return: instance of this class

        """
        if not cls.instance:
            cls.instance = object.__new__(cls, *args, **kargs)
        return cls.instance

    def AddMessage(self, msg):
        """Adds a message to the reporters list of session errors
        @param msg: The Error Message to save

        """
        if msg not in self._sessionerr:
            self._sessionerr.append(msg)

    def GetErrorStack(self):
        """Returns all the errors caught during this session
        @return: formatted log message of errors

        """
        return "\n\n".join(self._sessionerr)

    def GetLastError(self):
        """Gets the last error from the current session
        @return: Error Message String

        """
        if len(self._sessionerr):
            return self._sessionerr[-1]

        
ID_SEND = wx.NewId()
class ErrorDialog(BaseDialog):
    """
    Dialog for showing errors and and notifying gui2exe-users should the
    user choose so.
    @note: from Editra.dev_tool
    """
    ABORT = False
    REPORTER_ACTIVE = False
    def __init__(self, message):
        """Initialize the dialog
        @param message: Error message to display
        """
        ErrorDialog.REPORTER_ACTIVE = True

        topWindow = wx.GetApp().GetTopWindow()
        version = topWindow.GetVersion()
        
        BaseDialog.__init__(self, topWindow)
        
        # Give message to ErrorReporter
        ErrorReporter().AddMessage(message)
        
        self.SetIcon(topWindow.GetIcon())
        self.SetTitle("Error/Crash Reporter")

        # Attributes
        self.err_msg = "%s\n\n%s\n%s\n%s" % (EnvironmentInfo(version), \
                                             "#---- Traceback Info ----#", \
                                             ErrorReporter().GetErrorStack(), \
                                             "#---- End Traceback Info ----#")

        errorBmp = topWindow.CreateBitmap("gui2exe_bug")
        abortBmp = topWindow.CreateBitmap("abort")
        sendBmp = topWindow.CreateBitmap("send")
        cancelBmp = topWindow.CreateBitmap("exit")

        self.errorBmp = wx.StaticBitmap(self, -1, errorBmp)

        
        self.textCtrl = wx.TextCtrl(self, value=self.err_msg, style=wx.TE_MULTILINE |
                                    wx.TE_READONLY)
        
        self.abortButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_ABORT, abortBmp, _("Abort"), size=(-1, 26))
        self.sendButton = buttons.ThemedGenBitmapTextButton(self, ID_SEND, sendBmp, _("Report Error"), size=(-1, 26))
        self.sendButton.SetDefault()
        self.closeButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CLOSE, cancelBmp, _("Close"), size=(-1, 26))

        # Layout
        self.DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Auto show at end of init
        self.CenterOnParent()
        self.ShowModal()


    def DoLayout(self):
        """
        Layout the dialog and prepare it to be shown
        
        @note: Do not call this method in your code
        """

        # Objects
        mainmsg = wx.StaticText(self, 
                                label=_("Error: Oh no, something bad happened!\n"
                                        "Help improve GUI2Exe by clicking on "
                                        "Report Error\nto send the Error "
                                        "Traceback shown below."))
        t_lbl = wx.StaticText(self, label=_("Error Traceback:"))

        t_lbl.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        # Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        topSizer.Add(self.errorBmp, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 20)
        topSizer.Add(mainmsg, 0, wx.EXPAND|wx.RIGHT, 20)
        mainSizer.Add(topSizer, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 20)
        mainSizer.Add(t_lbl, 0, wx.LEFT|wx.TOP|wx.RIGHT, 5)
        mainSizer.Add((0, 2))
        mainSizer.Add(self.textCtrl, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM|wx.RIGHT, 5)
        bottomSizer.Add(self.abortButton, 0, wx.ALL, 5)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.sendButton, 0, wx.TOP|wx.BOTTOM, 5)
        bottomSizer.Add((0, 10))
        bottomSizer.Add(self.closeButton, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 5)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        mainSizer.Layout()
        
        self.Fit()
        

    def OnButton(self, evt):
        """Handles button events
        @param evt: event that called this handler
        @postcondition: Dialog is closed
        @postcondition: If Report Event then email program is opened

        """
        e_id = evt.GetId()
        if e_id == wx.ID_CLOSE:
            self.Close()
        elif e_id == ID_SEND:
            msg = "mailto:%s?subject=Error Report&body=%s"
            addr = "andrea.gavana@gmail.com"
            msg = msg % (addr, self.err_msg)
            msg = msg.replace("'", '')
            webbrowser.open(msg)
            self.Close()
        elif e_id == wx.ID_ABORT:
            ErrorDialog.ABORT = True
            # Try a nice shutdown first time through
            wx.CallLater(500, wx.GetApp().OnExit, 
                         wx.MenuEvent(wx.wxEVT_MENU_OPEN, wx.ID_EXIT),
                         True)
            self.Close()
        else:
            evt.Skip()

    def OnClose(self, evt):
        """Cleans up the dialog when it is closed
        @param evt: Event that called this handler

        """
        ErrorDialog.REPORTER_ACTIVE = False
        self.Destroy()
        evt.Skip()
        
