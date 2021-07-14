import sunpy
from sunpy.net import Fido
from sunpy.net import attrs as a

import astropy.time
import astropy.units as u

import os

import numpy as np

import matplotlib.pyplot as plt

peak = astropy.time.Time("2011-06-08 16:45:01.655082")
duration = 10 #B: 10, C: 12, M: 24, X: 30
number = 20
interval = duration/number * 60 * u.s #duration(min)/num_images * 60 seconds/min

location = [362, 857]

def get_file(time):
    results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(171 * u.angstrom), time)
    for result in results[0]:
        fn_head = str(result['Start Time'])  # 2011-06-08 163:53:48.000
        fn_head = fn_head.replace('-', '_')  # 2011_06_08 13:53:48.000
        fn_head = fn_head.replace(':', '_')  # 2011_06_08 13_53_48.000
        fn_head = fn_head.replace(' ', 't')  # 2011_06_08t13_53_48.000
        fn_head = fn_head[:-4]  # 2011_06_08t13_53_48
        fn_head = "aia_lev1_171a_" + fn_head  # aia_lev1_171a_2011_06_08t13_53_48

        file = None
        for filename in os.listdir("./Data"):
            if filename.startswith(fn_head):
                file = "./Data/" + filename
                print("Found existing file at " + file)
        if file is None:
            file = Fido.fetch(result, path='./Data/{file}')

        return file

# 1: iterate through images forwards, adding to list
#     a: check 100x100 frame of pixels at the location of the peak, finding the maximum
#     b: add to list
# 2: repeat but backwards

#calc bounding box for search
xmin = max(0, location[0] - 50)
xmax = min(1024, location[0] + 51)
ymin = max(0, location[1] - 50)
ymax = min(1024, location[1] + 51)

data = []
for i in range(int(number/2)):
    #get file and map, etc
    file = get_file(a.Time(peak + interval*(i + 1), peak + interval*(i + 2)))
    map = sunpy.map.Map(file)
    df = map.to_dataframe

    #iterate through each pixel, recording brightest
    brightest = -np.Inf
    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            brightest = max(df[x][y], brightest)

    #add to list
    data.append(2*brightest/map.meta['exptime'])

for i in range(number/2):
    #get file, map, etc
    file = get_file(a.Time(peak - interval*(i + 1), peak - interval*i))
    map = sunpy.map.Map(file)
    df = map.to_dataframe

    brightest = -np.Inf
    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            brightest = max(df[x][y], brightest)

    data.insert(0, 2*brightest/map.meta['exptime'])

plt.plot(data)
plt.show()
