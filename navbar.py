import tkinter as tk
from tkinter import ttk

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends._backend_tk import ToolTip, NavigationToolbar2Tk
from matplotlib.backend_bases import NavigationToolbar2, cursors, _api
from matplotlib import cbook

from enum import Enum

class _Mode(str, Enum):
    NONE = ""
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    SELECT = "select flare location"

    def __str__(self):
        return self.value

    @property
    def _navigate_mode(self):
        return self.name if self is not _Mode.NONE else None

class Navbar(NavigationToolbar2Tk):
    # list of toolitems to add to the toolbar, format is:
    # (
    #   text, # the text of the button (often not visible to users)
    #   tooltip_text, # the tooltip shown on hover (where possible)
    #   image_file, # name of the image for the button (without the extension)
    #   name_of_method, # name of the method in NavigationToolbar2 to call
    # )
    toolitems = (
        ('Home', 'Reset original view', str(cbook._get_data_path("images/home.png")), 'home'),
        ('Back', 'Back to previous view', str(cbook._get_data_path("images/back.png")), 'back'),
        ('Forward', 'Forward to next view', str(cbook._get_data_path("images/forward.png")), 'forward'),
        (None, None, None, None),
        ('Pan', 'Left button pans, Right button zooms\nx/y fixes axis, CTRL fixes aspect', str(cbook._get_data_path("images/move.png")), 'pan'),
        ('Zoom', 'Zoom to rectangle\nx/y fixes axis, CTRL fixes aspect', str(cbook._get_data_path("images/zoom_to_rect.png")), 'zoom'),
        ('Select', 'Toggle to select flare location', './assets/cursor.png', 'select')
    )

    def __init__(self, canvas, window, *, pack_toolbar=True):
        # Avoid using self.window (prefer self.canvas.get_tk_widget().master),
        # so that Tool implementations can reuse the methods.
        self.window = window

        tk.Frame.__init__(self, master=window, borderwidth=2,
                          width=int(canvas.figure.bbox.width), height=50)

        self._buttons = {}
        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                # Add a spacer; return value is unused.
                self._Spacer()
            else:
                self._buttons[text] = button = self._Button(
                    text,
                    image_file,
                    toggle=callback in ["zoom", "pan", "select"],
                    command=getattr(self, callback),
                )
                if tooltip_text is not None:
                    ToolTip.createToolTip(button, tooltip_text)

        # This filler item ensures the toolbar is always at least two text
        # lines high. Otherwise the canvas gets redrawn as the mouse hovers
        # over images because those use two-line messages which resize the
        # toolbar.
        label = tk.Label(master=self,
                         text='\N{NO-BREAK SPACE}\n\N{NO-BREAK SPACE}')
        label.pack(side=tk.RIGHT)

        self.message = tk.StringVar(master=self)
        self._message_label = tk.Label(master=self, textvariable=self.message)
        self._message_label.pack(side=tk.RIGHT)

        #NavigationToolbar2.__init__(self, canvas) need to modify NavigationToolbar2 __init__

        self.canvas = canvas
        canvas.toolbar = self
        self._nav_stack = cbook.Stack()
        # This cursor will be set after the initial draw.
        self._lastCursor = cursors.POINTER

        init = _api.deprecate_method_override(
            __class__._init_toolbar, self, allow_empty=True, since="3.3",
            addendum="Please fully initialize the toolbar in your subclass' "
                     "__init__; a fully empty _init_toolbar implementation may be kept "
                     "for compatibility with earlier versions of Matplotlib.")
        if init:
            init()

        self._id_press = self.canvas.mpl_connect(
            'button_press_event', self._zoom_pan_select_handler)
        self._id_release = self.canvas.mpl_connect(
            'button_release_event', self._zoom_pan_select_handler)
        self._id_drag = self.canvas.mpl_connect(
            'motion_notify_event', self.mouse_move)
        self._pan_info = None
        self._zoom_info = None

        self.mode = _Mode.NONE  # a mode string for the status bar
        self.set_history_buttons()


        if pack_toolbar:
            self.pack(side=tk.BOTTOM, fill=tk.X)

    def _Button(self, text, image_file, toggle, command):
        image = (tk.PhotoImage(master=self, file=image_file)
                 if image_file is not None else None)
        if not toggle:
            b = ttk.Button(master=self, text=text, image=image, command=command, takefocus=False)
        else:
            temp = tk.Frame(master=self, background="#adadad", padx=1, pady=1)
            temp2 = tk.Frame(master=temp, background="#e1e1e1", padx=1, pady=1)
            temp.pack(side=tk.LEFT, padx=1, pady=1)
            temp2.pack()
            var = tk.IntVar(master=self)
            b = tk.Checkbutton(
                master=temp2, text=text, image=image, command=command, variable=var, indicatoron=False, bd=0, bg="#e1e1e1")
            b.var = var
        b._ntimage = image
        b.pack(side=tk.LEFT)
        return b

    def _update_buttons_checked(self):
        # sync button checkstates to match active mode
        for text, mode in [('Zoom', _Mode.ZOOM), ('Pan', _Mode.PAN), ('Select', _Mode.SELECT)]:
            if text in self._buttons:
                if self.mode == mode:
                    self._buttons[text].select()  # NOT .invoke()
                else:
                    self._buttons[text].deselect()

    def select(self):
        """Toggle select flare mode."""
        if self.mode == _Mode.SELECT:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.SELECT
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def zoom(self, *args):
        """Toggle zoom to rect mode."""
        if self.mode == _Mode.ZOOM:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.ZOOM
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def pan(self, *args):
        """
        Toggle the pan/zoom tool.

        Pan with left button, zoom with right.
        """
        if self.mode == _Mode.PAN:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.PAN
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def _zoom_pan_select_handler(self, event):
        if self.mode == _Mode.PAN:
            if event.name == "button_press_event":
                self.press_pan(event)
            elif event.name == "button_release_event":
                self.release_pan(event)
        if self.mode == _Mode.ZOOM:
            if event.name == "button_press_event":
                self.press_zoom(event)
            elif event.name == "button_release_event":
                self.release_zoom(event)
        if self.mode == _Mode.SELECT and event.name == "button_release_event":
            self.release_select(event)

    def release_select(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            try:
                #print(event.inaxes.format_coord(event.xdata, event.ydata))
                self.window.master.click(event)

            except (ValueError, OverflowError):
                pass

    def draw_rubberband(self, event, x0, y0, x1, y1):
        height = self.canvas.figure.bbox.height
        y0 = height - y0
        y1 = height - y1
        if hasattr(self, "lastrect"):
            self.canvas._tkcanvas.delete(self.lastrect)
        self.lastrect = self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, outline='white')
