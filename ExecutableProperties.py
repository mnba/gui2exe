# Start the imports
import wx
import sys

import wx.lib.mixins.listctrl as listmix

from Utilities import GetExecutableData
from Constants import _sizeIcons, _bookIcons, _defaultCompilers


class ExecutableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):

    def __init__(self, parent):

        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.SUNKEN_BORDER)
        # Initialize the auto width mixin. We always need it        
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        
class ExecutableProperties(wx.Panel):

    def __init__(self, parent):
        """
        Default class constructor.

        @param parent: the parent widget

        """
        
        wx.Panel.__init__(self, parent)

        self.MainFrame = wx.GetTopLevelParent(self)
        self.listCtrl = ExecutableListCtrl(self)
        
        # Layout the listctrl
        self.DoLayout()
        # Insert the columns in the listctrl
        self.InsertColumns()
        self.BuildImageList()

        # Blank out all the executable information
        self.PopulateList(blank=True)
        self.listCtrl.setResizeColumn(1)
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #

    def DoLayout(self):
        """ Layouts the widgets in the panel. """

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.listCtrl, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

    
    def InsertColumns(self):
        """ Inserts the columns in the list control. """

        columnNames = ["Builder", "Size (MB)   ", "Files     "]
        # Loop over all the column names        
        for indx, column in enumerate(columnNames):
            self.listCtrl.InsertColumn(indx, column)
            if indx > 0:
                self.listCtrl.SetColumnWidth(indx, wx.LIST_AUTOSIZE_USEHEADER)


    def BuildImageList(self):
        """ Build the image list for the list control. """

        imgList = wx.ImageList(16, 16)
        for png in _sizeIcons:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        self.listCtrl.AssignImageList(imgList, wx.IMAGE_LIST_SMALL)


    def PopulateList(self, blank=False, project=None):
        """ Adds executable information to the listCtrl. """

        numFiles, fileSizes = [""]*5, [""]*5

        if project:
            # Get information about the executable file
            for indx, compiler in enumerate(_defaultCompilers):
                if compiler in project:
                    numFiles[indx], fileSizes[indx]= GetExecutableData(project, compiler)
                
        self.listCtrl.DeleteAllItems()
        for indx, names in enumerate(_bookIcons):
            idx = self.listCtrl.InsertImageStringItem(sys.maxint, names, indx)
            self.listCtrl.SetStringItem(idx, 1, fileSizes[indx], 5)
            self.listCtrl.SetStringItem(idx, 2, numFiles[indx], 6)
                    
            
            
        