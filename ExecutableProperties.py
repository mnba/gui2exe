########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

# Start the imports
import wx
import sys

import wx.lib.mixins.listctrl as listmix

from Utilities import GetExecutableData
from Constants import _sizeIcons, _bookIcons, _defaultCompilers

# Get the I18N things
_ = wx.GetTranslation


class ExecutableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    """ Simple base class which holds a list control and a mixin. """

    def __init__(self, parent):
        """
        Default class constructor.

        
        **Parameters:**

        * parent: the list control parent widget.
        """

        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.SUNKEN_BORDER)
        # Initialize the auto width mixin. We always need it        
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        
class ExecutableProperties(wx.Panel):
    """
    A small panel in the lower left corner of the main GUI, which holds information
    about the executable size/executable folder size and number of files generated
    in the building process.
    """

    def __init__(self, parent):
        """
        Default class constructor.

        
        **Parameters:**

        * parent: the parent widget.

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

        # That's an easy layout...
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.listCtrl, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)

    
    def InsertColumns(self):
        """ Inserts the columns in the list control. """

        columnNames = [_("Builder"), _("Size (MB)   "), _("Files     ")]
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

        # Assign the imagelist to the list control, so we don't keep
        # a reference of it around
        self.listCtrl.AssignImageList(imgList, wx.IMAGE_LIST_SMALL)


    def PopulateList(self, blank=False, project=None):
        """
        Adds executable information to the listCtrl.

        
        **Parameters:**

        * blank: whether to clear the list control or not;
        * project: the project from where to get all the data.
        """

        numFiles, fileSizes = [""]*5, [""]*5

        if project:
            # Get information about the executable file
            for indx, compiler in enumerate(_defaultCompilers):
                if compiler in project:
                    numFiles[indx], fileSizes[indx]= GetExecutableData(project, compiler)

        # Clear all the items in the list control                
        self.listCtrl.DeleteAllItems()
        # Add all the executable information we have
        for indx, names in enumerate(_bookIcons):
            idx = self.listCtrl.InsertImageStringItem(sys.maxint, names, indx)
            self.listCtrl.SetStringItem(idx, 1, fileSizes[indx], 5)
            self.listCtrl.SetStringItem(idx, 2, numFiles[indx], 6)
                    
            
