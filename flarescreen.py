import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backend_bases import MouseEvent
import matplotlib.patches as patches

import astropy.units as u
import astropy.time

import screen
import datetime
import numpy as np
import _thread
import moviescreen

import time

class FlareScreen(screen.Screen):
    def __init__(self, root, flare, ts):
        super().__init__(root)
        self.flare = flare
        self.ts = ts
        self.left_container = tk.Frame(self)
        self.top_left_container = tk.Frame(self.left_container)
        self.rect = None
        self.x_selection = self.flare.x_pixel
        self.y_selection = self.flare.y_pixel

        self.fig, self.ax = plt.subplots()

        self.flux_graph()
        self.aia()
        self.info_box()
        self.selection_box()

        self.left_container.grid(row=0, column=0, padx=(0, 20), pady=(0, 20))
        self.top_left_container.grid(row=0, column=0, sticky="NW")

        self.aiaplots = {}

        self.id = "flarescreen"

    def flux_graph(self):
        plt.xticks(rotation=45)
        duration = {'B': 20, 'C': 24, 'M': 48, 'X': 60}[self.flare.classification] * 3
        self.graphframe = tk.Frame(self.left_container, background='#81868F', padx=1, pady=1)
        self.graphframe.grid(row=1, column=0)
        self.line = self.ax.plot(self.ts.truncate((astropy.time.Time(self.flare.peak) - duration/2 * u.minute).to_datetime(), (astropy.time.Time(self.flare.peak) + duration/2 * u.minute).to_datetime()).data['xrsb'], label="GOES XRS", color='red')
        self.ax.legend()
        plt.yscale("log")
        plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        self.fig.suptitle("Flare at " + str(self.flare.peak))
        plt.xlabel("Time")
        self.fig.set_size_inches(4.02, 4)
        #self.ax.xticks(rotation=45)

        self.graph = FigureCanvasTkAgg(self.fig, master=self.graphframe)
        self.graph.draw()

        self.graph.get_tk_widget().grid(row=0, column=0)
        self.update()

    def aia(self):
        fig = plt.figure()
        self.aia_ax = plt.subplot(projection=self.flare.map)
        self.aiaframe = tk.Frame(self, background='#81868F', padx=1, pady=1)
        self.aiaframe.grid(row=0, column=1, sticky="NW")
        self.flare.map.plot(self.aia_ax)
        fig.set_size_inches(6, 5.36)
        self.aia_ax.plot_coord(self.flare.coords, 'wx', fillstyle='none', markersize=10)

        self.image = FigureCanvasTkAgg(fig, master=self.aiaframe)

        self.xlim = self.aia_ax.get_xlim()
        self.ylim = self.aia_ax.get_ylim()
        xmin, xmax = self.xlim
        ymin, ymax = self.ylim
        x = self.flare.y_pixel/4096 * (xmax - xmin) + xmin
        y = self.flare.x_pixel/4096 * (ymax - ymin) + ymin
        self.draw_box(x, y, 250/4096 * (xmax - xmin))

        self.image.mpl_connect('button_press_event', self.click)

        self.image.get_tk_widget().grid(row=0, column=0)
        self.update()

    def info_box(self):
        self.infoframe = tk.Frame(self.top_left_container)
        self.infoborderframe = tk.Frame(self.infoframe, background='#81868F', padx=1, pady=1)
        self.labels = tk.Label(self.infoborderframe, padx=10, pady=10, justify="left", background='#FFFFFF', text="Class: " + "\n" + "Intensity: " + "\n" + "Start Time: " + "\n" + "Peak Time: " + "\n" + "End Time: " + "\n" + "Coordinates: ")
        self.values = tk.Label(self.infoborderframe, padx=10, pady=10, justify="left", background='#FFFFFF', text=self.flare.classification + "\n" + str(self.flare.intensity) + "\n" + str(self.flare.start) + "\n" + str(self.flare.peak) + "\n" + str(self.flare.end) + "\n" + self.flare.coords.to_string()[0])


        self.infoframe.grid(row=0, column=0, pady=(0, 20), padx=(0, 20))
        self.infoborderframe.grid(row=1, column=0)
        self.labels.grid(row=0, column=0)
        self.values.grid(row=0, column=1)
        self.update()

    def selection_box(self):
        self.selectionframe = tk.Frame(self.top_left_container)
        self.selectionborderframe = tk.Frame(self.selectionframe, background='#81868F', padx=1, pady=1)
        self.selectioncontentframe = tk.Frame(self.selectionborderframe, background='#FFFFFF', padx=10, pady=10)
        self.selectionbuttonframe = tk.Frame(self.selectioncontentframe, background='#FFFFFF')
        self.buttons = []
        self.buttonvar = []

        for i, wavelength in enumerate(sorted([171, 193, 211, 335, 94, 131])):
            var = tk.IntVar()
            self.buttonvar.append(var)
            button = ttk.Checkbutton(self.selectionbuttonframe, text=str(wavelength) + "   ", variable=self.buttonvar[-1], takefocus=False)
            self.buttons.append(button)
            self.buttons[-1].grid(row=i%3, column=int(i/3), sticky="NW")

        self.graph_button = ttk.Button(self.selectioncontentframe, text="Graph!", command=self.update_plot)

        self.graph_button.grid(row=1, column=0, pady=(5, 0))
        self.selectionframe.grid(row=0, column=1, sticky="NW")
        self.selectionborderframe.grid(row=0, column=0)
        self.selectioncontentframe.grid(row=0, column=0)
        self.selectionbuttonframe.grid(row=0, column=0)

        self.update()

    def update_plot(self):
        _thread.start_new_thread(self.plot_aia, ())

    def plot_aia(self):
        self.delete(self.graphframe)

        loadingframe = tk.Frame(self.left_container, padx=20, pady=20)
        count = 0
        for i in range(6):
            if self.buttonvar[i].get():
                count += 1
        wavelengthlabel = tk.Label(loadingframe, text="")
        wavelengthbar = ttk.Progressbar(loadingframe, maximum=count)
        wavelengthlabel.grid(row=0, column=0)
        wavelengthbar.grid(row=0, column=1)
        loadingframe.grid(row=1, column=0, sticky="NW")

        self.fig, self.ax = plt.subplots()
        wavelengths = []
        colors = ['green', 'blue', 'cyan', 'magenta', 'yellow', 'black']
        lines = self.line
        for i, wavelength in enumerate(sorted([171, 193, 211, 335, 94, 131])):
            if self.buttonvar[i].get():
                imagelabel = tk.Label(loadingframe, text="")
                imagebar = ttk.Progressbar(loadingframe, maximum=20)
                imagelabel.grid(row=1, column=0)
                imagebar.grid(row=1, column=1)
                wavelengthlabel.configure(text="Processing wavelength " + str(wavelength))
                self.update()

                plt.xticks(rotation=45)

                #print(self.x_selection, self.y_selection)
                self.flare.get_graphs(wavelength, progressbar=imagebar, progresslabel=imagelabel, x=self.x_selection, y=self.y_selection)
                temp = self.ax.twinx()
                self.aiaplots[wavelength] = temp
                lines += self.aiaplots[wavelength].plot(self.flare.graphs[wavelength][0], self.flare.graphs[wavelength][1], color=colors[i], label="AIA $" + str(wavelength) + " \AA$")
                wavelengths.append(str(wavelength))
                self.aiaplots[wavelength].tick_params(axis='y', which='both', left=False, right=False, labelleft=False,
                                                      labelright=False)
                # fig, ax = plt.subplots()
                # ax.plot(self.flare.graphs[wavelength][0], np.gradient(self.flare.graphs[wavelength][1]))
                # plt.show()

                wavelengthbar.step()
                imagebar.grid_forget()
                imagelabel.grid_forget()
                self.update()
        self.delete(loadingframe)
        self.flux_graph()


        labels = [line.get_label() for line in lines]
        self.ax.legend(lines, labels)
        self.graph.draw()
        self.update()
        #self.start_movie()

    def click(self, event):
        if event.xdata is None:
            return
        x = event.xdata
        y = event.ydata
        xmin, xmax = self.xlim
        ymin, ymax = self.ylim
        self.x_selection = 4096 * (y - ymin)/(ymax - ymin)
        self.y_selection = 4096 * (x - xmin)/(xmax - xmin)
        self.draw_box(x, y, 250/4096 * (xmax - xmin))

    def draw_box(self, x, y, w):
        if self.rect is not None:
            self.rect.remove()
        self.rect = patches.Rectangle((x - w/2, y - w/2), w, w, linewidth=1, edgecolor='white', facecolor='black', alpha=0.2)
        self.aia_ax.add_patch(self.rect)
        self.image.draw()
        self.update()

    # def start_movie(self):
    #     self.movieframe = tk.Frame(self, background='#81868F', padx=1, pady=1)
    #     self.movieframe.grid(row=0, column=2, padx=(20, 20))
    #     w = 0
    #     longest = 0
    #     for wavelength in [171, 193, 211, 335, 94, 131]:
    #         if wavelength in self.flare.graphs and len(self.flare.graphs[wavelength]) > longest:
    #             longest = len(self.flare.graphs[wavelength])
    #             w = wavelength
    #
    #     images = []
    #     for image in self.flare.images[w]:
    #         fig = plt.figure()
    #         fig.set_size_inches(6, 5.36)
    #         ax = plt.subplot(projection=image)
    #         image.plot(ax)
    #         ax.plot_coord(self.flare.coords, 'wx', fillstyle='none', markersize=10)
    #
    #         moviecanvas = FigureCanvasTkAgg(fig, master=self.movieframe)
    #         moviecanvas.draw()
    #         images.append(moviecanvas)
    #     _thread.start_new_thread(self.cycle, (images,))
    #
    # def cycle(self, images):
    #     idx = 0
    #     while self.active:
    #         images[idx].get_tk_widget().grid(row=0, column=0)
    #         self.update()
    #         time.sleep(0.5)
    #         images[idx].get_tk_widget().grid_forget()
    #         idx += 1
    #         if idx >= len(images):
    #             idx = 0

    def next(self):
        return moviescreen.MovieScreen(self.root, self.flare)

    def data(self):
        return 1, [self.flare, self.ts]











