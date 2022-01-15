import tkinter as tk
from tkinter import ttk
import screen
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import time
import _thread
import sunpy
import sunpy.map
from astropy import units as u
from astropy.coordinates import SkyCoord
import numpy as np

class MovieScreen(screen.Screen):
    def __init__(self, root, flare):
        super().__init__(root)

        self.flare = flare
        #self.full_image()
        self.options()

        self.id = "moviescreen"

    def options(self):
        self.optionsframe = tk.Frame(self, background='#81868F', padx=1, pady=1)
        self.optionsbackground = tk.Frame(self.optionsframe, background='#FFFFFF')
        self.optionsframe.grid(row=0, column=0, sticky="NW")
        self.optionsbackground.grid(row=0, column=0, sticky="NW")

        self.wavelength = tk.StringVar(self)
        self.wavelength.set("")

        selections = [""]
        for wavelength in sorted([171, 193, 211, 335, 94, 131]):
            if wavelength in self.flare.images:
                selections.append(wavelength)

        self.wavelengthlabel = tk.Label(self.optionsbackground, text='Wavelength:', background='white')
        self.wavelengthlabel.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="NW")

        self.selectorframe = tk.Frame(self.optionsbackground, background='#81868F', padx=1, pady=1)
        self.selectorframe.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="NW")
        self.wavelengthselector = ttk.OptionMenu(self.selectorframe, self.wavelength, *selections)
        self.wavelengthselector.config(width=15)
        self.wavelengthselector.grid(row=0, column=0)

        self.speedlabel = tk.Label(self.optionsbackground, text='Play Speed:', background='white')
        self.speedlabel.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="NW")

        self.speedslider = ttk.Scale(self.optionsbackground, from_=20, to=1, orient=tk.HORIZONTAL, value=2)
        self.speedslider.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="NW")

        self.usecutout = tk.IntVar()
        self.usecutout.set(0)
        self.cutoutcheckbox = ttk.Checkbutton(self.optionsbackground, text="Generate Cutouts", variable=self.usecutout, command=self.checkedbox, takefocus=False)
        self.cutoutcheckbox.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="NW")

        self.cutoutlabel = tk.Label(self.optionsbackground, text='Cutout Size: 250px', background='white')
        self.cutoutlabel.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="NW")

        self.cutoutslider = ttk.Scale(self.optionsbackground, from_=50, to=1000, orient=tk.HORIZONTAL, value=250, command=self.update_cutout, state="disabled")
        self.cutoutslider.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="NW")

        self.derivative = tk.IntVar()
        self.derivative.set(0)
        self.derivativecheckbox = ttk.Checkbutton(self.optionsbackground, text="Plot Derivative", variable=self.derivative, takefocus=False)
        self.derivativecheckbox.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="NW")

        self.playbutton = ttk.Button(self.optionsbackground, text='Play', command=self.play)
        self.playbutton.grid(row=20, column=0, pady=(0, 20))

        self.stopbutton = ttk.Button(self.optionsbackground, text='Stop', command=self.stop)
        self.stopbutton.grid(row=21, column=0, pady=(0, 20))

        self.movieframe = tk.Frame(self, background='#81868f', padx=1, pady=1)
        self.movieframe.grid(row=0, column=1, padx=20, pady=(0, 20), sticky="NW")

        self.fullimageframe = tk.Frame(self.movieframe, background='#ffffff')
        self.fullimageframe.grid(row=0, column=0, sticky="NW")

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.flare.map.plot(self.ax)
        #plt.axis('off')
        plt.title('Select the cutout location:')
        plt.autoscale(tight=True)
        plt.clim(0, 15000)
        self.imagecanvas = FigureCanvasTkAgg(self.fig, master=self.fullimageframe)
        self.imagecanvas.draw_idle()
        self.imagecanvas.get_tk_widget().grid(row=0, column=0, sticky="NW")
        self.rect = None
        self.x_selection = self.flare.x_pixel
        self.y_selection = self.flare.y_pixel
        self.rectx = self.flare.x_pixel
        self.recty = self.flare.y_pixel
        self.cutout = 250
        self.imagecanvas.mpl_connect('button_press_event', self.click)

    def checkedbox(self):
        if self.usecutout.get():
            self.cutoutslider.configure(state='enable')
            self.draw_box(self.flare.x_pixel, self.flare.y_pixel, self.cutout)
        else:
            self.cutoutslider.configure(state='disabled')
            if self.rect is not None:
                self.rect.remove()
            self.imagecanvas.draw_idle()

        self.update_idletasks()

    def play(self):
        self.playing = True
        self.imageslider = ttk.Scale(self.movieframe, from_=0, to=len(self.flare.images[int(self.wavelength.get())])-1, orient=tk.HORIZONTAL,
                                     length = 640, command=self.scroll)
        self.imageslider.grid(row=1, column=0, sticky="NW")
        self.imagecanvas.get_tk_widget().grid_forget()
        self.playbutton.configure(text="Pause", command=self.pause)
        self.idx = -1
        _thread.start_new_thread(self.full_image, (int(self.wavelength.get()),))

    def stop(self):
        self.playing = False
        self.imageslider.grid_remove()
        self.imagecanvas.get_tk_widget().grid()
        self.cutouts[self.idx].get_tk_widget().grid_forget()
        self.playbutton.configure(text="Play", command=self.play)

    def full_image(self, w):
        if self.usecutout.get():
            self.generate_cutouts(w)
            return

        self.cutouts = []
        if self.derivative.get():
            d = self.flare.images[w].raw_data()
            d = np.gradient(d, axis=0)
            clim = np.amax(d)

        for i, image in enumerate(self.flare.images[w]):
            if self.derivative.get():
                fig, ax, _ = image.plot(clim=clim, data=d[i])
            else:
                fig, ax, _ = image.plot(clim=True)
            #plt.axis('off')
            plt.autoscale(tight=True)

            moviecanvas = FigureCanvasTkAgg(fig, master=self.fullimageframe)
            moviecanvas.draw_idle()
            self.cutouts.append(moviecanvas)

        for i in range(len(self.cutouts)):
            self.cutouts[i].get_tk_widget().grid(row=0, column=0)
            self.update_idletasks()
            self.cutouts[i].get_tk_widget().grid_forget()

        _thread.start_new_thread(self.cycle, ())

    def generate_cutouts(self, w):
        self.cutouts = []

        if self.derivative.get():
            d = self.flare.images[w].raw_data()
            d = np.gradient(d, axis=0)
            clim = np.amax(d)

        for i, image in enumerate(self.flare.images[w]):
            if self.derivative.get():
                fig, ax, _ = image.plot_cutout(self.x_selection, self.y_selection, self.cutout, clim=clim, data=d[i])
            else: fig, ax, _ = image.plot_cutout(self.x_selection, self.y_selection, self.cutout, clim=True)
            plt.autoscale(tight=True)

            moviecanvas = FigureCanvasTkAgg(fig, master=self.fullimageframe)
            moviecanvas.draw_idle()
            self.cutouts.append(moviecanvas)

        for i in range(len(self.cutouts)):
            self.cutouts[i].get_tk_widget().grid(row=0, column=0)
            self.update_idletasks()
            self.cutouts[i].get_tk_widget().grid_forget()

        _thread.start_new_thread(self.cycle, ())

    def cycle(self):
        while self.active and self.playing:
            self.update_image((self.idx + 1)%len(self.cutouts))
            time.sleep(self.speedslider.get()/10)

    def update_image(self, i, last=None):
        self.cutouts[self.idx].get_tk_widget().grid_forget()
        self.cutouts[i].get_tk_widget().grid(row=0, column=0)
        self.update_idletasks()
        self.idx = i
        self.imageslider.configure(value=i)

    def pause(self):
        if not self.playing: return
        self.playing = False
        self.playbutton.configure(text="Play", command=self.cont)

    def cont(self):
        self.playing = True
        self.playbutton.configure(text="Pause", command=self.pause)
        _thread.start_new_thread(self.cycle, ())

    def scroll(self, _):
        self.pause()
        idx = int(self.imageslider.get() + 0.5)
        self.update_image(idx)

    def click(self, event):
        if not self.usecutout.get() or event is None or event.xdata is None:
            return
        self.x_selection = event.xdata
        self.y_selection = event.ydata
        self.draw_box(event.xdata, event.ydata, self.cutout)

    def draw_box(self, x, y, w):
        if self.rect is not None:
            try: self.rect.remove()
            except ValueError: pass
        self.rect = patches.Rectangle((x - w / 2, y - w / 2), w, w, linewidth=1, edgecolor='white', facecolor='black',
                                      alpha=0.2)
        self.ax.add_patch(self.rect)
        self.imagecanvas.draw_idle()
        self.update_idletasks()

    def update_cutout(self, _):
        self.cutout = self.cutoutslider.get()
        self.cutoutlabel.configure(text=f"Cutout Size: {int(self.cutout)}px")
        self.click(None)

    def data(self):
        return 0, [self.flare]
