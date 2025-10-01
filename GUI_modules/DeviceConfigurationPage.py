import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_device_Configuaration_page(container, pages, add_nav):

    # ── DATA MONITOR page ────
    configPage= ttk.Frame(container)
    configPage.grid(row=0, column=0, sticky="nsew")
    pages["Config"] = configPage
    add_nav("Dev Config", "Config")

    config_fr = ttk.LabelFrame(configPage, text="Device Configuration")
    config_fr.pack(fill="x", **PADDING) # type: ignore

    selected_zip = tk.StringVar(value='No file selected — click "Choose archive…"')
    style = ttk.Style()
    style.configure("Hint.TLabel", foreground="#6b7280")

    zip_label = ttk.Label(
        config_fr,
        textvariable=selected_zip,
        anchor="w",
        style="Hint.TLabel",
    )
    zip_label.pack(fill="x", **PADDING)  # type: ignore

    