import tkinter as tk
from tkinter import ttk

class TimeEntry():
    def __init__(self, root):
        self.root = root

        self.frame = tk.Frame(self.root, background='#FFFFFF')

        hvcmd = (self.root.register(self.validate_hour), '%P')
        self.hour = ttk.Entry(self.frame, validate='all', validatecommand=hvcmd, width=4)
        self.hour.grid(row=0, column=0, sticky="NW")

        self.colon = tk.Label(self.frame, text=":", background='#FFFFFF')
        self.colon.grid(row=0, column=1, sticky="NW")

        mvcmd = (self.root.register(self.validate_minute), '%P')
        self.minute = ttk.Entry(self.frame, validate='all', validatecommand=mvcmd, width=4)
        self.minute.grid(row=0, column=2, sticky="NW")

    def validate_hour(self, value_if_allowed):
        if value_if_allowed == "":
            return True
        try:
            temp = int(value_if_allowed)
            return 24 > temp >= 0
        except ValueError:
            return False

    def validate_minute(self, value_if_allowed):
        if value_if_allowed == "":
            return True
        try:
            temp = int(value_if_allowed)
            return 60 > temp >= 0
        except ValueError:
            return False

    def get_time(self):
        try:
            return "{:02d}:{:02d}".format(int(self.hour.get()), int(self.minute.get()))
        except ValueError:
            return False

