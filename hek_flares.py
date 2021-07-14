import matplotlib.pyplot as plt

from sunpy.net import Fido
from sunpy.net import attrs as a
from sunpy.time import parse_time
from sunpy.timeseries import TimeSeries

date = "2011-02-10"

tr = a.Time(date + " 00:00", date + " 23:59")
results = Fido.search(tr, a.Instrument.xrs & a.goes.SatelliteNumber(15) | a.hek.FL & (a.hek.FRM.Name == 'SWPC'))

files = Fido.fetch(results)
goes = TimeSeries(files)

hek_results = results['hek']

fig, ax = plt.subplots()
goes.plot()

for event in hek_results:
    ax.axvline(parse_time(event['event_peaktime']).datetime)
    ax.axvspan(parse_time(event['event_starttime']).datetime,
               parse_time(event['event_endtime']).datetime,
               alpha=0.2, label=event['fl_goescls'])
    print(event['hpc_coord'])
ax.set_yscale('log')

plt.show()


