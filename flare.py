import sunpy
import sunpy.map

import astropy.time
import astropy.units as u

import numpy as np

import matplotlib.pyplot as plt

from os.path import exists
import drms
import urllib.request

import maps, imagesequence

class Flare():
    def __init__(self, start, peak, flux):
        self.start = start
        self.peak = peak
        self.end = None
        self.flux = flux

        self.map = None
        self.classification = None
        self.x = None
        self.y = None
        self.intensity = None
        self.x_pixel = None
        self.y_pixel = None

        self.directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]

        self.images = {}
        self.graphs = {}

        self.background_flux = None

    def __eq__(self, other):
        return self.start == other.start

    def get_class(self):
        if self.classification is None:
            if self.flux < 1e-7:
                self.classification = "A"
                self.intensity = self.flux/1e-8
            elif 1e-7 <= self.flux < 1e-6:
                self.classification = "B"
                self.intensity = self.flux / 1e-7
            elif 1e-6 <= self.flux < 1e-5:
                self.classification = "C"
                self.intensity = self.flux / 1e-6
            elif 1e-5 <= self.flux < 1e-4:
                self.classification = "M"
                self.intensity = self.flux / 1e-5
            elif 1e-4 <= self.flux:
                self.classification = "X"
                self.intensity = self.flux / 1e-4

    def get_file(self, t, wavelength=171, aec=True, gen_map=True):
        #when collecting files, get all filedata at the same time

        jsoc = drms.Client()
        k, s = jsoc.query(f"aia.lev1_euv_12s[{t.to_value('fits')[:-4]}/15s][{wavelength}]", key=['T_OBS', 'WAVELNTH', 'AECTYPE'],
                          seg='image')

        #print(k)

        files = ['http://jsoc.stanford.edu' + image for image in s.image]

        # sunpy downloads the file only if another file with the same name doesn't exist (everything from drms has the same filename)
        # remember to manually download to ./data with a unique filename

        #print(k['T_OBS'][0])
        if aec and int(k['AECTYPE'][0]) <= 0:
            return self.get_file(t + 12*u.s, wavelength=wavelength, aec=aec, gen_map=gen_map)
        fh = f"./Data/aia.lev1_euv_12s[{k['T_OBS'][0].replace(':', '-')}][{wavelength}].fits"
        #print("downloading")
        try: urllib.request.urlretrieve(files[0], fh)
        except urllib.error.URLError:
            return self.get_file(t, wavelength=wavelength, aec=aec, gen_map=gen_map)
        #print("done downloading")
        #print("working")
        if not gen_map:
            return fh
        map = sunpy.map.Map(fh)
        return map

        #except urllib.error.URLError

    def calc_location(self):
        if self.x is None:
            t = astropy.time.Time(self.peak)
            # results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(171*u.angstrom), a.Time(t, t + 2*u.minute))
            # print(results.all_colnames)
            # for result in results[0]:
            #     temp = ""
            #     for item in results.all_colnames:
            #         temp += str(result[item]) + " "
            #     print(temp)
            #     file = Fido.fetch(result, path='./Data/{file}')
            #     print(file)
            #     map = sunpy.map.Map(file)
            #     if map.meta.original_meta['aecmode'] == "ON":
            #         self.map = map
            #         break

            self.map = self.get_file(t, 171)

            brightest = np.argwhere(self.map.data == self.map.data.max())
            #print(brightest)
            brightest_hpc = self.map.pixel_to_world(brightest[:, 1]*u.pix, brightest[:, 0]*u.pix)
            self.coords = brightest_hpc
            temp = self.coords.to_string()[0].split(' ')
            self.x = temp[0]
            self.y = temp[1]
            self.x_pixel = brightest[0][0]
            self.y_pixel = brightest[0][1]
            # print(self.x_pixel, self.y_pixel)

    def get_images(self, wavelength=171, progressbar=None, progresslabel=None):
        if wavelength not in [171, 193, 211, 335, 94, 131]:
            return

        duration = {'B' : 20, 'C' : 24, 'M' : 48, 'X' : 60}[self.classification] * 3
        number = 20
        interval = duration/number * 60 * u.s
        peak = astropy.time.Time(self.peak)

        images = []
        count = 1

        for i in range(int(number/2 + 0.5)):
            if progresslabel is not None:
                progresslabel.configure(text="Downloading image " + str(count) + " of 20")
                count += 1
                progresslabel._nametowidget(progresslabel.winfo_parent()).update()

            image = self.get_file(peak + interval*(i + 1), wavelength=wavelength, gen_map=False)
            if image is None:
                print("Skipped File at time" + str(peak + interval*(i + 1)))
                continue
            #image = self.normalize(image)
            images.append(image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        for i in range(int(number/2 + 0.5)):
            if progresslabel is not None:
                progresslabel.configure(text="Downloading image " + str(count) + " of 20")
                count += 1
                progresslabel._nametowidget(progresslabel.winfo_parent()).update()

            image = self.get_file(peak - interval*(i + 1), wavelength=wavelength, gen_map=False)
            if image is None:
                print("Skipped File at time" + str(peak - interval*(i + 1)))
                continue
            #image = self.normalize(image)
            images.insert(0, image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        self.images[wavelength] = imagesequence.ImageSequence(images, self.x_pixel, self.y_pixel)

    def get_graphs(self, wavelength=171, progressbar=None, progresslabel=None, x=None, y=None):
        #cant reference self in parameters
        # if x is None:
        #     x = self.x_pixel
        # if y is None:
        #     y = self.y_pixel
        #
        if not wavelength in self.images:
            self.get_images(wavelength, progressbar, progresslabel)
        #
        # data = []
        # times = []
        #
        # for image in self.images[wavelength]:
        #     sum = map.get_graph(image, x, y)
        #
        #     data.append(sum)
        #     times.append(image.date.datetime)
        # self.graphs[wavelength] = [times, data]
        self.extend_left()

        self.graphs[wavelength] = self.images[wavelength].get_plotdata(x=x, y=y)

    def normalize(self, image):
        if image is None: return None
        return sunpy.map.Map(image.data/image.meta['exptime'], image.meta)

    def extend_left(self):
        if self.background_flux is not None:
            return
        #this doesnt make any sense anymore, but it works, so i'm leaving it
        duration = {'B': 20, 'C': 24, 'M': 48, 'X': 60}[self.classification] * 2
        number = 20
        interval = duration / number * 60 * 2

        #extend forward first to find background flux
        #average slope / current value should be less than 0.02
        #steps to consider:
        #make sure that image in the given time range exists; if not, skip to the next one
        #make sure that you never get the same image twice (to avoid divide by 0)

        start_time = self.images[171][0].time
        i = 3
        t = [(start_time - j*interval*u.s).to_datetime() for j in range(3)]
        arr = [maps.Image(self.get_file(astropy.time.Time(time), wavelength=171, aec=False, gen_map=False), self.x_pixel, self.y_pixel) for time in t]
        f =  False
        while True:
            #print(graphs[-1])
            d = (arr[-3].flux - arr[-1].flux) / (t[-3] - t[-1]).seconds
            if abs(d) <= 500:
                if f:
                    break
                f = True
            else:
                f = False
            t.append((start_time - i*interval*u.s).to_datetime())
            arr.append(maps.Image(self.get_file(astropy.time.Time(t[-1]), wavelength=171, aec=False, gen_map=False), self.x_pixel, self.y_pixel))
            i += 1
            if i > 30:
                break

        for image in arr:
            self.images[171].insert(0, image)

        self.background_flux = self.images[171][0].flux
        self.extend_right()

    def extend_right(self):
        if self.background_flux is None:
            self.extend_left()

        duration = {'B': 20, 'C': 24, 'M': 48, 'X': 60}[self.classification] * 2
        number = 20
        interval = duration / number * 60 * 2

        peak_flux = -1
        for image in self.images[171]:
            peak_flux = max(peak_flux, image.flux)

        #print(peak_flux)

        t = self.images[171][-1].time
        arr = []
        times = []

        i = 1
        while(True):
            times.append((t + i*interval*u.s).to_datetime())
            arr.append(maps.Image(self.get_file(astropy.time.Time(times[-1]), wavelength=171, aec=False, gen_map=False), self.x_pixel, self.y_pixel))
            if arr[-1].flux <= (peak_flux + self.background_flux)/2: break
            i += 1
            if i > 30:
                break

        for image in arr:
            self.images[171].append(image)





