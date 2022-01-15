import numpy as np
import os
import urllib
import pytz

import tkinter as tk
from tkinter import ttk

import matplotlib.dates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from astropy.convolution import Box1DKernel, convolve
import astropy.units as u

import sunpy
from sunpy import timeseries as ts
from sunpy.net import Fido
from sunpy.net import attrs as a

import flare
import screen
import _thread
import flarescreen
import entry

class XRS(screen.Screen):
    def __init__(self, root, tstart, tend, ts=None, peaks=None):
        super().__init__(root)

        self.listframe = tk.Frame(self)
        self.canvasframe = ttk.Frame(self)

        self.screens = {}
        self.flare = None
        self.tstart = tstart
        self.tend = tend
        self.ts1 = ts
        self.peaks = peaks
        self.ready = True

        self.load_text = ttk.Label(self, text="Downloading XRS Data...")
        try:
            _thread.start_new_thread(self.graph, (tstart, tend))
        except urllib.error.URLError:
            self.load_text.config(text="Something went wrong with the server. Please try again later")
            return
        except sunpy.util.datatype_factory_base.NoMatchError:
            self.load_text.config(text="Unfortunately, the downloaded file was corrupted. Please try a different date")
            return

        self.id = "xrs"

    def getTS(self, tstart, tend):
        if tstart < "2020-03-01 00:00" and tend > "2020-03-01 00:00":
            return self.getTS(tstart, "2020-02-29 23:59").concatenate(self.getTS("2020-03-01 00:00", tend))
        result = Fido.search(a.Time(tstart, tend), a.Instrument("XRS"), a.goes.SatelliteNumber(16 if tstart > "2020-03-01 00:00" else 15))

        files = []

        for file in result[0]:
            idx = -1
            path = str(file['url'])
            while path[idx] != '/':
                idx -= 1
            path = './Data/' + path[idx+1:]
            if os.path.exists(path):
                print(f'Found existing file at {path}')
                files.append(path)
            else:
                files.append(Fido.fetch(file, path='Data/{file}'))

        try:
            return ts.TimeSeries(files, concatenate=True)
        except:
            return ts.TimeSeries(Fido.fetch(result), concatenate=True)

    def graphTS(self, tstart, tend):
        if self.ts1 is None:
            self.ts1 = self.getTS(tstart, tend)
            self.ts1 = self.ts1.truncate(tstart, tend)

            # fig, ax = plt.subplots()
            # ax.plot(self.ts1.index, convolve(np.gradient(self.ts1.quantity('xrsb')), kernel=Box1DKernel(100)))
            # fig.autofmt_xdate()
            # plt.show()

            self.ts1.data['xrsa'] = convolve(self.ts1.quantity('xrsa'), kernel=Box1DKernel(100))
            self.ts1.data['xrsb'] = convolve(self.ts1.quantity('xrsb'), kernel=Box1DKernel(100))
            self.df = self.ts1.to_dataframe()

            self.peaks = self.findpeaks_derivative(self.ts1)

        self.fig, self.ax = plt.subplots()
        self.ax.plot(self.ts1.index, self.ts1.quantity('xrsa'), label="0.5--4.0 $\AA$", color='red')
        self.ax.plot(self.ts1.index, self.ts1.quantity('xrsb'), label="1.0--8.0 $\AA$", color='blue')
        self.ax.legend(loc=1)
        plt.yscale('log')


        self.fig.set_size_inches(14.38, 4)

        self.ax.set_xlabel('Time')
        self.ax.set_ylabel("Flux Wm$^{-2}$")
        self.ax.set_title('GOES Xray Flux')

        self.ax.grid(True)
        self.ax.semilogy()
        self.ax.set_ylim(10e-10, 10e-3)

        self.ax2 = self.ax.secondary_yaxis('right')
        self.ax2.set_ylim(self.ax.get_ylim())
        self.ax2.set_yticks(3.162*np.array([1e-4, 1e-5, 1e-6, 1e-7, 1e-8]))
        self.ax2.set_yticklabels(['X', 'M', 'C', 'B', 'A'])
        self.ax2.minorticks_off()

    def graph(self, tstart, tend):
        self.canvasframe = tk.Frame(self, background='#81868F', padx=1, pady=1)

        self.canvasframe.grid(row=0, column=0)
        self.load_text.grid(row=0, column=1, sticky="NW")
        self.load_text.update()


        self.graphTS(tstart, tend)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvasframe)
        self.canvas.draw()
        self.cursor = Cursor(self.ax, self.canvas, self.canvasframe, tstart, flares=self.peaks, text=True)

        # self.toolbar = NavigationToolbar2Tk(self.canvas, self.canvasframe)

        self.canvas.get_tk_widget().pack()
        self.load_text.grid_forget()
        self.canvasframe.update()

        self.flareslist()

    def findpeaks_derivative(self, series):
        bg_threshold = 0.1e-9 * u.W / u.m / u.m
        peak_delta = 1e-9 * u.W / u.m / u.m
        valley_delta = -1e-10 * u.W / u.m / u.m
        bg_time = 0
        peaks = []
        start = 0
        peak = 0
        flux = convolve(np.gradient(series.quantity('xrsb')), kernel=Box1DKernel(100))
        times = series.index
        find_peak = False
        found_peak = False
        find_end = False
        for i in range(len(times)):
            # print(flux[i], times[i], find_peak, found_peak, find_end)
            if abs(flux[i]) <= bg_threshold and not find_peak and not found_peak and not find_end:
                bg_time = times[i]
            if flux[i] > peak_delta and not find_peak and not found_peak and not find_end:
                start = bg_time
                find_peak = True
            if find_peak and flux[i] < 1e-10 * u.W / u.m / u.m:
                peak = times[i]
                found_peak = True
                find_peak = False
            if found_peak and flux[i] <= valley_delta:
                find_end = True
                found_peak = False
            if find_end and flux[i] >= -bg_threshold:
                find_end = False
                peaks.append(flare.Flare(start, peak, times[i], self.df['xrsb'][peak]))

        if peaks[0].start == 0:
            return peaks[1:]
        return peaks

    def flareslist(self):
        self.listframe = ttk.Frame(self)
        self.listtitle = ttk.Label(self.listframe, text="")
        self.treeviewframe = ttk.Frame(self.listframe)
        self.load_frame = ttk.Frame(self.listframe)
        self.bar = ttk.Progressbar(self.load_frame, maximum = len(self.peaks))
        self.load_text2 = ttk.Label(self.load_frame, text="")

        self.treeviewframe.grid(row=1, column=0)
        self.listframe.grid(row=1, column=0, sticky="NW")
        self.load_frame.grid(row=0, column=0, pady=20)
        self.load_text2.grid(row=0, column=0, sticky="NW")
        self.bar.grid(row=0, column=1, sticky="NW")
        self.listframe.update()

        self.list = ttk.Treeview(self.treeviewframe, selectmode="browse", columns=('#1', '#2', '#3', '#4'), height=23)
        self.list.bind('<<TreeviewSelect>>', self.get_selection)

        self.list.column("#0", minwidth=0, width=0, stretch=tk.NO)
        self.list.column("#1", minwidth=100, width=100, stretch=tk.NO)
        self.list.column("#2", minwidth=225, width=225, stretch=tk.NO)
        self.list.column("#3", minwidth=225, width=225, stretch=tk.NO)
        self.list.column("#4", minwidth=225, width=225, stretch=tk.NO)

        self.list.heading("#1", text="Class", anchor=tk.W)
        self.list.heading("#2", text="Peak Time")
        self.list.heading("#3", text="Start Time")
        self.list.heading("#4", text="End Time")

        # self.scrollbar = ttk.Scrollbar(self.treeviewframe, orient="vertical", command=self.list.yview)
        # self.list.configure(yscroll=self.scrollbar.set)

        for i, flare in enumerate(self.peaks):
            self.load_text2['text'] = "Processing Flare " + str(i + 1) + " of " + str(len(self.peaks)) + ":   "
            self.listframe.update()
            flare.get_class()
            self.list.insert("", 0, text=i, values=(flare.classification + str(int(flare.intensity*10 + 0.5)/10)[:3], flare.peak, flare.start, flare.end, flare.x, flare.y))
            self.bar.step()
            self.listframe.update()

        self.load_text2.grid_forget()
        self.bar.grid_forget()
        self.load_frame.grid_forget()
        self.listtitle.grid(row=0, column=0)
        self.list.pack(side='left')
        # self.scrollbar.pack(side='right', fill='x')
        self.cursor.set_list(self.list)

    def get_selection(self, _, flare=None):
        try:
            self.aiacanvas.get_tk_widget().grid_forget()
        except AttributeError:
            pass
        except tk.TclError:
            pass

        self.aiacanvasframe = tk.Frame(self.listframe, background='#81868F', padx=1, pady=1)

        if flare is None:
            self.flare = self.peaks[int(self.list.item(self.list.focus())['text'])]
        else:
            self.flare = flare

        _thread.start_new_thread(self.draw_selection, ())

    def draw_selection(self):
        self.ready = False
        fig = plt.figure()
        fig.set_size_inches(6.4, 4.855)
        tempcanvas = tk.Canvas(self.aiacanvasframe, bg="white", width=int(6.4*fig.dpi+0.5), height=int(4.855*fig.dpi+0.5), borderwidth=0)
        tempcanvas.create_text(100, 100, text="loading...")
        tempcanvas.grid(row=0, column=0)
        self.aiacanvasframe.grid(row=1, column=1, sticky="NW", padx=(20, 0))
        self.update()
        self.flare.calc_location()
        ax = plt.subplot(projection=self.flare.map)
        self.flare.map.plot(ax)
        ax.plot_coord(self.flare.coords, 'wx', fillstyle='none', markersize=10)
        plt.clim(0, 15000)
        plt.colorbar()
        tempcanvas.grid_remove()
        self.aiacanvas = FigureCanvasTkAgg(fig, master=self.aiacanvasframe)
        self.aiacanvas.draw()
        self.aiacanvas.get_tk_widget().grid(row=0, column=0)
        self.update()
        self.ready = True

    def next(self):
        if self.flare is None or not self.ready or self.flare.map is None:
            return "error"
        return flarescreen.FlareScreen(self.root, self.flare, self.ts1)

    def data(self):
        return 2, [self.peaks, [self.ts1, self.tstart, self.tend]]

