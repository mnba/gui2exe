import wx
import sys
import types

from control import RibbonControl

from art_internal import RibbonPageTabInfo
from art_msw import RibbonMSWArtProvider
from art import *

wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGED = wx.NewEventType()
wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGING = wx.NewEventType()
wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_DOWN = wx.NewEventType()
wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_UP = wx.NewEventType()
wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_DOWN = wx.NewEventType()
wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_UP = wx.NewEventType()

EVT_RIBBONBAR_PAGE_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGED, 1)
EVT_RIBBONBAR_PAGE_CHANGING = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGING, 1)
EVT_RIBBONBAR_TAB_MIDDLE_DOWN = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_DOWN, 1)
EVT_RIBBONBAR_TAB_MIDDLE_UP = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_UP, 1)
EVT_RIBBONBAR_TAB_RIGHT_DOWN = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_DOWN, 1)
EVT_RIBBONBAR_TAB_RIGHT_UP = wx.PyEventBinder(wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_UP, 1)


def SET_FLAG(variable, flag):

    refresh_tabs = False
    if variable & flag != flag:
        variable |= flag
        refresh_tabs = True

    return variable, refresh_tabs

def UNSET_FLAG(variable, flag):

    refresh_tabs = False
    if variable & flag:
        variable &= ~flag
        refresh_tabs = True 

    return variable, refresh_tabs


class RibbonBarEvent(wx.NotifyEvent):

    def __init__(self, command_type=None, win_id=0, page=None):
    
        wx.NotifyEvent.__init__(self, command_type, win_id)
        self._page = page

        self._isAllowed = True        


    def Clone(self):

        return RibbonBarEvent(self)
    

    def GetPage(self):

        return self._page

    
    def SetPage(self, page):

        self._page = page


    def Allow(self):

        self._isAllowed = True


    def Veto(self):

        self._isAllowed = False


    def IsAllowed(self):

        return self._isAllowed        


