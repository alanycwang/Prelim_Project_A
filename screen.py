import tkinter as tk
from tkinter import ttk

class Screen:
    def __init__(self, root, style):
        self.root = root
        self.style = style

        self.frame = ttk.Frame(self.root, borderwidth=20)

    def clear(self):
        self.cleared = self.frame.winfo_children()
        to_remove = []
        for i, item in enumerate(self.cleared):
            if item.grid_info():
                item.grid_remove()
            else:
                to_remove.append(i)
            self.cleared.extend(item.winfo_children())

        for i in reversed(to_remove):
            self.cleared.pop(i)

        self.frame.grid_remove()

    def restore(self):
        for item in self.cleared:
            item.grid()
        self.frame.grid()

    def delete(self, frame):
        children = frame.winfo_children()
        for item in children:
            item.grid_forget()
            children.extend(item.winfo_children())
        frame.grid_forget()

