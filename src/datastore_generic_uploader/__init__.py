# -*- coding: utf-8 -*-
# __init__.py

import tkinter as tk
from .gui import GUI

__version__ = '0.1.0'

if __name__ == '__main__':
    root = tk.Tk()
    app = GUI(root)
    app.run()
