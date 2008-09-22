# Start the imports
import os
import sys
import wx
import glob
import wx.lib.mixins.listctrl as listmix
import wx.stc as stc
import wx.combo
import wx.lib.buttons as buttons

if wx.Platform == "__WXMAC__":
    # For the PList editor
    from py2app.apptemplate import plist_template
    import plistlib
    import wx.gizmos as gizmos
    
# This is needed by BaseListCtrl
from bisect import bisect
# This is needed by the StyledTextCtrl
import keyword

from Utilities import opj, flatten, unique, RecurseSubDirs
from Constants import ListType, _iconFromName, _unWantedLists, _faces
from Constants import _stcKeywords, _pywild, _pypackages, _dllbinaries
from Constants import _xcdatawild, _dylibwild, _comboImages

_libimported = None

if wx.Platform == "__WXMSW__":
    osVersion = wx.GetOsVersion()
    # Shadows behind menus are supported only in XP
    if osVersion[1] == 5 and osVersion[2] == 1:
        try:
            import win32api
            import win32con
            import winxpgui
            import win32gui
            _libimported = "MH"
        except ImportError:
            _libimported = None
    else:
        _libimported = None
        
                 
class BaseListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.TextEditMixin,
                   listmix.ColumnSorterMixin):

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
        """ Inserts the columns in the list control. """

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
        
        event.Skip()


    def OnEndEdit(self, event):
        """ Handles the wx.EVT_LIST_END_LABEL_EDIT event for the list control. """
        
        if event.IsEditCancelled():
            # Nothing to do, the user cancelled the editing
            event.Skip()
            return

        event.Skip()

        # Adjust the data for the column sorter mixin
        indx = event.GetItem().GetId()
        tuple = ()
        # Loop over all the columns, populating a tuple
        for col in xrange(self.GetColumnCount()):
            item = self.GetItem(indx, col)
            tuple += (item.GetText(),)

        # Store the data
        self.SetItemData(indx, indx)
        self.itemDataMap[indx] = tuple
        # Initialize the column sorter mixin (if needed)
        self.InizializeSorter()

        # Update the project, as something changed
        wx.CallAfter(self.UpdateProject)
        

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
        item = wx.MenuItem(menu, self.popupId3, "Add Item(s)")
        bmp = self.MainFrame.CreateBitmap("add")
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        menu.AppendSeparator()        
        # Well, we can either delete the selected item(s)...
        item = wx.MenuItem(menu, self.popupId1, "Delete selected")
        bmp = self.MainFrame.CreateBitmap("delete_selected")
        item.SetBitmap(bmp)
        menu.AppendItem(item)
        # Or clear completely the list
        item = wx.MenuItem(menu, self.popupId2, "Clear all")
        bmp = self.MainFrame.CreateBitmap("clear_all")
        item.SetBitmap(bmp)
        menu.AppendItem(item)

        # Popup the menu on ourselves
        self.PopupMenu(menu)
        menu.Destroy()


    def OnRightUp(self, event):
        """ Handles the wx.EVT_RIGHT_UP event for the list control. """

        menu = wx.Menu()
        item = wx.MenuItem(menu, self.popupId3, "Add Item(s)")
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
        # Get all the selected items
        indices = self.GetSelectedIndices()
        # Reverse them, to delete them safely
        indices.reverse()

        # Loop over all the indices        
        for ind in indices:
            # Pop the data from the column sorter mixin dictionary
            indx = self.GetItemData(ind)
            self.itemDataMap.pop(indx)
            # Delete the item from the list
            self.DeleteItem(ind)

        # Time to warm up...
        self.Thaw()
        wx.EndBusyCursor()

        # Update the project, something changed
        wx.CallAfter(self.UpdateProject)


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

        name = self.GetName()
        compiler = self.GetParent().GetName()
        
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

        
    def OnItemActivated(self, event):

        if self.GetName() != "multipleexe":
            event.Skip()
            return

        x, y = event.GetPosition()
        row, flags = self.HitTest((x, y))

        if row < 0:
            event.Skip()
            return
            
        col_locs = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            col_locs.append(loc)

        column = bisect(col_locs, x+self.GetScrollPos(wx.HORIZONTAL)) - 1
        self.selectedItem = row
        rect = self.GetItemRect(self.selectedItem)

        if column == 1:
            # Choosing between Windows and Console program            
            rect.x += self.GetColumnWidth(0)
                
            if not self.GetRect().ContainsRect(rect):
                # simplified scrollbar compensate
                rect.SetWidth(max(self.GetColumnWidth(1), self.dummyCombo.GetBestSize().x))

            wx.CallAfter(self.ShowDummyControl, self.dummyCombo, rect)
            
        elif column == 2:
            for indx in xrange(3):
                rect.x += self.GetColumnWidth(indx)
            rect.x -= 26

            if not self.GetRect().ContainsRect(rect):
                rect.SetWidth(25)
            
            wx.CallAfter(self.ShowDummyControl, self.dummyButton, rect)
            
        else:
            event.Skip()

            
    def ShowDummyControl(self, control, rect):
        
        control.SetRect(rect)
        control.SetFocus()
        control.Show()
        control.Raise()


    def OnKillFocus(self, event):

        obj = event.GetEventObject()
        if obj == self.dummyButton:
            self.dummyButton.Hide()
            return
        
        shown = self.dummyCombo.IsShown()
        self.dummyCombo.Hide()
        if shown:
            value = self.dummyCombo.GetValue()
            self.SetStringItem(self.selectedItem, 1, value)
            self.UpdateProject()


    def OnChooseScript(self, event):

        # Launch the file dialog        
        dlg = wx.FileDialog(self.MainFrame, message="Add Python Script ...",
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
        
        self.UpdateProject()

            
    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def PopulateList(self, configuration):
        """ Populates the list control based on the input configuration. """

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


    def HandleNewResource(self, name):
        """ Handles the user request to add new resources. """

        if name.find("bitmap") >= 0:   # bitmap resources
            wildcard = "Bitmap files (*.bmp)|*.bmp"
        elif name.find("icon") >= 0:   # icon resources
            wildcard = "Icon files (*.ico)|*.ico"
        else:                          # whatever other resource
            wildcard = "All files (*.*)|*.*"

        # Run a file dialog with multiple selection            
        dlg = wx.FileDialog(self.MainFrame, message="New resources", wildcard=wildcard,
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
        wx.CallAfter(self.EditLabel, indx)
        

    def HandleDataFiles(self):
        """ Handles the user request to add new data files. """

        compiler = self.GetParent().GetName()
        
        if self.MainFrame.recurseSubDirs:

            # Here we recurse and add all the files in a particular folder
            # and its subfolder
            dlg = wx.DirDialog(self, "Choose a data files directory:",
                               style=wx.DD_DEFAULT_STYLE)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return

            path = dlg.GetPath()
            defaultDir = os.path.basename(path)
            
        else:            
            # Run a file dialog with multiple selection        
            wildcard = "All files (*.*)|*.*"
            dlg = wx.FileDialog(self.MainFrame, message="New data files", wildcard=wildcard,
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
            dlg = wx.TextEntryDialog(self.MainFrame, "Please enter the name of the folder for py2exe:",
                                     "Directory Name")
            dlg.SetValue(defaultDir)
            
            if dlg.ShowModal() != wx.ID_OK:
                # No choice made, no items added
                return

            # Get the user choice
            defaultDir = dlg.GetValue().strip()
            dlg.Destroy()

            if not defaultDir.strip():
                # Empty folder name?
                self.MainFrame.RunError("Error", "Invalid folder name.")
                return

        wx.BeginBusyCursor()
        if self.MainFrame.recurseSubDirs:
            if compiler == "py2exe":
                config = RecurseSubDirs(path, defaultDir)
            else:
                config = glob.glob(path + "/*")
        else:
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
        multipleOptions = ["windows", "", "", "0.1", "No Company", "No Copyrights",
                           "Py2Exe Sample File"]
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
        """ Handles the Dylib/Frameworks/XCDataModels options for Mac. """

        if name.find("dylib") >= 0 or name.find("frameworks") >= 0:
            message = "Add Dylib/Frameworks"
            wildcard = _dylibwild
        else:
            message = "Add XC Data Models"
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
            self.SetStringItem(indx, i, path)


    def AddFilesWithPath(self, name):
        """
        Processes all the list controls option for PyInstaller except the Path
        and Hooks extensions.
        """

        # A bunch of if switches to handle all the possibility offered
        # by PyInstaller
        if name == "scripts":
            message = "Add Python Scripts"
            wildcard = _pywild
        elif name == "includes":
            message = "Add Python Modules"
            wildcard = _pywild
        elif name == "packages":
            message = "Add Python Packages"
            wildcard = _pypackages
        elif name[0:3] == "dll":
            message = "Add Dll/Binary Files"
            wildcard = _dllbinaries
        else:
            if self.MainFrame.recurseSubDirs:
                self.AddDataFiles()
                return                
            message = "Add Data Files"
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
        """ Utility function to handle properly the PyInstaller options. """

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
        dlg = wx.DirDialog(self, "Choose a data files directory:",
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        path = dlg.GetPath()
        fileNames = []
        for root, dirs, files in os.walk(path):
            for name in files:
                fileNames.append(os.path.normpath(os.path.join(root, name)))

        self.AddFiles(fileNames, 3)            
            

    def AddDirectories(self):
        """ Handles the Path and Hooks extensions for PyInstaller. """

        dlg = GUI2ExeDirSelector(self.MainFrame, title="Browse For Folders...")

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
        """ Returns the indices of the selected items in the list control. """

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


    def UpdateProject(self, changeIcon=True):
        """ Updates the project in the database, as something changed. """

        # Translate the list control values to something understandable
        # by the model stored in the database
        values = self.TranslateToProject()
        # Give feedback to the user if something changed (different icon)
        self.GetParent().GiveScreenFeedback(self.GetName(), values, changeIcon)
        

class CustomCodeViewer(wx.Frame):

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

        wx.Frame.__init__(self, parent, title="GUI2Exe Code Viewer", size=(700, 550))

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
            self.saveButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, -1, saveBmp, " Save ")
            self.discardButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, -1, discardBmp, " Discard ")
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
        """ Sets few properties for the frame and the StyledTextCtrl. """

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
            

    def LayoutItems(self, readOnly):
        """ Layout the widgets with sizers. """
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        stcSizer = wx.BoxSizer(wx.HORIZONTAL)
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        if readOnly:
            topLabel = "This is the Setup file as it comes out after the pre-processing\n" \
                       "work done by GUI2Exe."
        else:
            topLabel = "Enter your custom code below and it will be inserted inside the\n" \
                       "Setup script. Note that you can use as 'keywords' also the compiler\n" \
                       "options like data_files, ignores and icon_resources."

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
        """ Binds the events for our CustomCodeViewer. """

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
        question = "The current code has changed.\nDo you want to save changes?"
        answer = self.MainFrame.RunError("Question", question)
        
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

    def __init__(self, parent, readOnly):
        """
        Default class constructor.

        @param readOnly: indicates if the StyledTextCtrl should be in read-only mode

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
    
    def OnUpdateUI(self, evt):
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


    def OnMarginClick(self, evt):
        """ Handles the stc.EVT_STC_MARGINCLICK event for PythonSTC. """
        
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
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

    def __init__(self, parent, project, dll=False):
        """
        Default class constructor.

        @param parent: the parent widget
        @param project: the project as stored in the database
        @param dll: indicates whether we are going to show the missing binary
                    dependencies (dll) or the missing modules (py)

        """
        
        wx.Frame.__init__(self, parent, size=(500, 400))
        
        self.MainFrame = parent
        self.mainPanel = wx.Panel(self)

        # Build column names dinamically depending on the dll value
        name = (dll and ["binarydependencies"] or ["missingmodules"])[0]
        if dll:
            columnNames = ["DLL Name", "DLL Path"]
        else:
            # There might be some strange sub-sub-sub module imported...
            columnNames = ["Main Module", "Sub-Module 1", "Sub-Module 2", "Sub-Module 3"]

        # Build the base list control            
        self.list = BaseListCtrl(self.mainPanel, columnNames, name, self.MainFrame)

        # Build a couple of fancy and useless buttons        
        okBmp = self.MainFrame.CreateBitmap("project_ok")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
        self.okButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, wx.ID_OK, okBmp, " Ok ")
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self.mainPanel, wx.ID_CANCEL, cancelBmp, " Cancel ")

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
        """ Sets few properties for the Py2ExeMissing frame. """        

        if dll:
            # We are showing binary dependencies
            title = "Py2Exe Binary Dependencies"
        else:
            # These are what py2exe thinks are the missing modules
            title = "Py2Exe Missing Modules"
            
        self.SetTitle(title)
        self.SetIcon(self.MainFrame.GetIcon())

        # We want the second column to fill all the available space
        self.list.setResizeColumn(2)    
        self.okButton.SetDefault()


    def LayoutItems(self, dll):
        """ Layouts the widgets with sizers. """        

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        if dll:
            # We are showing binary dependencies
            label = "Make sure you have the license if you distribute any of them, and\n"  \
                    "make sure you don't distribute files belonging to the operating system."
        else:
            # These are what py2exe thinks are the missing modules
            label = "Py2Exe thinks that these modules (and sub-modules) are missing.\n" \
                    "Inclusion of one or more of them may allow your compiled application to run."

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
        

    # ============== #
    # Event handlers #
    # ============== #
    
    def OnOk(self, event):
        """ Handles the wx.EVT_BUTTON event for Py2ExeMissing. """

        # Very useful these buttons, eh?
        self.Destroy()
        event.Skip()


class GUI2ExeDirSelector(wx.Dialog):

    def __init__(self, parent, id=wx.ID_ANY, title="", pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
    
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        self.MainFrame = parent

        self.dirCtrl = wx.GenericDirCtrl(self, size=(300, 200), style=wx.DIRCTRL_3D_INTERNAL|wx.DIRCTRL_DIR_ONLY)
        
        # Build a couple of fancy buttons
        okBmp = self.MainFrame.CreateBitmap("project_ok")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
        self.okButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_OK, okBmp, " Ok ")
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CANCEL, cancelBmp, " Cancel ")
        self.okButton.SetDefault()
        
        self.SetupDirCtrl()
        self.LayoutItems()
        

    def SetupDirCtrl(self):

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
        treeCtrl.SetWindowStyle(treeCtrl.GetWindowStyle() | wx.TR_MULTIPLE)

        executable = os.path.split(sys.executable)[0]            
        self.dirCtrl.ExpandPath(executable)
        self.dirCtrl.SetDefaultPath(executable)
        self.dirCtrl.SetPath(executable)
        

    def LayoutItems(self):

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        staticText = wx.StaticText(self, -1, "Choose one or more folders:")
        staticText.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        
        mainSizer.Add(staticText, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(self.dirCtrl, 1, wx.EXPAND|wx.ALL, 10)

        bottomSizer.Add(self.okButton, 0, wx.ALL, 10)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 10)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        mainSizer.Layout()
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)


    def GetSelectedFolders(self):

        treeCtrl = self.dirCtrl.GetTreeCtrl()
        selections = treeCtrl.GetSelections()

        folders = []

        for select in selections:
            itemText = treeCtrl.GetItemText(select)
            folder = self.RecurseTopDir(select, itemText)
            folders.append(os.path.normpath(folder))

        return folders
    

    def RecurseTopDir(self, item, itemText):

        treeCtrl = self.dirCtrl.GetTreeCtrl()
        parent = treeCtrl.GetItemParent(item)
        if parent != treeCtrl.GetRootItem():            
            itemText = treeCtrl.GetItemText(parent) + "/" + itemText
            itemText = self.RecurseTopDir(parent, itemText)

        return itemText


class PyInfoFrame(wx.Frame):
    """ Base class for PyBusyInfo. """

    def __init__(self, parent, message, useCustom):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, "Busy", wx.DefaultPosition,
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
            panel.Bind(wx.EVT_PAINT, self.OnPaint)
            panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
            
        else:
            text.Centre(wx.BOTH)
            
        self.Centre(wx.BOTH)

        size = self.GetSize()
        bmp = wx.EmptyBitmap(size.x, size.y)
        dc = wx.BufferedDC(None, bmp)
        dc.SetBackground(wx.Brush(wx.Color(0, 0, 0), wx.SOLID))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Color(0, 0, 0), 1))
        dc.DrawRoundedRectangle(0, 0, size.x, size.y, 12)                
        r = wx.RegionFromBitmapColour(bmp, wx.Color(0, 0, 0))
        self.reg = r

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetBusyShape)
        else:
            self.SetBusyShape()
                    
        gui2exe = wx.GetApp().GetTopWindow()
        self._icon = gui2exe.CreateBitmap("GUI2Exe_small")


    def SetBusyShape(self, event=None):

        self.SetShape(self.reg)
        if event:
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

        rect2 = wx.Rect(*rect)
        rect2.height += 20
        dc.DrawLabel(self._message, rect2, alignment=wx.ALIGN_CENTER|wx.ALIGN_CENTER)

        font.SetWeight(wx.BOLD)
        dc.SetFont(font)
        dc.SetPen(wx.Pen(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT)))
        dc.SetTextForeground(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT))
        dc.DrawBitmap(self._icon, 5, 5)
        dc.DrawText("GUI2Exe Busy Message", 26, 5)
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

        pass

                
# -------------------------------------------------------------------- #
# The actual PyBusyInfo implementation
# -------------------------------------------------------------------- #

if wx.Platform == "__WXMAC__":

    class PyBusyInfo(wx.BusyInfo):

        def __init__(self, message, parent=None):

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
        """ Default class constructor. """

        wx.combo.OwnerDrawnComboBox.__init__(self, parent, choices=choices,
                                             style=style, name=name)

        self.MainFrame = wx.GetTopLevelParent(self)
        self.compiler = compiler
        self.option = name

        # Find out the longest element
        lengths = [len(choice) for choice in choices]
        index = lengths.index(max(lengths))
        longestChoice = choices[index]

        choiceWidth, dummy = self.GetTextExtent(longestChoice)
        nameWidth, dummy = self.GetTextExtent(name)
        width = max(choiceWidth, nameWidth) + self.GetButtonSize().x + 35
        self.SetMinSize((width, 22))

        self.BuildImageList()


    def BuildImageList(self):

        images = _comboImages[self.compiler][self.option]
        self.imageList = []
        
        for png in images:
            self.imageList.append(self.MainFrame.CreateBitmap(png))
        
    # Overridden from OwnerDrawnComboBox, called to draw each
    # item in the list
    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            # painting the control, but there is no valid item selected yet
            return

        r = wx.Rect(*rect)  # make a copy
        r.Deflate(3, 5)

        pen = wx.Pen(dc.GetTextForeground(), 1)
        dc.SetPen(pen)

        string = self.GetString(item)
        indx = self.GetItems().index(string)
        bmp = self.imageList[indx]
        y = (r.y+r.height/2-8)
        dc.DrawBitmap(bmp, r.x+3, y, True)
        dc.DrawText(string, r.x + 25, r.y + (r.height/2 - dc.GetCharHeight()/2)-1)
            

    # Overridden from OwnerDrawnComboBox, called for drawing the
    # background area of each item.
    def OnDrawBackground(self, dc, rect, item, flags):
        # If the item is selected, or its item # iseven, or we are painting the
        # combo control itself, then use the default rendering.

        if flags & (wx.combo.ODCB_PAINTING_CONTROL | wx.combo.ODCB_PAINTING_SELECTED):
            wx.combo.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return
        
        string = self.GetString(item)
        # Otherwise, draw every other background with different colour.
        bgCol = wx.WHITE
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        dc.DrawRectangleRect(rect)

        
    # Overridden from OwnerDrawnComboBox, should return the height
    # needed to display an item in the popup, or -1 for default
    def OnMeasureItem(self, item):
        # Simply demonstrate the ability to have variable-height items
        return 19


    # Overridden from OwnerDrawnComboBox.  Callback for item width, or
    # -1 for default/undetermined
    def OnMeasureItemWidth(self, item):

        dc = wx.ClientDC(self)
        string = self.GetString(item)

        return dc.GetTextExtent(string)[0] + 25


class BuildDialog(wx.Dialog):
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

        wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.MainFrame = parent

        header, text = outputText.split("/-/-/")
        self.outputTextCtrl = wx.TextCtrl(self, -1, text.strip(), style=wx.TE_MULTILINE|wx.TE_READONLY)

        saveBmp = self.MainFrame.CreateBitmap("save_to_file")
        clipboardBmp = self.MainFrame.CreateBitmap("copy_to_clipboard")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
            
        self.exportButton = buttons.ThemedGenBitmapTextButton(self, -1, saveBmp, " Save to file... ")
        self.clipboardButton = buttons.ThemedGenBitmapTextButton(self, -1, clipboardBmp, " Export to clipboard ")
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CANCEL, cancelBmp, " Cancel ")

        self.SetProperties()
        self.DoLayout(header, projectName, compiler)

        self.Bind(wx.EVT_BUTTON, self.OnSave, self.exportButton)
        self.Bind(wx.EVT_BUTTON, self.OnClipboard, self.clipboardButton)
        self.CenterOnParent()


    def SetProperties(self):

        self.SetTitle("Full Build Ouput Dialog")
        self.SetIcon(self.GetParent().GetIcon())

        size = self.MainFrame.GetSize()
        self.SetSize((2*size.x/3, 2*size.y/3))


    def DoLayout(self, header, projectName, compiler):

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Build output text for %s (%s):\nBuilt on %s"% \
                              (projectName, compiler, header))
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        mainSizer.Add(label, 0, wx.ALL, 10)
        mainSizer.Add(self.outputTextCtrl, 1, wx.ALL|wx.EXPAND, 10)
        bottomSizer.Add(self.exportButton, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        bottomSizer.Add((5, 0), 0, 0, 0)
        bottomSizer.Add(self.clipboardButton, 0, wx.TOP|wx.BOTTOM, 10)
        bottomSizer.Add((0, 0), 1, 0, 0)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 10)
        mainSizer.Add(bottomSizer, 0, wx.EXPAND, 0)
        self.SetSizer(mainSizer)
        self.Layout()


    def OnSave(self, event):

        # Launch the save dialog        
        dlg = wx.FileDialog(self, message="Save file as ...",
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
            self.MainFrame.SendMessage("Message", "Build output file %s successfully saved"%path)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()
        

    def OnClipboard(self, event):

        self.do = wx.TextDataObject()
        self.do.SetText(self.outputTextCtrl.GetValue())
        
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(self.do)
            wx.TheClipboard.Close()
            self.MainFrame.SendMessage("Message", "Build output text successfully copied to the clipboard")
        else:
            self.MainFrame.RunError("Error", "Unable to open the clipboard.")


class TransientPopup(wx.PopupWindow):
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
        self.panel = wx.Panel(self, -1)

        self.MainFrame = parent.MainFrame
        self.bmp = self.MainFrame.CreateBitmap("GUI2Exe_small")
        self.option = option
        self.tip = tip.capitalize()
        self.note = note
        self.compiler = compiler

        if note:
            self.warnbmp = self.MainFrame.CreateBitmap("note")
            self.note.capitalize()
        
        dc = wx.ClientDC(self)
        self.bigfont = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        self.boldfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, True)
        self.normalfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False)
        self.slantfont = wx.Font(8, wx.SWISS, wx.FONTSTYLE_ITALIC, wx.NORMAL, False)
        dc.SetFont(self.bigfont)
        width1, height1 = dc.GetTextExtent("GUI2Exe Help Tip (%s)"%compiler)
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

        size = wx.Size(fullwidth, fullheight)
        self.panel.SetSize(size)
        self.SetSize(size)
        self.panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.DropShadow()

        self.AdjustPosition(size)        
        self.Show()        
        

    def OnPaint(self, event):
        """ Draw the full TransientPopup. """

        dc = wx.PaintDC(self.panel)
        rect = self.panel.GetClientRect()

        # Fill the background with a gradient shading
        startColour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        endColour = wx.WHITE

        dc.GradientFillLinear(rect, startColour, endColour, wx.SOUTH)
        
        dc.DrawBitmap(self.bmp, 5, 5)
        dc.SetFont(self.bigfont)
        dc.SetTextForeground(wx.SystemSettings_GetColour(wx.SYS_COLOUR_CAPTIONTEXT))

        width, height = dc.GetTextExtent("GUI2Exe Help Tip")
        ypos = 13 - height/2
        dc.DrawBitmap(self.bmp, 5, ypos)
        dc.DrawText("GUI2Exe Help Tip (%s)"%self.compiler, 26, ypos)

        newYpos = ypos + height + 6
        dc.SetPen(wx.GREY_PEN)
        dc.DrawLine(rect.x+5, newYpos, rect.width-5, newYpos)

        newYpos += 5        

        dc.SetFont(self.boldfont)
        dc.SetTextForeground(wx.BLACK)
        
        width2, height2, dummy = dc.GetMultiLineTextExtent(self.option)
        textRect = wx.Rect(10, newYpos, width2, height2)
        dc.DrawLabel(self.option, textRect)

        newYpos += height2 + 6
        
        dc.SetFont(self.normalfont)
        width3, height3, dummy = dc.GetMultiLineTextExtent(self.tip)
        textRect = wx.Rect(10, newYpos, width3, height3)
        dc.DrawLabel(self.tip, textRect)

        newYpos += height3 + 6
        if not self.note:
            dc.DrawLine(rect.x+10, newYpos, rect.width-10, newYpos)
            return

        dc.SetFont(self.slantfont)        
        width4, height4, dummy = dc.GetMultiLineTextExtent(self.note)
        textRect = wx.Rect(26, newYpos, width4, height4)
        dc.DrawBitmap(self.warnbmp, 5, newYpos+height4/2-8)
        dc.DrawLabel(self.note, textRect)
        newYpos += height4 + 6
        dc.DrawLine(rect.x+5, newYpos, rect.width-5, newYpos)
        

    def AdjustPosition(self, size):
        """
        Adjust the position of TransientPopup accordingly to the TransientPopup
        size, mouse position and screen geometry.
        """

        XMousePos, YMousePos = wx.GetMousePosition()
        XScreen, YScreen = wx.GetDisplaySize()

        if XMousePos + size.x > XScreen:
            if YMousePos + size.y > YScreen:
                xPos, yPos = XMousePos - size.x, YMousePos - size.y
            else:
                xPos, yPos = XMousePos - size.x, YMousePos
        else:
            if YMousePos + size.y > YScreen:
                xPos, yPos = XMousePos, YMousePos - size.y
            else:
                xPos, yPos = XMousePos, YMousePos
            
        self.SetPosition((xPos, yPos))


    def OnEraseBackground(self, event):
        pass
    

    def OnMouseLeftDown(self, event):

        self.Show(False)
        self.Destroy()


    def DropShadow(self, drop=True):
        """ Adds a shadow under the window (Windows Only). """

        if not _libimported:
            return
        
        if wx.Platform != "__WXMSW__":
            return

        hwnd = self.GetHandle()

        size = self.GetSize()
        rgn = win32gui.CreateRoundRectRgn(0, 0, size.x, size.y, 9, 9)
        win32gui.SetWindowRgn(hwnd, rgn, True)
        
        CS_DROPSHADOW = 0x00020000
                
        if not hasattr(self, "_winlib"):
            self._winlib = win32api.LoadLibrary("user32")
        
        csstyle = win32api.GetWindowLong(hwnd, win32con.GCL_STYLE)
        if csstyle & CS_DROPSHADOW:
            return
        else:
            csstyle |= CS_DROPSHADOW     #Nothing to be done
                
        GCL_STYLE= -26
        cstyle= win32gui.GetClassLong(hwnd, GCL_STYLE)
        if cstyle & CS_DROPSHADOW == 0:
            win32api.SetClassLong(hwnd, GCL_STYLE, cstyle | CS_DROPSHADOW)

        

class PListEditor(wx.Dialog):
    """ A simple PList editor for GUI2Exe (py2app only). """

    def __init__(self, parent, CFBundleExecutable, pListFile=None, pListCode={}):
        """
        Default class constructor.

        @param parent: the dialog parent;
        @param CFBundleExecutable: the program name;
        @param pListFile: a PList file, if any, to be merged with pListCode;
        @param pListCode: the existing PList code (if any).
        """

        wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.MainFrame = parent
        
        PFile = {}
        if pListFile:
            # We got a file from the user
            PFile = plistlib.readPlist(pListFile)
            
        PTemplate = plist_template.infoPlistDict(CFBundleExecutable, pListCode)
        for key in PFile.keys():
            if key not in PTemplate:
                PTemplate[key] = PFile[key]

        self.treeList = gizmos.TreeListCtrl(self, -1, style=wx.TR_DEFAULT_STYLE | wx.TR_ROW_LINES |
                                            wx.TR_COLUMN_LINES | wx.TR_FULL_ROW_HIGHLIGHT)

        # Build a couple of fancy and useless buttons        
        okBmp = self.MainFrame.CreateBitmap("project_ok")
        cancelBmp = self.MainFrame.CreateBitmap("exit")
        self.okButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_OK, okBmp, " Ok ")
        self.cancelButton = buttons.ThemedGenBitmapTextButton(self, wx.ID_CANCEL, cancelBmp, " Cancel ")

        # Do the hard work        
        self.SetProperties()
        self.LayoutItems()
        self.BuildImageList()
        self.PopulateTree(PTemplate)

        size = self.MainFrame.GetSize()
        self.SetSize((size.x/2, size.y/2))

        self.CenterOnParent()
        self.Show()

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets few properties for the dialog. """        

        self.SetTitle("Simple PList editor for py2app")
        self.SetIcon(self.MainFrame.GetIcon())
        self.okButton.SetDefault()


    def LayoutItems(self):
        """ Layouts the widgets with sizers. """        

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        label = "You can edit the properties below or add new ones:"

        label = wx.StaticText(self, -1, label)
        label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

        mainSizer.Add(label, 0, wx.ALL, 10)
        mainSizer.Add(self.treeList, 1, wx.EXPAND|wx.ALL, 5)

        # Add the fancy and useless buttons
        bottomSizer.Add(self.okButton, 0, wx.ALL, 15)
        bottomSizer.Add((0, 0), 1, wx.EXPAND)
        bottomSizer.Add(self.cancelButton, 0, wx.ALL, 15)

        mainSizer.Add(bottomSizer, 0, wx.EXPAND)
        # Add everything to the main sizer        
        self.SetSizer(mainSizer)
        mainSizer.Layout()


    def BuildImageList(self):
        """ Builds the image list for the tree list control. """
        
        images = ["home"] + [str(i) for i in xrange(1, 6)] + ["mac"]
        imgList = wx.ImageList(16, 16)
        
        for png in images:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        self.treeList.AssignImageList(imgList)            


    def PopulateTree(self, PTemplate):
        """ Populates the tree list control using the PList dictionary. """

        self.treeList.AddColumn("Property List ")
        self.treeList.AddColumn("Class          ", flag=wx.ALIGN_CENTER)
        self.treeList.AddColumn("Value", edit=True)
        
        self.treeList.SetMainColumn(0) # the one with the tree in it...
        self.root = self.treeList.AddRoot("Root", 0)

        self.itemCounter = 1
        self.AutoAddChildren(self.root, PTemplate, 0)
        self.treeList.SortChildren(self.root)
        self.treeList.SetItemText(self.root, "Dictionary", 1)
        self.treeList.SetItemText(self.root, "%d key/value pairs"%len(PTemplate.keys()), 2)

        boldFont = self.GetFont()
        pointSize = boldFont.GetPointSize()
        boldFont.SetWeight(wx.BOLD)
        boldFont.SetPointSize(pointSize+2)
        self.treeList.SetItemFont(self.root, boldFont)
        
        self.treeList.ExpandAll(self.root)
        colWidth, dummy = self.CalculateColumnWidth(self.root, 0)
        self.treeList.SetColumnWidth(0, colWidth)
        self.treeList.SetColumnWidth(2, 300)
        
        self.treeList.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnLabelEdit)
        
        del self.itemCounter


    def AutoAddChildren(self, itemParent, PTemplate, level):
        """ Recursively adds children to the tree item. """

        white, blue = wx.WHITE, wx.Colour(234, 242, 255)
        boldFont = self.GetFont()
        boldFont.SetWeight(wx.BOLD)
        treeList = self.treeList

        keys = PTemplate.keys()
        keys.sort()
        for item in keys:
            child = treeList.AppendItem(itemParent, item, level+1)
            colour = (self.itemCounter%2 == 0 and [white] or [blue])[0]
            treeList.SetItemBackgroundColour(child, colour)
            self.itemCounter += 1
            if isinstance(PTemplate[item], dict):
                treeList.SetItemText(child, "Dictionary", 1)
                treeList.SetItemText(child, "%d key/value pairs"%len(PTemplate[item].keys()), 2)
                treeList.SetItemFont(child, boldFont)
                level = self.AutoAddChildren(child, PTemplate[item], level+1)
            else:
                treeList.SetItemImage(child, level+1)
                value = PTemplate[item]
                if isinstance(value, list):
                    kind = "Array"
                else:
                    kind = "String"

                treeList.SetItemText(child, kind, 1)                    
                treeList.SetItemText(child, str(value), 2)
                treeList.SetItemImage(child, 6, 2)
                treeList.SetPyData(child, kind)
                
        return level
    

    def CalculateColumnWidth(self, item, colWidth, level=1):
        """ Calculates the correct column widths for the tree list control columns. """

        treeList = self.treeList
        child, cookie = treeList.GetFirstChild(self.root)
        
        while child.IsOk():
            if treeList.HasChildren(child):
                colWidths, level = self.CalculateColumnWidth(child, colWidth, level+1)

            rect = treeList.GetBoundingRect(child)
            colWidth = max(colWidth, rect.width + 40*level+16)
            child, cookie = treeList.GetNextChild(item, cookie)
            
        return colWidth, level
            
                
    # ============== #
    # Event handlers #
    # ============== #


    def OnLabelEdit(self, event):
        """ Handles the wx.EVT_TREE_BEGIN_LABEL_EDIT event for the tree list control. """

        item = event.GetItem()
        if self.treeList.HasChildren(item):
            # No no, you can't edit items with children
            event.Veto()
            return

        event.Skip()

    
    def GetPList(self, item=None, PList={}):
        """ Returns the newly edited PList as a dictionary. """

        if item is None:
            item = self.root
            PList = dict()

        treeList = self.treeList        
        child, cookie = treeList.GetFirstChild(item)
        while child.IsOk():
            key = treeList.GetItemText(child)
            value = treeList.GetItemText(child, 2)
            kind = treeList.GetPyData(child)
            if treeList.HasChildren(child):
                PList[key] = {}
                PList[key] = self.GetPList(child, PList[key])
            else:
                if kind == "String":
                    PList[key] = value
                else:
                    PList[key] = eval(value)

            child, cookie = treeList.GetNextChild(item, cookie)        

        return PList

    
            
                