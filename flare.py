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

    def calc_location_old(self):
        if self.x is None:
            t = astropy.time.Time(self.peak)
            results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(193*u.angstrom), a.Time(t, t + 13*u.s))

            file = Fido.fetch(results[0][0], path='./Data/{file}')

            mp = sunpy.map.Map(file)
            mp = mp.resample([1024, 1024]*u.pix)

            regions, region_data = self.find_regions(mp)

            largest = Region(0, 0, 0)
            for region in region_data:
                largest = max(largest, region)

            self.coords = largest.coords
            temp = self.coords.to_string()[0].split(' ')
            self.x = temp[0]
            self.y = temp[1]
            self.map = mp

    def get_file(self, time):
        results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(171*u.angstrom), time)
        for result in results[0]:
            fn_head = str(result['Start Time'])     #2011-06-08 163:53:48.000
            fn_head = fn_head.replace('-', '_')               #2011_06_08 13:53:48.000
            fn_head = fn_head.replace(':', '_')               #2011_06_08 13_53_48.000
            fn_head = fn_head.replace(' ', 't')               #2011_06_08t13_53_48.000
            fn_head = fn_head[:-4]                  #2011_06_08t13_53_48
            fn_head = "aia_lev1_171a_" + fn_head    #aia_lev1_171a_2011_06_08t13_53_48

            file = None
            for filename in os.listdir("./Data"):
                if filename.startswith(fn_head):
                    file = "./Data/" + filename
                    print("Found existing file at " + file)
            if file is None:
                file = Fido.fetch(result, path='./Data/{file}')
            map = sunpy.map.Map(file)
            if map.meta.original_meta['aecmode'] == "ON":
                return file

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

            self.map = sunpy.map.Map(self.get_file(a.Time(t, t + 2*u.minute)))
            self.map = self.map.resample([1024, 1024] * u.pix)

            brightest = np.argwhere(self.map.data == self.map.data.max()) * u.pix
            brightest_hpc = self.map.pixel_to_world(brightest[:, 1], brightest[:, 0])
            self.coords = brightest_hpc
            temp = self.coords.to_string()[0].split(' ')
            self.x = temp[0]
            self.y = temp[1]
            self.x_pixel = brightest[0][0]
            self.y_pixel = brightest[0][1]
            print(self.x_pixel, self.y_pixel)

    def find_regions(self, mp):
        exp = mp.meta['exptime']
        print(exp)
        mask = mp.data < mp.max() * exp/2 * 0.13
        mask = ndimage.gaussian_filter(mp.data * ~mask, 10)
        mask[mask < 100] = 0
        data = sunpy.map.Map(mask, mp.meta)
        data.peek()
        data = data.data
        regions = np.zeros(data.shape)

        region_data = []
        idx = 1
        for i in range(len(regions)):
            for j in range(len(regions[i])):
                if not regions[i][j] and data[i][j]:
                    xavg, yavg, intensity, area = self.bfs(i, j, data, regions, idx, mp)

                    map_pixel = [[xavg, yavg]] * u.pix
                    print(map_pixel)
                    hpc = mp.pixel_to_world(map_pixel[:, 1], map_pixel[:, 0])
                    region_data.append(Region(hpc, intensity, area))

                    idx += 1

        return regions, region_data


    def bfs(self, x, y, data, regions, idx, mp):
        q = [[x, y]]
        xsum = x
        ysum = y
        intensity = [mp.data[x][y]]
        area = 1
        regions[x][y] = idx

        while len(q) > 0:
            cur = q[0]
            q.pop(0)

            for direction in self.directions:
                next = [cur[0] + direction[0], cur[1] + direction[1]]
                if next[0] >= 0 and next[1] >= 0 and next[0] < len(data) and next[1] < len(data[0]) and not regions[next[0]][next[1]] and data[next[0]][next[1]]:
                    q.append(next)

                    area += 1
                    intensity.append(mp.data[next[0]][next[1]])
                    regions[next[0]][next[1]] = idx
                    xsum += next[0]
                    ysum += next[1]


        return xsum/area, ysum/area, mean(intensity), area


class Region():
    def __init__(self, coords, intensity, area):
        self.coords = coords
        self.intensity = intensity
        self.area = area

    def __lt__(self, other):
        return self.intensity < other.intensity

    def __eq__(self, other):
        return self.intensity == other.intensity