class Cursor:
    def __init__(self, ax, canvas, frame, time, flares=None, text=False, x=0.01, y=0.95):
        self.list = None
        self.flares = flares
        if flares is None: self.flares = []
        self.ax = ax
        self.background = None
        self.line = ax.axvline(time)
        self.text = False
        if text:
            self.text = ax.text(x, y, '', transform=ax.transAxes, va='top')
        self.lines = []
        c = True
        for flare in self.flares:
            color = '#ff6f00'
            if c:
                color = '#ff4800'
            c = not c

            temp = []
            temp.append(self.ax.axvline(flare.peak, color=color))
            # print(type(flare.end), type(flare.peak), flare.end)
            temp.append(self.ax.axvspan(flare.start, flare.end, alpha=0.2, color=color))
            temp.append(c)
            self.lines.append(temp)
        canvas.mpl_connect('motion_notify_event', self.update)
        canvas.mpl_connect('button_press_event', self.click)
        self.canvas = canvas
        self.frame = frame
        self._creating_background = False
        self.on_draw(None)
        canvas.mpl_connect('draw_event', self.on_draw)

    def set_visibility(self, visible):
        if self.line.get_visible() == visible:
            return False
        self.line.set_visible(visible)
        if self.text:
            self.text.set_visible(visible)
        return True

    def set_all_visibility(self, visible):
        self.set_visibility(visible)
        if len(self.flares) == 0 or not len(self.lines) == 0 or self.lines[0][0].get_visible() == visible:
            return
        for line in self.lines:
            line[0].set_visible(visible)
            line[1].set_visible(visible)

    def update(self, event):
        if self.background is None:
            self.on_draw(None)
        if not event.inaxes:
            self.set_visibility(False)
            return
        if self.set_visibility(True):
            self.canvas.restore_region(self.background)
            self.canvas.blit(self.ax.bbox)
            self.frame.update_idletasks()
        self.line.set_xdata(event.xdata)
        if self.text:
            self.text.set_text(matplotlib.dates.num2date(event.xdata).strftime('%d-%m-%y %H:%M'))
        t = matplotlib.dates.num2date(event.xdata)
        for i, flare in enumerate(self.flares):
            if t <= flare.end.replace(tzinfo=pytz.UTC) and t >= flare.start.replace(tzinfo=pytz.UTC):
                self.lines[i][1].set_alpha(0.5)
            else:
                self.lines[i][1].set_alpha(0.2)

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        if self.text:
            self.ax.draw_artist(self.text)
        for line in self.lines:
            self.ax.draw_artist(line[1])
        self.canvas.blit(self.ax.bbox)
        self.frame.update_idletasks()

    def on_draw(self, _):
        if self._creating_background:
            return
        self._creating_background = True
        self.set_all_visibility(False)
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.set_all_visibility(True)
        self._creating_background = False

    def set_list(self, list):
        self.list = list

    def click(self, event):
        if self.list is not None:
            t = matplotlib.dates.num2date(event.xdata)
            for i, flare in enumerate(self.flares):
                if t <= flare.end.replace(tzinfo=pytz.UTC) and t >= flare.start.replace(tzinfo=pytz.UTC):
                    id = self.list.get_children()[-(i+1)]
                    self.list.focus(id)
                    self.list.selection_set(id)
                    return

        elif isinstance(self.frame, entry.TimeSelector):
            t = matplotlib.dates.num2date(event.xdata)
            self.frame.select(t)


