import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import CrashHandler
from JsonHandler import load_prov_json, save_prov_json
import pandas as pd
import os
from Threading import start_thread
from Constants import CTM_LOGS_DIR

PADDING: dict[str, int] = {"padx": 12, "pady": 8}

def get_magic_string():
    cfg = load_prov_json()
    magic_string = cfg.get("magic_string", "Set magic string")
    return magic_string

def set_magic_string(path_var, magic_string: str):  # Fixed typo: sting -> string
    print("setting the string")
    cfg = load_prov_json()
    cfg.update({"magic_string": magic_string})
    save_prov_json(cfg)
    path_var.set(magic_string)
    return

log_box = None  # Global log box variable
def create_crash_forecast_page(container, pages, add_nav):
    crash_frame = ttk.Frame(container)
    crash_frame.grid(row=0, column=0, sticky="nsew")
    pages["Crash"] = crash_frame
    add_nav("Crash Processing", "Crash")

    # Configure grid weights to allow expansion
    crash_frame.rowconfigure(0, weight=1)
    crash_frame.columnconfigure(0, weight=1)

    # Create Canvas and vertical scrollbar only
    canvas = tk.Canvas(crash_frame, highlightthickness=0)
    vsb = ttk.Scrollbar(crash_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    # Grid layout for canvas and scrollbar
    canvas.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    # Configure grid weights for scrollbar
    crash_frame.columnconfigure(1, weight=0)

    # Create the main scrollable frame inside canvas
    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Update scroll region after widgets are added
    def update_scroll_region():
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    # Bind mousewheel for scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    magic_string = get_magic_string()
    path_var = tk.StringVar(value=magic_string)

    ########################################################################

    # Single LabelFrame containing everything
    update_crash_rename_from_csv_header = ttk.LabelFrame(
        scrollable_frame, text="Update Crash Rename Fields from CSV"
    )  # Fixed: added closing parenthesis

    update_crash_rename_from_csv_header.pack(fill="x", **PADDING)  # type: ignore

    # First row frame for entry and button
    update_row1_frame = ttk.Frame(update_crash_rename_from_csv_header)
    update_row1_frame.pack(fill="x", padx=10, pady=(10, 5))

    ttk.Button(
        update_row1_frame,
        text="Update Crash Rename Fields from CSV",
        command=lambda: [CrashHandler.set_naming_convention_from_crash_rename_csv(log_box), update_crash_rename_fields() ]
    ).pack(fill="x", **PADDING)  # type: ignore



            #messagebox.showerror("Error", f"Failed to update crash rename fields:\n{str(e)}")

    separator = ttk.Separator(update_crash_rename_from_csv_header, orient="horizontal")
    separator.pack(fill="x", padx=20, pady=(12, 0))

    ########################################################################

    crash_page_header = ttk.LabelFrame(scrollable_frame, text="Magic String")
    crash_page_header.pack(fill="x", **PADDING)  # type: ignore

    # First row frame for entry and button
    row1_frame = ttk.Frame(crash_page_header)
    row1_frame.pack(fill="x", padx=10, pady=(10, 5))

    # Entry field and button in the same row
    Text_value = ttk.Entry(row1_frame, textvariable=path_var)
    Text_value.pack(side="left", fill="x", expand=True)

    ttk.Button(
        row1_frame,
        text="Set Magic String",
        command=lambda: set_magic_string(path_var, Text_value.get()),  # Fixed: typo in function name
    ).pack(side="right", padx=(10, 0))

    separator = ttk.Separator(crash_page_header, orient="horizontal")
    separator.pack(fill="x", padx=20, pady=(12, 0))

    ########################################################################

    crash_page_main = ttk.LabelFrame(scrollable_frame, text="Crash Renaming and Upload")
    crash_page_main.pack(fill="x", **PADDING)  # type: ignore

    # Get the string values from your method
    market_str, name_str, fstid_str, operator_str, tdc_serial_str,magicString= (
        CrashHandler.get_naming_convention()
    )  # Fixed: added closing parenthesis

    # Create a grid-based layout (3 columns, 2 rows)
    entry_grid_frame = ttk.Frame(crash_page_main)
    entry_grid_frame.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Configure grid weights for even distribution
    for i in range(3):
        entry_grid_frame.columnconfigure(i, weight=1)
    for i in range(2):
        entry_grid_frame.rowconfigure(i, weight=0)

    # Row 1 - Market, Naming, FST ID
    market_var = tk.StringVar(value=market_str)
    ttk.Label(entry_grid_frame, text="Market:").grid(row=0, column=0, sticky="w", **PADDING)  # type: ignore
    market_name = ttk.Entry(entry_grid_frame, textvariable=market_var, width=20)
    market_name.grid(row=0, column=0, sticky="ew", **PADDING)  # type: ignore

    naming_var = tk.StringVar(value=name_str)
    ttk.Label(entry_grid_frame, text="Naming:").grid(row=0, column=1, sticky="w", **PADDING)  # type: ignore
    naming = ttk.Entry(entry_grid_frame, textvariable=naming_var, width=20)
    naming.grid(row=0, column=1, sticky="ew", **PADDING)  # type: ignore

    fst_id_var = tk.StringVar(value=fstid_str)
    ttk.Label(entry_grid_frame, text="FST ID:").grid(row=0, column=2, sticky="w", **PADDING)  # type: ignore
    fst_id_name = ttk.Entry(entry_grid_frame, textvariable=fst_id_var, width=20)
    fst_id_name.grid(row=0, column=2, sticky="ew", **PADDING)  # type: ignore

    # Row 2 - Operator, TDC Serial, Button
    operator_var = tk.StringVar(value=operator_str)
    ttk.Label(entry_grid_frame, text="Operator:").grid(row=1, column=0, sticky="w", **PADDING)  # type: ignore
    operator = ttk.Entry(entry_grid_frame, textvariable=operator_var, width=20)
    operator.grid(row=1, column=0, sticky="ew", **PADDING)  # type: ignore

    tdc_serial_var = tk.StringVar(value=tdc_serial_str)
    ttk.Label(entry_grid_frame, text="TDC Serial:").grid(row=1, column=1, sticky="w", **PADDING)  # type: ignore
    tdc_serial = ttk.Entry(entry_grid_frame, textvariable=tdc_serial_var, width=20)
    tdc_serial.grid(row=1, column=1, sticky="ew", **PADDING)  # type: ignore

    ttk.Button(
        entry_grid_frame,
        text="Update Fields",
        command=lambda: CrashHandler.set_naming_convention(
            market_name.get(),
            naming.get(),
            fst_id_name.get(),
            operator.get(),
            tdc_serial.get(),
        ),
    ).grid(row=1, column=2, sticky="ew", **PADDING)  # type: ignore

    def update_crash_rename_fields():
        
        market_str, name_str, fstid_str, operator_str, tdc_serial_str,magicString= (
            CrashHandler.get_naming_convention()
        )  # Fixed: added closing parenthesis
        
        market_var.set(market_str)  # type: ignore
        naming_var.set(name_str)  # type: ignore
        tdc_serial_var.set(tdc_serial_str)  # type: ignore
        operator_var.set(operator_str)  # type: ignore
        fst_id_var.set(fstid_str)  # type: ignore
        path_var.set(magicString)

    ########################################################################

    second_row_frame = ttk.Frame(crash_page_main)
    second_row_frame.pack(fill="x", **PADDING)  # type: ignore

    # Now the separator will be on its own line
    separator = ttk.Separator(second_row_frame, orient="horizontal")
    separator.pack(fill="x", padx=20, pady=(12, 0))

    crash_naming_label = ttk.Label(
        second_row_frame, text="Current Renaming: \n\n", wraplength=1000
    )  # Fixed: added closing parenthesis

    crash_naming_label.pack(fill="x", **PADDING)  # type: ignore

    ttk.Button(
        crash_page_main,
        text="GET Crash Naming",
        command=lambda: crash_naming_label.config(
            text=f"Current Renaming: \n\n{CrashHandler.get_crash_naming()}"
        ),
    ).pack(fill="x", **PADDING)  # type: ignore

    separator = ttk.Separator(crash_page_main, orient="horizontal")
    separator.pack(fill="x", padx=20, pady=(12, 0))

    ########################################################################

    # Table for Crash Info
    Crash_table = ttk.LabelFrame(crash_page_main, text="Crash Table")
    Crash_table.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Make the LabelFrame act like a grid container
    Crash_table.rowconfigure(0, weight=1)  # table row grows
    Crash_table.rowconfigure(1, weight=0)
    Crash_table.rowconfigure(2, weight=0)
    Crash_table.columnconfigure(0, weight=1)

    COLUMNS = ("ROOT_CAUSE", "ADB_ID", "CRASH_PATH", "TIMESTAMP", "FST_ID")

    tree = ttk.Treeview(
        Crash_table,
        columns=COLUMNS,
        show="headings",
        height=4,  # visible rows
    )  # Fixed: added closing parenthesis

    # Headings
    tree.heading("ROOT_CAUSE", text="ROOT_CAUSE")
    tree.heading("ADB_ID", text="ADB_ID")
    tree.heading("CRASH_PATH", text="CRASH_PATH")
    tree.heading("TIMESTAMP", text="TIMESTAMP")
    tree.heading("FST_ID", text="FST_ID")

    # Column widths
    tree.column("ROOT_CAUSE", width=170, anchor="center")
    tree.column("ADB_ID", width=120, anchor="center")
    tree.column("CRASH_PATH", width=120, anchor="center")
    tree.column("TIMESTAMP", width=140, anchor="center")
    tree.column("FST_ID", width=180, anchor="center")

    # Scrollbars for Treeview
    vscroll = ttk.Scrollbar(Crash_table, orient="vertical", command=tree.yview)

    # Wire scrollbars to the tree
    tree.configure(yscrollcommand=vscroll.set)

    # Layout
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns")

    buttons_frame = ttk.Frame(Crash_table)
    buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 0))

    buttons_frame.columnconfigure(0, weight=1)  # Left section
    buttons_frame.columnconfigure(1, weight=0)  # Center section
    buttons_frame.columnconfigure(2, weight=1)  # Right section

    # Left button
    ttk.Button(
        buttons_frame,
        text="Crash Forecast",
        command=lambda:crash_forecast_updateTable()
    ).grid(row=0, column=0, sticky="w", **PADDING)  # type: ignore
     
    def crash_forecast_updateTable():
           CrashHandler.forecast_crashes(get_selected_crash_paths()),
           load_crash_table()

    # 2nd button
    ttk.Button(
        buttons_frame,
        text="Zip & Upload Crash dump",
        command=lambda: start_thread(
            CrashHandler.zip_and_upload_crash_dump,
            "Zip and upload thread",
            daemon=True,
            crash_dir_list=get_selected_crash_paths(),  
            log_box=log_box,
            callback=load_crash_table(),
        ),
    ).grid(row=0, column=1, sticky="e", **PADDING)  # type: ignore
    
   
        

    # 3rd button
    ttk.Button(
        buttons_frame,
        text="Refresh Data",
        command=lambda: load_crash_table(),
    ).grid(row=0, column=2, pady=8)

    # Right button
    ttk.Button(
        buttons_frame,
        text="Delete",
        command=lambda: start_thread(
            CrashHandler.remove_crash_entries,
            "Delete Crash entries thread",
            daemon=True,
            filepaths=get_selected_crash_paths(),
            callback=load_crash_table(),
        ),
    ).grid(row=0, column=3, pady=8)

    def load_crash_table():
        """Read CSV and populate the table."""
        try:
            crash_meta_csv = os.path.join(CTM_LOGS_DIR, "CrashMetaInfo.csv")
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
                      
                        row.get("FST_ID", ""),
                    ),
                )  # Fixed: added closing parenthesis

        except Exception as e:
            add_log(f"Exception during load_crash_table: {e}")

    # initial fill
    load_crash_table()

    def get_selected_crash_paths():
        selected_items = tree.selection()  # Returns tuple of selected item IDs
        if not selected_items:
            #print("No rows selected")
            add_log("No rows selected")
            return []

        crash_paths = []
        for item_id in selected_items:
            item_data = tree.item(item_id)  # Returns dict with 'values' key
            values = item_data["values"]  # List of column values
            crash_path = values[2]  # CRASH_PATH is index 2
            crash_paths.append(crash_path)

        add_log(f"Selected crash paths: {crash_paths}")
        return crash_paths

    bottom_frame = ttk.LabelFrame(scrollable_frame, text="Logs")
    bottom_frame.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Configure grid for the LabelFrame
    bottom_frame.rowconfigure(0, weight=1)  # Log box grows
    bottom_frame.rowconfigure(1, weight=0)  # Button row doesn't grow
    bottom_frame.columnconfigure(0, weight=1)

    # Create Text widget with scrollbar for logs
    log_box = tk.Text(
        bottom_frame,
        height=10,
        wrap="word",
        relief="sunken",
        borderwidth=1,
    )

    # Vertical scrollbar for log box
    log_scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=log_box.yview)
    log_box.configure(yscrollcommand=log_scrollbar.set)

    # Grid layout for log box and scrollbar
    log_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
    log_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 5))

    # Clear button
    button_frame = ttk.Frame(bottom_frame)
    button_frame.grid(row=1, column=0, columnspan=2, sticky="e", padx=10, pady=(0, 10))

    ttk.Button(
        button_frame,
        text="Clear Logs",
        command=lambda: log_box.delete("1.0", "end"),
    ).pack(side="right")

    # Function to add logs to the log box
    def add_log(message: str):
        """Add a log message to the log box and scroll to the bottom."""
        log_box.insert("end", message + "\n")
        log_box.see("end")  # Auto-scroll to the latest log

    # Update scroll region after all widgets are added
    update_scroll_region()

    return crash_frame