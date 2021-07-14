import sunpy
from sunpy.net import Fido
from sunpy.net import attrs as a
import sunpy.map
from sunpy.data.sample import AIA_193_IMAGE
import sunpy.data.sample
import astropy
import astropy.units as u
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import ndimage
import numpy as np
from statistics import median
import json
from skimage.transform import resize
import datetime

class AIA():
    def __init__(self, root, style):
        self.root = root
        self.style = style
        self.frame = ttk.Frame(self.root, borderwidth=20)
        self.directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]

    def draw_image(self, map):
        self.map = map
        mask = self.map.data < self.map.max() * 0.13
        mask = ndimage.gaussian_filter(self.map.data * ~mask, 14)
        mask[mask < 100] = 0
        map2 = sunpy.map.Map(mask, self.map.meta)
        labels, _ = self.find_regions(map2.data)

        fig = plt.figure()
        ax = plt.subplot(projection=self.map)
        self.map.plot()
        plt.contour(labels)

        return fig, ax

    def find_location(self, tpeak):
        # t = astropy.time.Time(tpeak)
        # results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(193*u.angstrom), a.Time(t - 1*u.h, t + 1*u.h))
        # self.files = []
        #
        # for i in range(0, len(results[0]), 25):
        #     self.files.append(Fido.fetch(results[0][i]))

        spots = [] #list of list of [x, y, intensity, time]
        peaks = [] #list of maximum intensity and peak time for each spot

        # with open('files.json', 'w') as fh:
        #     json.dump(str(self.files), fh)

        with open('files.json', 'r') as fh:
            self.files = json.load(fh)

        self.files = self.files[1:-1].split(',')
        for i, file in enumerate(self.files):
            self.files[i] = file[len('<parfive.results.Results object at 0x000001F555763130>'):].replace('\n', '').replace('[', '').replace(']', '').replace('>', '').replace("'", '').replace('\\\\', '\\')

        for file in self.files:
            map = sunpy.map.Map(file)
            map = map.resample([1024, 1024]*u.pixel)

            median_overall = np.median(map.data)
            mask = map.data < median_overall * 60 * 0.13
            mask = ndimage.gaussian_filter(map.data * ~mask, 14)
            mask[mask < 100] = 0
            map2 = sunpy.map.Map(mask, map.meta)
            labels, region_data = self.find_regions(map2.data, map=map.data)

            for region in region_data:
                found = False

                for i, spot in enumerate(spots):
                    if (abs(region[1] - spot[-1][0]) <= len(map.data)*.1 and abs(region[2] - spot[-1][1]) <= len(map.data)*.1):
                        found = True
                        spots[i].append(region[1:] + [map.meta.get('t_obs')])

                        if peaks[i][0] < region[3]/map.meta['exptime']:
                            peaks[i][0] = region[3]/map.meta['exptime']
                            peaks[i][1] = map.meta.get('t_obs')

                        break

                if not found:
                    spots.append([region[1:] + [map.meta.get('t_obs')]])
                    peaks.append([region[3], map.meta.get('t_obs')])

            fig = plt.figure()
            ax = plt.subplot(projection=map)
            map.plot()
            plt.contour(labels)
            plt.show()

        delta = datetime.timedelta(days=5)
        closest = -1
        for i, peak in enumerate(peaks):
            t = datetime.datetime.strptime(peak[1], "%Y-%m-%dT%H:%M:%S.%fZ")
            if abs(t - tpeak) < delta:
                delta = abs(t - tpeak)
                closest = i

            if abs(t - tpeak) == delta and peak[0] > peaks[closest][0]:
                closest = i

        print(peaks)
        print(closest)
        print(spots[closest][-1][0], spots[closest][-1][1])

        fig, ax = self.draw_image(sunpy.map.Map(self.files[0]).resample([1024, 1024]*u.pixel))
        ax.plot(spots[closest][-1][0]*u.pixel, spots[closest][-1][1]*u.pixel, 'x', color='white')

        self.canvas = FigureCanvasTkAgg(fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.frame.grid(row=1, column=1)

    def find_regions(self, arr, map=None):
        regions = np.zeros(arr.shape)
        region_data = []
        idx = 1
        for i in range(len(arr)):
            for j in range(len(arr)):
                if not regions[i][j] and arr[i][j]:
                    xavg, yavg, med, area = self.bfs(i, j, arr, regions, idx, map)
                    idx += 1
                    if area > 1000:
                        region_data.append([idx, xavg, yavg, med])

        return regions, region_data

    def bfs(self, x, y, arr, regions, idx, map):
        q = [[x, y]]
        regions[x][y] = idx

        xsum = x
        ysum = y
        if map is not None:
            intensity = [map[x][y]]
        area = 1

        while len(q) > 0:
            loc = q[0]
            q.pop(0)
            for direction in self.directions:
                next = [loc[0] + direction[0], loc[1] + direction[1]]
                if next[0] > 0 and next[1] > 0 and next[0] < len(arr) and next[1] < len(arr[0]) and not regions[next[0]][next[1]] and arr[next[0]][next[1]]:
                    regions[next[0]][next[1]] = idx
                    q.append(next)
                    xsum += next[0]
                    ysum += next[1]
                    if map is not None:
                        intensity.append(map[next[0]][next[1]])
                    area += 1

        return xsum/area, ysum/area, (None if map is None else median(intensity)), area