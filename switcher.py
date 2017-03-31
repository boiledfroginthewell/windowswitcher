#!/usr/bin/env python
# vim: fileencoding=utf-8

# Note
# only one-letter labels are supported
# Currently only one-letter label is supported, since the event handeler
# accept only one letter.

import gtk
import wnck
import pango
import sys

# Window name for this program. 
# This name should be different from the other programs. UUID is used to avoid overlapping.
WINDOW_NAME = "Window Switcher\t\t__5f9781ea926f40f88783c5a743662cf1__"

class Switch():
    """
    A label for a window. 
    The associated window is activated by pressing the key writtin in this label.
    """

    # number of created instances of this class
    _counter = 0
    # keys used for labeling
    LABEL_LETTERS = "UEIOA.PYJK"  # Left hand only (Dvorak layout)
    # LABEL_LETTERS = "UEIOA.PYJKDHTNSFGCBMWV"  # both hands (Dvorak layout)
    # LABEL_LETTERS = "FDGSARET"  # Left hand only (QWERTY layout)
    # LABEL_LETTERS = "FDGSARETJDKLUIO"  # Both hands (QWERTY layout)

    @staticmethod
    def activate_wnck_window(wnck_win):
        wnck_win.activate(gtk.gdk.x11_get_server_time(gtk.gdk.get_default_root_window()))

    @staticmethod
    def new_label():
        """
        Returns a label for new instance
        """
        # Too many windows
        if len(Switch.LABEL_LETTERS) <= Switch._counter: return None

        # label assignment
        label = Switch.LABEL_LETTERS[Switch._counter]
        Switch._counter += 1
        return label

    def _create_window(self):
        # create popup window
        win = gtk.Window(gtk.WINDOW_POPUP)
        #win.set_opacity(0.8)
        win.set_border_width(1)
        win.set_decorated(False)
        win.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        win.set_keep_above(True)

        # create border and set layout
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        hbox = gtk.HBox()
        eb.add(hbox)
        win.add(eb)

        # create text label
        icon = gtk.Image()
        icon.set_from_gicon(self.win.get_icon(), 2)
        label = gtk.Label(" "+ self.get_switch_label() +": "+ self.win.get_name())
        label.set_justify(gtk.JUSTIFY_CENTER)
        label.modify_font(pango.FontDescription("sans bold 12"))

        hbox.add(icon)
        hbox.add(label)

        win.show_all()
        return win
       
    def __init__(self, wnckwindow):
        self.win = wnckwindow
        self.switch_label = Switch.new_label()
        self.switch = self._create_window()

    def get_switch_label(self):
        return self.switch_label

    def get_associated_window(self):
        return self.win

    def move(self, x, y):
        self.switch.move(x, y)

    def get_size(self):
        return self.switch.get_size()

    def activate(self, timeout = None):
        """
        Activates the window associated with this switch.
        """
        if timeout is None:
            timeout = gtk.gdk.x11_get_server_time(gtk.gdk.get_default_root_window())
        self.win.activate(timeout)

    def __str__(self):
        return self.get_switch_label() +":"+ self.win.get_name()
   

class LayoutManager():
    Y_WEIGHT = 4.0 / 3.0
    MARGIN_X = 4
    MARGIN_Y = 0

    @staticmethod
    def is_overlap(box1, box2):
        return \
             abs(box1.x - box2.x) < (box1.wid + box2.wid) / 2 \
            and abs(box1.y - box2.y) < (box1.hei + box2.hei) / 2 

    @staticmethod
    def manage_layout(sws):
        """
        Changes the postions of switch-popup windows
        so that they do not overlap each other.
        """
        switches = []
        for key in Switch.LABEL_LETTERS[:len(sws)]:
            sw = sws[key]
            if sw.get_switch_label() is None: continue

            sw.x, sw.y, _, _ = sw.get_associated_window().get_geometry()
            sw.wid, sw.hei = sw.switch.get_size()
            # move a switch inside of the screen
            if sw.x < 0: sw.x = 0
            if sw.y < 0: sw.y = 0

            switches.append(sw)

        switches.sort(lambda lhs, rhs: (lhs.x - rhs.x) or (lhs.y - rhs.y))
        # move switches to left or right
        for index, switch in enumerate(switches):
            for previous in switches[:index]:
                if LayoutManager.is_overlap(switch, previous):
                    LayoutManager.is_moved_to_x = True
                    new_x_candidate = previous.x + previous.wid
                    new_y_candidate = previous.y + previous.hei
                    if new_x_candidate - switch.x <= (new_y_candidate - switch.y) * LayoutManager.Y_WEIGHT:
                        switch.x = new_x_candidate + LayoutManager.MARGIN_X
                    else:
                        switch.y = new_y_candidate + LayoutManager.MARGIN_Y

            switch.move(switch.x, switch.y)




        # Arrange switches for maximized windows
        """
        if x < 60 and y < 40:  # switch is located at top left corner
            # Note: If a taskbar is located on the left or top, 
            # x or y for a maximized window is not equal to 0.
            sw.move(x, topleftoffset) # vertically arrange switches
            topleftoffset += sw.get_size()[1]
        else:
            # not a maximize window
            sw.move(x, y)
        """


# switches for the current desktop
switches = dict()

def to_symbol(x):
    x = x.upper()
    if x == "PERIOD":
        return "."
    return x

def activate_window(widget, event):
    """
    Activates the window associated with the pressed key, 
    and finishs this program.
    """
    try:
        key = to_symbol(gtk.gdk.keyval_name(event.keyval))
        switches[key].activate()
    except (ValueError, KeyError):
        # the key is not associated with any window
        pass
    finally:
        gtk.main_quit()


# get window list
screen = wnck.screen_get_default()
screen.force_update()
for x in screen.get_windows():
    name = x.get_name()
    # window switcher is already running. 
    if name == WINDOW_NAME: sys.exit()
    # filter out panels or desktops
    if name == "xfce4-panel" or name == "デスクトップ":
        continue
    # include only windows in the current workspace
    workspace = x.get_workspace()
    if workspace == screen.get_active_workspace() or workspace is None:
        sw = Switch(x)
        switches[sw.get_switch_label()] = sw

# special cases (switch-popup windows are not used)
if len(switches) == 0:
    # there're no windows to be activated
    exit()
elif len(switches) == 1:
    # activate current window if there's only one window
    switches.popitem()[1].activate()
    exit()
elif len(switches) == 2:
    # Number of windows is 2;
    # If one window is active, activate the other.
    # If no window is active, activate the previously active window.
    # If both current and previously active window is None,
    # normal window switching is used.
    awin = screen.get_active_window()
    pawin = screen.get_previously_active_window()

    if awin is not None:
        # get non-activated window(s)
        notactive = [x for x in switches.values() if x.get_associated_window() != awin]
        # Note: awin is not always included in switches 
        # because some windows such as panels are excluded from switches. 
        # In this case len(notactive) can be two.
        if len(notactive) == 1:
            # awin is included in switches
            notactive[0].activate()
            exit()

    if pawin is not None:
        # activate previous
        Switch.activate_wnck_window(pawin)
        exit()


# arrange positions of switch popups
LayoutManager.manage_layout(switches)

# create the main window to accept a key input.
# this window is located at outside of the screen
mainwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
mainwin.set_title(WINDOW_NAME)
mainwin.set_skip_taskbar_hint(True)
mainwin.connect("key-press-event", activate_window)
mainwin.connect("focus-out-event", gtk.main_quit)
mainwin.set_decorated(False)
mainwin.set_default_size(0, 0)
mainwin.move(-50, -50)
mainwin.show()

gtk.main()
