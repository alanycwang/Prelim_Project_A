import tkinter as tk
from tkinter import ttk

import screen, flare, flarescreen, moviescreen

class FlareInfo(screen.Screen):
    def __init__(self, root, flare):
        super().__init__(root)

        self.flare  = flare

        self.show_info()

        self.id = "flareinfo"

    def show_info(self):
        infoborder = tk.Frame(self, background='#81868F', padx=1, pady=1)
        infoborder.grid(row=0, column=0, sticky="NW")

        infoframe = tk.Frame(infoborder, background='#FFFFFF')
        infoframe.grid(row=0, column=0, sticky="NW")

        info = tk.Frame(infoframe, background='#FFFFFF')
        info.pack(padx=20, pady=20)

        #col 1: label
        info.columnconfigure(0, weight=1)
        labels = ["Start Time: ", "Peak Time: ", "End Time: ", "Peak Flux: ", "Class: ", "Location: "]
        for i, label in enumerate(labels):
            l = ttk.Label(info, text=label, background="#FFFFFF")
            l.grid(row=i, column=0, sticky="nswe")
            labels[i] = l

        #col 2: values
        info.columnconfigure(1, weight=1)
        flare = self.flare
        values = [flare.start.strftime('%d-%m-%y %H:%M:%S'), flare.peak.strftime('%d-%m-%y %H:%M:%S'),
                  flare.end.strftime('%d-%m-%y %H:%M:%S'), flare.flux,
                  flare.classification + str(int(flare.intensity * 10 + 0.5) / 10)[0:3], self.flare.peak_location()]
        for i, value in enumerate(values):
            v = ttk.Label(info, text=value, background="#FFFFFF")
            v.grid(row=i, column=1, sticky="nswe", padx=(10, 0))
            values[i] = v

        #buttons:
        labels = ['View Images', 'Graph Data']
        functions = [self.new_movie, self.new_flarescreen]
        for i in range(len(labels)):
            b = ttk.Button(info, text=labels[i], command=functions[i])
            b.grid(row=6+i, column=0, columnspan=3, sticky="nswe", pady=(10, 0), padx=20)

    def new_movie(self):
        new = moviescreen.MovieScreen(self.root, self.flare)
        self.root.add(new, text=new.id)
        self.root.select(tab_id=self.root.index("end")-1)
        self.update_idletasks()

    def new_flarescreen(self):
        new = flarescreen.FlareScreen(self.root, self.flare, self.flare.ts)
        self.root.add(new, text=new.id)
        self.root.select(tab_id=self.root.index("end") - 1)
        self.update_idletasks()