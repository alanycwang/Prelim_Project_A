import tkinter as tk
import urllib

from tkcalendar import DateEntry
from tkinter import ttk

from datetime import datetime

import timeEntry
import xrs
import flare

import sunpy


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Prelim Project A")
        self.geometry('1920x1080')

        self.style = ttk.Style()
        self.style.configure("TTreeview", padding=0, background="#ffffff", borderwidth=0)

        self.graph = xrs.XRS(self, self.style)

        self.dateEntry()

    def dateEntry(self):
        self.entryFrameContainer = ttk.Frame(self, borderwidth=20)
        self.entryFrame = ttk.Frame(self.entryFrameContainer)

        self.error_message = ttk.Label(self.entryFrameContainer, text="", foreground = 'red')
        self.error_message.grid(row=0, column=0, sticky="NW")

        self.start_text = ttk.Label(self.entryFrame, text="Start Date:", padding=2)
        self.start_text.grid(row=1, column=0, sticky="NW")

        self.start_cal = DateEntry(self.entryFrame, selectmode='day', year=2011, month=6, day=8, width=7)
        self.start_cal.grid(row=1, column=1, sticky="NW")

        self.start_time_text = ttk.Label(self.entryFrame, text="Start Time:", padding=2)
        self.start_time_text.grid(row=2, column=0, sticky="NW")

        self.start_time = timeEntry.TimeEntry(self.entryFrame)
        self.start_time.hour.insert(0, "00")
        self.start_time.minute.insert(0, "00")
        self.start_time.frame.grid(row=2, column=1, sticky="NW")

        self.end_text = ttk.Label(self.entryFrame, text="End Date:", padding=2)
        self.end_text.grid(row=4, column=0, sticky="NW")

        self.end_cal = DateEntry(self.entryFrame, selectmode='day', year=2011, month=6, day=8, width=7)
        self.end_cal.grid(row=4, column=1, sticky="NW")

        self.end_time_text = ttk.Label(self.entryFrame, text="End Time:", padding=2)
        self.end_time_text.grid(row=5, column=0, sticky="NW")

        self.end_time = timeEntry.TimeEntry(self.entryFrame)
        self.end_time.hour.insert(0, "23")
        self.end_time.minute.insert(0, "00")
        self.end_time.frame.grid(row=5, column=1, sticky="NW")

        self.graph_button = ttk.Button(self.entryFrameContainer, text='Graph!', command=self.graphDate)
        self.graph_button.grid(row=3, column=0, sticky="NW")

        self.entryFrame.grid(row=2, column=0, sticky="NW")
        self.entryFrameContainer.grid(row=0, column=0, sticky="NW")

    def graphDate(self):
        if (not self.start_time.get_time()):
            self.error_message.config(text="Please enter a valid start time")
            return
        if (not self.end_time.get_time()):
            self.error_message.config(text="Please enter a valid end time")

        start_date_time = datetime.combine(self.start_cal.get_date(), datetime.strptime(self.start_time.get_time(), '%H:%M').time())
        end_date_time = datetime.combine(self.end_cal.get_date(), datetime.strptime(self.end_time.get_time(), '%H:%M').time())

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

        for widget in self.all_children(self.graph.frame):
            widget.grid_forget()
        self.graph.frame.update()

        # print(str(start_date_time))

        try:
            self.graph.graph(str(start_date_time), str(end_date_time))
        except urllib.error.URLError:
            self.error_message.config(text="Something went wrong with the server. Please try again later")
            return
        except sunpy.util.datatype_factory_base.NoMatchError:
            self.error_message.config(text="Unfortunately, the downloaded file was corrupted. Please try a different date")
            return
        # except IndexError:
        #     self.error_message.config(text="Could not find any data for this time interval. Please try a different time")
        #     return

        # selection = self.graph.get_selection()

    def all_children(self, window):
        list = window.winfo_children()

        for item in list:
            if item.winfo_children():
                list.extend(item.winfo_children())

        return list



if __name__ == "__main__":
    app = App()
    app.mainloop()