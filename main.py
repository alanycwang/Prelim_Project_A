import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile

import xrs
import flarescreen
import entryscreen
import pickle
import savefile
import screen
import customnotebook

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Prelim Project A")
        self.geometry('1920x1080')

        self.style = ttk.Style(self)
        self.style.configure("TTreeview", padding=0, background="#ffffff", borderwidth=0)
        self.style.configure("Horizontal.TScale", background='#ffffff')
        self.style.configure('TCheckbutton', background='#FFFFFF')
        self.style.configure("TNotebook", expand=True)

        self.tabFrame = tk.Frame(self)
        self.tabFrame.grid(row = 1, column=0, padx=(20, 0), pady=(20, 0), sticky="NW")

        self.tab_parent = customnotebook.CustomNotebook(self.tabFrame)
        new = entryscreen.EntryScreen(self.tab_parent)
        self.tab_parent.add(new, text=new.id)
        self.show_navigation()
        self.tab_parent.grid(row=0, column=0)

    def show_navigation(self):
        self.navigationFrame = tk.Frame(self)
        self.next_button = ttk.Button(self.navigationFrame, text='Next', command=self.next_screen)
        # self.back_button = ttk.Button(self.navigationFrame, text='Back')
        self.save_button = ttk.Button(self.navigationFrame, text='Save Progress', command=self.save)

        self.navigationFrame.grid(row=0 , column=0, sticky="NW", padx=(20, 0), pady=(20, 0))
        self.next_button.grid(row=0, column=1, padx=(0, 10))
        # self.back_button.grid(row=0, column=0, padx=(0, 10))
        self.save_button.grid(row=0, column=2)

    def save(self):
        path = asksaveasfile(filetypes=[('Pickle Files', '*.pkl')], defaultextension=[("Pickle Files", "*.pkl")])
        screens = [self.tab_parent.nametowidget(tab) for tab in self.tab_parent.tabs()]
        s = savefile.SaveFile(screens)
        pickle.dump(s, open(path.name, 'wb'))
        print("Saved File to " + path.name)

    def load(self, file):
        self.tab_parent.grid_remove()
        self.tab_parent = customnotebook.CustomNotebook(self.tabFrame)
        self.tab_parent.grid(row=0, column=0)
        self.update_idletasks()
        screens = savefile.unpack(file, self.tab_parent)
        for screen in screens:
            self.tab_parent.add(screen, text=screen.id)


    def next_screen(self):
        new = self.tab_parent.nametowidget(self.tab_parent.select()).next()
        if not issubclass(type(new), screen.Screen):
            if new == "error":
                print("Something went wrong, please try again")
                return
            self.load(new)
            return
        self.tab_parent.add(new, text=new.id)
        self.tab_parent.select(tab_id=self.tab_parent.index("end")-1)
        self.update_idletasks()

if __name__ == "__main__":
    app = App()
    app.mainloop()