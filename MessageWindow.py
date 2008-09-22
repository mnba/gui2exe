# Start the imports

import sys
import wx
import textwrap
import wx.lib.buttons as buttons

# For the nice throbber
import wx.animate

from Widgets import BaseListCtrl
from Utilities import opj, shortNow
from Constants import _iconMapper


class MessageWindow(wx.Panel):

    def __init__(self, parent):
        """ Default class constructor. """

        wx.Panel.__init__(self, parent)
        self.MainFrame = wx.GetTopLevelParent(self)        

        # Add the fancy list at the bottom
        self.list = BaseListCtrl(self, columnNames=["Time        ", "Compiler Messages"],
                                 name="messages")

        # Create 3 themed bitmap buttons
        dryBmp = self.MainFrame.CreateBitmap("dry")
        compileBmp = self.MainFrame.CreateBitmap("compile")
        killBmp = self.MainFrame.CreateBitmap("kill")

        # This is a bit tailored over py2exe, but it's the only one I know
        self.dryrun = buttons.ThemedGenBitmapTextButton(self, -1, dryBmp, " Dry Run ", size=(-1, 25))
        self.compile = buttons.ThemedGenBitmapTextButton(self, -1, compileBmp, " Compile ", size=(-1, 25))
        self.kill = buttons.ThemedGenBitmapTextButton(self, -1, killBmp, " Kill ", size=(-1, 25))
        # The animation control
        ani = wx.animate.Animation(opj(self.MainFrame.installDir +"/images/throbber.gif"))
        self.throb = wx.animate.AnimationCtrl(self, -1, ani)
        self.throb.SetUseWindowBackgroundColour()

        # Store an id for the popup menu
        self.popupId = wx.NewId()

        # Fo the hard work on other methods
        self.SetProperties()        
        self.LayoutItems()
        self.BindEvents()


    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def SetProperties(self):
        """ Sets few properties for the list control. """

        font = self.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        
        # Set a bigger for for the compile and kill buttons
        self.compile.SetFont(font)
        self.kill.SetFont(font)
        self.kill.Enable(False)
        

    def LayoutItems(self):
        """ Layout the widgets with sizers. """

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # We have the main list filling all the space with a small reserved
        # zone on the right for the buttons
        buttonSizer.Add(self.dryrun, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)
        buttonSizer.Add(self.compile, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.throb, 0, wx.ALIGN_CENTER)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.kill, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT, 5)

        buttonSizer.Show(self.throb, False)
        buttonSizer.Layout()

        # Add everything to the main sizer        
        mainSizer.Add(self.list, 1, wx.EXPAND)
        mainSizer.Add(buttonSizer, 0, wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Layout()

        # Keep a reference to the buttonSizer
        self.buttonSizer = buttonSizer

        
    def BindEvents(self):
        """ Bind the events for the list control. """

        self.Bind(wx.EVT_BUTTON, self.OnDryRun, self.dryrun)
        self.Bind(wx.EVT_BUTTON, self.OnCompile, self.compile)
        self.Bind(wx.EVT_BUTTON, self.OnKill, self.kill)
        self.Bind(wx.EVT_MENU, self.OnHistoryClear, id=self.popupId)
        self.list.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnRightClick)
        self.list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)


    # ============== #
    # Event handlers #
    # ============== #
    
    def OnDryRun(self, event):
        """ Handles the wx.EVT_BUTTON event for the dry run button. """
        
        # Delegate the action to the main frame
        self.MainFrame.RunCompile(view=False, run=False)


    def OnCompile(self, event):
        """ Handles the wx.EVT_BUTTON event for the compile button. """

        # Delegate the action to the main frame
        self.MainFrame.RunCompile(view=False, run=True)


    def OnKill(self, event):
        """ Handles the wx.EVT_BUTTON event for the kill button. """

        # Delegate the action to the main frame
        self.MainFrame.KillCompile()

        # Hide the throb
        self.ShowThrobber(False)
                          

    def OnRightClick(self, event):
        """
        Handles the wx.EVT_LIST_COL_RIGHT_CLICK/wx.EVT_LIST_ITEM_RIGHT_CLICK
        event for the list control.
        """

        menu = wx.Menu()
        # This pops up the "clear all" message
        item = wx.MenuItem(menu, self.popupId, "Clear History")
        bmp = self.MainFrame.CreateBitmap("history_clear")
        item.SetBitmap(bmp)
        menu.AppendItem(item)        

        # Pop up the menu
        self.list.PopupMenu(menu)
        menu.Destroy()


    def OnHistoryClear(self, event):
        """ Handles the wx.EVT_MENU event for the list control. """

        # Freeze everything... It helps with flicker
        self.list.Freeze()
        # Delete all the items, the user cleared all
        self.list.DeleteAllItems()
        # Time to warm up
        self.list.Thaw()


    # ================= #
    # Auxiliary methods #
    # ================= #


    def ShowThrobber(self, show):
        """ Shows/hides the throbber. """
        
        # Show the throb
        self.buttonSizer.Show(self.throb, show)
        self.buttonSizer.Layout()
        self.Refresh()
        if show:
            self.throb.Play()
        else:
            self.throb.Stop()


    def GetMaxWidth(self):
        """
        Returns the maximum number of characters that can fit in the message
        column.
        """

        width = self.list.GetColumnWidth(2)
        font = self.list.GetFont()
        dc = wx.ClientDC(self.list)
        dc.SetFont(font)
        textWidth = dc.GetCharWidth()

        return int(width/float(textWidth))


    def InsertError(self, currentTime):
        """ Insert some fancy line when an error happens. """

        indx = self.list.InsertImageStringItem(sys.maxint, "", _iconMapper["Error"])
        self.list.SetStringItem(indx, 1, currentTime)
        self.list.SetStringItem(indx, 2, "Error Message")
        self.list.SetItemBackgroundColour(indx, wx.NamedColor("yellow"))
        font = self.list.GetFont()
        font.SetWeight(wx.BOLD)
        self.list.SetItemFont(indx, font)

        return indx        
    
    
    def SendMessage(self, kind, message, copy=False):
        """ Prints an user-friendly message on the list control. """

        # Get the current time slightly dirrently formatted
        currentTime = shortNow()

        # Wrap the message... error messages are often too long
        # to be seen in the list control
        width = self.GetMaxWidth()
        if kind == "Error":
            # Insert the correct icon (message, error, etc...) in the first column
            indx = self.InsertError(currentTime)
            messages = message.splitlines()
            message = []
            for msg in messages:
                message.extend(textwrap.wrap(msg, width))
        else:
            message = [message]

        for msg in message:
            # Insert the correct icon (message, error, etc...) in the first column
            indx = self.list.InsertImageStringItem(sys.maxint, "", _iconMapper[kind])
            # Insert the current time and the message
            self.list.SetStringItem(indx, 1, currentTime)
            self.list.SetStringItem(indx, 2, msg)

        # Ensure the last item is visible
        self.list.EnsureVisible(indx)
        if wx.Platform == "__WXGTK__":
            self.list.Refresh()
        if copy:
            self.list.lastMessage = [kind, msg]


    def CopyLastMessage(self):
        """ Re-sends the previous message to the log window (for long processes). """

        if not hasattr(self.list, "lastMessage"):
            return
        
        # Get the current time slightly dirrently formatted
        currentTime = shortNow()
        
        # Insert the correct icon (message, error, etc...) in the first column
        kind, msg = self.list.lastMessage
        indx = self.list.InsertImageStringItem(sys.maxint, "", _iconMapper[kind])
        # Insert the current time and the message
        self.list.SetStringItem(indx, 1, currentTime)
        self.list.SetStringItem(indx, 2, msg)

        # Ensure the last item is visible
        self.list.EnsureVisible(indx)
        
        if wx.Platform == "__WXGTK__":
            self.list.Refresh()
            

    def EnableButtons(self, enable):
        """
        Enables/Disables the run buttons depending on the external
        process status.
        """

        # dry run and compile buttons are enabled when the kill button is
        # not, and vice-versa
        self.dryrun.Enable(enable)
        self.compile.Enable(enable)
        self.kill.Enable(not enable)
        

    def EnableDryRun(self, book):
        """
        Enables/Disables the dry-run button depending on the selected compiler
        (dry-run is available only for py2exe).
        """

        pageNum = book.GetSelection()
        self.dryrun.Enable(pageNum == 0)

        