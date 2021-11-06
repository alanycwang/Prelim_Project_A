import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile

import xrs
import flarescreen
import entryscreen
import pickle
import savefile
import screen

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Prelim Project A")
        self.geometry('1920x1080')

        self.style = ttk.Style(self)
        self.style.configure("TTreeview", padding=0, background="#ffffff", borderwidth=0)
        self.style.configure("Horizontal.TScale", background='#ffffff')
        self.style.configure('TCheckbutton', background='#FFFFFF')

        self.tabFrame = tk.Frame(self)
        self.tabFrame.grid(row = 1, column=0, padx=(20, 0), pady=(20, 0), sticky="NW")

        self.tab_parent = ttk.Notebook(self.tabFrame)
        new = entryscreen.EntryScreen(self.tab_parent)
        self.screens = {str(new) : new}
        self.tab_parent.add(new, text=new.id)
        self.show_navigation()
        self.tab_parent.grid(row=0, column=0)
        self.loaded = False

    def show_navigation(self):
        self.navigationFrame = tk.Frame(self)
        self.next_button = ttk.Button(self.navigationFrame, text='Next', command=self.next_screen)
        self.back_button = ttk.Button(self.navigationFrame, text='Back')
        self.save_button = ttk.Button(self.navigationFrame, text='Save Progress', command=self.save)

        self.navigationFrame.grid(row=0, column=0, sticky="NW", padx=(20, 0), pady=(20, 0))
        self.next_button.grid(row=0, column=1, padx=(0, 10))
        self.back_button.grid(row=0, column=0, padx=(0, 10))
        self.save_button.grid(row=0, column=2)

    def save(self):
        path = asksaveasfile(filetypes=[('Pickle Files', '*.pkl')], defaultextension=[("Pickle Files", "*.pkl")])
        pickle.dump(self.screens, open(path.name, 'wb'))
        print("Saved File to " + path.name)

    def next_screen(self):

        # if self.current_screen == 0:
        #     flare = self.screens[0].peaks[int(self.screens[0].list.item(self.screens[0].list.focus())['text'])]
        #     if len(self.screens) <= 1:
        #         self.screens.append(flarescreen.FlareScreen(self, self.style, flare, self.screens[0].ts1))
        #     else:
        #         self.screens[1] = flarescreen.FlareScreen(self, self.style, flare, self.screens[0].ts1)

        new = self.screens[self.tab_parent.select()].next()
        if not issubclass(type(new), screen.Screen):
            self.screens = new
            for item in self.screens:
                self.tab_parent.add(item, text=item.id)
        self.screens[str(new)] = new
        self.tab_parent.add(new, text=new.id)
        self.update_idletasks()

if __name__ == "__main__":
    app = App()
    app.mainloop()