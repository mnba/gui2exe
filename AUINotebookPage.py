# Start the imports
import wx

import LabelBook as LB

# Import all our executable-builders panels
from Py2ExePanel import Py2ExePanel
from cx_FreezePanel import cx_FreezePanel
from bbFreezePanel import bbFreezePanel
from PyInstallerPanel import PyInstallerPanel
from Py2AppPanel import Py2AppPanel

from Constants import _lbStyle, _bookIcons, _defaultCompilers


class AUINotebookPage(LB.FlatImageBook):

    def __init__(self, parent, project, compilers):
        """
        Default class constructor.

        
        **Parameters:**

        * parent: the parent widget;
        * project: the project associated to this book;
        * compilers: the available compilers on this machine.
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
        bmpC, bmpP = self.MainFrame.CreateBitmap("cLetter"), self.MainFrame.CreateBitmap("pLetter")

        # Maybe the icons are not that nice...
        for indx in xrange(4):
            for png in _bookIcons:
                if indx == 0:
                    imgList.Add(self.MainFrame.CreateBitmap(png))
                else:
                    image = self.AddOverlay(self.MainFrame.CreateBitmap(png), indx, bmpC, bmpP)
                    imgList.Add(image)

        # Assign the image list to the book
        self.AssignImageList(imgList)


    def AddOverlay(self, bitmap, index, bmpC, bmpP):
        """ Adds small letters C and P as overlay. """

        img = bitmap.ConvertToImage()
        img.ConvertAlphaToMask()
        bitmap = img.ConvertToBitmap()

        baseBMP = wx.EmptyBitmap(32, 32)
        memory = wx.MemoryDC()
        memory.SelectObject(baseBMP)
        
        mdc = wx.GraphicsContext.Create(memory)
        mdc.DrawBitmap(bitmap, 0, 0, 32, 32)

        # Draw overlay onto bitmap
        if index == 1:
            # Only the C Letter on the top right
            mdc.DrawBitmap(bmpC, 0, 0, 12, 12)
        elif index == 2:
            mdc.DrawBitmap(bmpP, 20, 20, 12, 12)
        else:
            mdc.DrawBitmap(bmpC, 0, 0, 12, 12)
            mdc.DrawBitmap(bmpP, 20, 20, 12, 12)

        memory.SelectObject(wx.NullBitmap)            
        return baseBMP


    def CreateBookPages(self, project, compilers):
        """
        Creates the FlatImageBook pages.

        
        **Parameters:**

        * project: the project associated with this L{LabelBook};
        * compilers: the available compilers in GUI2Exe.
        """

        # Loop over all the icons we have (5 at the moment)
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
        """
        Stores the tree item associated with us.

        
        **Parameters:**

        * treeItem: a tree control item.
        """

        self.treeItem = treeItem


    def GetTreeItem(self):
        """ Retrieves the tree item associated with us. """

        return self.treeItem


    def SetProject(self, project):
        """
        Stores the project associated with us.

        
        **Parameters:**

        * project: the project to be stored.
        """

        self.project = project

        # Loop over all the compilers and populate the pages
        for indx, compiler in enumerate(_defaultCompilers):
            page = self.GetPage(indx)
            if compiler in project:
                page.SetConfiguration(project[compiler])
            else:
                defaultConfig = self.MainFrame.GetDefaultConfiguration(compiler)
                page.SetConfiguration(defaultConfig)
                project.SetConfiguration(compiler, defaultConfig)


    def GetProject(self):
        """ Retrieves the project associated with us. """

        return self.project


    def OnPageChanged(self, event):
        """ Handles the wx.EVT_NOTEBOOK_PAGE_CHANGED for L{Labelbook}. """

        if not self.MainFrame.process:
            # Disable the dry-run button if not using py2exe
            self.MainFrame.messageWindow.EnableDryRun(self)

        page = self.GetPage(event.GetSelection())
        wx.CallAfter(page.SetFocusIgnoringChildren)

        
    def UpdatePageImages(self):
        """
        Updates the Labelbook images depending on the presence of user custom code
        and/or post-compilation code.
        """

        project = self.GetProject()
        
        for indx, compiler in enumerate(_defaultCompilers):
            customCode, postCode = project.GetCustomCode(compiler).strip(), \
                                   project.GetPostCompileCode(compiler).strip()
            if customCode and postCode:
                # Both are there, use the double overlay
                self.SetPageImage(indx, 15+indx)
            elif postCode:
                # We only have post-compilation code
                self.SetPageImage(indx, 10+indx)
            elif customCode:
                # We only have custom code
                self.SetPageImage(indx, 5+indx)
            else:
                # No custom or post-compilation code...
                self.SetPageImage(indx, indx)
                
        self._pages.Refresh()

        