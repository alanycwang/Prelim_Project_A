import tkinter as tk
import screen
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import time
import _thread
import sunpy

class MovieScreen(screen.Screen):
    def __init__(self, root, style, flare):
        super().__init__(root, style)
        self.flare = flare
        self.full_image()

    def full_image(self):
        self.fullimageframe = tk.Frame(self.frame, background='#81868F', padx=1, pady=1)
        self.fullimageframe.grid(row=0, column=0)

        w = 0
        longest = 0
        for wavelength in [171, 193, 211, 335, 94, 131]:
            if wavelength in self.flare.graphs and len(self.flare.graphs[wavelength]) > longest:
                longest = len(self.flare.graphs[wavelength])
                w = wavelength

        self.full_images = []
        for image in self.flare.images[w]:
            fig = plt.figure()
            i = self.normalize(image)
            ax = plt.subplot(projection=i)
            i.plot(ax)
            plt.clim(0, 10000)

            moviecanvas = FigureCanvasTkAgg(fig, master=self.fullimageframe)
            moviecanvas.draw()
            self.full_images.append(moviecanvas)

        _thread.start_new_thread(self.cycle, ())

    def cycle(self):
        self.rect = None
        for image in self.full_images:
            image.get_tk_widget().grid(row=0, column=0)
            self.frame.update()
            image.get_tk_widget().grid_forget()
        idx = 0
        while self.active:
            self.full_images[idx].get_tk_widget().grid(row=0, column=0)
            self.frame.update()
            time.sleep(0.5)
            self.full_images[idx].get_tk_widget().grid_forget()
            idx += 1
            if idx >= len(self.full_images):
                idx = 0

    def normalize(self, image):
        return sunpy.map.Map(image.data/image.meta['exptime'], image.meta)

