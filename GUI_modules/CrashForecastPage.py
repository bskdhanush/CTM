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


def set_magic_string(path_var, magic_string: str):
    print("setting the string")
    cfg = load_prov_json()
    cfg.update({"magic_string": magic_string})
    save_prov_json(cfg)
    path_var.set(magic_string)


log_box = None


def create_crash_forecast_page(container, pages, add_nav):
    crash_frame = ttk.Frame(container)
    crash_frame.grid(row=0, column=0, sticky="nsew")
    pages["Crash"] = crash_frame
    add_nav("Crash Processing", "Crash")

    # CRITICAL: Configure grid weights for main frame
    crash_frame.rowconfigure(0, weight=1)
    crash_frame.columnconfigure(0, weight=1)

    # CRITICAL: Canvas must have sticky="nsew" and fill both axes
    canvas = tk.Canvas(crash_frame, highlightthickness=0, bg="black")
    vsb = ttk.Scrollbar(crash_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    crash_frame.columnconfigure(1, weight=0)

    scrollable_frame = ttk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    scrollable_frame.columnconfigure(0, weight=1)
    scrollable_frame.rowconfigure(0, weight=0)
    scrollable_frame.rowconfigure(1, weight=0)
    scrollable_frame.rowconfigure(2, weight=0)
    scrollable_frame.rowconfigure(3, weight=1)

    def update_scroll_region():
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        # CRITICAL: Update canvas window width to match canvas width
        canvas_width = canvas.winfo_width()
        if canvas_width > 1:
            canvas.itemconfig(canvas_window, width=canvas_width)

    def on_canvas_resize(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", on_canvas_resize)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    magic_string = get_magic_string()
    path_var = tk.StringVar(value=magic_string)

    # ===== UPDATE CRASH RENAME FROM CSV =====
    update_crash_rename_from_csv_header = ttk.LabelFrame(
        scrollable_frame, text="Update Crash Rename Fields from CSV"
    )
    update_crash_rename_from_csv_header.pack(fill="both", expand=False, **PADDING)

    update_row1_frame = ttk.Frame(update_crash_rename_from_csv_header)
    update_row1_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    def update_crash_rename_fields():
        market_str, name_str, fstid_str, operator_str, tdc_serial_str, magicString = (
            CrashHandler.get_naming_convention()
        )
        market_var.set(market_str)
        naming_var.set(name_str)
        tdc_serial_var.set(tdc_serial_str)
        operator_var.set(operator_str)
        fst_id_var.set(fstid_str)
        path_var.set(magicString)

    ttk.Button(
        update_row1_frame,
        text="Update Crash Rename Fields from CSV",
        command=lambda: [
            CrashHandler.set_naming_convention_from_crash_rename_csv(log_box),
            update_crash_rename_fields(),
        ],
    ).pack(fill="both", expand=True, **PADDING)

    separator = ttk.Separator(update_crash_rename_from_csv_header, orient="horizontal")
    separator.pack(fill="both", expand=False, padx=20, pady=(12, 0))

    # ===== MAGIC STRING SECTION =====
    crash_page_header = ttk.LabelFrame(scrollable_frame, text="Magic String")
    crash_page_header.pack(fill="both", expand=False, **PADDING)

    row1_frame = ttk.Frame(crash_page_header)
    row1_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    Text_value = ttk.Entry(row1_frame, textvariable=path_var)
    Text_value.pack(side="left", fill="both", expand=True)

    ttk.Button(
        row1_frame,
        text="Set Magic String",
        command=lambda: set_magic_string(path_var, Text_value.get()),
    ).pack(side="right", padx=(10, 0))

    separator = ttk.Separator(crash_page_header, orient="horizontal")
    separator.pack(fill="both", expand=False, padx=20, pady=(12, 0))

    # ===== CRASH RENAMING AND UPLOAD =====
    crash_page_main = ttk.LabelFrame(
        scrollable_frame, text="Crash Renaming and Upload"
    )
    crash_page_main.pack(fill="both", expand=False, **PADDING)

    market_str, name_str, fstid_str, operator_str, tdc_serial_str, magicString = (
        CrashHandler.get_naming_convention()
    )

    entry_grid_frame = ttk.Frame(crash_page_main)
    entry_grid_frame.pack(fill="both", expand=True, **PADDING)

    for i in range(3):
        entry_grid_frame.columnconfigure(i, weight=1)
    for i in range(2):
        entry_grid_frame.rowconfigure(i, weight=0)

    market_var = tk.StringVar(value=market_str)
    ttk.Label(entry_grid_frame, text="Market:").grid(
        row=0, column=0, sticky="w", **PADDING
    )
    market_name = ttk.Entry(entry_grid_frame, textvariable=market_var, width=20)
    market_name.grid(row=0, column=0, sticky="ew", **PADDING)

    naming_var = tk.StringVar(value=name_str)
    ttk.Label(entry_grid_frame, text="Naming:").grid(
        row=0, column=1, sticky="w", **PADDING
    )
    naming = ttk.Entry(entry_grid_frame, textvariable=naming_var, width=20)
    naming.grid(row=0, column=1, sticky="ew", **PADDING)

    fst_id_var = tk.StringVar(value=fstid_str)
    ttk.Label(entry_grid_frame, text="FST ID:").grid(
        row=0, column=2, sticky="w", **PADDING
    )
    fst_id_name = ttk.Entry(entry_grid_frame, textvariable=fst_id_var, width=20)
    fst_id_name.grid(row=0, column=2, sticky="ew", **PADDING)

    operator_var = tk.StringVar(value=operator_str)
    ttk.Label(entry_grid_frame, text="Operator:").grid(
        row=1, column=0, sticky="w", **PADDING
    )
    operator = ttk.Entry(entry_grid_frame, textvariable=operator_var, width=20)
    operator.grid(row=1, column=0, sticky="ew", **PADDING)

    tdc_serial_var = tk.StringVar(value=tdc_serial_str)
    ttk.Label(entry_grid_frame, text="TDC Serial:").grid(
        row=1, column=1, sticky="w", **PADDING
    )
    tdc_serial = ttk.Entry(entry_grid_frame, textvariable=tdc_serial_var, width=20)
    tdc_serial.grid(row=1, column=1, sticky="ew", **PADDING)

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
    ).grid(row=1, column=2, sticky="ew", **PADDING)

    second_row_frame = ttk.Frame(crash_page_main)
    second_row_frame.pack(fill="both", expand=True, **PADDING)

    separator = ttk.Separator(second_row_frame, orient="horizontal")
    separator.pack(fill="both", expand=False, padx=20, pady=(12, 0))

    crash_naming_label = ttk.Label(
        second_row_frame, text="Current Renaming: \n\n", wraplength=1000
    )
    crash_naming_label.pack(fill="both", expand=True, **PADDING)

    ttk.Button(
        crash_page_main,
        text="GET Crash Naming",
        command=lambda: crash_naming_label.config(
            text=f"Current Renaming: \n\n{CrashHandler.get_crash_naming()}"
        ),
    ).pack(fill="both", expand=False, **PADDING)

    separator = ttk.Separator(crash_page_main, orient="horizontal")
    separator.pack(fill="both", expand=False, padx=20, pady=(12, 0))

    # ===== CRASH TABLE SECTION =====
    Crash_table = ttk.Frame(crash_page_main, border=1) 
    Crash_table.pack(fill="both", expand=False, **PADDING)

    # Create header frame
    header_frame = ttk.Frame(Crash_table)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")  # Use grid instead of pack

    header_frame.columnconfigure(1, weight=1)  # Spacer column expands

    # Left side - "Crash Table" label
    header_label = ttk.Label(header_frame, text="Crash Table")
    header_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Right side - text label
    auto_forecastText= ttk.Label(header_frame, text="Enable/Disable Auto-ForeCast: ")
    auto_forecastText.grid(row=0, column=2, sticky="e", padx=(5, 2))

    def is_AutoForecast_enabled() -> bool:
        cfg = load_prov_json()
        return cfg.get("Auto_forecast", False)

    def update_AutoForeCast_value():
        cfg = load_prov_json()
        cfg["Auto_forecast"] = bool(checkbox_var.get())
        save_prov_json(cfg)
        print(f"Updated Auto_forecast to: {cfg['Auto_forecast']}")

    # Right side - checkbox (rightmost)
    checkbox_var = tk.BooleanVar(value=is_AutoForecast_enabled())
    auto_forecastCheckBox = ttk.Checkbutton(
        header_frame,
        variable=checkbox_var,
        command=update_AutoForeCast_value  # no parentheses!
    )
    auto_forecastCheckBox.grid(row=0, column=3, sticky="e", padx=(0, 5))

    



    # Configure grid for Crash_table
    Crash_table.rowconfigure(1, weight=1)  # Tree row expands
    Crash_table.rowconfigure(2, weight=0)
    Crash_table.columnconfigure(0, weight=1)

    COLUMNS = ("ROOT_CAUSE", "ADB_ID", "CRASH_PATH", "TIMESTAMP", "FST_ID")

    tree = ttk.Treeview(
        Crash_table,
        columns=COLUMNS,
        show="headings",
        height=6,
    )

    tree.heading("ROOT_CAUSE", text="ROOT_CAUSE")
    tree.heading("ADB_ID", text="ADB_ID")
    tree.heading("CRASH_PATH", text="CRASH_PATH")
    tree.heading("TIMESTAMP", text="TIMESTAMP")
    tree.heading("FST_ID", text="FST_ID")

    tree.column("ROOT_CAUSE", width=170, anchor="center") 
    tree.column("ADB_ID", width=120, anchor="center")
    tree.column("CRASH_PATH", width=120, anchor="center")
    tree.column("TIMESTAMP", width=140, anchor="center")
    tree.column("FST_ID", width=180, anchor="center")

    vscroll = ttk.Scrollbar(Crash_table, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vscroll.set)

    tree.grid(row=1, column=0, sticky="nsew")
    vscroll.grid(row=1, column=1, sticky="ns")

    buttons_frame = ttk.Frame(Crash_table)
    buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(6, 0))

    buttons_frame.columnconfigure(0, weight=1)
    buttons_frame.columnconfigure(1, weight=0)
    buttons_frame.columnconfigure(2, weight=1)
    buttons_frame.columnconfigure(3, weight=0)
    def load_crash_table():
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
                )
        except Exception as e:
            add_log(f"Exception during load_crash_table: {e}")

    load_crash_table()

    def get_selected_crash_paths():
        selected_items = tree.selection()
        if not selected_items:
            add_log("No rows selected")
            return []
        crash_paths = []
        for item_id in selected_items:
            item_data = tree.item(item_id)
            values = item_data["values"]
            crash_path = values[2]
            crash_paths.append(crash_path)
        add_log(f"Selected crash paths: {crash_paths}")
        return crash_paths

    def crash_forecast_updateTable():
        CrashHandler.forecast_crashes(get_selected_crash_paths())
        load_crash_table()

    ttk.Button(
        buttons_frame,
        text="Crash Forecast",
        command=lambda: crash_forecast_updateTable(),
    ).grid(row=0, column=0, sticky="ew", **PADDING)

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
    ).grid(row=0, column=1, sticky="ew", **PADDING)

    ttk.Button(
        buttons_frame,
        text="Refresh Data",
        command=lambda: load_crash_table(),
    ).grid(row=0, column=2, sticky="ew", **PADDING)

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
    ).grid(row=0, column=3, sticky="ew", **PADDING)

    # ===== LOGS SECTION =====
    bottom_frame = ttk.LabelFrame(scrollable_frame, text="Logs")
    bottom_frame.pack(fill="both", expand=True, **PADDING)

    bottom_frame.rowconfigure(0, weight=1)
    bottom_frame.rowconfigure(1, weight=0)
    bottom_frame.columnconfigure(0, weight=1)

    log_box = tk.Text(
        bottom_frame,
        height=12,
        wrap="word",
        relief="sunken",
        borderwidth=1,
    )

    log_scrollbar = ttk.Scrollbar(
        bottom_frame, orient="vertical", command=log_box.yview
    )
    log_box.configure(yscrollcommand=log_scrollbar.set)

    log_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
    log_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 5))

    button_frame = ttk.Frame(bottom_frame)
    button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

    ttk.Button(
        button_frame,
        text="Clear Logs",
        command=lambda: log_box.delete("1.0", "end"),
    ).pack(side="right")

    def add_log(message: str):
        log_box.insert("end", message + "\n")
        log_box.see("end")

    update_scroll_region()

    return crash_frame
