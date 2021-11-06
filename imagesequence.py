import maps
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

class ImageSequence(list):
    def __init__(self, files, flare_x, flare_y):
        super().__init__()
        for file in files:
            self.append(maps.Image(file, flare_x, flare_y))

    def get_plotdata(self, x, y):
        times = []
        flux = []
        for image in self:
            times.append(image.time.to_datetime())
            flux.append(image.get_flux(x, y))

        return [times, flux]




