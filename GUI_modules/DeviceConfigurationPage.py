import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from GUI_modules import DeviceConfigNavigator

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_device_Configuaration_page(container, pages, add_nav, device_name):


    section_names = ["Meta", "Mpss", "QCN", "NVs","End_to_End"]
    # Page container
    configPage = ttk.Frame(container)
    configPage.grid(row=0, column=0, sticky="nsew")
    configPage.columnconfigure(0, weight=1)
    configPage.rowconfigure(1, weight=1)  # content area expands
    pages["Config"] = configPage
    add_nav("Dev Config", "Config")

    # Top labelframe (title area)
    header_fr = ttk.LabelFrame(configPage, text="Device Configuration")
    header_fr.grid(row=0, column=0, sticky="ew", **PADDING) # type: ignore
    header_fr.columnconfigure(0, weight=1)

    # Button bar
    button_bar = ttk.Frame(header_fr)
    button_bar.grid(row=0, column=0, sticky="ew")
    for i in range(5):
        button_bar.columnconfigure(i, weight=1)

    # Content stack (holds 5 frames overlaid)
    content_stack = ttk.Frame(configPage)
    content_stack.grid(row=1, column=0, sticky="nsew", **PADDING) # type: ignore
    content_stack.rowconfigure(0, weight=1)
    content_stack.columnconfigure(0, weight=1)

    # Create 5 content frames
    frames: dict[str, ttk.Frame] = {}

    def make_frame(Pagename: str) -> ttk.Frame:
        fr = ttk.Frame(content_stack)
        fr.grid(row=0, column=0, sticky="nsew")


        if Pagename  == "Meta":
            # Build and mount the external section 1 UI
            section_ui = DeviceConfigNavigator.Meta_page(fr,Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=8)

        elif Pagename == "Mpss":
            section_ui = DeviceConfigNavigator.Mpss_page(fr,Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=8)

        else:
            # Placeholder for other sections
            demo = ttk.Label(fr, text=f"UI for section {Pagename}", font=("Segoe UI", 12))
            demo.pack(padx=16, pady=16)
        return fr

    for Pagename in  section_names:
        frames[Pagename] = make_frame(Pagename)

    # Raise the selected frame and update button styles
    style = ttk.Style()
    # Optional: distinct style for active button
    style.configure("TabButton.TButton", padding=(8, 6))
    style.configure("TabButton.Active.TButton", padding=(8, 6), relief="sunken")

    current_name = tk.StringVar(value=section_names[0])
    def show(Pagename: str):
        frames[Pagename].tkraise()
        current_name.set(Pagename)
        for n, b in buttons.items():
            b.configure(style="TabButton.Active.TButton" if n == Pagename else "TabButton.TButton")

    # Create buttons
    for i in range(len(section_names)):
        button_bar.columnconfigure(i, weight=1)

    buttons: dict[str, ttk.Button] = {}

    for i, Pagename in enumerate(section_names):
        btn = ttk.Button(
            button_bar,
            text=Pagename,
            style="TabButton.TButton",
            command=lambda nm=Pagename: show(nm)
        )
        btn.grid(row=0, column=i, padx=4, pady=6, sticky="ew")
        buttons[Pagename] = btn

    # Initialize with first tab visible
    show(section_names[0])



    