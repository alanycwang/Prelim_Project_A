import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile

import xrs
import flarescreen
import entryscreen
import pickle
import savefile

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Prelim Project A")
        self.geometry('1920x1080')

        self.style = ttk.Style()
        self.style.configure("TTreeview", padding=0, background="#ffffff", borderwidth=0)

        self.screenFrame = tk.Frame(self)
        self.screenFrame.grid(row = 1, column=0, padx=(20, 0), pady=(20, 0), sticky="NW")
        self.screens = [entryscreen.EntryScreen(self.screenFrame, self.style)]
        self.current_screen = 0
        self.show_navigation()

        self.loaded = False

    def show_navigation(self):
        self.navigationFrame = tk.Frame(self)
        self.next_button = ttk.Button(self.navigationFrame, text='Next', command=self.next_screen)
        self.back_button = ttk.Button(self.navigationFrame, text='Back', command=self.last_screen)
        self.save_button = ttk.Button(self.navigationFrame, text='Save Progress', command=self.save)

        self.navigationFrame.grid(row=0, column=0, sticky="NW", padx=(20, 0), pady=(20, 0))
        self.next_button.grid(row=0, column=1, padx=(0, 20))
        self.back_button.grid(row=0, column=0, padx=(0, 20))
        self.save_button.grid(row=0, column=2)

        self.load_button = ttk.Button(self.navigationFrame, text='Load Progress', command=self.load)
        self.load_button.grid(row=0, column=3)

    def save(self):
        path = asksaveasfile(filetypes=[('Pickle Files', '*.pkl')], defaultextension=[("Pickle Files", "*.pkl")])
        pickle.dump(savefile.SaveFile(self.screens), open(path.name, 'wb'))
        print("Saved File to " + path.name)

    def load(self):
        path = tk.filedialog.askopenfilename(filetypes=[("Pickle Files", "*.pkl")])
        if len(self.screens) > 1:
            del self.screens[1:]
        self.screens.append(savefile.generate_screens(pickle.load(open(path, "rb")), self.screenFrame, self.style))
        self.loaded = True

    def next_screen(self):

        print("asfdjk;")

        # if self.current_screen == 0:
        #     flare = self.screens[0].peaks[int(self.screens[0].list.item(self.screens[0].list.focus())['text'])]
        #     if len(self.screens) <= 1:
        #         self.screens.append(flarescreen.FlareScreen(self, self.style, flare, self.screens[0].ts1))
        #     else:
        #         self.screens[1] = flarescreen.FlareScreen(self, self.style, flare, self.screens[0].ts1)

        self.screens[self.current_screen].clear()
        if self.current_screen > 0 or not self.loaded:
            new_screen = self.screens[self.current_screen].next()
        if (not self.loaded or self.current_screen > 0) and new_screen is not None:
            del self.screens[self.current_screen + 1:]
            self.screens.append(new_screen)
            print("idk, the program doesn't work either way")
        if self.current_screen >= len(self.screens) - 1:
            self.screens[self.current_screen].restore()
            return
        self.current_screen += 1
        self.screens[self.current_screen].restore()

    def last_screen(self):
        if self.current_screen <= 0:
            return
        self.screens[self.current_screen].clear()
        self.current_screen -= 1
        self.screens[self.current_screen].restore()

if __name__ == "__main__":
    app = App()
    app.mainloop()