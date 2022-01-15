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

from scipy import stats

class FlareScreen(screen.Screen):
    def __init__(self, root, flare, ts):
        super().__init__(root)
        self.flare = flare
        self.flare.ts = ts
        self.ts = ts
        self.left_container = tk.Frame(self)
        self.rect = None
        self.x_selection = self.flare.x_pixel
        self.y_selection = self.flare.y_pixel

        self.fig, self.ax = plt.subplots()

        if not flare.location_verified:
            self.fix_location()


        self.aia()
        self.info_box()
        self.selection_box()
        self.flux_graph()

        self.left_container.grid(row=0, column=0, padx=(0, 20), pady=(0, 20))

        self.aiaplots = {}

        self.id = "flarescreen"

    def fix_location(self):
        arr = []
        for wavelength in [171, 193, 211, 335, 94, 131]:
            x, y = self.calc_location(wavelength)
            arr.append([x, y])
        arr = np.array(arr)
        xavg = stats.trim_mean([i[0] for i in arr], 0.1)
        yavg = stats.trim_mean([i[1] for i in arr], 0.1)
        self.flare.x_pixel = xavg
        self.flare.y_pixel = yavg
        self.flare.location_verified = True

    def calc_location(self, wavelength):
        t = astropy.time.Time(self.flare.peak)
        if wavelength not in self.flare.maps:
            self.flare.maps[wavelength] = self.flare.get_file(t, wavelength)
        map = self.flare.maps[wavelength]
        brightest = np.argwhere(map.data == map.data.max())
        return brightest[0][1], brightest[0][0]

    def flux_graph(self):
        self.fig, self.ax = plt.subplots()
        plt.xticks(rotation=45)
        duration = {'B': 20, 'C': 24, 'M': 48, 'X': 60}[self.flare.classification] * 3
        self.graphframe = tk.Frame(self, background='#81868F', padx=1, pady=1)
        self.graphframe.grid(row=0, column=1, padx=(0, 20))
        times = self.ts.truncate((astropy.time.Time(self.flare.peak) - duration/2 * u.minute).to_datetime(), (astropy.time.Time(self.flare.peak) + duration/2 * u.minute).to_datetime()).index
        data = self.ts.truncate((astropy.time.Time(self.flare.peak) - duration/2 * u.minute).to_datetime(), (astropy.time.Time(self.flare.peak) + duration/2 * u.minute).to_datetime()).quantity('xrsb')
        if self.graph_derivative.get(): data = np.gradient(data)
        self.line = self.ax.plot(times, data, label="GOES XRSB 1.0--8.0 $\AA$", color='red')
        self.ax.legend()
        plt.yscale("log")
        plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        self.fig.suptitle(f"Flare at {self.flare.peak}")
        plt.xlabel("Time")
        self.fig.set_size_inches(6, 5.36)
        #self.ax.xticks(rotation=45)

        self.graph = FigureCanvasTkAgg(self.fig, master=self.graphframe)
        self.graph.draw()

        self.graph.get_tk_widget().grid(row=0, column=0)
        self.update()

    def aia(self):
        fig = plt.figure()
        self.aia_ax = plt.subplot(projection=self.flare.map)
        self.aiaframe = tk.Frame(self, background='#81868F', padx=1, pady=1)
        self.aiaframe.grid(row=0, column=2, sticky="NW")
        self.flare.map.plot(self.aia_ax)
        fig.set_size_inches(6, 5.36)
        self.aia_ax.plot_coord(self.flare.coords, 'wx', fillstyle='none', markersize=10)

        self.image = FigureCanvasTkAgg(fig, master=self.aiaframe)

        x = self.flare.x_pixel
        y = self.flare.y_pixel
        self.draw_box(x, y, 250)

        self.image.mpl_connect('button_press_event', self.click)

        self.image.get_tk_widget().grid(row=0, column=0)
        self.update()

    def info_box(self):
        self.infoframe = tk.Frame(self.left_container)
        self.infoborderframe = tk.Frame(self.infoframe, background='#81868F', padx=1, pady=1)
        self.labels = tk.Label(self.infoborderframe, padx=10, pady=10, justify="left", background='#FFFFFF', text="Class: " + "\n" + "Intensity: " + "\n" + "Start Time: " + "\n" + "Peak Time: " + "\n" + "End Time: " + "\n" + "Location: ")
        self.values = tk.Label(self.infoborderframe, padx=10, pady=10, justify="left", background='#FFFFFF', text=self.flare.classification + str(int(self.flare.intensity*10 + 0.5)/10)[0:3] + "\n" + str(self.flare.intensity)[0:10] + "\n" + self.flare.start.strftime('%d-%m-%y %H:%M:%S') + "\n" + self.flare.peak.strftime('%d-%m-%y %H:%M:%S') + "\n" + self.flare.end.strftime('%d-%m-%y %H:%M:%S') + "\n" + self.flare.peak_location())


        self.infoframe.grid(row=0, column=0, pady=(0, 20))
        self.infoborderframe.grid(row=1, column=0)
        self.labels.grid(row=0, column=0)
        self.values.grid(row=0, column=1)
        self.update()

    def selection_box(self):
        self.selectionframe = tk.Frame(self.left_container)
        self.selectionborderframe = tk.Frame(self.selectionframe, background='#81868F', padx=1, pady=1)
        self.selectioncontentframe = tk.Frame(self.selectionborderframe, background='#FFFFFF', padx=0, pady=0)
        self.selectionbuttonframe = tk.Frame(self.selectioncontentframe, background='#FFFFFF')
        self.buttons = []
        self.buttonvar = []

        self.selectiontext = tk.Label(self.selectioncontentframe, text="Select a wavelength to graph", background='#FFFFFF')
        self.selectiontext.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="NW")

        for i, wavelength in enumerate(sorted([171, 193, 211, 335, 94, 131])):
            var = tk.IntVar()
            self.buttonvar.append(var)
            button = ttk.Checkbutton(self.selectionbuttonframe, text=str(wavelength) + "   ", variable=self.buttonvar[-1], takefocus=False, command=self.update_wavelengths)
            self.buttons.append(button)
            self.buttons[-1].grid(row=int(i/3), column=int(i%3), sticky="NW")

        self.graph_derivative = tk.IntVar()
        self.graph_derivative.set(0)
        self.derivativecheckbox = ttk.Checkbutton(self.selectioncontentframe, text="Graph Derivative", variable=self.graph_derivative, takefocus=False)
        self.derivativecheckbox.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="NW")

        self.extend = tk.IntVar()
        self.extend.set(0)
        self.extendcheckbox = ttk.Checkbutton(self.selectioncontentframe, text="Refine Start/End times", variable=self.extend, command=self.checkedbox, takefocus=False)
        self.extendcheckbox.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="NW")

        self.extendselectorframe = tk.Frame(self.selectioncontentframe, background='#81868F', padx=1, pady=1)
        self.extendselectorframe.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="NW")
        self.wavelength = tk.StringVar(self)
        self.wavelength.set("")
        temp = []
        self.extendselector = ttk.OptionMenu(self.extendselectorframe, self.wavelength, *temp)
        self.extendselector.config(width=15)
        self.checkedbox()
        self.extendselector.grid(row=0, column=0)
        self.update_wavelengths()

        self.graph_button = ttk.Button(self.selectioncontentframe, text="Graph!", command=self.update_plot)

        self.graph_button.grid(row=10, column=0, padx=20, pady=(0, 20), sticky="NW")
        self.selectionframe.grid(row=1, column=0, sticky="NW")
        self.selectionborderframe.grid(row=0, column=0, sticky="NW")
        self.selectioncontentframe.grid(row=0, column=0, sticky="NW")
        self.selectionbuttonframe.grid(row=1, column=0, pady=(0, 20), padx=20, sticky="NW")

        self.update()

    def checkedbox(self):
        if self.extend.get():
            self.extendselector.configure(state='enable')
        else:
            self.extendselector.configure(state='disabled')
        self.update_idletasks()

    def update_wavelengths(self):
        selections = []
        for i, wavelength in enumerate(sorted([171, 193, 211, 335, 94, 131])):
            if self.buttonvar[i].get():
                selections.append(str(wavelength))
        self.extendselector["menu"].delete(0, "end")
        for string in selections:
            self.extendselector["menu"].add_command(label=string, command=tk._setit(self.wavelength, string))

    def update_plot(self):
        _thread.start_new_thread(self.plot_aia, ())

    def plot_aia(self):
        derivative = False
        extend = False
        if self.graph_derivative.get(): derivative = True
        if self.extend.get(): extend = True

        self.selectionframe.grid_remove()
        self.delete(self.graphframe)
        self.flux_graph()
        loadingframe = tk.Frame(self.left_container, padx=20, pady=20)
        count = 0
        for i in range(6):
            if self.buttonvar[i].get():
                count += 1
        if extend: count += 1
        wavelengthlabel = tk.Label(loadingframe, text="")
        wavelengthbar = ttk.Progressbar(loadingframe, maximum=count)
        wavelengthlabel.grid(row=0, column=0)
        wavelengthbar.grid(row=0, column=1)
        loadingframe.grid(row=1, column=0, sticky="NW")

        wavelengths = []
        colors = ['green', 'blue', 'cyan', 'magenta', 'yellow', 'black']
        lines = self.line

        if extend and self.wavelength.get() != '' and int(self.wavelength.get()) in [171, 193, 211, 335, 94, 131]:
            imagelabel = tk.Label(loadingframe, text="")
            imagebar = ttk.Progressbar(loadingframe, maximum=20)
            imagelabel.grid(row=1, column=0)
            imagebar.grid(row=1, column=1)
            wavelengthlabel.configure(text="Processing wavelength " + str(self.wavelength.get()))
            self.flare.get_graphs(int(self.wavelength.get()), progressbar=imagebar, progresslabel=imagelabel, x=self.x_selection, y=self.y_selection, extend=True)
            count += 1

        for i, wavelength in enumerate(sorted([171, 193, 211, 335, 94, 131])):
            if self.buttonvar[i].get():
                plt.yscale("log")
                imagelabel = tk.Label(loadingframe, text="")
                imagebar = ttk.Progressbar(loadingframe, maximum=20+self.flare.right_extend+self.flare.left_extend)
                imagelabel.grid(row=1, column=0)
                imagebar.grid(row=1, column=1)
                wavelengthlabel.configure(text="Processing wavelength " + str(wavelength))
                self.update()

                plt.xticks(rotation=45)

                #print(self.x_selection, self.y_selection)
                self.flare.get_graphs(wavelength, progressbar=imagebar, progresslabel=imagelabel, x=self.x_selection, y=self.y_selection)

                temp = self.ax.twinx()
                self.aiaplots[wavelength] = temp
                data = self.flare.graphs[wavelength][1]
                if derivative:
                    data = np.gradient(data)
                lines += self.aiaplots[wavelength].plot(self.flare.graphs[wavelength][0], data, color=colors[i], label=f"AIA ${wavelength} \AA$")
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
        self.selectionframe.grid()
        labels = [line.get_label() for line in lines]
        self.ax.legend(lines, labels)
        self.graph.draw()
        self.update()
        #self.start_movie()

    def click(self, event):
        if event.xdata is None:
            return
        self.x_selection = event.xdata
        self.y_selection = event.ydata
        self.draw_box(event.xdata, event.ydata, 250)

    def draw_box(self, x, y, w):
        if self.rect is not None:
            self.rect.remove()
        self.rect = patches.Rectangle((x - w/2, y - w/2), w, w, linewidth=1, edgecolor='white', facecolor='black', alpha=0.2)
        self.aia_ax.add_patch(self.rect)
        self.image.draw()
        self.update()

    def next(self):
        return moviescreen.MovieScreen(self.root, self.flare)

    def data(self):
        return 1, [self.flare, self.ts]











