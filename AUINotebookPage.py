# Start the imports
import wx

import LabelBook as LB
from Py2ExePanel import Py2ExePanel
from cx_FreezePanel import cx_FreezePanel
from bbFreezePanel import bbFreezePanel
from PyInstallerPanel import PyInstallerPanel
from Py2AppPanel import Py2AppPanel

from NotImplementedOrMissingPanel import NotImplementedOrMissingPanel

from Utilities import opj
from Constants import _lbStyle, _bookIcons, _defaultCompilers


class AUINotebookPage(LB.FlatImageBook):

    def __init__(self, parent, project, compilers):
        """
        Default class constructor.

        @param parent: the parent widget
        @param project: the project associated to this book
        @param compilers: the available compilers on this machine

        """        

        # Initialize the custom FlatImageBook
        LB.FlatImageBook.__init__(self, parent, style=_lbStyle)

        self.MainFrame = wx.GetTopLevelParent(self)

        # Build the image list and add the pages to it
        self.BuildImageList()
        self.CreateBookPages(project, compilers)
        self.Bind(LB.EVT_IMAGENOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


    def BuildImageList(self):
        """ Builds the image list for FlatImageBook. """

        imgList = wx.ImageList(32, 32)
        # Maybe the icons are not that nice...
        for png in _bookIcons:
            imgList.Add(self.MainFrame.CreateBitmap(png))

        # Assign the image list to the book
        self.AssignImageList(imgList)


    def CreateBookPages(self, project, compilers):
        """ Creates the FlatImageBook pages. """

        # Loop over all the icons we have (4 at the moment)
        for ii, png in enumerate(_bookIcons):
            if ii == 0:
                # Is a py2exe
                page = Py2ExePanel(self, project.GetName(), project.GetCreationDate())
            elif ii == 2:
                # Is a cx_Freeze
                page = cx_FreezePanel(self, project.GetName(), project.GetCreationDate())
            elif ii == 3:
                # Is a PyInstaller
                page = PyInstallerPanel(self, project.GetName(), project.GetCreationDate())
            elif ii == 4:
                # Is a bbFreeze
                page = bbFreezePanel(self, project.GetName(), project.GetCreationDate())
            else:
                # No work dne on other compilers
                page = Py2AppPanel(self, project.GetName(), project.GetCreationDate())

            # Add the page to FlatImageBook            
            self.AddPage(page, png, imageId=ii)

        # Select the first page, py2exe
        self.SetSelection(0)
        for indx in xrange(self.GetPageCount()):
            page = self.GetPage(indx)
            page.BindToolTips()

        
    def SetTreeItem(self, treeItem):
        """ Stores the tree item associated with us. """

        self.treeItem = treeItem


    def GetTreeItem(self):
        """ Retrieves the tree item associated with us. """

        return self.treeItem


    def SetProject(self, project):
        """ Stores the project associated with us. """

        self.project = project

        # Loop over all the compilers and populate the pages
        for indx, compiler in enumerate(_defaultCompilers):
            page = self.GetPage(indx)
            if compiler in project:
                page.SetConfiguration(project[compiler])
            elif not isinstance(page, NotImplementedOrMissingPanel):
                defaultConfig = self.MainFrame.GetDefaultConfiguration(compiler)
                page.SetConfiguration(defaultConfig)
                project.SetConfiguration(compiler, defaultConfig)


    def GetProject(self):
        """ Retrieves the project associated with us. """

        return self.project


    def OnPageChanged(self, event):
        """ Handles the wx.EVT_NOTEBOOK_PAGE_CHANGED for Labelbook. """

        if not self.MainFrame.process:
            # Disable the dry-run button if not using py2exe
            self.MainFrame.messageWindow.EnableDryRun(self)


