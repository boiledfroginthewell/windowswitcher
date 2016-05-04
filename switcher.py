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

class switch():
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
        if len(switch.LABEL_LETTERS) <= switch._counter: return None

        # label assignment
        label = switch.LABEL_LETTERS[switch._counter]
        switch._counter += 1
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
        self.switch_label = switch.new_label()
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
    


def manage_layout(sws):
    """
    Changes the postions of switch-popup windows
    so that they do not overlap each other.
    """
    topleftoffset = 0 # y-coordinate for maximized windows
    for key in switch.LABEL_LETTERS[:len(sws)]:
        sw = sws[key]
        if sw.get_switch_label() is None: continue

        x, y, wid, hei = sw.get_associated_window().get_geometry()
        # move a switch inside of the screen
        if x < 0: x = 0
        if y < 0: y = 0

        # Arrange switches for maximized windows
        if x < 60 and y < 40:  # switch is located at top left corner
            # Note: If a taskbar is located on the left or top, 
            # x or y for a maximized window is not equal to 0.
            sw.move(x, topleftoffset) # vertically arrange switches
            topleftoffset += sw.get_size()[1]
        else:
            # not a maximize window
            sw.move(x, y)


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
        sw = switch(x)
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
        switch.activate_wnck_window(pawin)
        exit()


# arrange positions of switch popups
manage_layout(switches)

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
