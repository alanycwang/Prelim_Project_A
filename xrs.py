import numpy as np
import datetime
import pandas as pd
import statistics
import os
import urllib

import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import MultiCursor

from astropy.convolution import Box1DKernel, convolve
import astropy.units as u

import sunpy
from sunpy import timeseries as ts
from sunpy.net import Fido
from sunpy.net import attrs as a
from sunpy.time import parse_time

import flare
import screen
import _thread
import flarescreen

class XRS(screen.Screen):
    def __init__(self, root, tstart, tend, from_save=False, ts=None, peaks=None, flares=[]):
        super().__init__(root)

        self.listframe = tk.Frame(self)
        self.canvasframe = ttk.Frame(self)

        self.screens = {}
        self.flare = None
        self.flares = flares
        self.ts1 = ts
        self.tstart = tstart
        self.tend = tend
        self.peaks = peaks

        self.load_text = ttk.Label(self, text="Downloading XRS Data...")
        try:
            _thread.start_new_thread(self.graph, (tstart, tend))
        except urllib.error.URLError:
            self.load_text.config(text="Something went wrong with the server. Please try again later")
            return
        except sunpy.util.datatype_factory_base.NoMatchError:
            self.load_text.config(text="Unfortunately, the downloaded file was corrupted. Please try a different date")
            return

        if len(self.flares) > 0:
            self.get_selection(None, self.flares[0])

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

        self.fig = plt.figure()
        self.ax = self.ts1.plot()

        self.fig.set_size_inches(15.63, 4)

        c = True
        for flare in self.peaks:
            color='#ff6f00'
            if c:
                color = '#ff4800'
            c = not c

            self.ax.axvline(flare.peak, color=color)
            #print(type(flare.end), type(flare.peak), flare.end)
            self.ax.axvspan(flare.start, flare.end, alpha=0.2, color=color)

        self.ax.set_xlabel('Time')
        self.ax.set_ylabel("Flux Wm$^{-2}$")
        self.ax.set_title('GOES Xray Flux')

        self.ax.legend()
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

        # self.toolbar = NavigationToolbar2Tk(self.canvas, self.canvasframe)

        cursor = MultiCursor(self.canvas, [self.ax], vertOn=True)

        self.canvas.get_tk_widget().pack()
        self.load_text.grid_forget()
        self.canvasframe.update()

        self.flareslist()

    def findpeaks_derivative(self, series):
        bg_threshold = 0.1e-9 * u.W/u.m/u.m
        peak_delta = 1e-9 * u.W/u.m/u.m
        valley_delta = -0.9e-10 * u.W/u.m/u.m

        bg_time = 0
        peaks = []
        start = 0
        peak = 0
        current = []
        flux = convolve(np.gradient(series.quantity('xrsb')), kernel=Box1DKernel(100))
        times = series.index

        find_peak = False
        found_peak = False
        for i in range(len(times))[100:-100]:
            # print(flux[i], times[i], find_peak, found_peak, find_end)

            if abs(flux[i]) <= bg_threshold and not find_peak and not found_peak:
                bg_time = times[i]

            if flux[i] > peak_delta and not find_peak and not found_peak:
                start = bg_time
                find_peak = True

            if find_peak and flux[i] < 1e-10 * u.W/u.m/u.m:
                peak = times[i]
                found_peak = True
                find_peak = False

            if found_peak and flux[i] <= valley_delta:
                found_peak = False
                current.append(flare.Flare(start, peak, self.df['xrsb'][peak]))

            to_remove = []
            for j, f in enumerate(current):
                if self.df['xrsb'][i] <= (self.df['xrsb'][f.peak] + self.df['xrsb'][f.start])/2:
                    f.end = times[i]
                    #print(f.end)
                    peaks.append(f)
                    to_remove.append(j)
            for item in reversed(to_remove):
                current.pop(item)


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

        self.list = ttk.Treeview(self.treeviewframe, selectmode="browse", columns=('#1', '#2', '#3', '#4', '#5', '#6', '#7'), height=23)
        self.list.bind('<<TreeviewSelect>>', self.get_selection)

        self.list.column("#0", minwidth=0, width=0, stretch=tk.NO)
        self.list.column("#1", minwidth=50, width=50, stretch=tk.NO)
        self.list.column("#2", minwidth=125, width=125, stretch=tk.NO)
        self.list.column("#3", minwidth=175, width=175, stretch=tk.NO)
        self.list.column("#4", minwidth=175, width=175, stretch=tk.NO)
        self.list.column("#5", minwidth=175, width=175, stretch=tk.NO)
        self.list.column("#6", minwidth=100, width=100, stretch=tk.NO)
        self.list.column("#7", minwidth=100, width=100, stretch=tk.NO)

        self.list.heading("#1", text="Class", anchor=tk.W)
        self.list.heading("#2", text="Intensity")
        self.list.heading("#3", text="Peak Time")
        self.list.heading("#4", text="Start Time")
        self.list.heading("#5", text="End Time")
        self.list.heading("#6", text="HPC X")
        self.list.heading("#7", text="HPC Y")

        # self.scrollbar = ttk.Scrollbar(self.treeviewframe, orient="vertical", command=self.list.yview)
        # self.list.configure(yscroll=self.scrollbar.set)

        for i, flare in enumerate(self.peaks):
            self.load_text2['text'] = "Processing Flare " + str(i + 1) + " of " + str(len(self.peaks)) + ":   "
            self.listframe.update()
            flare.get_class()
            flare.calc_location()
            self.list.insert("", 0, text=i, values=(flare.classification, flare.intensity, flare.peak, flare.start, flare.end, flare.x, flare.y))
            self.bar.step()
            self.listframe.update()

        self.load_text2.grid_forget()
        self.bar.grid_forget()
        self.load_frame.grid_forget()
        self.listtitle.grid(row=0, column=0)
        self.list.pack(side='left')
        # self.scrollbar.pack(side='right', fill='x')

    def get_selection(self, event, flare=None):
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
        fig = plt.figure()
        fig.set_size_inches(6.4, 4.855)
        ax = plt.subplot(projection=self.flare.map)
        self.flare.map.plot(ax)
        ax.plot_coord(self.flare.coords, 'wx', fillstyle='none', markersize=10)
        plt.colorbar()

        self.aiacanvas = FigureCanvasTkAgg(fig, master=self.aiacanvasframe)
        self.aiacanvas.draw()
        self.aiacanvas.get_tk_widget().grid(row=0, column=0)
        self.aiacanvasframe.grid(row=1, column=1, sticky="NW", padx=(20, 0))

    def next(self):
            return flarescreen.FlareScreen(self.root, self.flare, self.ts1)
