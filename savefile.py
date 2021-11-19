import moviescreen
import screen
import entryscreen
import xrs
import flarescreen

#because pickle doesnt like tkinter objects
class SaveFile():
    def __init__(self, screens):
        self.order = []
        contents = []

        # 1: go through each screen
        for item in screens:
            # 2: check id and add it to a list
            self.order.append(item.id)

            # 3: record contents
            rank, c = item.data()
            contents.append([rank, c])

        # 4: compress contents
        # 4.1: dump all important contents into an array (ts, flare, peaks)

        self.flares = []  # [[flare, rank, [[frame#, frame#, ...], [list#, list#, ... ]]], ...]
        self.lists = []  # [[list, frame#], ...]
        self.other = []  # [[ts, frame#], ...]
        for i, item in enumerate(contents):
            if item[0] == 0 or item[0] == 1:
                found = False
                for flare in self.flares:
                    if item[1][0] == flare[0]:
                        found = True
                        if item[0] > flare[1]:
                            flare[0] = item[1][0]
                        flare[2][0].append(i)
                        break
                if not found:
                    self.flares.append([item[1][0], item[0], [[i], []]])
            if item[0] == 2:
                self.lists.append([[], i])
                idx = len(self.lists) - 1
                for f in item[1][0]:
                    found = False
                    for flare in self.flares:
                        if f == flare[0]:
                            found = True
                            flare[2][1].append(idx)
                            break
                    if not found:
                        self.flares.append([f, item[0], [[], [idx]]])
            if item[0] == 2 or item[0] == 1:
                self.other.append([item[1][1], i])

        # 4.2: create a list of all individual peaks (including contents of peaks)
        # 4.3: create a new array that matches each screen with its resepctive content from 4.2
        # 5 pickle dump

def unpack(file, root):
    contents = []
    for _ in file.order:
        contents.append([])
    lists = file.lists
    for flare in file.flares:
        for frame in flare[2][0]:
            contents[frame].append(flare[0])
        for lst in flare[2][1]:
            lists[lst][0].append(flare[0])
    for lst in lists:
        contents[lst[1]].append(lst[0])
    for ts1 in file.other:
        contents[ts1[1]].append(ts1[0])

    screens = []
    for i, screen in enumerate(file.order):
        new = None
        if screen == "entryscreen":
            new = (entryscreen.EntryScreen(root))
        if screen == "xrs":
            new = (xrs.XRS(root, contents[i][1][1], contents[i][1][2], ts=contents[i][1][0], peaks=contents[i][0]))
        if screen == "flarescreen":
            new = (flarescreen.FlareScreen(root, contents[i][0], contents[i][1]))
        if screen == "moviescreen":
            new = (moviescreen.MovieScreen(root, contents[i][0]))
        screens.append(new)

    return screens
