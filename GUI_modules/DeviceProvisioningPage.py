import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from GUI_modules import ProvisioningNavigator
from JsonHandler import load_prov_json, save_prov_json
from EndToEndDevProvsioningController import get_provisioning_base

PADDING: dict[str, int] = {"padx": 12, "pady": 2}


def set_prov_path(path_var,label):
     folderpath = ProvisioningNavigator.getFolderPath("")
     path_var.set(folderpath)
     label.config(foreground="white")
     cfg = load_prov_json()
     cfg.update({"provisioning_path": folderpath})
     save_prov_json(cfg)

def create_device_Configuaration_page(container, pages, add_nav, device_name, mpss_id):
    section_names = ["Meta", "Mpss", "QCN", "MBN", "NV", "Full_Provisioning", "FOTA"]
    
    # Page container
    configPage = ttk.Frame(container)
    configPage.grid(row=0, column=0, sticky="nsew")
    configPage.columnconfigure(0, weight=1)
    configPage.rowconfigure(1, weight=1)
    
    pages["Config"] = configPage
    add_nav("Device Provisioning", "Config")
    
    # Header frame - using pack
    Header_frame = ttk.LabelFrame(configPage, text="Set Provisioning Script Path")
    Header_frame.pack(side="top", fill="x", padx=12, pady=(8, 8))

    filepath = get_provisioning_base()

    if filepath==None:
        path_var = tk.StringVar(value="provisioning_path is not configured. Please check")
        label = ttk.Label(Header_frame, textvariable=path_var,foreground="red")
        label.pack(side="left", padx=(10, 0))
    else:
        path_var = tk.StringVar(value=filepath)
        label = ttk.Label(Header_frame, textvariable=path_var,foreground="white")
        label.pack(side="left", padx=(10, 0))

  

    button = ttk.Button(
        Header_frame,
        text="Select Script Path",
        command=lambda: set_prov_path(path_var,label))
    button.pack(side="right", padx=(0, 10),pady=(0,6))
    
    # Main labelframe (title area) - using pack
    Main_frame = ttk.LabelFrame(configPage, text="Device Configuration")
    Main_frame.pack(side="top", fill="x", padx=12, pady=2)
    
    # Button bar
    button_bar = ttk.Frame(Main_frame)
    button_bar.pack(side="top", fill="x", padx=0, pady=0)
    
    # Content stack (holds 7 frames overlaid) - using pack
    content_stack = ttk.Frame(configPage)
    content_stack.pack(side="top", fill="both", expand=True, padx=12, pady=2)
    
    # Create 7 content frames
    frames: dict[str, ttk.Frame] = {}
    
    def make_frame(Pagename: str) -> ttk.Frame:
        fr = ttk.Frame(content_stack)
        fr.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        if Pagename == "Meta":
            section_ui = ProvisioningNavigator.Meta_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "Mpss":
            section_ui = ProvisioningNavigator.Mpss_page(fr, Pagename, mpss_id)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "QCN":
            section_ui = ProvisioningNavigator.QCN_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "MBN":
            section_ui = ProvisioningNavigator.MBN_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "NV":
            section_ui = ProvisioningNavigator.NV_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "Full_Provisioning":
            section_ui = ProvisioningNavigator.Full_Provisioning_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "FOTA":
            section_ui = ProvisioningNavigator.FOTA_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        
        return fr
    
    for Pagename in section_names:
        frames[Pagename] = make_frame(Pagename)
    
    # Style configuration
    style = ttk.Style()
    style.configure("TabButton.TButton", padding=(8, 4))
    style.configure("TabButton.Active.TButton", padding=(8, 4), relief="sunken")
    
    current_name = tk.StringVar(value=section_names[0])
    
    def show(Pagename: str):
        frames[Pagename].tkraise()
        current_name.set(Pagename)
        for n, b in buttons.items():
            b.configure(style="TabButton.Active.TButton" if n == Pagename else "TabButton.TButton")
    
    # Create buttons using pack for horizontal layout
    buttons: dict[str, ttk.Button] = {}
    for Pagename in section_names:
        btn = ttk.Button(
            button_bar,
            text=Pagename,
            style="TabButton.TButton",
            command=lambda nm=Pagename: show(nm)
        )
        btn.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        buttons[Pagename] = btn
    
    # Initialize with first tab visible
    show(section_names[0])

   



