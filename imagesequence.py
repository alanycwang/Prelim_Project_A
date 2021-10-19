import image
import numpy as np
import matplotlib.pyplot as plt

class ImageSequence(list):
    def __init__(self, files, flare_x, flare_y):
        super().__init__()
        for file in files:
            self.append(image.Image(file, flare_x, flare_y))

    def get_plotdata(self, ax, **kwargs):
        times = []
        flux = []
        for image in self:
            times.append(image.time)
            flux.append(image.get_flux(kwargs))

        return times, flux




