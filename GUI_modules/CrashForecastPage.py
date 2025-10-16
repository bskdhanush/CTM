
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import CrashHandler
from JsonHandler import load_prov_json, save_prov_json
import pandas as pd
import os
from Threading import start_thread

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def get_magic_string():
    cfg = load_prov_json()
    magic_string = cfg.get("magic_string", "Set magic string")
    return magic_string

def set_magic_sting(path_var,magic_string:str):
    print("setting the string")
    cfg = load_prov_json()
    cfg.update({"magic_string": magic_string})
    save_prov_json(cfg)

    path_var.set(magic_string)
    #current_label.config(text=f"Current Magic String: \n\n{magic_string}")
    return 

def create_crash_forecat_page(container, pages, add_nav):
    crash_frame = ttk.Frame(container)
    crash_frame.grid(row=0, column=0, sticky="nsew")
    pages["Crash"] = crash_frame
    add_nav("Crash Processing", "Crash")

    magic_string = get_magic_string()
    path_var = tk.StringVar(value=magic_string)
    
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
        command=lambda: set_magic_sting(path_var, Text_value.get()),
    ).pack(side="right", padx=(10, 0))
    
    separator = ttk.Separator(crash_page_header, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    # Current magic string label on a new line

    # current_string_label = ttk.Label(crash_page_header, text=f"Current Magic String: \n\n{magic_string}", wraplength=1000)
    # current_string_label.pack(fill="x", **PADDING)  # type: ignore

    ttk.Button(
         crash_page_header, text="Crash Processing", command=lambda:CrashHandler.get_crash_path()
    ).pack(fill="x",**PADDING)# type: ignore

    crash_page_main = ttk.LabelFrame(crash_frame, text="Crash Renaming and Upload")
    crash_page_main.pack(fill="x", **PADDING) # type: ignore
    

    # Market = tk.StringVar()
    # Name = tk.StringVar()
    # FstID = tk.StringVar()

    # Get the string values from your method
    market_str, name_str, fstid_str, operator_str, tdc_serial_str = CrashHandler.get_naming_convention()

    # Manually set the StringVar values
    entry_row_frame = ttk.Frame(crash_page_main)
    entry_row_frame.pack(fill="x", **PADDING)  # type: ignore

    market_name = ttk.Entry(entry_row_frame, width=20)
    market_name.insert(0, market_str)
    market_name.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    naming = ttk.Entry(entry_row_frame, width=20)
    naming.insert(0, name_str)
    naming.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    fst_id_name = ttk.Entry(entry_row_frame, width=20)
    fst_id_name.insert(0, fstid_str)
    fst_id_name.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    operator = ttk.Entry(entry_row_frame, width=20)
    operator.insert(0, operator_str)
    operator.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    tdc_serial = ttk.Entry(entry_row_frame, width=20)
    tdc_serial.insert(0, tdc_serial_str)
    tdc_serial.pack(side="left", fill="x", expand=True, **PADDING)  # type: ignore

    ttk.Button(
        entry_row_frame,
        text="Update Fields",
        command=lambda: CrashHandler.set_naming_convention(
            market_name.get(), naming.get(), fst_id_name.get(), operator.get(), tdc_serial.get()),
    ).pack(fill="x", **PADDING) # type: ignore
    


    second_row_frame = ttk.Frame(crash_page_main)
    second_row_frame.pack(fill="x", **PADDING)  # type: ignore
    # Now the separator will be on its own line
    separator = ttk.Separator(second_row_frame, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    
    crash_naming_label = ttk.Label(second_row_frame, text="Current Renaming: \n\n", wraplength=1000)
    crash_naming_label.pack(fill="x", **PADDING) # type: ignore
    ttk.Button(
        crash_page_main,
        text="GET Crash Naming",
        command=lambda: crash_naming_label.config(text=f"Current Renaming: \n\n{CrashHandler.get_crash_naming()}"),
    ).pack(fill="x", **PADDING) # type: ignore
     
    
    separator = ttk.Separator(crash_page_main, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    # Table for Crash Info

    Crash_table = ttk.LabelFrame(crash_page_main, text="Crash Table")
    Crash_table.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Make the LabelFrame act like a grid container
    Crash_table.rowconfigure(0, weight=0)  # table row grows
    Crash_table.columnconfigure(0, weight=1)

    COLUMNS = ("ROOT_CAUSE", "ADB_ID", "CRASH_PATH", "TIMESTAMP", "FST_ID")

    tree = ttk.Treeview(
        Crash_table,
        columns=COLUMNS,
        show="headings",
        height=4,  # visible rows
    )

    # Headings
    tree.heading("ROOT_CAUSE", text="ROOT_CAUSE")
    tree.heading("ADB_ID", text="ADB_ID")
    tree.heading("CRASH_PATH", text="CRASH_PATH")
    tree.heading("TIMESTAMP", text="TIMESTAMP")
    tree.heading("FST_ID", text="FST_ID")

    # Column widths; set some stretch=False so total width exceeds widget -> enables X scroll
    tree.column("ROOT_CAUSE", width=170, anchor="center", stretch=False)
    tree.column("ADB_ID", width=120, anchor="center", stretch=False)
    tree.column("CRASH_PATH", width=120, anchor="center", stretch=False)
    tree.column("TIMESTAMP", width=140, anchor="center", stretch=False)
    tree.column("FST_ID", width=180, anchor="center", stretch=True)

    # Scrollbars
    vscroll = ttk.Scrollbar(Crash_table, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(Crash_table, orient="horizontal", command=tree.xview)

    # Wire scrollbars to the tree
    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hsb.set)

    # Layout (tree row 0, hsb row 1, button row 2; vscroll spans rows 0-1)
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns", rowspan=2)
    hsb.grid(row=1, column=0, sticky="ew")

    # Refresh button BELOW the hscrollbar (row 2)
    ttk.Button(
        Crash_table,
        text="Refresh Data",
        command=lambda: (load_crash_table()),
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 0))

    def load_crash_table():
        """Read CSV and populate the table."""
        try:
            crash_meta_csv = os.path.join(r'C:\QSTAF\CTM_logs', 'CrashMetaInfo.csv')
            df = pd.DataFrame()
            if os.path.exists(crash_meta_csv):
                df = pd.read_csv(crash_meta_csv)

            tree.delete(*tree.get_children())
            for index, row in df.iterrows():
                tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("ROOT_CAUSE", ""),
                        row.get("ADB_ID", ""),
                        row.get("CRASH_PATH", ""),
                        row.get("TIMESTAMP", ""),
                        row.get("FST_ID", "")
                    )
                )
        except Exception as e:
            print(f'Exception during load_crash_table: {e}')

    # initial fill
    load_crash_table()

    separator = ttk.Separator(crash_page_main, orient='horizontal')
    separator.pack(fill='x', padx=20, pady=(12, 0))

    ttk.Button(
        crash_page_main,
        text="Zip & Upload Crash dump",
        command=lambda: start_thread(CrashHandler.zip_and_upload_crash_dump(),"Zip and upload thread", daemon=True)
    ).pack(fill="x", **PADDING) # type: ignore



    return crash_frame

