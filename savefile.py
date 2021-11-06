import screen
import entryscreen
import xrs
import flarescreen

class SaveFile():
    def __init__(self, screens):
        order = []
        contents = []

        # 1: go through each screen
        for item in screens:

            # 2: check id and add it to a list
            order.append(type(item))

            # 3: record contents
            rank, c = item.save()
            contents.append([rank, c])

        # 4: compress contents
        # 4.1: dump all important contents into an array (ts, flare, peaks)

        flares = []
        times = []
        for item in contents:
            pass
        # 4.2: create a list of all individual peaks (including contents of peaks)
        # 4.3: create a new array that matches each screen with its resepctive content from 4.2
        # 5 pickle dump