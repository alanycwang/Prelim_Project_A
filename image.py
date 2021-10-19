#purely for faster movies; use Sunpy Map for coordinate system
#add functionality for:
#graphing
#cutouts
#time (astropy.time)
#flux (through flare.get_graph)

import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

import astropy.time
import astropy.units as u
from astropy.io import fits

from sunpy.visualization.colormaps import cm


class Image():
    def __init__(self, file, flare_x, flare_y):
        with fits.open(file) as hdul:
            self.header = hdul[1].header
            self.exp = self.header['EXPTIME']
            self.time = astropy.time.Time(self.header['DATE-OBS'])
            self.wavelength = self.header['WAVELNTH']
            self.data = hdul[1].data/self.exp
            #print(self.header)

        self.flux = get_graph(self.data, flare_x, flare_y)
        self.flare_x = flare_x
        self.flare_y = flare_y

    def plot(self, clim=None, data=None):
        if data is None: data = self.data

        fig, ax = plt.subplots()
        ax.imshow(data, cmap=cm.cmlist['sdoaia'+str(self.wavelength)], norm=PowerNorm(gamma=0.5), origin='lower')
        if clim is not None: plt.clim(0, clim)
        return fig, ax

    def plot_cutout(self, x, y, w, clim=None):
        data = self.data[x-w/2:x+w/2, y-w/2:y+w/2]
        self.plot(clim=clim, data=data)

    def get_flux(self, x=None, y=None, w=250):
        if (x is None and y is None) or (x == self.flare_x and y == self.flare_y):
            return self.flux
        return get_graph(self.data, x, y, w=w)

def get_graph(data, x, y, w=250, res=4096):
    xmin = max(0, x - w)
    xmax = min(res, x + w + 1)
    ymin = max(0, y - w)
    ymax = min(res, y + w + 1)

    sum = 0
    for i in range(int(xmin + 0.5), int(xmax + 0.5)):
        for j in range(int(ymin + 0.5), int(ymax + 0.5)):
            sum += data[i][j]
    return sum

