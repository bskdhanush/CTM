import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from GUI_modules import MetaPage

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_device_Configuaration_page(container, pages, add_nav):
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
    frames: dict[int, ttk.Frame] = {}

    def make_frame(index: int) -> ttk.Frame:
        fr = ttk.Frame(content_stack)
        fr.grid(row=0, column=0, sticky="nsew")


        if index == 1:
            # Build and mount the external section 1 UI
            section_ui = MetaPage.Meta_page(fr)
            section_ui.pack(fill="x", padx=8, pady=8)
        else:
            # Placeholder for other sections
            demo = ttk.Label(fr, text=f"UI for section {index}", font=("Segoe UI", 12))
            demo.pack(padx=16, pady=16)
        return fr

    for idx in range(1, 6):
        frames[idx] = make_frame(idx)

    # Raise the selected frame and update button styles
    style = ttk.Style()
    # Optional: distinct style for active button
    style.configure("TabButton.TButton", padding=(8, 6))
    style.configure("TabButton.Active.TButton", padding=(8, 6), relief="sunken")

    current_idx = tk.IntVar(value=1)

    def show(idx: int):
        frames[idx].tkraise()
        current_idx.set(idx)
        # Update button styles
        for j, b in buttons.items():
            b.configure(style="TabButton.Active.TButton" if j == idx else "TabButton.TButton")

    # Create buttons
    buttons: dict[int, ttk.Button] = {}
    for i in range(1, 6):
        btn = ttk.Button(button_bar, text=str(i), style="TabButton.TButton", command=lambda k=i: show(k))
        btn.grid(row=0, column=i-1, padx=4, pady=6, sticky="ew")
        buttons[i] = btn

    # Initialize with first tab visible
    show(1)



    