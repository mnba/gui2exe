import wx

class RibbonControl(wx.PyControl):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 validator=wx.DefaultValidator, name="RibbonControl"):

        wx.PyControl.__init__(self, parent, id, pos, size, style, validator, name)
        self._art = None

        if isinstance(parent, RibbonControl):
            self._art = parent.GetArtProvider()
    

    def SetArtProvider(self, art):

        self._art = art


    def GetArtProvider(self):

        return self._art


    def IsSizingContinuous(self):

        return True

    
    def DoGetNextSmallerSize(self, direction, size):

        # Dummy implementation for code which doesn't check for IsSizingContinuous() == true
        minimum = self.GetMinSize()
        
        if direction & wx.HORIZONTAL and size.x > minimum.x:
            size.x -= 1        
        if direction & wx.VERTICAL and size.y > minimum.y:
            size.y -= 1
        
        return size


    def DoGetNextLargerSize(self, direction, size):

        # Dummy implementation for code which doesn't check for IsSizingContinuous() == true
        if direction & wx.HORIZONTAL:
            size.x += 1
        if direction & wx.VERTICAL:
            size.y += 1
        
        return size


    def GetNextSmallerSize(self, direction, relative_to=None):

        if relative_to is not None:
            return self.DoGetNextSmallerSize(direction, relative_to)

        return self.DoGetNextSmallerSize(direction, self.GetSize())


    def GetNextLargerSize(self, direction, relative_to=None):

        if relative_to is not None:
            return self.DoGetNextLargerSize(direction, relative_to)

        return self.DoGetNextLargerSize(direction, self.GetSize())


    def Realize(self):

        pass


    def Realise(self):

        pass

    

