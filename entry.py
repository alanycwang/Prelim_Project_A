import tkinter as tk
from tkinter import ttk

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches

import flare
import xrs
import navbar

class LocationSelector(tk.Toplevel):
    def __init__(self, master, title, prompt, map):
        try:
            super().__init__(master=master)
            self.title(title)
            self.resizable(width=False, height=False)
            self.configure(background="#FFFFFF")

            master.attributes('-disabled', 1)
            self.transient(master)
            self.grab_set()

            self.frame = tk.Frame(self, background="#FFFFFF")
            self.frame.pack(padx=20, pady=20)
            self.point = None

            fig = plt.figure()
            self.ax = plt.subplot(projection=map)
            map.plot(self.ax)
            plt.title(prompt)

            self.canvas = FigureCanvasTkAgg(fig, master=self.frame)
            toolbar = navbar.Navbar(self.canvas, self.frame)
            toolbar.pack(side="bottom")
            # self.canvas.mpl_connect('button_press_event', lambda e: self.click(e, self.ax.get_xlim(), self.ax.get_ylim()))
            self.canvas.get_tk_widget().pack()

            master.wait_window(self)

        finally:
            master.attributes('-disabled', 0)
            master.lift()

    def click(self, event):
        if event.xdata is None:
            return
        self.x_selection = event.xdata
        self.y_selection = event.ydata

        self.destroy()

class MultiEntry(tk.Toplevel):
    def __init__(self, master, title, prompt, layout, resizable=False):
        try:
            super().__init__(master=master)
            self.title(title)
            self.resizable(width=resizable, height=resizable)
            self.configure(background="#FFFFFF")

            master.attributes('-disabled', 1)
            self.transient(master)
            self.grab_set()

            self.frame = tk.Frame(self, background="#FFFFFF")
            self.frame.pack(padx=20, pady=20)

            p = ttk.Label(self.frame, text=prompt, background="#FFFFFF")
            p.pack(side="top", anchor="w", pady=(0, 20))

            self.frame2 = tk.Frame(self.frame, background="#FFFFFF")
            self.frame2.pack(side="top")
            self.values = []
            l = []
            for item in layout:
                if isinstance(item, list):
                    v = tk.StringVar()
                    v.set(item[1])
                    temp = ttk.Entry(self.frame2, background="#FFFFFF", width=item[0], textvariable=v)
                    self.values.append(v)
                else:
                    temp = ttk.Label(self.frame2, text=item, background="#FFFFFF")

                temp.pack(side="left")
                l.append(temp)

            b = ttk.Button(self.frame, text="Enter", command=self.destroy)
            b.pack(side="bottom", pady=(20, 0), expand=True, fill='both')

            master.wait_window(self)

        finally:
            master.attributes('-disabled', 0)
            master.lift()

class Msgbox(tk.Toplevel):
    def __init__(self, title, question, master):
        try:
            super().__init__(master=master)
            self.title(title)
            self.resizable(width=False, height=False)
            self.configure(background="#FFFFFF")

            master.attributes('-disabled', 1)
            self.transient(master)
            self.grab_set()

            self.v = None

            self.frame = tk.Frame(self, background="#FFFFFF")
            self.frame.pack(padx=20, pady=20)

            l = ttk.Label(self.frame, text=question, background="#FFFFFF")
            l.pack(side="top", pady=(0, 20))

            y = ttk.Button(self.frame, text="Yes", command=lambda: self.delete(True))
            y.pack(side="left")

            n = ttk.Button(self.frame, text="No", command=lambda: self.delete(False))
            n.pack(side="left")

            master.wait_window(self)

        finally:
            master.attributes('-disabled', 0)
            master.lift()

    def delete(self, v):
        self.v = v
        self.destroy()

class TimeSelector(tk.Toplevel):
    def __init__(self, flare, title, master=None):
        try:
            super().__init__(master=master)
            self.title(title)
            self.resizable(width=False, height=False)

            master.attributes('-disabled', 1)
            self.transient(master)
            self.grab_set()

            self.xrs(flare, title)

            master.wait_window(self)
        finally:
            master.attributes('-disabled', 0)
            master.lift()

    def xrs(self, flare, title):
        colors = ['green', 'blue', 'cyan', 'magenta', 'yellow', 'black']
        self.xrsframe = tk.Frame(self, background="#81868F", padx=1, pady=1)
        self.xrsframe.grid(row=0, column=0)
        truncated = flare.ts.truncate(flare.peak - (flare.peak - flare.start) * 2,
                                      flare.peak + (flare.end - flare.peak) * 2)
        fig, ax = plt.subplots()
        self.line = ax.plot(truncated.index, truncated.quantity('xrsb'), color='red', label="GOES 1.0--8.0 $\AA$")
        plt.yscale("log")
        ax.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)

        for i, wavelength in enumerate(flare.graphs.keys()):
            temp = ax.twinx()
            self.line += temp.plot(flare.graphs[wavelength][0], flare.graphs[wavelength][1], color=colors[i],
                                   label=f"AIA ${wavelength} \AA$")
            temp.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)

        plt.title(title)
        fig.set_size_inches(6, 3)
        labels = [line.get_label() for line in self.line]
        ax.legend(self.line, labels)

        self.xrsgraph = FigureCanvasTkAgg(fig, master=self.xrsframe)
        self.xrsgraph.get_tk_widget().pack()

        xrs.Cursor(ax, self.xrsgraph, self, flare.peak - (flare.peak - flare.start) * 2, text=True)

    def select(self, time):
        temp = Msgbox("Confrim Time", f"Is the selected time correct?\n{time.strftime('%d-%m-%y %H:%M:%S')}",
                             self)
        if (temp.v):
            self.t = time.replace(tzinfo=None)
            self.destroy()