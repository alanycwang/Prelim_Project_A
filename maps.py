import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

import astropy.time
import astropy.units as u
from astropy.io import fits

from sunpy.visualization.colormaps import cm

from skimage.transform import resize

#purely for faster movies; use Sunpy Map for coordinate system
#add functionality for:
#graphing
#cutouts
#time (astropy.time)
#flux (through flare.get_graph)


class Image():
    def __init__(self, file, flare_x, flare_y):
        with fits.open(file) as hdul:
            header = hdul[1].header
            self.exp = header['EXPTIME']
            self.time = astropy.time.Time(header['T_OBS'])
            self.wavelength = header['WAVELNTH']
            self.data = hdul[1].data/self.exp
            #print(header)

        self.flux = get_graph(self.data, flare_x, flare_y)
        self.flare_x = flare_x
        self.flare_y = flare_y

    def plot(self, clim=False, data=None):
        if data is None: data = self.data
        data = resize(data, (512, 512))
        fig, ax = plt.subplots()
        im = ax.imshow(data, cmap=cm.cmlist['sdoaia'+str(self.wavelength)], norm=PowerNorm(gamma=0.5), origin='lower')
        if clim: im.set_clim(0, {171 : 5000, 193 : 7000, 211 : 7000, 335 : 500, 94 : 300, 131 : 1000}[int(self.wavelength)])
        return fig, ax, im

    def plot_cutout(self, x, y, w, clim=None, data=None):
        if data is None: data = self.data
        data = data[int(x-w/2):int(x+w/2), int(y-w/2):int(y+w/2)]
        return self.plot(clim=clim, data=data)

    def get_flux(self, x=None, y=None, w=250):
        if (x is None and y is None) or (x == self.flare_x and y == self.flare_y):
            return self.flux
        return get_graph(self.data, x, y, w=w)

def get_graph(data, x, y, w=250, res=4096):

    xmin = max(0, x - int(w/2+ 0.5))
    xmax = min(res, x + int(w/2+ 0.5) + 1)
    ymin = max(0, y - int(w/2+ 0.5))
    ymax = min(res, y + int(w/2+ 0.5) + 1)

    sum = 0
    for i in range(int(xmin + 0.5), int(xmax + 0.5)):
        for j in range(int(ymin + 0.5), int(ymax + 0.5)):
            sum += data[j][i]
    return sum