class RibbonBar(RibbonControl):
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=RIBBON_BAR_DEFAULT_STYLE,
                 validator=wx.DefaultValidator, name="RibbonBar"):

        RibbonControl.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
        
        self._flags = 0
        self._tabs_total_width_ideal = 0
        self._tabs_total_width_minimum = 0
        self._tab_margin_left = 0
        self._tab_margin_right = 0
        self._tab_height = 0
        self._tab_scroll_amount = 0
        self._current_page = -1
        self._current_hovered_page = -1
        self._tab_scroll_left_button_state = RIBBON_SCROLL_BTN_NORMAL
        self._tab_scroll_right_button_state = RIBBON_SCROLL_BTN_NORMAL
        self._tab_scroll_buttons_shown = False
        self._pages = []

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMouseMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMouseMiddleUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.CommonInit(style)
        

    def AddPage(self, page):

        info = RibbonPageTabInfo()

        info.page = page
        info.active = False
        info.hovered = False
        # info.rect not set (intentional)

        dcTemp = wx.ClientDC(self)
        label = ""
        if self._flags & RIBBON_BAR_SHOW_PAGE_LABELS:
            label = page.GetLabel()
            
        icon = wx.NullBitmap
        if self._flags & RIBBON_BAR_SHOW_PAGE_ICONS:
            icon = page.GetIcon()

        info.ideal_width, info.small_begin_need_separator_width, \
        info.small_must_have_separator_width, info.minimum_width = self._art.GetBarTabWidth(dcTemp, self, label, icon, info.ideal_width,
                                                                                            info.small_begin_need_separator_width,
                                                                                            info.small_must_have_separator_width, info.minimum_width)

        if not self._pages:
            self._tabs_total_width_ideal = info.ideal_width
            self._tabs_total_width_minimum = info.minimum_width
        else:
            sep = self._art.GetMetric(RIBBON_ART_TAB_SEPARATION_SIZE)
            self._tabs_total_width_ideal += sep + info.ideal_width
            self._tabs_total_width_minimum += sep + info.minimum_width

        self._pages.append(info)

        page.Hide() # Most likely case is that self new page is not the active tab
        page.SetArtProvider(self._art)

        if len(self._pages) == 1:
            self.SetActivePage(0)
    

    def DismissExpandedPanel(self):

        if self._current_page == -1:
            return False
        
        return self._pages[self._current_page].page.DismissExpandedPanel()


    def SetWindowStyleFlag(self, style):

        self._flags = style
        
        if self._art:
            self._art.SetFlags(style)


    def GetWindowStyleFlag(self):

        return self._flags


    def Realize(self):

        status = True

        dcTemp = wx.ClientDC(self)
        sep = self._art.GetMetric(RIBBON_ART_TAB_SEPARATION_SIZE)
        numtabs = len(self._pages)

        for i, info in enumerate(self._pages):
        
            self.RepositionPage(info.page)
            if not info.page.Realize():
                status = False
            
            label = ""
            if self._flags & RIBBON_BAR_SHOW_PAGE_LABELS:
                label = info.page.GetLabel()
                
            icon = wx.NullBitmap
            if self._flags & RIBBON_BAR_SHOW_PAGE_ICONS:
                icon = info.page.GetIcon()

            info.ideal_width, info.small_begin_need_separator_width, \
                              info.small_must_have_separator_width, \
                              info.minimum_width = self._art.GetBarTabWidth(dcTemp, self, label, icon, info.ideal_width,
                                                                            info.small_begin_need_separator_width, info.small_must_have_separator_width,
                                                                            info.minimum_width)

            if i == 0:
                self._tabs_total_width_ideal = info.ideal_width
                self._tabs_total_width_minimum = info.minimum_width
            else:
                self._tabs_total_width_ideal += sep + info.ideal_width
                self._tabs_total_width_minimum += sep + info.minimum_width
            
        self._tab_height = self._art.GetTabCtrlHeight(dcTemp, self, self._pages)

        self.RecalculateMinSize()
        self.RecalculateTabSizes()
        self.Refresh()

        return status


    def OnMouseMove(self, event):

        x, y = event.GetX(), event.GetY()
        hovered_page = -1
        refresh_tabs = False
        
        if y < self._tab_height:
            # It is quite likely that the mouse moved a small amount and is still over the same tab
            if self._current_hovered_page != -1 and self._pages[self._current_hovered_page].rect.Contains((x, y)):
                hovered_page = self._current_hovered_page
                # But be careful, if tabs can be scrolled, then parts of the tab rect may not be valid
                if self._tab_scroll_buttons_shown:
                    if x >= self._tab_scroll_right_button_rect.GetX() or x < self._tab_scroll_left_button_rect.GetRight():
                        hovered_page = -1
                    
            else:
            
                hovered_page, dummy = self.HitTestTabs(event.GetPosition())

        if hovered_page != self._current_hovered_page:
            if self._current_hovered_page != -1:
                self._pages[self._current_hovered_page].hovered = False
            
            self._current_hovered_page = hovered_page
            if self._current_hovered_page != -1:
                self._pages[self._current_hovered_page].hovered = True
            
            refresh_tabs = True
        
        if self._tab_scroll_buttons_shown:
            if self._tab_scroll_left_button_rect.Contains((x, y)):
                self._tab_scroll_left_button_state, refresh_tabs = SET_FLAG(self._tab_scroll_left_button_state, RIBBON_SCROLL_BTN_HOVERED)
            else:
                self._tab_scroll_left_button_state, refresh_tabs = UNSET_FLAG(self._tab_scroll_left_button_state, RIBBON_SCROLL_BTN_HOVERED)

            if self._tab_scroll_right_button_rect.Contains((x, y)):
                self._tab_scroll_right_button_state, refresh_tabs = SET_FLAG(self._tab_scroll_right_button_state, RIBBON_SCROLL_BTN_HOVERED)
            else:
                self._tab_scroll_right_button_state, refresh_tabs = UNSET_FLAG(self._tab_scroll_right_button_state, RIBBON_SCROLL_BTN_HOVERED)
        
        if refresh_tabs:
            self.RefreshTabBar()
        

    def OnMouseLeave(self, event):

        # The ribbon bar is (usually) at the top of a window, and at least on MSW, the mouse
        # can leave the window quickly and leave a tab in the hovered state.
        refresh_tabs = False

        if self._current_hovered_page != -1:
            self._pages[self._current_hovered_page].hovered = False
            self._current_hovered_page = -1
            refresh_tabs = True
        
        if self._tab_scroll_left_button_state & RIBBON_SCROLL_BTN_HOVERED:
            self._tab_scroll_left_button_state &= ~RIBBON_SCROLL_BTN_HOVERED
            refresh_tabs = True
        
        if self._tab_scroll_right_button_state & RIBBON_SCROLL_BTN_HOVERED:
            self._tab_scroll_right_button_state &= ~RIBBON_SCROLL_BTN_HOVERED
            refresh_tabs = True
        
        if refresh_tabs:
            self.RefreshTabBar()
    

    def GetPage(self, n):

        if n < 0 or n >= len(self._pages):
            return 0
        
        return self._pages[n].page


    def SetActivePage1(self, page):

        if self._current_page == page:
            return True

        if page >= len(self._pages):
            return False
        
        if self._current_page != -1:
            self._pages[self._current_page].active = False
            self._pages[self._current_page].page.Hide()
        
        self._current_page = page
        self._pages[page].active = True
        
        wnd = self._pages[page].page
        self.RepositionPage(wnd)
        wnd.Layout()
        wnd.Show()
        
        self.Refresh()

        return True


    def SetActivePage2(self, page):

        for i in xrange(len(self._pages)):
            if self._pages[i].page == page:
                return self.SetActivePage1(i)
            
        return False


    def SetActivePage(self, page):

        if isinstance(page, types.IntType):
            return self.SetActivePage1(page)

        return self.SetActivePage2(page)
    

    def GetActivePage(self):

        return self._current_page


    def SetTabCtrlMargins(self, left, right):

        self._tab_margin_left = left
        self._tab_margin_right = right

        self.RecalculateTabSizes()


    def OrderPageTabInfoBySmallWidthAsc(self, first, second):

        return first.small_must_have_separator_width - second.small_must_have_separator_width


    def RecalculateTabSizes(self):

        numtabs = len(self._pages)

        if numtabs == 0:
            return

        width = self.GetSize().GetWidth() - self._tab_margin_left - self._tab_margin_right
        tabsep = self._art.GetMetric(RIBBON_ART_TAB_SEPARATION_SIZE)
        x = self._tab_margin_left
        y = 0

        if width >= self._tabs_total_width_ideal:
            # Simple case: everything at ideal width
            for info in self._pages:
                info.rect.x = x
                info.rect.y = y
                info.rect.width = info.ideal_width
                info.rect.height = self._tab_height
                x += info.rect.width + tabsep
            
            self._tab_scroll_buttons_shown = False
            self._tab_scroll_left_button_rect.SetWidth(0)
            self._tab_scroll_right_button_rect.SetWidth(0)
        
        elif width < self._tabs_total_width_minimum:
            # Simple case: everything minimum with scrollbar
            for info in self._pages:            
                info.rect.x = x
                info.rect.y = y
                info.rect.width = info.minimum_width
                info.rect.height = self._tab_height
                x += info.rect.width + tabsep
            
            if not self._tab_scroll_buttons_shown:            
                self._tab_scroll_left_button_state = RIBBON_SCROLL_BTN_NORMAL
                self._tab_scroll_right_button_state = RIBBON_SCROLL_BTN_NORMAL
                self._tab_scroll_buttons_shown = True
            
            temp_dc = wx.ClientDC(self)
            self._tab_scroll_left_button_rect.SetWidth(self._art.GetScrollButtonMinimumSize(temp_dc, self,
                                                                                            RIBBON_SCROLL_BTN_LEFT | RIBBON_SCROLL_BTN_NORMAL |
                                                                                            RIBBON_SCROLL_BTN_FOR_TABS).GetWidth())
            self._tab_scroll_left_button_rect.SetHeight(self._tab_height)
            self._tab_scroll_left_button_rect.SetX(self._tab_margin_left)
            self._tab_scroll_left_button_rect.SetY(0)
            self._tab_scroll_right_button_rect.SetWidth(self._art.GetScrollButtonMinimumSize(temp_dc, self,
                                                                                             RIBBON_SCROLL_BTN_RIGHT | RIBBON_SCROLL_BTN_NORMAL |
                                                                                             RIBBON_SCROLL_BTN_FOR_TABS).GetWidth())
            self._tab_scroll_right_button_rect.SetHeight(self._tab_height)
            self._tab_scroll_right_button_rect.SetX(self.GetClientSize().GetWidth() - self._tab_margin_right - self._tab_scroll_right_button_rect.GetWidth())
            self._tab_scroll_right_button_rect.SetY(0)
            
            if self._tab_scroll_amount == 0:
                self._tab_scroll_left_button_rect.SetWidth(0)
            
            elif self._tab_scroll_amount + width >= self._tabs_total_width_minimum:
                self._tab_scroll_amount = self._tabs_total_width_minimum - width
                self._tab_scroll_right_button_rect.SetX(self._tab_scroll_right_button_rect.GetX() + self._tab_scroll_right_button_rect.GetWidth())
                self._tab_scroll_right_button_rect.SetWidth(0)
            
            for info in self._pages:
                info.rect.x -= self._tab_scroll_amount
                    
        else:
            self._tab_scroll_buttons_shown = False
            self._tab_scroll_left_button_rect.SetWidth(0)
            self._tab_scroll_right_button_rect.SetWidth(0)
            # Complex case: everything sized such that: minimum <= width < ideal
            #
            #   Strategy:
            #     1) Uniformly reduce all tab widths from ideal to small_must_have_separator_width
            #     2) Reduce the largest tab by 1 pixel, repeating until all tabs are same width (or at minimum)
            #     3) Uniformly reduce all tabs down to their minimum width
            #
            smallest_tab_width = sys.maxint
            total_small_width = tabsep * (numtabs - 1)

            for info in self._pages:
                if info.small_must_have_separator_width < smallest_tab_width:                
                    smallest_tab_width = info.small_must_have_separator_width
                
                total_small_width += info.small_must_have_separator_width
            
            if width >= total_small_width:
                # Do (1)
                total_delta = self._tabs_total_width_ideal - total_small_width
                total_small_width -= tabsep*(numtabs - 1)
                width -= tabsep*(numtabs - 1)
                for info in self._pages:
                    delta = info.ideal_width - info.small_must_have_separator_width
                    info.rect.x = x
                    info.rect.y = y
                    info.rect.width = info.small_must_have_separator_width + delta*(width - total_small_width)/total_delta
                    info.rect.height = self._tab_height

                    x += info.rect.width + tabsep
                    total_delta -= delta
                    total_small_width -= info.small_must_have_separator_width
                    width -= info.rect.width
                
            else:
            
                total_small_width = tabsep*(numtabs - 1)
                for info in self._pages:
                    if info.minimum_width < smallest_tab_width:
                        total_small_width += smallest_tab_width
                    else:                    
                        total_small_width += info.minimum_width
                    
                if width >= total_small_width:
                    # Do (2)
                    sorted_pages = []
                    for info in self._pages:
                        # Sneaky obj array trickery to not copy the tab descriptors
                        sorted_pages.append(info)
                    
                    sorted_pages.sort(self.OrderPageTabInfoBySmallWidthAsc)
                    width -= tabsep*(numtabs - 1)

                    for i, info in enumerate(self._pages):
                        if info.small_must_have_separator_width*(numtabs - i) <= width:
                            info.rect.width = info.small_must_have_separator_width
                        else:                        
                            info.rect.width = width/(numtabs - i)
                        
                        width -= info.rect.width
                    
                    for i, info in enumerate(self._pages):
                        info.rect.x = x
                        info.rect.y = y
                        info.rect.height = self._tab_height
                        x += info.rect.width + tabsep
                        sorted_pages.pop(numtabs - (i + 1))
                    
                else:
                
                    # Do (3)
                    total_small_width = (smallest_tab_width + tabsep)*numtabs - tabsep
                    total_delta = total_small_width - self._tabs_total_width_minimum
                    total_small_width = self._tabs_total_width_minimum - tabsep*(numtabs - 1)
                    width -= tabsep*(numtabs - 1)
                    
                    for info in self._pages:
                        delta = smallest_tab_width - info.minimum_width
                        info.rect.x = x
                        info.rect.y = y
                        info.rect.width = info.minimum_width + delta*(width - total_small_width)/total_delta
                        info.rect.height = self._tab_height

                        x += info.rect.width + tabsep
                        total_delta -= delta
                        total_small_width -= info.minimum_width
                        width -= info.rect.width


    def CommonInit(self, style):

        self.SetName("RibbonBar")

        self._flags = style
        self._tabs_total_width_ideal = 0
        self._tabs_total_width_minimum = 0
        self._tab_margin_left = 50
        self._tab_margin_right = 20
        self._tab_height = 20 # initial guess
        self._tab_scroll_amount = 0
        self._current_page = -1
        self._current_hovered_page = -1
        self._tab_scroll_left_button_state = RIBBON_SCROLL_BTN_NORMAL
        self._tab_scroll_right_button_state = RIBBON_SCROLL_BTN_NORMAL
        self._tab_scroll_buttons_shown = False
        self._tab_scroll_left_button_rect = wx.Rect()
        self._tab_scroll_right_button_rect = wx.Rect()

        if not self._art:
            self.SetArtProvider(RibbonMSWArtProvider())
        
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)


    def SetArtProvider(self, art):

        self._art = art

        if art:
            art.SetFlags(self._flags)
        
        for info in self._pages:
            if info.page.GetArtProvider() != art:
                info.page.SetArtProvider(art)
            

    def OnPaint(self, event):

        dc = wx.AutoBufferedPaintDC(self)

        if not self.GetUpdateRegion().ContainsRect(wx.Rect(0, 0, self.GetClientSize().GetWidth(), self._tab_height)):
            # Nothing to do in the tab area, and the page area is handled by the active page
            return
        
        self.DoEraseBackground(dc)

        numtabs = len(self._pages)
        sep_visibility = 0.0
        draw_sep = False
        tabs_rect = wx.Rect(self._tab_margin_left, 0, self.GetClientSize().GetWidth() - self._tab_margin_left - self._tab_margin_right, self._tab_height)
        
        if self._tab_scroll_buttons_shown:
            tabs_rect.x += self._tab_scroll_left_button_rect.GetWidth()
            tabs_rect.width -= self._tab_scroll_left_button_rect.GetWidth() + self._tab_scroll_right_button_rect.GetWidth()
        
        for info in self._pages:
            dc.DestroyClippingRegion()
            if self._tab_scroll_buttons_shown:
                if not tabs_rect.Intersects(info.rect):
                    continue
                dc.SetClippingRect(tabs_rect)
            
            dc.SetClippingRect(info.rect)
            self._art.DrawTab(dc, self, info)

            if info.rect.width < info.small_begin_need_separator_width:
                draw_sep = True
                if info.rect.width < info.small_must_have_separator_width:
                    sep_visibility += 1.0
                else:                
                    sep_visibility += float(info.small_begin_need_separator_width - info.rect.width)/ \
                                      float(info.small_begin_need_separator_width - info.small_must_have_separator_width)
        
        if draw_sep:
        
            rect = wx.Rect(*self._pages[0].rect)
            rect.width = self._art.GetMetric(RIBBON_ART_TAB_SEPARATION_SIZE)
            sep_visibility /= float(numtabs)
            
            for i in xrange(0, numtabs-1):
                info = self._pages[i]
                rect.x = info.rect.x + info.rect.width

                if self._tab_scroll_buttons_shown and not tabs_rect.Intersects(rect):                
                    continue
                
                dc.DestroyClippingRegion()
                dc.SetClippingRect(rect)
                self._art.DrawTabSeparator(dc, self, rect, sep_visibility)

        if self._tab_scroll_buttons_shown:        
            dc.DestroyClippingRegion()
            if self._tab_scroll_left_button_rect.GetWidth() != 0:            
                self._art.DrawScrollButton(dc, self, self._tab_scroll_left_button_rect, RIBBON_SCROLL_BTN_LEFT |
                                           self._tab_scroll_left_button_state | RIBBON_SCROLL_BTN_FOR_TABS)
            
            if self._tab_scroll_right_button_rect.GetWidth() != 0:            
                self._art.DrawScrollButton(dc, self, self._tab_scroll_right_button_rect, RIBBON_SCROLL_BTN_RIGHT |
                                           self._tab_scroll_right_button_state | RIBBON_SCROLL_BTN_FOR_TABS)
            

    def OnEraseBackground(self, event):

        # Background painting done in main paint handler to reduce screen flicker
        pass


    def DoEraseBackground(self, dc):

        tabs = wx.RectS(self.GetSize())
        tabs.height = self._tab_height
        self._art.DrawTabCtrlBackground(dc, self, tabs)


    def OnSize(self, event):

        self.RecalculateTabSizes()
        if self._current_page != -1:
            self.RepositionPage(self._pages[self._current_page].page)

        self.RefreshTabBar()
        event.Skip()


    def RepositionPage(self, page):

        w, h = self.GetSize()
        page.SetSizeWithScrollButtonAdjustment(0, self._tab_height, w, h - self._tab_height)


    def HitTestTabs(self, position):

        tabs_rect = wx.Rect(self._tab_margin_left, 0, self.GetClientSize().GetWidth() - self._tab_margin_left - self._tab_margin_right, self._tab_height)
        
        if self._tab_scroll_buttons_shown:        
            tabs_rect.SetX(tabs_rect.GetX() + self._tab_scroll_left_button_rect.GetWidth())
            tabs_rect.SetWidth(tabs_rect.GetWidth() - self._tab_scroll_left_button_rect.GetWidth() - self._tab_scroll_right_button_rect.GetWidth())
        
        if tabs_rect.Contains(position):
            for i, info in enumerate(self._pages):
                if info.rect.Contains(position):
                    return i, info

        return -1, None


    def OnMouseLeftDown(self, event):

        index, tab = self.HitTestTabs(event.GetPosition())
        if tab and tab != self._pages[self._current_page]:
            query = RibbonBarEvent(wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGING, self.GetId(), tab.page)
            query.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(query)

            if query.IsAllowed(): 
                self.SetActivePage(query.GetPage())
                notification = RibbonBarEvent(wxEVT_COMMAND_RIBBONBAR_PAGE_CHANGED, self.GetId(), self._pages[self._current_page].page)
                notification.SetEventObject(self)
                self.GetEventHandler().ProcessEvent(notification)
            
        elif tab == None:
            if self._tab_scroll_left_button_rect.Contains(event.GetPosition()):
                self._tab_scroll_left_button_state |= RIBBON_SCROLL_BTN_ACTIVE | RIBBON_SCROLL_BTN_HOVERED
                self.RefreshTabBar()
            
            elif self._tab_scroll_right_button_rect.Contains(event.GetPosition()):
                self._tab_scroll_right_button_state |= RIBBON_SCROLL_BTN_ACTIVE | RIBBON_SCROLL_BTN_HOVERED
                self.RefreshTabBar()
            
        
    def OnMouseLeftUp(self, event):

        if not self._tab_scroll_buttons_shown:
            return
        
        amount = 0
        
        if self._tab_scroll_left_button_state & RIBBON_SCROLL_BTN_ACTIVE:        
            amount = -1
        
        elif self._tab_scroll_right_button_state & RIBBON_SCROLL_BTN_ACTIVE:        
            amount = 1
        
        if amount != 0:
            self._tab_scroll_left_button_state &= ~RIBBON_SCROLL_BTN_ACTIVE
            self._tab_scroll_right_button_state &= ~RIBBON_SCROLL_BTN_ACTIVE
            self.ScrollTabBar(amount*8)
        

    def ScrollTabBar(self, amount):

        show_left = True
        show_right = True
        
        if self._tab_scroll_amount + amount <= 0:
            amount = -self._tab_scroll_amount
            show_left = False
        
        elif self._tab_scroll_amount + amount + (self.GetClientSize().GetWidth() - \
                                                 self._tab_margin_left - self._tab_margin_right) >= \
                                                 self._tabs_total_width_minimum:
            amount = self._tabs_total_width_minimum - self._tab_scroll_amount - \
                     (self.GetClientSize().GetWidth() - self._tab_margin_left - self._tab_margin_right)
            show_right = False
        
        if amount == 0:
            return
        
        self._tab_scroll_amount += amount
        for info in self._pages:
            info.rect.SetX(info.rect.GetX() - amount)
        
        if show_right != (self._tab_scroll_right_button_rect.GetWidth() != 0) or \
           show_left != (self._tab_scroll_left_button_rect.GetWidth() != 0):
        
            temp_dc = wx.ClientDC(self)
            
            if show_left:            
                self._tab_scroll_left_button_rect.SetWidth(self._art.GetScrollButtonMinimumSize(temp_dc, self, RIBBON_SCROLL_BTN_LEFT |
                                                                                                RIBBON_SCROLL_BTN_NORMAL |
                                                                                                RIBBON_SCROLL_BTN_FOR_TABS).GetWidth())
            else:            
                self._tab_scroll_left_button_rect.SetWidth(0)
            
            if show_right:            
                if self._tab_scroll_right_button_rect.GetWidth() == 0:                
                    self._tab_scroll_right_button_rect.SetWidth(self._art.GetScrollButtonMinimumSize(temp_dc, self,
                                                                                                     RIBBON_SCROLL_BTN_RIGHT |
                                                                                                     RIBBON_SCROLL_BTN_NORMAL |
                                                                                                     RIBBON_SCROLL_BTN_FOR_TABS).GetWidth())
                    self._tab_scroll_right_button_rect.SetX(self._tab_scroll_right_button_rect.GetX() - self._tab_scroll_right_button_rect.GetWidth())
            else:
            
                if self._tab_scroll_right_button_rect.GetWidth() != 0:                
                    self._tab_scroll_right_button_rect.SetX(self._tab_scroll_right_button_rect.GetX() + self._tab_scroll_right_button_rect.GetWidth())
                    self._tab_scroll_right_button_rect.SetWidth(0)
                
        self.RefreshTabBar()


    def RefreshTabBar(self):

        tab_rect = wx.Rect(0, 0, self.GetClientSize().GetWidth(), self._tab_height)
        self.Refresh(False, tab_rect)


    def OnMouseMiddleDown(self, event):

        self.DoMouseButtonCommon(event, wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_DOWN)


    def OnMouseMiddleUp(self, event):

        self.DoMouseButtonCommon(event, wxEVT_COMMAND_RIBBONBAR_TAB_MIDDLE_UP)


    def OnMouseRightDown(self, event):

        self.DoMouseButtonCommon(event, wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_DOWN)


    def OnMouseRightUp(self, event):

        self.DoMouseButtonCommon(event, wxEVT_COMMAND_RIBBONBAR_TAB_RIGHT_UP)


    def DoMouseButtonCommon(self, event, tab_event_type):

        index, tab = self.HitTestTabs(event.GetPosition())
        
        if tab:        
            notification = RibbonBarEvent(tab_event_type, self.GetId(), tab.page)
            notification.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(notification)


    def RecalculateMinSize(self):

        min_size = wx.Size(-1, -1)
        numtabs = len(self._pages)
        
        if numtabs != 0:
            min_size = wx.Size(*self._pages[0].page.GetMinSize())

            for info in self._pages:
                page_min = info.page.GetMinSize()
                min_size.x = max(min_size.x, page_min.x)
                min_size.y = max(min_size.y, page_min.y)
            
        if min_size.y != -1:
            # TODO: Decide on best course of action when min height is unspecified
            # - should we specify it to the tab minimum, or leave it unspecified?
            min_size.IncBy(0, self._tab_height)

        self._minWidth = min_size.GetWidth()
        self._minHeight = min_size.GetHeight()


    def DoGetBestSize(self):

        best = wx.Size(0, 0)
        
        if self._current_page != -1:
            best = wx.Size(*self._pages[self._current_page].page.GetBestSize())

        if best.GetHeight() == -1:
            best.SetHeight(self._tab_height)
        else:        
            best.IncBy(0, self._tab_height)

        return best


    def HasMultiplePages(self):

        return True


    def GetDefaultBorder(self):

        return wx.BORDER_NONE

    