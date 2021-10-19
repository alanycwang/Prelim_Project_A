import screen
import entryscreen
import xrs
import flarescreen

def generate_screens(save, root):
    if len(save) > 1:
        return xrs.XRS(root, save.tstart, save.tend, from_save=True, ts=save.ts1, peaks=save.peaks, flares=save.flares)
    return None

class SaveFile():
    def __init__(self, screens):
        self.length = len(screens)

        if len(screens) < 2:
            self.flare = None
            self.ts1 = None
            self.peaks = None
            return

        self.flares = []
        for screen in screens[1].screens:
            self.flares.append(screens[1].screens[screen].flare)
        self.ts1 = screens[1].ts1
        self.peaks = screens[1].peaks
        self.tstart = screens[1].tstart
        self.tend = screens[1].tend


    def __len__(self):
        return self.length

