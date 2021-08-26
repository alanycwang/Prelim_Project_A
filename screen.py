import tkinter as tk
from tkinter import ttk

class Screen:
    def __init__(self, root, style):
        self.root = root
        self.style = style

        self.frame = ttk.Frame(self.root)
        self.active = True
        self.cleared = []
        self.frame.grid(row=0, column=1)

        self.id = "screen"

    def clear(self):
        self.active = False
        self.cleared = self.frame.winfo_children()
        to_remove = []
        for i, item in enumerate(self.cleared):
            try:
                if item.grid_info():
                    item.grid_remove()
                else:
                    to_remove.append(i)
            except AttributeError:
                pass

            self.cleared.extend(item.winfo_children())

        for i in reversed(to_remove):
            self.cleared.pop(i)

        self.frame.grid_remove()
        self.root.update()

    def restore(self):
        self.active = True
        for item in self.cleared:
            item.grid()
        self.frame.grid()

    def delete(self, frame):
        children = frame.winfo_children()
        for item in children:
            item.grid_forget()
            children.extend(item.winfo_children())
        frame.grid_forget()

    def next(self):
        return None

    def data(self):
        return None
