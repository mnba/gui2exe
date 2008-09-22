# Start the imports
import wx
import time
import wx.lib.customtreectrl as CT

from Widgets import PyBusyInfo
from Utilities import opj
from Constants import _treeIcons


class ProjectTreeCtrl(CT.CustomTreeCtrl):

    def __init__(self, parent):
        """ Default class constructor. """

        CT.CustomTreeCtrl.__init__(self, parent, style=wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_EDIT_LABELS
                                   |wx.TR_MULTIPLE|wx.TR_HAS_VARIABLE_ROW_HEIGHT)

        # Remember our main frame (GUI2Exe application window)
        self.MainFrame = wx.GetTopLevelParent(self)
        self.popupIds = [wx.NewId() for i in xrange(6)]
        # A flag to monitor if we are in dragging mode or not
        self.isDragging = False

        # Build all the tree control
        self.BuildImageList()
        self.SetProperties()
        self.BindEvents()

        # Add a root: if someone has a fancier name for the roor item, let me know :-D
        self.rootItem = self.AddRoot("My Projects", image=0)
        # Make it bigger, so it is clear that it is a root item
        self.SetItemFont(self.rootItem, wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, False))

        # Store a particular font, we are going to use it later
        self.boldFont = self.GetFont()
        self.boldFont.SetWeight(wx.FONTWEIGHT_BOLD)


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def BuildImageList(self):
        """ Builds the image list for the tree control. """

        imgList = wx.ImageList(16, 16)
        for png in _treeIcons:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        self.AssignImageList(imgList)
        

    def SetProperties(self):
        """ Sets few properties of the tree control (enable the Vista selection). """
        
        self.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        self.EnableSelectionVista(True)


    def BindEvents(self):
        """ Bind all the events we need to the tree control. """

        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnBeginDrag)
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.Bind(wx.EVT_TREE_DELETE_ITEM, self.OnDeleteItem)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnLoadProject)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.OnKeyDown)
        # Bind all the popup menu events with a single handler
        self.Bind(wx.EVT_MENU_RANGE, self.OnPopupMenu, id=self.popupIds[0],
                  id2=self.popupIds[-1])


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnBeginEdit(self, event):
        """ Handles the wx.EVT_TREE_BEGIN_LABEL_EDIT event for the tree control. """

        if event.GetItem() == self.rootItem:
            # You can't edit the root item, no way
            event.Veto()
            return

        self.oldProjectName = self.GetItemText(event.GetItem())        
        event.Skip()


    def OnEndEdit(self, event):
        """ Handles the wx.EVT_TREE_END_LABEL_EDIT event for the tree control. """

        if event.IsEditCancelled():
            # Nothing changes, user pressed ESC or similar
            return

        projectName = event.GetLabel()
        if not self.CheckProjectName(projectName, True):
            # Check if the project already exists
            event.Veto()
            return

        treeItem = event.GetItem()
        # Rename the project, sending it to the main frame that will call
        # the database and update the information on screen
        self.MainFrame.RenameProject(treeItem, self.oldProjectName, projectName)
        # Store the new project name in the tree data
        self.SetPyData(treeItem, projectName)
        event.Skip()


    def OnBeginDrag(self, event):
        """ Handles the wx.EVT_TREE_BEGIN_DRAG event for the tree control. """

        if event.GetItem() == self.rootItem:
            # You can't drag the root
            event.Veto()
            return

        # Store the selected items, we are going to need them in the OnEndDrag
        self.draggedItems = self.GetSelections()
        # Explicitely allow the event (it's a no-op)
        event.Allow() 


    def OnEndDrag(self, event):
        """ Handles the wx.EVT_TREE_END_DRAG event for the tree control. """

        # Get the item we have been dropped on
        droppedItem = event.GetItem()
        if droppedItem in self.draggedItems:
            # No way, we have been dropped in a dragged item (!)
            return

        # Reverse them, to insert them in the correct order
        self.draggedItems.reverse()

        # Look if we have been dragged over the root item or not
        appendToRoot = (droppedItem==self.rootItem and [True] or [False])[0]
        # Reposition the items as the user chose
        self.RepositionItems(appendToRoot, droppedItem)
                
        event.Skip()


    def OnDeleteItem(self, event):
        """ Handles the wx.EVT_TREE_DELETE_ITEM event for the tree control. """

        if self.isDragging:
            # We are in drag 'n' drop mode, don't do anything
            event.Skip()
            return
        
        treeItem = event.GetItem()
        # Delete the project from tha database
        itemText = self.GetItemText(treeItem)
        self.MainFrame.dataBase.DeleteProject(itemText)

        # Delete the page in the center pane (if it exists)
        wx.CallAfter(self.MainFrame.CloseAssociatedPage, treeItem)
        event.Skip()


    def OnLoadProject(self, event):
        """ Handles the wx.EVT_TREE_ITEM_ACTIVATED event for the tree control. """

        treeItem = event.GetItem()
        if treeItem == self.rootItem:
            # The root item can't be loaded
            return

        # Load the project in another method, I need it also elsewhere
        # The input must be a list as the tree control has the wx.TR_MULTIPLE
        # style and multiple projects can be loaded in one go
        self.LoadProject([treeItem])
        event.Skip()


    def OnRightClick(self, event):
        """ Handles the wx.EVT_TREE_ITEM_RIGHT_CLICK event for the tree control. """

        item = event.GetItem()
        if not item:
            # No item selected
            return

        selections = self.GetSelections()
        if len(selections) > 1 and self.rootItem in selections:
            # The user chose a mix of children plus the root item
            # Don't do anything, as there are no actions to do
            return

        menu = wx.Menu()
        
        if item == self.rootItem:

            # The user clicked on the root item
            # There are a couple of options here: either add a new project or
            # delete all the existing projects from the tree
            item = wx.MenuItem(menu, self.popupIds[0], "New project...")
            bmp = self.MainFrame.CreateBitmap("project")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            item = wx.MenuItem(menu, self.popupIds[1], "Delete all projects")
            bmp = self.MainFrame.CreateBitmap("delete_all")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            item.Enable(self.HasChildren(self.rootItem))

        else:

            self.selectedItem = item
            
            # The user clicked on one of children (the project)
            # There are a couple of options here: either load the selected projects or
            # delete them
            item = wx.MenuItem(menu, self.popupIds[2], "Load project(s)")
            bmp = self.MainFrame.CreateBitmap("load_project")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            item = wx.MenuItem(menu, self.popupIds[3], "Edit project name")
            bmp = self.MainFrame.CreateBitmap("project_edit")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            menu.AppendSeparator()
            item = wx.MenuItem(menu, self.popupIds[4], "Delete project(s)")
            bmp = self.MainFrame.CreateBitmap("delete_project")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            menu.AppendSeparator()
            item = wx.MenuItem(menu, self.popupIds[5], "Import from file...")
            bmp = self.MainFrame.CreateBitmap("importproject")
            item.SetBitmap(bmp)
            menu.AppendItem(item)
            item.Enable(len(selections) == 1)

        # Pop up the menu on ourselves
        self.PopupMenu(menu)
        menu.Destroy()

        event.Skip()


    def OnKeyDown(self, event):
        """ Handles the wx.EVT_KEY_DOWN event for the tree control. """

        if event.GetKeyCode() == wx.WXK_DELETE:
            # Get all the selected items in the tree
            selections = self.GetSelections()
            if not selections:
                return
            msg = "Are you sure you want to delete the selected projects from your database?"
            answer = self.MainFrame.RunError("Question", msg)
            if answer != wx.ID_YES:
                # No, user doesn't want to do that
                return
            # Delete the selected items
            self.DeleteProject(selections)
            
        event.Skip()


    def OnPopupMenu(self, event):
        """ Handles the wx.EVT_MENU_RANGE event for the tree control. """

        # Retrieve all the selected items
        selections = self.GetSelections()
        
        if event.GetId() == self.popupIds[0]:
            # The user wants to add a new project
            self.NewProject()
        elif event.GetId() == self.popupIds[1]:
            # User wants to delete all the children projects
            msg = "Are you sure you want to delete all the projects from your database?"
            answer = self.MainFrame.RunError("Question", msg)
            if answer != wx.ID_YES:
                # No, user doesn't want to do that
                return
            # Delete all the children of our tree
            self.DeleteChildren(self.rootItem)
        elif event.GetId() == self.popupIds[2]:
            # The user wants to load the selected project(s)
            self.LoadProject(selections)
        elif event.GetId() == self.popupIds[3]:
            # User wants to edit a project name
            self.EditLabel(selections[0])
        elif event.GetId() == self.popupIds[4]:
            # The user wants to delete all the selected project(s)
            msg = "Are you sure you want to delete the selected projects from your database?"
            answer = self.MainFrame.RunError("Question", msg)
            if answer != wx.ID_YES:
                # No, user doesn't want to do that
                return
            # Delete the selected items
            self.DeleteProject(selections)
        else:
            # The user wants to import a project from file
            self.LoadFromFile()
            
            
    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def LoadProject(self, treeItems):
        """ Actually loads the project, calling the main frame method. """

        busy = PyBusyInfo("Loading project(s) from database...")
        wx.SafeYield()
        
        # Freeze the main frame. It speeds up a bit the drawing
        self.MainFrame.Freeze()

        for item in treeItems:
            # Load one project at a time
            self.MainFrame.LoadProject(item, self.GetItemText(item))
            # Set the item state as "in editing"
            self.SetItemEditing(item, True)

        # Time to warm up...
        self.MainFrame.Thaw()
        del busy

        
    def NewProject(self):
        """ Creates a new project, appending a new item to the tree control. """

        # Generate a unique project name, not conflicting with the existing ones
        uniqueName = self.GetUniqueProjectName()
        # Ask the user to enter a project name
        dlg = wx.TextEntryDialog(self.MainFrame, "Enter a name for the new project:", "New project")
        dlg.SetValue(uniqueName)
        
        if dlg.ShowModal() != wx.ID_OK:
            # Do you want to think about it, eh?
            return

        projectName = dlg.GetValue()
        dlg.Destroy()

        if not self.CheckProjectName(projectName):
            # The selected project name already exists!
            return

        # Go with the new project
        treeItem = self.AppendItem(self.rootItem, projectName, image=2)
        self.MainFrame.AddNewProject(treeItem, projectName)

        # Expand all the root item children, if it's needed
        self.ExpandAll()


    def DeleteProject(self, treeItems):
        """ Auxiliary called by external modules. """

        # Freeze the main frame... it helps with flicker
        self.MainFrame.Freeze()

        # Store the items
        existingItems = []
        child, cookie = self.GetFirstChild(self.rootItem)
        if child:
            existingItems = [child]

        # Loop over all the tree items
        while child:            
            child, cookie = self.GetNextChild(self.rootItem, cookie)
            existingItems.append(child)
        
        # Loop over all the passed items
        for item in treeItems:
            if item in existingItems:
                # Delete the item. Its event handles will take care of everything
                self.Delete(item)

        # Time to warm up...
        self.MainFrame.Thaw()


    def CheckProjectName(self, projectName, usePyData=False):
        """ Checks if a project is valid and it doesn't already exists in the tree control. """

        if not projectName.strip():
            # Project name is empty?
            self.MainFrame.RunError("Error", "Invalid project name (empty string).")
            return False

        if self.IsProjectExisting(projectName, usePyData):
            # This project already exists
            self.MainFrame.RunError("Error", "The project name you chose already exists.")
            return False

        # Project name valid!
        return True
        

    def GetUniqueProjectName(self):
        """ Generates an unique project name, not conflicting with the existing ones. """

        # Start with a default project name
        startName = "GUI2Exe Project"
        trialName = startName
        count = 1
        
        # Loop until an unique project name is found
        while self.IsProjectExisting(trialName):
            trialName = startName + " (%d)"%count
            count += 1

        return trialName


    def IsProjectExisting(self, projectName, usePyData=False):
        """ Checks if a project with the given name already exists. """
        
        child, cookie = self.GetFirstChild(self.rootItem)
        while child:
            itemText = (usePyData and [self.GetPyData(child)] or [self.GetItemText(child)])[0]
            if itemText == projectName:
                # It exists, kick the value
                return True
            child, cookie = self.GetNextChild(self.rootItem, cookie)

        # The project name is unique
        return False


    def SortItems(self):
        """ Sorts the tree items using the projects' creation dates. """

        self.SortChildren(self.rootItem)
        

    def OnCompareItems(self, item1, item2):
        """ Re-implemented from CT.CustomTreeCtrl. """

        database = self.MainFrame.dataBase
        key1, key2 = item1.GetData(), item2.GetData()
        node1, node2 = database.LoadProject(key1), database.LoadProject(key2)

        creationDate1 = time.strptime(node1.creationDate, "%d %B %Y @ %H:%M:%S")
        creationDate2 = time.strptime(node2.creationDate, "%d %B %Y @ %H:%M:%S")
        
        if creationDate1 < creationDate2:
            return -1
        elif creationDate1 == creationDate2:
            return 0
        else:
            return 1        

    
    def PopulateTree(self, dbKeys):
        """ Populates the tree with the keys coming from the database. """

        # Freeze all... it helps with flicker
        self.Freeze()

        # Append the items to the tree
        for key in dbKeys:
            treeItem = self.AppendItem(self.rootItem, key.encode(), image=1)
            self.SetPyData(treeItem, key)

        # Expand the root item
        self.ExpandAll()
        # Time to warm up...
        self.Thaw()


    def SetItemEditing(self, treeItem, editState):
        """ Sets the state of a particular item as "in editing" or not. """

        # Change item image depending on the state
        itemImage = (editState and [2] or [1])[0]
        # Assign the image to the tree item
        self.SetItemImage(treeItem, itemImage)
        # Refresh the tree item line
        self.RefreshLine(treeItem)


    def HighlightItem(self, treeItem, highlight):

        # Change item font depending on the highlight
        font = (highlight and [self.boldFont] or [self.GetFont()])[0]
        # Assign the font to the item
        self.SetItemFont(treeItem, font)


    def RepositionItems(self, appendToRoot, droppedItem):
        """ Repositions the items after a drag and drop operation. """

        # I need this flag to avoid the call to OnDeleteItem
        self.isDragging = True
        
        for oldItem in self.draggedItems:
            if appendToRoot:
                # We have been dragged over the root item
                newItem = self.PrependItem(self.rootItem, oldItem.GetText(),
                                           image=oldItem.GetImage(), data=oldItem.GetData())
            else:
                # We have been dragged over another child
                newItem = self.InsertItem(self.rootItem, droppedItem, oldItem.GetText(),
                                          image=oldItem.GetImage(), data=oldItem.GetData())

            # Reassign the new item to the main wx.aui.AuiNotebook page (if any)                            
            self.MainFrame.ReassignPageItem(oldItem, newItem)
            # Delete the old item
            self.Delete(oldItem)

        self.isDragging = False


    def LoadFromFile(self):
        """ Load a project from a file. """

        fileName = self.GetItemText(self.selectedItem)

        dlg = wx.FileDialog(self, message="Please select a GUI2Exe project file...",
                            defaultFile=fileName, wildcard="All files (*.*)|*.*",
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        dlg.CenterOnParent()
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()            
        else:
            # Destroy the dialog. Don't do this until you are done with it!
            # BAD things can happen otherwise!
            dlg.Destroy()
            return

        fid = open(path, "r")
        strs = fid.read()
        fid.close()

        try:
            project = self.MainFrame.dataBase.LoadProject(fileName)
        except:
            self.MainFrame.RunError("Error", "This project has not been saved yet. Please save it and retry.")
            return

        try:
            code = compile(strs, "__dummy__.txt", 'single')
            glbs, lcls = {}, {}
            exec code in glbs, lcls
            projectDict = lcls["projectDict"]
        except:
            self.MainFrame.RunError("Error", "Invalid or corrupted project file.")
            return

        busy = PyBusyInfo("Updating project from file...")
        wx.SafeYield()

        # Set the configurations for every compiler    
        for keys, values in projectDict.items():
            project.SetConfiguration(keys, values)

        self.MainFrame.dataBase.SaveProject(project)
        self.MainFrame.ResetConfigurations(self.selectedItem, project)
            
        del busy
        wx.SafeYield()

        