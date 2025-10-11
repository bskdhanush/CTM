import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from GUI_modules import DeviceConfigNavigator
import JsonHandler


PADDING: dict[str, int] = {"padx": 12, "pady": 2}



def get_POV_Script_path_json():
    with open(JsonHandler.POV_config_FIle, "r", encoding="utf-8") as f:
                 cfg=json.load(f)
    folderpath =cfg["POV_Path"]
    #print(f"called{folderpath}")
    return folderpath 
def set_POV_Script_path_json(path_var):
     folderpath=DeviceConfigNavigator.getFolderPath(path_var, "POV")
     cfg=JsonHandler.load_POV_json()
     cfg["POV_Path"]=folderpath
     JsonHandler.save_POV_json(cfg)

def create_device_Configuaration_page(container, pages, add_nav, device_name):
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

    filepath=get_POV_Script_path_json()
    
    path_var = tk.StringVar(value=filepath)
    label = ttk.Label(Header_frame, textvariable=path_var)
    label.pack(side="left", padx=(10, 0))
    
    button = ttk.Button(
        Header_frame,
        text="Select Script Path",
        command=lambda: set_POV_Script_path_json(path_var))
    button.pack(side="right", padx=(0, 10), pady=6)
    
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
            section_ui = DeviceConfigNavigator.Meta_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "Mpss":
            section_ui = DeviceConfigNavigator.Mpss_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "QCN":
            section_ui = DeviceConfigNavigator.QCN_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "MBN":
            section_ui = DeviceConfigNavigator.MBN_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "NV":
            section_ui = DeviceConfigNavigator.NV_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "Full_Provisioning":
            section_ui = DeviceConfigNavigator.Full_Provisioning_page(fr, Pagename, device_name)
            section_ui.pack(fill="x", padx=8, pady=2)
        elif Pagename == "FOTA":
            section_ui = DeviceConfigNavigator.FOTA_page(fr, Pagename, device_name)
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
