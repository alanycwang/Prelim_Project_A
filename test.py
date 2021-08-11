import sunpy
from sunpy.net import Fido
from sunpy.net import attrs as a
import sunpy.map

import astropy.time
import astropy.units as u

import os

import numpy as np

import matplotlib.pyplot as plt

import pandas as pd

peak = astropy.time.Time("2011-06-08 16:45")
duration = 20 #B: 10, C: 12, M: 24, X: 30
number = 20
interval = duration/number * 60 * u.s #duration(min)/num_images * 60 seconds/min

location = [354, 858]

def get_file(time, wavelength):
    results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(wavelength * u.angstrom), time)
    for result in results[0]:
        fn_head = str(result['Start Time'])  # 2011-06-08 163:53:48.000
        fn_head = fn_head.replace('-', '_')  # 2011_06_08 13:53:48.000
        fn_head = fn_head.replace(':', '_')  # 2011_06_08 13_53_48.000
        fn_head = fn_head.replace(' ', 't')  # 2011_06_08t13_53_48.000
        fn_head = fn_head[:-4]  # 2011_06_08t13_53_48
        fn_head = "aia_lev1_" + str(wavelength) + "a_" + fn_head  # aia_lev1_171a_2011_06_08t13_53_48

        file = None
        for filename in os.listdir("./Data"):
            if filename.startswith(fn_head):
                file = "./Data/" + filename
                print("Found existing file at " + file)
        if file is None:
            file = Fido.fetch(result, path='./Data/{file}')
        map = sunpy.map.Map(file)
        if map.meta.original_meta['aectype'] > 0:
            return map

graphs = []
for wavelength in [171, 193, 211, 335, 94, 131]:
    # 1: iterate through images forwards, adding to list
    #     a: check 100x100 frame of pixels at the location of the peak, finding the maximum
    #     b: add to list
    # 2: repeat but backwards

    #calc bounding box for search
    xmin = max(0, location[0] - 100)
    xmax = min(1024, location[0] + 101)
    ymin = max(0, location[1] - 100)
    ymax = min(1024, location[1] + 101)

    data = []
    times = []
    print(interval)
    for i in range(int(number/2 + 0.5)):
        #get file and map, etc
        map = get_file(a.Time(peak + interval*(i + 1), peak + interval*(i + 2) + 13*u.s), wavelength)
        map = map.resample([1024, 1024]*u.pix)
        df = map.data

        if i == 0:
            ax = plt.subplot(projection=map)
            loc = [[location[0], location[1]]] * u.pix
            brightest_hpc = map.pixel_to_world(loc[:, 1], loc[:, 0])
            map.plot(ax)
            ax.plot_coord(brightest_hpc, 'wx', fillstyle='none', markersize=10)
            plt.show()

        #iterate through each pixel, recording brightest
        sum = 0
        brightest = -np.Inf
        for x in range(xmin, xmax):
            for y in range(ymin, ymax):
                brightest = max(df[x][y], brightest)
                sum += df[x][y]

        #add to list
        data.append(sum/map.meta['exptime']/map.meta.original_meta['aectype'])
        times.append(map.date.datetime)
        # print(map.meta['exptime'])
        # print(map.meta.original_meta['aiaecenf'])
        # print(map.meta.original_meta['aectype'])

    for i in range(int(number/2 + 0.5)):
        #get file, map, etc
        map = get_file(a.Time(peak - interval*(i + 1), peak - interval*i + 13*u.s), wavelength)
        map = map.resample([1024, 1024] * u.pix)
        df = map.data

        brightest = -np.Inf
        sum = 0
        for x in range(xmin, xmax):
            for y in range(ymin, ymax):
                brightest = max(df[x][y], brightest)
                sum += df[x][y]

        data.insert(0, sum/map.meta['exptime']/map.meta.original_meta['aectype'])
        times.insert(0, map.date.datetime)

plt.plot(times, data)
plt.show()
