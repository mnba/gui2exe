########### GUI2Exe SVN repository information ###################
# $Date: $
# $Author: $
# $Revision: $
# $URL: $
# $Id: $
########### GUI2Exe SVN repository information ###################

import wx

class NotImplementedOrMissingPanel(wx.Panel):

    def __init__(self, parent, notimplemented=True, missing=None):

        wx.Panel.__init__(self, parent)
        self.MainFrame = wx.GetTopLevelParent(self)

        if notimplemented:
            text = "The options relative to this compiler have not been implemented yet."
        elif missing:
            text = "Module " + missing + " is not installed on your site-packages director"

        static = wx.StaticText(self, -1, text, pos=(20, 20))
        static.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False))


        