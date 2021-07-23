import sunpy
from sunpy.net import Fido
from sunpy.net import attrs as a
import sunpy.map

import astropy.time
import astropy.units as u

from scipy import ndimage

import numpy as np

from statistics import median, mean

import os

class Flare():
    def __init__(self, start, peak, end, flux):
        self.start = start
        self.peak = peak
        self.end = end
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

    # def calc_location_old(self):
    #     if self.x is None:
    #         t = astropy.time.Time(self.peak)
    #         results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(193*u.angstrom), a.Time(t, t + 13*u.s))
    #
    #         file = Fido.fetch(results[0][0], path='./Data/{file}')
    #
    #         mp = sunpy.map.Map(file)
    #         mp = mp.resample([1024, 1024]*u.pix)
    #
    #         regions, region_data = self.find_regions(mp)
    #
    #         largest = Region(0, 0, 0)
    #         for region in region_data:
    #             largest = max(largest, region)
    #
    #         self.coords = largest.coords
    #         temp = self.coords.to_string()[0].split(' ')
    #         self.x = temp[0]
    #         self.y = temp[1]
    #         self.map = mp

    def get_file(self, time, wavelength):
        results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(wavelength*u.angstrom), time)
        for result in results[0]:
            fn_head = str(result['Start Time'])     #2011-06-08 163:53:48.000
            fn_head = fn_head.replace('-', '_')               #2011_06_08 13:53:48.000
            fn_head = fn_head.replace(':', '_')               #2011_06_08 13_53_48.000
            fn_head = fn_head.replace(' ', 't')               #2011_06_08t13_53_48.000
            fn_head = fn_head[:-4]                  #2011_06_08t13_53_48
            fn_head = "aia_lev1_" + str(wavelength) + "a_" + fn_head    #aia_lev1_171a_2011_06_08t13_53_48

            file = None
            for filename in os.listdir("./Data"):
                if filename.startswith(fn_head):
                    file = "./Data/" + filename
                    print("Found existing file at " + file)
            if file is None:
                file = Fido.fetch(result, path='./Data/{file}')
            try:
                map = sunpy.map.Map(file)
            except RuntimeError:
                return None
            if map.meta.original_meta['aectype'] > 0:
                return map

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

            self.map = self.get_file(a.Time(t, t + 2*u.minute), 193)

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

            image = (self.get_file(a.Time(peak + interval*(i + 1), peak + interval*(i + 2) + 1*u.minute), wavelength))
            if image is None:
                print("Skipped File at time" + str(peak + interval*(i + 1)))
                continue
            images.append(image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        for i in range(int(number/2 + 0.5)):
            if progresslabel is not None:
                progresslabel.configure(text="Downloading image " + str(count) + " of 20")
                count += 1
                progresslabel._nametowidget(progresslabel.winfo_parent()).update()

            image = self.get_file(a.Time(peak - interval*(i + 1), peak - interval*i + 1*u.minute), wavelength)
            if image is None:
                print("Skipped File at time" + str(peak - interval*(i + 1)))
                continue
            images.insert(0, image)
            if progressbar is not None:
                progressbar.step()
                progressbar._nametowidget(progressbar.winfo_parent()).update()

        self.images[wavelength] = images

    def get_graphs(self, wavelength=171, progressbar=None, progresslabel=None, x=None, y=None):
        if x is None:
            x = self.x_pixel
        if y is None:
            y = self.y_pixel

        if not wavelength in self.images:
            self.get_images(wavelength, progressbar, progresslabel)

        bbox = 250
        xmin = max(0, x - bbox)
        xmax = min(4096, x + bbox + 1)
        ymin = max(0, y - bbox)
        ymax = min(4096, y + bbox + 1)

        data = []
        times = []

        for image in self.images[wavelength]:
            df = image.data
            sum = 0

            for i in range(int(xmin + 0.5), int(xmax + 0.5)):
                for j in range(int(ymin + 0.5), int(ymax + 0.5)):
                    sum += df[i][j]

            data.append(sum/image.meta['exptime']/image.meta.original_meta['aectype'])
            times.append(image.date.datetime)

        self.graphs[wavelength] = [times, data]





    # def calc_location_old(self):
    #     window = 200
    #     t = astropy.time.Time(self.peak)
    #     self.map = self.get_file(a.Time(t, t + 2*u.minute))
    #     self.map = self.map.resample([1024, 1024] * u.pix)
    #
    #
    #     _, regions, data = self.find_regions(self.map)
    #     idx = 0
    #     brightest = 0
    #     df = data
    #     for n, region in enumerate(regions):
    #         xmin = int(region.x - int(window/2 + 0.5))
    #         xmax = int(region.x + int(window/2 + 0.5))
    #         ymin = int(region.y - int(window/2 + 0.5))
    #         ymax = int(region.y + int(window/2 + 0.5))
    #         sum = 0
    #         area = 0
    #         for i in range(xmin, xmax):
    #             for j in range(ymin, ymax):
    #                 if df[i][j] > 10:
    #                     sum += df[i][j]
    #                     area += 1
    #         if sum/area > brightest:
    #             brightest = sum/area
    #             idx = n
    #
    #     self.coords = regions[idx].coords
    #     temp = self.coords.to_string()[0].split(' ')
    #     self.x = temp[0]
    #     self.y = temp[1]
    #     self.x_pixel = regions[idx].x
    #     self.y_pixel = regions[idx].y

    # def find_regions(self, mp):
    #     exp = mp.meta['exptime']
    #     print(exp)
    #     mask = mp.data < mp.max() * exp/2 * 0.13
    #     mask = ndimage.gaussian_filter(mp.data * ~mask, 2)
    #     mask[mask < 100] = 0
    #     data = sunpy.map.Map(mask, mp.meta)
    #     data.peek()
    #     data = data.data
    #     regions = np.zeros(data.shape)
    #
    #     region_data = []
    #     idx = 1
    #     for i in range(len(regions)):
    #         for j in range(len(regions[i])):
    #             if not regions[i][j] and data[i][j]:
    #                 xavg, yavg, area = self.bfs(i, j, data, regions, idx, mp)
    #
    #                 map_pixel = [[xavg, yavg]] * u.pix
    #                 # print(map_pixel)
    #                 hpc = mp.pixel_to_world(map_pixel[:, 1], map_pixel[:, 0])
    #                 region_data.append(Region(hpc, area, xavg, yavg))
    #
    #                 idx += 1
    #
    #     return regions, region_data, data
    #
    # def bfs(self, x, y, data, regions, idx, mp):
    #     q = [[x, y]]
    #     xsum = x
    #     ysum = y
    #     area = 1
    #     regions[x][y] = idx
    #
    #     while len(q) > 0:
    #         cur = q[0]
    #         q.pop(0)
    #
    #         for direction in self.directions:
    #             next = [cur[0] + direction[0], cur[1] + direction[1]]
    #             if next[0] >= 0 and next[1] >= 0 and next[0] < len(data) and next[1] < len(data[0]) and not regions[next[0]][next[1]] and data[next[0]][next[1]]:
    #                 q.append(next)
    #
    #                 area += 1
    #                 regions[next[0]][next[1]] = idx
    #                 xsum += next[0]
    #                 ysum += next[1]
    #
    #
    #     return xsum/area, ysum/area, area


# class Region():
#     def __init__(self, coords, area, x, y):
#         self.coords = coords
#         self.area = area
#         self.x = x
#         self.y = y
#
#     def __lt__(self, other):
#         return self.intensity < other.intensity
#
#     def __eq__(self, other):
#         return self.intensity == other.intensity