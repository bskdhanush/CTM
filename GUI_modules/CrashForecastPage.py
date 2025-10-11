
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import JsonHandler as JH

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_crash_forecat_page(container, pages, add_nav):
    crash_frame = ttk.Frame(container)
    crash_frame.grid(row=0, column=0, sticky="nsew")
    pages["Crash"] = crash_frame
    add_nav("Crash_Forcast", "Crash")

    
    crash_page = ttk.LabelFrame(crash_frame, text="Crash forecast")
    crash_page.pack(fill="x", **PADDING)# type: ignore  



    path_var = tk.StringVar(value='No file selected — click "Choose archive…"')
    label = ttk.Label(crash_page, textvariable=path_var,style="Hint.TLabel")
    label.pack(fill="x", **PADDING) # type: ignore


    ttk.Button(
    crash_page,
    text="Set Magic String",
    command='',
    ).pack(side="right", anchor="e", padx=(0, 10))







    







   


    return crash_frame

