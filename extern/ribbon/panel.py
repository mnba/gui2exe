import wx
import sys

from control import RibbonControl
from art import *

    
def IsAncestorOf(ancestor, window):

    while window is not None:    
        parent = window.GetParent()
        if parent == ancestor:
            return True
        else:
            window = parent
    
    return False


class RibbonPanel(RibbonControl):

    def __init__(self, parent, id=wx.ID_ANY, label="", minimised_icon=wx.NullBitmap,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=RIBBON_PANEL_DEFAULT_STYLE,
                 name="RibbonPanel"):

        RibbonControl.__init__(self, parent, id, pos, size, wx.BORDER_NONE, name=name)
        self.CommonInit(label, minimised_icon, style)

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseClick)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)


    def __del__(self):
        
        if self._expanded_panel:    
            self._expanded_panel._expanded_dummy = None
            self._expanded_panel.GetParent().Destroy()
    

    def SetArtProvider(self, art):

        self._art = art
        for child in self.GetChildren():
            if isinstance(child, RibbonControl):
                child.SetArtProvider(art)
        
        if self._expanded_panel:
            self._expanded_panel.SetArtProvider(art)


    def CommonInit(self, label, icon, style):

        self.SetName(label)
        self.SetLabel(label)

        self._minimised_size = wx.Size() # Unknown / none
        self._smallest_unminimised_size = wx.Size(0, 0) # Unknown / none
        self._preferred_expand_direction = wx.SOUTH
        self._expanded_dummy = None
        self._expanded_panel = None
        self._flags = style
        self._minimised_icon = icon
        self._minimised = False
        self._hovered = False

        if self._art == None:        
            parent = self.GetParent()
            if isinstance(parent, RibbonControl):
                self._art = parent.GetArtProvider()
            
        self.SetAutoLayout(True)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetMinSize(wx.Size(20, 20))


    def IsMinimised(self, at_size=None):
        
        if at_size is None:
            return self.IsMinimised1()
        
        return self.IsMinimised2(wx.Size(*at_size))
    

    def IsMinimised1(self):

        return self._minimised


    def IsHovered(self):

        return self._hovered


    def OnMouseEnter(self, event):

        self.TestPositionForHover(event.GetPosition())


    def OnMouseEnterChild(self, event):

        pos = event.GetPosition()
        child = event.GetEventObject()
        
        if child:        
            pos += child.GetPosition()
            self.TestPositionForHover(pos)
        
        event.Skip()


    def OnMouseLeave(self, event):

        self.TestPositionForHover(event.GetPosition())


    def OnMouseLeaveChild(self, event):

        pos = event.GetPosition()
        child = event.GetEventObject()
        
        if child:        
            pos += child.GetPosition()
            self.TestPositionForHover(pos)
        
        event.Skip()


    def TestPositionForHover(self, pos):

        hovered = False
        
        if pos.x >= 0 and pos.y >= 0:        
            size = self.GetSize()
            if pos.x < size.GetWidth() and pos.y < size.GetHeight():            
                hovered = True
                
        if hovered != self._hovered:        
            self._hovered = hovered
            self.Refresh(False)
    

    def AddChild(self, child):

        RibbonControl.AddChild(self, child)

        # Window enter / leave events count for only the window in question, not
        # for children of the window. The panel wants to be in the hovered state
        # whenever the mouse cursor is within its boundary, so the events need to
        # be attached to children too.
        child.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterChild)
        child.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeaveChild)


    def RemoveChild(self, child):

        child.Bind(wx.EVT_ENTER_WINDOW, None)
        child.Bind(wx.EVT_LEAVE_WINDOW, None)

        RibbonControl.RemoveChild(self, child)


    def OnSize(self, event):

        if self.GetAutoLayout():
            self.Layout()

        event.Skip()


    def DoSetSize(self, x, y, width, height, sizeFlags=wx.SIZE_AUTO):

        # At least on MSW, changing the size of a window will cause GetSize() to
        # report the new size, but a size event may not be handled immediately.
        # If self minimised check was performed in the OnSize handler, then
        # GetSize() could return a size much larger than the minimised size while
        # IsMinimised() returns True. This would then affect layout, as the panel
        # will refuse to grow any larger while in limbo between minimised and non.

        minimised = (self._flags & RIBBON_PANEL_NO_AUTO_MINIMISE) == 0 and self.IsMinimised(wx.Size(width, height))
            
        if minimised != self._minimised:        
            self._minimised = minimised

            for child in self.GetChildren():
                child.Show(not minimised)

            self.Refresh()

        RibbonControl.DoSetSize(self, x, y, width, height, sizeFlags)


    def IsMinimised2(self, at_size):

        if not self._minimised_size.IsFullySpecified():
            return False

