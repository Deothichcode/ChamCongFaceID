import tkinter as tk
from tkinter import ttk

# Font styles for main page
MAIN_TITLE_FONT = ("Arial", 24, "bold")
MAIN_NORMAL_FONT = ("Arial", 14)
MAIN_SMALL_FONT = ("Arial", 12)

# Font styles for sub-pages
SUB_TITLE_FONT = ("Arial", 28, "bold")
SUB_HEADING_FONT = ("Arial", 22, "bold")
SUB_NORMAL_FONT = ("Arial", 20)
SUB_SMALL_FONT = ("Arial", 18)

# Colors
PRIMARY_COLOR = "#2196F3"  # Blue
SUCCESS_COLOR = "#4CAF50"  # Green
DANGER_COLOR = "#F44336"   # Red
WARNING_COLOR = "#FFC107"  # Yellow
WHITE = "#FFFFFF"
BLACK = "#000000"

# Button styles for main page
def create_main_button(parent, text, command, bg_color=PRIMARY_COLOR, fg_color=WHITE):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=MAIN_NORMAL_FONT,
        bg=bg_color,
        fg=fg_color,
        width=18,
        height=1,
        relief=tk.RAISED,
        bd=2
    )

# Button styles for sub-pages
def create_button(parent, text, command, bg_color=PRIMARY_COLOR, fg_color=WHITE):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=SUB_NORMAL_FONT,
        bg=bg_color,
        fg=fg_color,
        width=28,
        height=2,
        relief=tk.RAISED,
        bd=3
    )

# Button styles for attendance page (smaller)
def create_attendance_button(parent, text, command, bg_color=PRIMARY_COLOR, fg_color=WHITE):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 14),
        bg=bg_color,
        fg=fg_color,
        width=15,
        height=1,
        relief=tk.RAISED,
        bd=2
    )

# Label styles for main page
def create_main_label(parent, text, font=MAIN_TITLE_FONT, fg=BLACK):
    return tk.Label(
        parent,
        text=text,
        font=font,
        fg=fg
    )

# Label styles for sub-pages
def create_label(parent, text, font=SUB_TITLE_FONT, fg=BLACK):
    return tk.Label(
        parent,
        text=text,
        font=font,
        fg=fg
    )

# Entry styles
def create_entry(parent, width=30):
    return tk.Entry(
        parent,
        font=SUB_NORMAL_FONT,
        width=width
    )

# Combobox styles
def create_combobox(parent, values, width=22):
    combobox = ttk.Combobox(
        parent,
        values=values,
        font=SUB_NORMAL_FONT,
        width=width
    )
    combobox.current(0)
    return combobox

# Treeview styles
def create_treeview(parent, columns, show="headings"):
    tree = ttk.Treeview(
        parent,
        columns=columns,
        show=show,
        height=15
    )
    
    # Configure style
    style = ttk.Style()
    style.configure("Treeview", font=SUB_NORMAL_FONT)
    style.configure("Treeview.Heading", font=SUB_HEADING_FONT)
    
    return tree 