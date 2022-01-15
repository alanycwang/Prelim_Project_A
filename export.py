import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile

import astropy.units as u

import pickle

import matplotlib.pyplot as plt

import entry
import flare as f

#things to export:
#start/peak/end times (can edit)
#peak flux (can edit)
#peak image
#class (calculated from flux)
#location (click on image)
#background flux (do not display)
#images


class Export(tk.Toplevel):
    def __init__(self, flare, master=None):
        try:
            super().__init__(master=master)
            self.title("Export Flare")

            master.attributes('-disabled', 1)
            self.transient(master)
            self.grab_set()

            self.configure(background="#FFFFFF")
            self.frame = tk.Frame(self, background="#FFFFFF")
            self.frame.pack(padx=20, pady=20)
            self.flare = flare

            #col 1: label
            self.columnconfigure(0, weight=1)
            labels = ["Start Time: ", "Peak Time: ", "End Time: ", "Peak Flux: ", "Class: ", "Location: "]
            for i, label in enumerate(labels):
                l = ttk.Label(self.frame, text=label, background="#FFFFFF")
                l.grid(row=i, column=0, sticky="nswe")
                labels[i] = l

            #col 2: values
            self.columnconfigure(1, weight=1)

            values = [flare.start.strftime('%d-%m-%y %H:%M:%S'), flare.peak.strftime('%d-%m-%y %H:%M:%S'), flare.end.strftime('%d-%m-%y %H:%M:%S'), flare.flux, flare.classification + str(int(flare.intensity*10 + 0.5)/10)[0:3], self.flare.peak_location()]
            for i, value in enumerate(values):
                v = ttk.Label(self.frame, text=value, background="#FFFFFF")
                v.grid(row=i, column=1, sticky="nswe", padx=10)
                values[i] = v

            #col 3: edit buttons
            commands = ["edit_start", "edit_peak", "edit_end", "edit_flux", None, "edit_location"]
            for i, command in enumerate(commands):
                if command is None:
                    continue
                b = ttk.Button(self.frame, text=u'\u2630', width=3, takefocus=False, padding=-3, command=lambda: getattr(self, command)(values))
                b.grid(row=i, column=2, sticky="nswe")

            #row 6: export as file button
            e = ttk.Button(self.frame, text="Export Flare Data", takefocus=False, command=self.exp)
            e.grid(row=6, column=0, columnspan=3, sticky="nswe", pady=(20, 0))


            master.wait_window(self)
        finally:
            master.attributes('-disabled', 0)
            master.lift()

    #still need to validate return values

    def edit_start(self, values):
        temp = entry.TimeSelector(self.flare, "Select a start time:", master=self)
        self.flare.start = temp.t
        values[0].configure(text=self.flare.start.strftime('%d-%m-%y %H:%M:%S'))

    def edit_peak(self, values):
        temp = entry.TimeSelector(self.flare, "Select a peak time:", master=self)
        self.flare.peak = temp.t
        values[1].configure(text=self.flare.peak.strftime('%d-%m-%y %H:%M:%S'))

    def edit_end(self, values):
        temp = entry.TimeSelector(self.flare, "Select an end time:", master=self)
        self.flare.end = temp.t
        values[2].configure(text=self.flare.end.strftime('%d-%m-%y %H:%M:%S'))

    def edit_flux(self, values):
        temp = entry.MultiEntry(self, "Change Peak Flux", "Change Peak Flux", [[20, "{:e}".format(self.flare.flux).split('e')[0]], "e", [5, "{:e}".format(self.flare.flux).split('e')[1]]])
        self.flare.flux = float(temp.values[0].get()) * 10**float(temp.values[1].get())
        values[3].configure(text=self.flare.flux)
        self.flare.reset_class()
        self.flare.get_class()
        values[4].configure(text=self.flare.classification + str(int(self.flare.intensity*10 + 0.5)/10)[0:3])

    def edit_location(self, values):
        temp = entry.LocationSelector(self, "Select Flare Location", "Select Flare Location: ", self.flare.map)
        self.flare.coords = self.flare.map.pixel_to_world(temp.x_selection*u.pix, temp.y_selection*u.pix)
        self.flare.x_pixel = temp.x_selection
        self.flare.y_pixel = temp.y_selection
        values[5].configure(text=  f.pixel_to_coord(temp.x_selection, temp.y_selection, temp.ax))

    def exp(self):
        path = asksaveasfile(filetypes=[('Pickle Files', '*.pkl')], defaultextension=[("Pickle Files", "*.pkl")])
        pickle.dump(self.flare, open(path.name, 'wb'))
        print("saved to " + path.name)
        self.destroy()





