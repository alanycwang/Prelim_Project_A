import sunpy
import sunpy.map

import astropy.time
import astropy.units as u

import numpy as np

import matplotlib.pyplot as plt

from os.path import exists
import drms
import urllib.request

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

        jsoc = drms.Client()
        k, s = jsoc.query(f"aia.lev1_euv_12s[{t.to_value('fits')[:-4]}/12s][{wavelength}]", key=['T_OBS', 'WAVELNTH', 'AECTYPE'],
                          seg='image')

        #print(k)

        files = ['http://jsoc.stanford.edu' + image for image in s.image]

        # sunpy downloads the file only if another file with the same name doesn't exist (everything from drms has the same filename)
        # remember to manually download to ./data with a unique filename

        #print(k['T_OBS'][0])
        if aec and int(k['AECTYPE'][0]) <= 0:
            return self.get_file(t + 12*u.s, wavelength=wavelength, aec=aec)
        fh = f"./Data/aia.lev1_euv_12s[{k['T_OBS'][0].replace(':', '-')}][{wavelength}].fits"
        urllib.request.urlretrieve(files[0], fh)
        if not gen_map: return fh
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
            print(brightest)
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

            image = self.get_file(peak + interval*(i + 1), wavelength)
            if image is None:
                print("Skipped File at time" + str(peak + interval*(i + 1)))
                continue
            image = self.normalize(image)
            images.append(image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        for i in range(int(number/2 + 0.5)):
            if progresslabel is not None:
                progresslabel.configure(text="Downloading image " + str(count) + " of 20")
                count += 1
                progresslabel._nametowidget(progresslabel.winfo_parent()).update()

            image = self.get_file(peak - interval*(i + 1), wavelength)
            if image is None:
                print("Skipped File at time" + str(peak - interval*(i + 1)))
                continue
            image = self.normalize(image)
            images.insert(0, image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        self.images[wavelength] = images

    def get_graph(self, image, x=None, y=None):
        if x is None:
            x = self.x_pixel
        if y is None:
            y = self.y_pixel

        bbox = 250
        xmin = max(0, x - bbox)
        xmax = min(4096, x + bbox + 1)
        ymin = max(0, y - bbox)
        ymax = min(4096, y + bbox + 1)

        df = image.data
        sum = 0
        for i in range(int(xmin + 0.5), int(xmax + 0.5)):
            for j in range(int(ymin + 0.5), int(ymax + 0.5)):
                sum += df[i][j]
        return sum

    def get_graphs(self, wavelength=171, progressbar=None, progresslabel=None, x=None, y=None):
        #cant reference self in parameters
        if x is None:
            x = self.x_pixel
        if y is None:
            y = self.y_pixel

        if not wavelength in self.images:
            self.get_images(wavelength, progressbar, progresslabel)

        data = []
        times = []

        for image in self.images[wavelength]:
            sum = self.get_graph(image, x, y)

            data.append(sum)
            times.append(image.date.datetime)
        self.graphs[wavelength] = [times, data]
        self.extend_left()

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

        start_time = astropy.time.Time(self.images[171][0].date.datetime)
        i = 3
        t = [(start_time - j*interval*u.s).to_datetime() for j in range(3)]
        arr = [self.normalize(self.get_file(astropy.time.Time(time), wavelength=171, aec=False)) for time in t]
        graphs = [self.get_graph(image) for image in arr]
        f =  False
        while True:
            #print(graphs[-1])
            d = (graphs[-3] - graphs[-1]) / (t[-3] - t[-1]).seconds
            if abs(d) <= 500:
                if f:
                    break
                f = True
            else:
                f = False
            t.append((start_time - i*interval*u.s).to_datetime())
            arr.append(self.normalize(self.get_file(astropy.time.Time(t[-1]), wavelength=171, aec=False)))
            graphs.append(self.get_graph(arr[-1]))
            i += 1

        arr.reverse()
        t.reverse()
        graphs.reverse()

        self.images[171] = arr + self.images[171]
        self.graphs[171][0] = t + self.graphs[171][0]
        self.graphs[171][1] = graphs + self.graphs[171][1]

        self.background_flux = self.graphs[171][1][0]
        self.extend_right()

    def extend_right(self):
        if self.background_flux is None:
            self.extend_left()

        duration = {'B': 20, 'C': 24, 'M': 48, 'X': 60}[self.classification] * 2
        number = 20
        interval = duration / number * 60 * 2

        peak_flux = -1
        for value in self.graphs[171][1]:
            peak_flux = max(peak_flux, value)

        print(peak_flux)

        t = astropy.time.Time(self.graphs[171][0][-1])
        arr = []
        times = []
        graphs = []

        i = 0
        while(True):
            times.append((t + i*interval*u.s).to_datetime())
            arr.append(self.normalize(self.get_file(astropy.time.Time(times[-1]), wavelength=171, aec=False)))
            graphs.append(self.get_graph(arr[-1]))
            if graphs[-1] <= (peak_flux + self.background_flux)/2: break
            i += 1

        self.images[171] = self.images[171] + arr
        self.graphs[171][0] = self.graphs[171][0] + times
        self.graphs[171][1] = self.graphs[171][1] + graphs





