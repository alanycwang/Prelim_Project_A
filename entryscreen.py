import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkcalendar import DateEntry

from datetime import datetime

import screen
import timeEntry
import savefile
import xrs
import pickle
import os

class EntryScreen(screen.Screen):
    def __init__(self, root):
        super().__init__(root)

        self.date_entry()
        self.file_loader()
        self.last_start_time = None
        self.last_end_time = None
        self.path=None
        self.previous_path=None

        self.id = "Home"

    def date_entry(self):
        self.dateentry = tk.Frame(self)
        self.dateentryborder = tk.Frame(self.dateentry, background='#81868F', padx=1, pady=1)
        self.entryFrameContainer = tk.Frame(self.dateentryborder, background='#FFFFFF', borderwidth=20)
        self.entryFrame = tk.Frame(self.entryFrameContainer, background='#FFFFFF')

        self.error_message = tk.Label(self.entryFrameContainer, text="", foreground='red', background="#FFFFFF")
        self.error_message.grid(row=1, column=0, sticky="NW", pady=(0, 10))

        self.dateentrylabel = tk.Label(self.entryFrameContainer, text="Option 1: Choose a Date Range", background='#FFFFFF')
        self.dateentrylabel.grid(row=0, column=0, sticky="N")
        self.start_text = tk.Label(self.entryFrame, text="Start Date:", padx=2, pady=2, background='#FFFFFF')
        self.start_text.grid(row=1, column=0, sticky="NW")

        self.start_cal = DateEntry(self.entryFrame, selectmode='day', year=2011, month=2, day=13, width=7)
        self.start_cal.grid(row=1, column=1, sticky="NW")

        self.start_time_text = tk.Label(self.entryFrame, text="Start Time:", padx=2, pady=2, background='#FFFFFF')
        self.start_time_text.grid(row=2, column=0, sticky="NW")

        self.start_time = timeEntry.TimeEntry(self.entryFrame)
        self.start_time.hour.insert(0, "00")
        self.start_time.minute.insert(0, "00")
        self.start_time.frame.grid(row=2, column=1, sticky="NW")

        self.end_text = tk.Label(self.entryFrame, text="End Date:", padx=2, pady=2, background='#FFFFFF')
        self.end_text.grid(row=4, column=0, sticky="NW")

        self.end_cal = DateEntry(self.entryFrame, selectmode='day', year=2011, month=2, day=13, width=7)
        self.end_cal.grid(row=4, column=1, sticky="NW")

        self.end_time_text = tk.Label(self.entryFrame, text="End Time:", padx=2, pady=2, background='#FFFFFF')
        self.end_time_text.grid(row=5, column=0, sticky="NW")

        self.end_time = timeEntry.TimeEntry(self.entryFrame)
        self.end_time.hour.insert(0, "23")
        self.end_time.minute.insert(0, "00")
        self.end_time.frame.grid(row=5, column=1, sticky="NW")

        self.entryFrame.grid(row=2, column=0, sticky="NW")
        self.entryFrameContainer.grid(row=0, column=0, sticky="NW")
        self.dateentryborder.grid(row=0, column=0, sticky="NW")
        self.dateentry.grid(row=0, column=0, sticky="NW")

    def file_loader(self):
        self.fileloader = tk.Frame(self, background='#81868F', padx=1, pady=1)
        self.fileloaderbackground = tk.Frame(self.fileloader, background='#FFFFFF')

        self.fileloaderlabel = tk.Label(self.fileloaderbackground, text="Option 2: Load data from a save file", background='#FFFFFF')
        self.fileloaderlabel.grid(row=0, column=0, sticky="NW", padx=(20, 60), pady=(20, 0))

        self.loadbutton = ttk.Button(self.fileloaderbackground, text="Select a file", command=self.load)
        self.loadbutton.grid(row=1, column=0, sticky="NW", padx=(20, 0), pady=(20, 0))

        self.unloadbutton = ttk.Button(self.fileloaderbackground, text="Unload File", command=self.unload)
        self.unloadbutton.grid(row=2, column=0, sticky="NW", padx=(20, 0), pady=(10, 0))

        self.filetext = tk.Label(self.fileloaderbackground, text="No file loaded", background="#FFFFFF")
        self.filetext.grid(row=3, column=0, sticky="NW", padx=(20, 20), pady=(20, 20))

        self.fileloaderbackground.grid(row=0, column=0)
        self.fileloader.grid(row=0, column=1, padx=(20, 20))

    def load(self):
        self.path = tk.filedialog.askopenfilename(filetypes=[("Pickle Files", "*.pkl")])
        self.filetext.configure(text="Loaded: " + self.path, fg="black")

    def unload(self):
        self.path = None
        self.filetext.configure(text="No file loaded", fg="black")

    def next(self):
        if self.path is not None and self.path.strip() != '':
            try:
                return pickle.load(open(self.path, "rb"))
            except:
                self.filetext.configure(text="Something went wrong, please try again", fg="black")
                return "error"


        if not self.start_time.get_time():
            self.error_message.config(text="Please enter a valid start time")
            return
        if not self.end_time.get_time():
            self.error_message.config(text="Please enter a valid end time")

        start_date_time = datetime.combine(self.start_cal.get_date(), datetime.strptime(self.start_time.get_time(), '%H:%M').time())
        end_date_time = datetime.combine(self.end_cal.get_date(), datetime.strptime(self.end_time.get_time(), '%H:%M').time())


        if start_date_time == self.last_start_time and end_date_time == self.last_end_time:
            return None

        if start_date_time < datetime(2010, 5, 1):
            self.error_message.config(text="Please enter a start date after May 2010")
            return
        if end_date_time < datetime(2010, 5, 1):
            self.error_message.config(text="Please enter an end date after May 2010")
            return

        if start_date_time > datetime.now():
            self.error_message.config(text="Please enter a start date from the past")
            return
        if end_date_time > datetime.now():
            self.error_message.config(text="Please enter an end date from the past")
            return

        if start_date_time >= end_date_time:
            self.error_message.config(text="Start date must be before the end date")
            return

        self.error_message.config(text="")

        # print(str(start_date_time))

        screen = xrs.XRS(self.root, str(start_date_time), str(end_date_time))
        self.last_start_time = start_date_time
        self.last_end_time = end_date_time

        return screen
        # except IndexError:
        #     self.error_message.config(text="Could not find any data for this time interval. Please try a different time")
        #     return

        # selection = self.screens[0].get_selection()