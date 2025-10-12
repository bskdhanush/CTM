
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import JsonHandler,CrashHandler

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def get_magic_string():
    with open(JsonHandler.POV_config_FIle, "r", encoding="utf-8") as f:
            cfg=json.load(f)
    magic_string=cfg["Magic_string"]
    #print(f"called{folderpath}")
    return magic_string 

def set_magic_sting(path_var,current_label,magic_string:str):
    print(" setting ther string")
    cfg=JsonHandler.load_POV_json()
    cfg["Magic_string"]=magic_string
    JsonHandler.save_POV_json(cfg)

    path_var.set(magic_string)
    current_label.config(text=f"Current Magic String: \n\n{magic_string}")

    return 

def create_crash_forecat_page(container, pages, add_nav):
    crash_frame = ttk.Frame(container)
    crash_frame.grid(row=0, column=0, sticky="nsew")
    pages["Crash"] = crash_frame
    add_nav("Crash_Forcast", "Crash")

    magic_string = get_magic_string()
    path_var = tk.StringVar(value="Set magic sting")
    
    # Single LabelFrame containing everything
    crash_page_header = ttk.LabelFrame(crash_frame, text="Magic String")
    crash_page_header.pack(fill="x", **PADDING) # type: ignore
    
    # First row frame for entry and button
    row1_frame = ttk.Frame(crash_page_header)
    row1_frame.pack(fill="x", padx=10, pady=(10, 5))
    
    # Entry field and button in the same row
    Text_value = ttk.Entry(row1_frame, textvariable=path_var)
    Text_value.pack(side="left", fill="x", expand=True)
    
    ttk.Button(
        row1_frame,
        text="Set Magic String",
        command=lambda: set_magic_sting(path_var,current_string_label, Text_value.get()),
    ).pack(side="right", padx=(10, 0))
    
    separator = ttk.Separator(crash_page_header, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    # Current magic string label on a new line

    current_string_label = ttk.Label(crash_page_header, text=f"Current Magic String: \n\n{magic_string}", wraplength=1000)
    current_string_label.pack(fill="x", **PADDING)  # type: ignore

    ttk.Button(
         crash_page_header, text="crash_Forecast" ,command=lambda:CrashHandler.get_crash_path()
    ).pack(fill="x",**PADDING)# type: ignore

    crash_page_main = ttk.LabelFrame(crash_frame, text="Crash Renaming and Upload")
    crash_page_main.pack(fill="x", **PADDING) # type: ignore
    

    # Market = tk.StringVar()
    # Name = tk.StringVar()
    # FstID = tk.StringVar()

    # Get the string values from your method
    market_str, name_str, fstid_str = CrashHandler.get_naming_convention()

    # Manually set the StringVar values
    entry_row_frame = ttk.Frame(crash_page_main)
    entry_row_frame.pack(fill="x", **PADDING)  # type: ignore

    Market_name = ttk.Entry(entry_row_frame, width=20)
    Market_name.insert(0, market_str)
    Market_name.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    Naming = ttk.Entry(entry_row_frame, width=20)
    Naming.insert(0, name_str)
    Naming.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    FSTID_name = ttk.Entry(entry_row_frame, width=20)
    FSTID_name.insert(0, fstid_str)
    FSTID_name.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    ttk.Button(
        entry_row_frame,
        text="Update Fields",
        command=lambda: CrashHandler.set_naming_convention(Market_name.get(),Naming.get(),FSTID_name.get()),
    ).pack(fill="x", **PADDING) # type: ignore
    


    second_row_frame = ttk.Frame(crash_page_main)
    second_row_frame.pack(fill="x", **PADDING)  # type: ignore
    # Now the separator will be on its own line
    separator = ttk.Separator(second_row_frame, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    
    crashNaming_label = ttk.Label(second_row_frame, text="Current Renaming: \n\n", wraplength=1000)
    crashNaming_label.pack(fill="x", **PADDING) # type: ignore
    ttk.Button(
        crash_page_main,
        text="GET Crash Naming",
        command=lambda: crashNaming_label.config(text=f"Current Renaming: \n\n{CrashHandler.get_crash_naming()}"),
    ).pack(fill="x", **PADDING) # type: ignore
     
    
    separator = ttk.Separator(crash_page_main, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    ttk.Button(
        crash_page_main,
        text="Upload crash dump ",
    ).pack(fill="x", **PADDING) # type: ignore









    
    




















    return crash_frame

