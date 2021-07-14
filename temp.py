import sunpy
import sunpy.map
from sunpy.net import Fido
from sunpy.net import attrs as a

import astropy.time
import astropy.units as u

from scipy import ndimage

import datetime

import numpy as np

t = astropy.time.Time("2012-02-10T00:09:00", scale='utc', format='isot')

results = Fido.search(a.Instrument.aia, a.Physobs.intensity, a.Wavelength(171*u.angstrom), a.Time(t - 6*u.s, t + 26*u.minute))

print(results)
print(results.all_colnames)

mp = sunpy.map.Map(Fido.fetch(results[0][0]))

# print(map.meta.original_meta['aecmode'])

data = mp.to_dataframe

x = 362
y = 857