##        if self.GetName() == "BUBBA":
##            print at_size, self._minimised_size, self._smallest_unminimised_size, (at_size.x <= self._minimised_size.x and \
##                at_size.y <= self._minimised_size.y) or \
##                at_size.x < self._smallest_unminimised_size.x or \
##                at_size.y < self._smallest_unminimised_size.y
            
        return (at_size.x <= self._minimised_size.x and \
                at_size.y <= self._minimised_size.y) or \
                at_size.x < self._smallest_unminimised_size.x or \
                at_size.y < self._smallest_unminimised_size.y


    def OnEraseBackground(self, event):

        # All painting done in main paint handler to minimise flicker
        pass


    def OnPaint(self, event):

        dc = wx.AutoBufferedPaintDC(self)

        if self._art != None:
            if self.IsMinimised():            
                self._art.DrawMinimisedPanel(dc, self, wx.RectS(self.GetSize()), self._minimised_icon_resized)
            else:
                self._art.DrawPanelBackground(dc, self, wx.RectS(self.GetSize()))
        

    def IsSizingContinuous(self):

        # A panel never sizes continuously, even if all of its children can,
        # as it would appear out of place along side non-continuous panels.
        return False


    def DoGetNextSmallerSize(self, direction, relative_to):

        if self._expanded_panel != None:
            # Next size depends upon children, who are currently in the
            # expanded panel
            return self._expanded_panel.DoGetNextSmallerSize(direction, relative_to)
        
        # TODO: Check for, and delegate to, a sizer

        # Simple (and common) case of single ribbon child
        if len(self.GetChildren()) == 1:
            child = self.GetChildren()[0]
            
            if self._art != None and isinstance(child, RibbonControl):            
                dc = wx.ClientDC(self)
                child_relative, dummy = self._art.GetPanelClientSize(dc, self, wx.Size(*relative_to), None)
                smaller = child.GetNextSmallerSize(direction, child_relative)

                if smaller == child_relative:                
                    if self.CanAutoMinimise():
                        minimised = wx.Size(*self._minimised_size)

                        if direction == wx.HORIZONTAL:
                            minimised.SetHeight(relative_to.GetHeight())
                        elif direction == wx.VERTICAL:
                            minimised.SetWidth(relative_to.GetWidth())

                        return minimised
                    
                    else:                    
                        return relative_to
                    
                else:                
                    return self._art.GetPanelSize(dc, self, wx.Size(*smaller), None)
                
        # Fallback: Decrease by 20% (or minimum size, whichever larger)
        current = wx.Size(*relative_to)
        minimum = wx.Size(*self.GetMinSize())
        
        if direction & wx.HORIZONTAL:        
            current.x = (current.x * 4) / 5
            if current.x < minimum.x:            
                current.x = minimum.x
            
        if direction & wx.VERTICAL:        
            current.y = (current.y * 4) / 5
            if current.y < minimum.y:            
                current.y = minimum.y
            
        return current


    def DoGetNextLargerSize(self, direction, relative_to):

        if self._expanded_panel != None:        
            # Next size depends upon children, who are currently in the
            # expanded panel
            return self._expanded_panel.DoGetNextLargerSize(direction, relative_to)
        
        if self.IsMinimised(relative_to):
            current = wx.Size(*relative_to)
            min_size = wx.Size(*self.GetMinNotMinimisedSize())

            if direction == wx.HORIZONTAL:
                if min_size.x > current.x and min_size.y == current.y:
                    return min_size

            elif direction == wx.VERTICAL:
                if min_size.x == current.x and min_size.y > current.y:
                    return min_size

            elif direction == wx.BOTH:
                if min_size.x > current.x and min_size.y > current.y:
                    return min_size        

        # TODO: Check for, and delegate to, a sizer

        # Simple (and common) case of single ribbon child
        if len(self.GetChildren()) == 1:
            child = self.GetChildren()[0]
            
            if isinstance(child, RibbonControl):            
                dc = wx.ClientDC(self)
                child_relative, dummy = self._art.GetPanelClientSize(dc, self, wx.Size(*relative_to), None)
                larger = child.GetNextLargerSize(direction, child_relative)
                
                if larger == child_relative:                
                    return relative_to
                else:                
                    dc = wx.ClientDC(self)
                    return self._art.GetPanelSize(dc, self, wx.Size(*larger), None)
                
        # Fallback: Increase by 25% (equal to a prior or subsequent 20% decrease)
        # Note that due to rounding errors, this increase may not exactly equal a
        # matching decrease - an ideal solution would not have these errors, but
        # avoiding them is non-trivial unless an increase is by 100% rather than
        # a fractional amount. This would then be non-ideal as the resizes happen
        # at very large intervals.
        current = wx.Size(*relative_to)
        
        if direction & wx.HORIZONTAL:        
            current.x = (current.x * 5 + 3) / 4
        
        if direction & wx.VERTICAL:
            current.y = (current.y * 5 + 3) / 4
        
        return current


    def CanAutoMinimise(self):

        return (self._flags & RIBBON_PANEL_NO_AUTO_MINIMISE) == 0 \
               and self._minimised_size.IsFullySpecified()


    def GetMinSize(self):

        if self._expanded_panel != None:        
            # Minimum size depends upon children, who are currently in the
            # expanded panel
            return self._expanded_panel.GetMinSize()
        
        if self.CanAutoMinimise():        
            return wx.Size(*self._minimised_size)
        else:        
            return self.GetMinNotMinimisedSize()
        

    def GetMinNotMinimisedSize(self):

        # TODO: Ask sizer

        # Common case of no sizer and single child taking up the entire panel
        if len(self.GetChildren()) == 1:
            child = self.GetChildren()[0]
            dc = wx.ClientDC(self)
            return self._art.GetPanelSize(dc, self, wx.Size(*child.GetMinSize()), None)
        
        return wx.Size(*RibbonControl.GetMinSize(self))


    def DoGetBestSize(self):

        # TODO: Ask sizer

        # Common case of no sizer and single child taking up the entire panel
        if len(self.GetChildren()) == 1:
            child = self.GetChildren()[0]
            dc = wx.ClientDC(self)
            return self._art.GetPanelSize(dc, self, wx.Size(*child.GetBestSize()), None)
        
        return wx.Size(*RibbonControl.DoGetBestSize(self))


    def Realize(self):

        status = True
        children = self.GetChildren()
        
        for child in children:
            if not isinstance(child, RibbonControl):
                continue
            
            if not child.Realize():            
                status = False

        minimum_children_size = wx.Size(0, 0)
        # TODO: Ask sizer if there is one
        
        if len(children) == 1:
            minimum_children_size = wx.Size(*children[0].GetMinSize())

        if self._art != None:
            temp_dc = wx.ClientDC(self)
            self._smallest_unminimised_size = self._art.GetPanelSize(temp_dc, self, wx.Size(*minimum_children_size), None)

            panel_min_size = self.GetMinNotMinimisedSize()
            self._minimised_size, bitmap_size, self._preferred_expand_direction = self._art.GetMinimisedPanelMinimumSize(temp_dc, self, 1, 1)
            
            if self._minimised_icon.IsOk() and self._minimised_icon.GetSize() != bitmap_size:            
                img = self._minimised_icon.ConvertToImage()
                img.Rescale(bitmap_size.GetWidth(), bitmap_size.GetHeight(), wx.IMAGE_QUALITY_HIGH)
                self._minimised_icon_resized = wx.BitmapFromImage(img)
            else:            
                self._minimised_icon_resized = self._minimised_icon
            
            if self._minimised_size.x > panel_min_size.x and self._minimised_size.y > panel_min_size.y:            
                # No point in having a minimised size which is larger than the
                # minimum size which the children can go to.
                self._minimised_size = wx.Size(-1, -1)
            else:            
                if self._art.GetFlags() & RIBBON_BAR_FLOW_VERTICAL:                
                    self._minimised_size.x = panel_min_size.x                
                else:                
                    self._minimised_size.y = panel_min_size.y
                
        else:        
            self._minimised_size = wx.Size(-1, -1)

        return self.Layout() and status


    def Layout(self):

        if self.IsMinimised():
            # Children are all invisible when minimised
            return True
        
        # TODO: Delegate to a sizer

        # Common case of no sizer and single child taking up the entire panel
        children = self.GetChildren()
        if len(children) == 1:        
            dc = wx.ClientDC(self)
            size, position = self._art.GetPanelClientSize(dc, self, wx.Size(*self.GetSize()), wx.Point())
            children[0].SetDimensions(position.x, position.y, size.GetWidth(), size.GetHeight())
        
        return True


    def OnMouseClick(self, event):

        if self.IsMinimised():        
            if self._expanded_panel != None:            
                self.HideExpanded()            
            else:            
                self.ShowExpanded()
            

    def GetExpandedDummy(self):

        return self._expanded_dummy


    def GetExpandedPanel(self):

        return self._expanded_panel


    def ShowExpanded(self):

        if not self.IsMinimised():        
            return False
        
        if self._expanded_dummy != None or self._expanded_panel != None:        
            return False

        size = self.GetBestSize()
        pos = self.GetExpandedPosition(wx.RectPS(self.GetScreenPosition(), self.GetSize()), size, self._preferred_expand_direction).GetTopLeft()

        # Need a top-level frame to contain the expanded panel
        container = wx.Frame(None, wx.ID_ANY, self.GetLabel(), pos, size, wx.FRAME_NO_TASKBAR | wx.BORDER_NONE)

        self._expanded_panel = RibbonPanel(container, wx.ID_ANY, self.GetLabel(), self._minimised_icon, wx.Point(0, 0), size, self._flags)
        self._expanded_panel.SetArtProvider(self._art)
        self._expanded_panel._expanded_dummy = self

        # Move all children to the new panel.
        # Conceptually it might be simpler to reparent self entire panel to the
        # container and create a new panel to sit in its place while expanded.
        # This approach has a problem though - when the panel is reinserted into
        # its original parent, it'll be at a different position in the child list
        # and thus assume a new position.
        # NB: Children iterators not used as behaviour is not well defined
        # when iterating over a container which is being emptied
        
        for child in self.GetChildren(): 
            child.Reparent(self._expanded_panel)
            child.Show()
        
        # TODO: Move sizer to new panel
        self._expanded_panel.Realize()
        self.Refresh()
        container.Show()
        self._expanded_panel.SetFocus()

        return True


    def ShouldSendEventToDummy(self, event):

        # For an expanded panel, filter events between being sent up to the
        # floating top level window or to the dummy panel sitting in the ribbon
        # bar.

        # Child focus events should not be redirected, as the child would not be a
        # child of the window the event is redirected to. All other command events
        # seem to be suitable for redirecting.
        return event.IsCommandEvent() and event.GetEventType() != wx.wxEVT_CHILD_FOCUS


    def TryAfter(self, event):

        if self._expanded_dummy and self.ShouldSendEventToDummy(event):
            propagateOnce = wx.PropagateOnce(event)
            return self._expanded_dummy.GetEventHandler().ProcessEvent(event)
        else:        
            return RibbonControl.TryAfter(self, event)
    

    def OnKillFocus(self, event):

        if self._expanded_dummy:
            receiver = event.GetWindow()
            
            if IsAncestorOf(self, receiver):            
                self._child_with_focus = receiver
                receiver.Bind(wx.EVT_KILL_FOCUS, self.OnChildKillFocus)
                
            elif receiver is None or receiver != self._expanded_dummy:
                self.HideExpanded()
        

    def OnChildKillFocus(self, event):

        if self._child_with_focus == None:
            return # Should never happen, but a check can't hurt

        self._child_with_focus.Bind(wx.EVT_KILL_FOCUS, None)
        self._child_with_focus = None

        receiver = event.GetWindow()
        if receiver == self or IsAncestorOf(self, receiver):        
            self._child_with_focus = receiver
            receiver.Bind(wx.EVT_KILL_FOCUS, self.OnChildKillFocus)
            event.Skip()
        
        elif receiver == None or receiver != self._expanded_dummy:
            self.HideExpanded()
            # Do not skip event, as the panel has been de-expanded, causing the
            # child with focus to be reparented (and hidden). If the event
            # continues propogation then bad things happen.
        
        else:        
            event.Skip()
        

    def HideExpanded(self):

        if self._expanded_dummy == None:        
            if self._expanded_panel:            
                return self._expanded_panel.HideExpanded()
            else:            
                return False
            
        # Move children back to original panel
        # NB: Children iterators not used as behaviour is not well defined
        # when iterating over a container which is being emptied
        for child in self.GetChildren():
            child.Reparent(self._expanded_dummy)
            child.Hide()

        # TODO: Move sizer back
        self._expanded_dummy._expanded_panel = None
        self._expanded_dummy.Realize()
        self._expanded_dummy.Refresh()
        parent = self.GetParent()
        self.Destroy()
        parent.Destroy()

        return True


    def GetExpandedPosition(self, panel, expanded_size, direction):

        # Strategy:
        # 1) Determine primary position based on requested direction
        # 2) Move the position so that it sits entirely within a display
        #    (for single monitor systems, this moves it into the display region,
        #     but for multiple monitors, it does so without splitting it over
        #     more than one display)
        # 2.1) Move in the primary axis
        # 2.2) Move in the secondary axis

        primary_x = False
        secondary_x = secondary_y = 0
        pos = wx.Point()

        if direction == wx.NORTH:
            pos.x = panel.GetX() + (panel.GetWidth() - expanded_size.GetWidth()) / 2
            pos.y = panel.GetY() - expanded_size.GetHeight()
            primary_x = True
            secondary_y = 1

        elif direction == wx.EAST:
            pos.x = panel.GetRight()
            pos.y = panel.GetY() + (panel.GetHeight() - expanded_size.GetHeight()) / 2
            secondary_x = -1

        elif direction == wx.SOUTH:
            pos.x = panel.GetX() + (panel.GetWidth() - expanded_size.GetWidth()) / 2
            pos.y = panel.GetBottom()
            primary_x = True
            secondary_y = -1

        else:        
            pos.x = panel.GetX() - expanded_size.GetWidth()
            pos.y = panel.GetY() + (panel.GetHeight() - expanded_size.GetHeight()) / 2
            secondary_x = 1
        
        expanded = wx.RectPS(pos, expanded_size)
        best = wx.Rect(*expanded)
        best_distance = sys.maxint

        display_n = wx.Display.GetCount()

        for display_i in xrange(display_n):
            display = wx.Display(display_i).GetGeometry()
            if display.ContainsRect(expanded):            
                return expanded
            
            elif display.Intersects(expanded):            
                new_rect = wx.Rect(*expanded)
                distance = 0

                if primary_x:                
                    if expanded.GetRight() > display.GetRight():                    
                        distance = expanded.GetRight() - display.GetRight()
                        new_rect.x -= distance
                    
                    elif expanded.GetLeft() < display.GetLeft():                    
                        distance = display.GetLeft() - expanded.GetLeft()
                        new_rect.x += distance
                
                else:                
                    if expanded.GetBottom() > display.GetBottom():                    
                        distance = expanded.GetBottom() - display.GetBottom()
                        new_rect.y -= distance
                    
                    elif expanded.GetTop() < display.GetTop():                    
                        distance = display.GetTop() - expanded.GetTop()
                        new_rect.y += distance                    
                
                if not display.Contains(new_rect):                
                    # Tried moving in primary axis, but failed.
                    # Hence try moving in the secondary axis.
                    dx = secondary_x * (panel.GetWidth() + expanded_size.GetWidth())
                    dy = secondary_y * (panel.GetHeight() + expanded_size.GetHeight())
                    new_rect.x += dx
                    new_rect.y += dy

                    # Squaring makes secondary moves more expensive (and also
                    # prevents a negative cost)
                    distance += dx * dx + dy * dy
                
                if display.Contains(new_rect) and distance < best_distance:                
                    best = new_rect
                    best_distance = distance
                
        return best


    def GetMinimisedIcon(self):

        return self._minimised_icon


    def GetDefaultBorder(self):

        return wx.BORDER_NONE

    
