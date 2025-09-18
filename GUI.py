from __future__ import annotations          # for | typing in <3.10

# ── stdlib ──────────────────────────────────────────────────────────────────
import  datetime as dt
import os
from functools import partial
import json
from pathlib import Path
import platform
import tkinter as tk
from tkinter import ttk ,filedialog, messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import logging

# ── 3rd-party ──────────────────────────────────────────────────────────────
import sv_ttk

# ── local app modules ──────────────────────────────────────────────────────
import ADBController
from GUI_modules import DataMonitorPage
import MainController
import WifiController
import QutsController
import AwsScheduler as aws
import DataMonitorController as dmc
import PlotDynamicRender as rdp
import CrashCountController as cc
import JsonHandler as JH
import gitReleases as gr
import QSTAFInstaller 


def add_copy_support(root: tk.Tk) -> None:
    is_mac = platform.system() == 'Darwin'
    accel = 'Command-C' if is_mac else 'Control-c'

    menu = tk.Menu(root, tearoff=0)

    def label_text(w):
        try:
            txt = w.cget("text")
            if not txt:
                var = w.cget("textvariable")
                if var:
                    txt = root.getvar(var)
            return str(txt)
        except Exception:
            return ""

    def copy_from_widget(widget=None):
        w = widget or root.focus_get()
        # Enable universal copy (labels, text, entries, listbox, treeview, logs)

        if w is None:
            return
        sel = ""
        try:
            if isinstance(w, (tk.Entry, ttk.Entry)):
                sel = w.selection_get()
            elif isinstance(w, (tk.Text, ScrolledText)):
                try:
                    sel = w.get("sel.first", "sel.last")
                except Exception:
                    # fallback: copy all text (handles disabled Text/ScrolledText)
                    state = str(w.cget("state"))
                    if state == "disabled":
                        w.configure(state="normal")
                        sel = w.get("1.0", "end-1c")
                        w.configure(state="disabled")
                    else:
                        sel = w.get("1.0", "end-1c")
            elif isinstance(w, tk.Listbox):
                indices = w.curselection()
                sel = "\n".join(w.get(i) for i in indices) if indices else ""
            elif isinstance(w, ttk.Treeview):
                items = w.selection()
                rows = []
                for iid in items:
                    vals = w.item(iid, "values")
                    if vals:
                        rows.append("\t".join(map(str, vals)))
                    else:
                        rows.append(str(w.item(iid, "text")))
                sel = "\n".join(rows)
            elif isinstance(w, (ttk.Label, tk.Label)):
                sel = label_text(w)
            else:
                try:
                    sel = root.selection_get()
                except Exception:
                    sel = ""
        except Exception:
            sel = ""
        if sel:
            root.clipboard_clear()
            root.clipboard_append(sel)

    def show_menu(e):
        w = e.widget
        menu.delete(0, 'end')
        if isinstance(w, (tk.Entry, tk.Text, ttk.Entry, ScrolledText)):
            menu.add_command(label="Cut", command=lambda: w.event_generate("<<Cut>>"))
            menu.add_command(label="Copy", command=lambda: copy_from_widget(w))
            menu.add_command(label="Paste", command=lambda: w.event_generate("<<Paste>>"))
            menu.add_separator()
            menu.add_command(label="Select All", command=lambda: w.event_generate("<<SelectAll>>"))
        elif isinstance(w, (tk.Listbox, ttk.Treeview, ttk.Label, tk.Label)):
            menu.add_command(label="Copy", command=lambda: copy_from_widget(w))
        if menu.index('end') is not None:
            menu.tk_popup(e.x_root, e.y_root)

    root.bind_all(f'<{accel}>', lambda e: (copy_from_widget(), "break"))
    # Right-click context menu
    if is_mac:
        root.bind_all("<Button-2>", show_menu, add="+")
    root.bind_all("<Button-3>", show_menu, add="+")

# ───────────────────────────────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────────────────────────────
PADDING:dict[str, int] = {"padx": 12, "pady": 8}
white_accent = "#FFFFFF"
red_accent  = "#E95959"


# ── Global toggle variable ─────────────────────────────────────────────────

root =None


def launch_gui() -> None:
    """Construct and run the UI."""
    global root 

    # ── json watcher  ──────────────────────────────────────────────────────────
    class JsonFileWatcher(FileSystemEventHandler):
        def __init__(self, callback, file_path_to_watch):
            self.callback = callback
            self.file_path_to_watch = file_path_to_watch

        def on_modified(self, event):
            # only react if *that* JSON file changed
            if event.src_path == str(self.file_path_to_watch):
                # schedule the UI update on the Tk main thread
                if root is not None:
                    root.after(0, self.callback)
            logging.info(f"JSON Watcher: File modified - {event.src_path}")

    def start_json_file_watcher(callback, file_path_to_watch):
        obs = Observer()
        handler = JsonFileWatcher(callback, file_path_to_watch)
        watch_dir = os.path.dirname(file_path_to_watch)
        if not os.path.exists(watch_dir):
            os.makedirs(watch_dir)
        obs.schedule(handler, watch_dir, recursive=False)
        obs.start()
        # keep it running in background
        threading.Thread(target=obs.join, daemon=True).start()
   

    # ── Window ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("CPE Test Manager V2.0")
    root.geometry("1024x768")
    root.resizable(True, True)
    sv_ttk.set_theme("dark")
    add_copy_support(root)

    # ── Styles ──────────────────────────────────────────────────────────
    style = ttk.Style(root)
    style.configure("Sidebar.TFrame", background="#2a2a2e")

    # ── header (mini) ───────────────────────────────────────────────────────
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)

    for col in range(7):
       header_frame.columnconfigure(col, weight=0)
    header_frame.columnconfigure(1, weight=1)   # left side expands
    
  
    meta_var = tk.StringVar(value="Meta : ")
    mpss_var = tk.StringVar(value="MPSS : ")

    ttk.Label(header_frame, textvariable=meta_var,  anchor="w") \
        .grid(row=0, column=0, sticky="w", padx=15)
    ttk.Label(header_frame, textvariable=mpss_var,  anchor="w") \
        .grid(row=1, column=0, sticky="w", padx=15)

    def refresh_meta_mpss() -> None:
        meta, mpss = MainController.get_meta_mpss()
        meta_var.set(f"Meta : {meta or 'UNKNOWN'}")
        mpss_var.set(f"MPSS : {mpss or 'UNKNOWN'}")
    refresh_meta_mpss()

    ttk.Button(
        header_frame, text="Get Build info",
        command=refresh_meta_mpss, width=12
    ).grid(row=2, column=0, sticky="w", padx=10, pady=5)

    # --- reboot button (centre-left, on its own row) ----------------------------
    ttk.Button(
        header_frame, text="Restart Device", width=12,
        command=lambda: WifiController.run_command("adb root && adb reboot")
    ).grid(row=2, column=2, sticky="w", padx=10, pady=5)

    # --- crash counters (hard-right) -------------------------------------------
    crash_var  = tk.StringVar(value="—")
    RDKB_var   = tk.StringVar(value="—")

    crash_text_lbl = ttk.Label(header_frame, text="Device Crashes:", anchor="e")
    crash_text_lbl.grid(row=0, column=3, sticky="e", padx=(10, 5))
    crash_lbl = ttk.Label(header_frame, textvariable=crash_var, anchor="w")
    crash_lbl.grid(row=0, column=4, sticky="w")

    RDKB_text_lbl = ttk.Label(header_frame, text="RDKB Crashes:",  anchor="e")
    RDKB_text_lbl.grid(row=1, column=3, sticky="e", padx=(10, 5))
    RDKB_lbl = ttk.Label(header_frame, textvariable=RDKB_var, anchor="w")
    RDKB_lbl.grid(row=1, column=4, sticky="w")

    ttk.Button(
        header_frame, text="Reset Counter", width=12,
        command=cc.rest_counter
    ).grid(row=2, column=3, columnspan=2, sticky="e", padx=20, pady=5)

    
    def load_counters():
        cfg = JH.load_json()
        crash_count = cfg.get("crash_counter", 0)
        rdkb_count = cfg.get("rdkbcrash_counter", 0)

        # update the StringVars
        crash_var.set(str(crash_count))
        RDKB_var.set(str(rdkb_count))
        if crash_count > 0:
            crash_lbl.config(foreground=red_accent)
            crash_text_lbl.configure(foreground=red_accent)
        else:
            crash_lbl.configure(foreground=white_accent)
            crash_text_lbl.configure(foreground=white_accent)

        if rdkb_count > 0:
            RDKB_lbl.configure(foreground=red_accent)
            RDKB_text_lbl.configure(foreground=red_accent)

        else:
            RDKB_lbl.configure(foreground=white_accent)
            RDKB_text_lbl.configure(foreground=white_accent)

    load_counters()  # initial

     # start watching the JSON for changes
    start_json_file_watcher(load_counters, cc.CONFIG_PATH)


    # ── Grid weights ─────────────────────────────────────────────────────
    root.columnconfigure(1, weight=1)  # column 1 = main content
    root.rowconfigure(1, weight=1)     # row 1   = sidebar  pages

    # ── Sidebar & container ───────────────────────────────────────────────
    sidebar   = ttk.Frame(root, style="Sidebar.TFrame")
    container = ttk.Frame(root)
    sidebar.grid(row=1, column=0, sticky="ns")
    container.grid(row=1, column=1, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    pages: dict[str, ttk.Frame] = {}
    nav_btns: dict[str, ttk.Button] = {}

    def show(page: str) -> None:
        pages[page].tkraise()
        for name, btn in nav_btns.items():
            btn.configure(style="Accent.TButton" if name == page else "TButton")

    def add_nav(text: str, key: str) -> None:
        btn = ttk.Button(sidebar, text=text, width=15, command=lambda k=key: show(k))
        btn.pack(fill="x", pady=6, padx=6)
        nav_btns[key] = btn


    # ── Footer / status bar ───────────────────────────────────────────────
    footer = ttk.Frame(root)
    footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 8))

    # give each of 4 columns equal weight
    footer.columnconfigure(0, weight=0)
    footer.columnconfigure(1, weight=1)
    footer.columnconfigure(2, weight=1)
    footer.columnconfigure(3, weight=0)

    # --- vars ---
    adb_var       = tk.StringVar(value="ADB ID: --")
    quts_stat_var = tk.StringVar(value="QUTS: Checking…")
    center_var    = tk.StringVar(value="Internet status")
    version_text  = f"QSTAF VERSION: {MainController.get_qstaf_version()}"

    # --- widgets in desired order ---
    adb_label = ttk.Label(footer, textvariable=adb_var)
    quts_label = tk.Label(
        footer,
        textvariable=quts_stat_var,
        font=("TkDefaultFont", 10, "bold"),
    )
    internet_label = tk.Label(
        footer,
        textvariable=center_var,
        font=("Segoe UI", 12),
        fg="white",
        anchor="center",
    )
    version_label = ttk.Label(footer, text=version_text)

    # --- grid them evenly ---
    adb_label.grid(    row=0, column=0, sticky="w",  padx=5)
    quts_label.grid(   row=0, column=1, sticky="ew", padx=5)
    internet_label.grid(   row=0, column=2, sticky="ew", padx=5)
    version_label.grid(  row=0, column=3, sticky="e",  padx=5)

    def update_label():
        try:
            with open(ADBController.json_path, "r") as f:
                data = json.load(f)
            adb_id = data.get("ADB ID", "--")
            adb_var.set(f"ADB ID: {adb_id}")
        except (FileNotFoundError, json.JSONDecodeError):
            adb_id = "--"

    update_label()
    start_json_file_watcher(update_label,Path(ADBController.json_path))

# # this returns immediately and never blocks your mainloop
    #MainController.start_adb_track_thread(root, update_label)


    def update_internet_status():
        status = dmc.get_internet_status()
        if status == 1:
            center_var.set("Internet status: GOOD")
            internet_label.configure(foreground="green", font=("Segoe UI", 14) )

        elif status == 0:
            center_var.set("Internet status: DOWN")
            internet_label.configure(foreground="red", font=("Segoe UI", 14))

        else:
            center_var.set("Internet status")
            internet_label.configure(foreground="white", font=("Segoe UI", 12))
            
        if root is not None:
            root.after(5000, update_internet_status)


    root.after(0, update_internet_status)


    def _update_quts() -> None:
        running = QutsController.is_service_running("QUTS")
        quts_stat_var.set(f"QUTS: {'Running' if running else 'Stopped'}")

        quts_label.config(
            fg=white_accent if running else red_accent)
        if root is not None:
            root.after(3_000, _update_quts)

  
    _update_quts()

    # ── MAIN PAGE ─────────────────────────────────────────────────────────
    main_pg = ttk.Frame(container)
    main_pg.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_pg
    add_nav("Main", "Main")

    # Framework control
    ctrl = ttk.LabelFrame(main_pg, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)# type: ignore
    control_ts_var = tk.StringVar(value="Control: Not started")
    traffic_ts_var = tk.StringVar(value="Traffic: Not started")
    relaunch_timer=tk.StringVar(value="The frameworks will restart in:")
    rest_timer=tk.StringVar(value="none")

    def update_timestamps():
        cfg = JH.load_json()
        cts = cfg.get("control_start_timestamp")
        tts = cfg.get("traffic_start_timestamp")
        rest_timer=cfg.get("relaunch_timer")
        control_ts_var.set(f"Control started at: {cts}" if cts else "Control: Not started")
        traffic_ts_var.set(f"Traffic started at: {tts}" if tts else "Traffic: Not started")
        relaunch_timer.set(f"The frameworks will restart in {rest_timer} hours")

    update_timestamps()
    start_json_file_watcher(update_timestamps, JH.get_json_path())


    row = ttk.Frame(ctrl)
    row.pack(fill="x", **PADDING)# type: ignore
    row_s = ttk.Frame(ctrl)
    row_s.pack(fill="x", **PADDING)# type: ignore
    row_text=ttk.Frame(ctrl)
    row_text.pack(fill="x", **PADDING)# type: ignore
    row_text.columnconfigure(0, weight=1)
    row_text.columnconfigure(1, weight=1)
    row_relaunch = ttk.Frame(ctrl)
    row_relaunch.pack(fill="x", **PADDING)# type: ignore

    ttk.Button(
        row,
        text="Launch Control Framework",
        command=lambda:MainController.start_framework("control"), # type: ignore
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row,
        text="Launch Traffic Framework",
        command=lambda:MainController.start_framework("traffic"), # type: ignore
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    ttk.Button(
        row_s,
        text="Stop Control Framework",
        command=partial(MainController.stop_framework,"control"),
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row_s,
        text="Stop Traffic Framework",
        command=partial(MainController.stop_framework,"traffic"),
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    ttk.Label(
        row_text,
        textvariable=control_ts_var,
        anchor="center"
    ).grid(row=0, column=0, sticky="ew", padx=5, pady=6)

    ttk.Label(
        row_text,
        textvariable=traffic_ts_var,
        anchor="center"
    ).grid(row=0, column=1, sticky="ew", padx=5, pady=6)

    ttk.Label(
        row_relaunch,
        textvariable=relaunch_timer,
    ).pack(side="left", expand=True, fill="x", padx=(20, 6), ipady=6)
    
    reset_val_var = tk.StringVar(value=" ")
    ttk.Entry(
    row_relaunch, 
    textvariable=reset_val_var, 
    width=4
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row_relaunch,
        text="Update Restart Timer",
        command=lambda: set_manual_count()
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)
    
    def set_manual_count() -> None:
        try:
            new_count = int(reset_val_var.get())
        except ValueError:
        # could pop up a warning here instead
            return

        cfg = JH.load_json()
        cfg["relaunch_timer"] = new_count
    # if you also want to set the RDKB counter too, uncomment:
    # cfg["rdkbcrash_counter"] = new_count

        JH.save_json(cfg)
        update_timestamps()    



    # AWS S3 uploader
    aws_fr = ttk.LabelFrame(main_pg, text="AWS S3 Uploader")
    aws_fr.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        aws_fr,
        text="Run S3 Uploader",
        command=MainController.run_s3_uploader,
    ).pack(fill="x", padx=16, pady=8, ipady=8)

    aws_var = tk.BooleanVar(value=aws.is_enabled())

    def _toggle_aws() -> None:
        aws.set_enabled(aws_var.get())

    ttk.Checkbutton(
        aws_fr,
        text="Auto-run daily at 4 PM",
        variable=aws_var,
        command=_toggle_aws,
    ).pack(anchor="w", padx=16)



    # ── QUTS page ────────────────────────────────────────────────────────
    quts_pg = ttk.Frame(container)
    quts_pg.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_pg
    add_nav("QUTS Tools", "QUTS")

    # Select which tools to manage (side-by-side)
    tools_fr = ttk.LabelFrame(quts_pg, text="Select Tools")
    tools_fr.pack(fill="x", **PADDING) # type: ignore

    quts_var = tk.BooleanVar(value=False)
    pcat_var = tk.BooleanVar(value=True)
    qxdm_var = tk.BooleanVar(value=False)

    # Use a little inner frame so the LabelFrame text stays above
    inner = ttk.Frame(tools_fr)
    inner.pack(padx=10, pady=6, fill="x")

    ttk.Checkbutton(inner, text="QUTS Service", variable=quts_var)\
        .grid(row=0, column=0, padx=8, pady=4, sticky="w")
    ttk.Checkbutton(inner, text="PCAT", variable=pcat_var)\
        .grid(row=0, column=1, padx=8, pady=4, sticky="w")
    ttk.Checkbutton(inner, text="QXDM", variable=qxdm_var)\
        .grid(row=0, column=2, padx=8, pady=4, sticky="w")

    # Start/Stop buttons
    btn_fr = ttk.Frame(quts_pg)
    btn_fr.pack(fill="x", **PADDING) # type: ignore

    def start_selected_tools():
        if quts_var.get() and pcat_var.get() and qxdm_var.get():
            MainController.start_all()
        else:
            if quts_var.get():
                QutsController.start_quts()
            if pcat_var.get():
                MainController.start_Pact_only()
            if qxdm_var.get():
                MainController.start_QXDM_only()

    def stop_selected_tools():
        if quts_var.get():
            QutsController.stop_quts()
        if pcat_var.get():
            MainController.stop_pcat_only()
        if qxdm_var.get():
            MainController.stop_qxdm_only()

    ttk.Button(
        btn_fr,
        text="Start",
        command=start_selected_tools,
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        btn_fr,
        text="Stop",
        command=stop_selected_tools,
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    # ── WIFI CONFIG page ────────────────────────────────────────────────
    wifi_pg = ttk.Frame(container)
    wifi_pg.grid(row=0, column=0, sticky="nsew")
    pages["Wifi"] = wifi_pg
    add_nav("Set/Rename WIFI", "Wifi")

        # ── Toggle Options ────────────────────────────────────────────────────

    toggle_fr = ttk.LabelFrame(wifi_pg, text="Toggle Options")
    toggle_fr.pack(fill="x", **PADDING) # type: ignore

    
    OWRT_CHOICES = ("3 SLO", "2G-5G MLO", "3 MLO")
    RDKB_CHOICES = ("3 SLO", "2G SLO + 5G-6G MLO")

    toggle_var = tk.StringVar(value="OWRT")

    # Two radiobuttons share the same StringVar, so only one can be “on” at a time


    ttk.Radiobutton(
        toggle_fr,
        text="OWRT (ATT)",
        variable=toggle_var,
        value="OWRT",
    ).pack(side="left", expand=True, fill="x", padx=6, pady=6)

    ttk.Radiobutton(
        toggle_fr,
        text="RDKB (TMO)",
        variable=toggle_var,
        value="RDKB",
    ).pack(side="left", expand=True, fill="x", padx=6, pady=6)



    wifi_sel = ttk.LabelFrame(wifi_pg, text="Select Config Type" )
    wifi_sel.pack(fill="x", **PADDING)# type: ignore

    wifi_dd = ttk.Combobox(wifi_sel, state="readonly")
    wifi_dd.pack(padx=20, pady=10)

    def _update_choices(*_):
        choices = OWRT_CHOICES if toggle_var.get() == "OWRT" else RDKB_CHOICES
        wifi_dd.configure(values=choices)
        # Set current value to first choice if not in choices
        cur = wifi_dd.get()
        wifi_dd.set(cur if cur in choices and cur else choices[0])

    toggle_var.trace_add("write", _update_choices)
    _update_choices() 


   

    ttk.Button(
        wifi_sel,
        text="Set config",
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Config_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    test_sel = ttk.LabelFrame(wifi_pg, text="This is to rename SSIDs before Speedtest")
    test_sel.pack(fill="x", **PADDING )# type: ignore  


    ttk.Button(
        test_sel,
        text="Set Test SSID",
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Test_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        test_sel,
        text="Set Default SSID",
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Default_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    # ── TESTING page ─────────────────────────────────────────────────────
    test_pg = ttk.Frame(container)
    test_pg.grid(row=0, column=0, sticky="nsew")
    pages["Testing"] = test_pg
    add_nav("SpeedTest", "Testing")

    
    SpeedTest = ttk.LabelFrame(test_pg, text="Start speed test")
    SpeedTest.pack(fill="x", **PADDING)# type: ignore  

    ttk.Label(
    SpeedTest,
    text="Enter the number of iterations:",
    anchor="w"
    ).pack(side="left", fill="x", expand=True,padx=(20, 0))

    iterationCount = tk.StringVar(value="1")
    ttk.Entry(
        SpeedTest,
        textvariable=iterationCount,
        width=4
    ).pack(side="left", padx=(8, 0))

    def get_iteration_count():
        try:
            return int(iterationCount.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for iteration count.")
            return None

    ttk.Button(
        SpeedTest,
        text="Start Speed Test",
        command=lambda:MainController.SpeedTest(get_iteration_count(), load_data_table),
    ).pack(fill="x", **PADDING)# type: ignore

    # ── Speed Test Data table ───────────────────────────────────────────
    
    SpeedTest_table = ttk.LabelFrame(test_pg, text="Speed Test Data")
    SpeedTest_table.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Make the LabelFrame act like a grid container
    SpeedTest_table.rowconfigure(0, weight=0)   # table row grows
    SpeedTest_table.columnconfigure(0, weight=1)

    COLUMNS = ("DL", "UL", "Band Info","Location","TimeStamp","adbid")  # include Location

    tree = ttk.Treeview(
        SpeedTest_table,
        columns=COLUMNS,
        show="headings",
        height=4,  # visible rows
    )

    # Headings
    tree.heading("TimeStamp", text="TimeStamp")
    tree.heading("DL",        text="DL (Mbps)")
    tree.heading("UL",        text="UL (Mbps)")
    tree.heading("adbid",     text="ADB ID")
    tree.heading("Location",    text="Location")
    tree.heading("Band Info",    text="Band Info")

    # Column widths; set some stretch=False so total width exceeds widget -> enables X scroll
    tree.column("TimeStamp", width=170, anchor="center", stretch=False)
    tree.column("DL",        width=120, anchor="center", stretch=False)
    tree.column("UL",        width=120, anchor="center", stretch=False)
    tree.column("adbid",     width=140, anchor="center", stretch=False)
    tree.column("Location",    width=180, anchor="center", stretch=True)
    tree.column("Band Info",    width=180, anchor="center", stretch=True)

    # Scrollbars
    vscroll = ttk.Scrollbar(SpeedTest_table, orient="vertical",   command=tree.yview)
    hsb     = ttk.Scrollbar(SpeedTest_table, orient="horizontal", command=tree.xview)

    # Wire scrollbars to the tree
    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hsb.set)

    # Layout (tree row 0, hsb row 1, button row 2; vscroll spans rows 0-1)
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns", rowspan=2)
    hsb.grid(row=1, column=0, sticky="ew")

    # Refresh button BELOW the hscrollbar (row 2)
    ttk.Button(
        SpeedTest_table,
        text="Refresh Data",
        command=lambda: (MainController.get_all_speedtest_results(), load_data_table()),
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 0))


    def load_data_table():
        """Read JSON list and (re)populate the table."""
        data = JH.load_json().get("SpeedTestData", []) 
        tree.delete(*tree.get_children())  # <-- adjust key to your JSON
    # Clear
        for row in data:
            tree.insert(
            "",
            "end",
            values=(
                row.get("DL", ""),
                row.get("UL", ""),
                row.get("BAND", ""),
                row.get("LOCATION", ""),
                row.get("TIMESTAMP", ""),
                row.get("ADBID", "")
            )
        )
    # initial fill
    load_data_table()
    #start_json_file_watcher(load_data_table, JH.get_json_path())
    

    # ── QSTAF update page ─────────────────────────────────────────────────────
    QSTAF_pg = ttk.Frame(container)
    QSTAF_pg.grid(row=0, column=0, sticky="nsew")
    pages["QSTAF"] = QSTAF_pg
    add_nav("Install QSTAF", "QSTAF")
    # avaible_ver=gr.get_all_tags()

    # ver_sel = ttk.LabelFrame(QSTAF_pg, text="select the version and download")
    # ver_sel.pack(fill="x", **PADDING)# type: ignore  

    # select_ver = ttk.Combobox(ver_sel, values=avaible_ver, state="readonly")
    # select_ver.current(0)
    # select_ver.pack(padx=20, pady=10)
    # selected_zip = tk.StringVar(value="No file selected")

    # ttk.Button(
        # ver_sel,
        # text="Download",
        # command=lambda:gr.download_asset_by_tag(avaible_ver[select_ver.current()], "."),
    # ).pack(fill="x", **PADDING)# type: ignore


    Qstaf_install = ttk.LabelFrame(QSTAF_pg, text="Select and install QSTAF")
    Qstaf_install.pack(fill="x", **PADDING)  # type: ignore

# Path label (with hint style)
    selected_zip = tk.StringVar(value='No file selected — click "Choose archive…"')
    style.configure("Hint.TLabel", foreground="#6b7280")

    zip_label = ttk.Label(
        Qstaf_install,
        textvariable=selected_zip,
        anchor="w",
        style="Hint.TLabel",
    )
    zip_label.pack(fill="x", **PADDING)  # type: ignore

# --- Progress  Logs ----------------------------------------------------------
    progress_var = tk.IntVar(value=0)
    progress_bar = ttk.Progressbar(Qstaf_install, maximum=100, variable=progress_var, mode="determinate")
    progress_bar.pack(fill="x", padx=16, pady=(0, 8))

    log_box = ScrolledText(Qstaf_install, height=10, wrap="word", state="disabled")
    log_box.pack(fill="both", expand=False, padx=16, pady=(0, 12))

    def _log(msg: str):
            ts = dt.datetime.now().strftime("%H:%M:%S")  # type: ignore
            log_box.configure(state="normal")
            log_box.insert("end", f"[{ts}] {msg}\n")
            log_box.see("end")
            log_box.configure(state="disabled")

    def _run_install(path: str) -> None:
        """Run QSTAF installer asynchronously and update GUI elements."""
        # Reset UI and start indeterminate progress
        progress_var.set(0)
        progress_bar.configure(mode="indeterminate")
        progress_bar.start(10)
        _log(f"Starting install for: {path}")

        top = QSTAF_pg.winfo_toplevel()

        def ui_status(msg: str):
            # Schedule status log update on the Tk main thread
            top.after(0, lambda: _log(msg))

        def ui_progress(pct: int):
            """Update determinate progress bar from 0‑100."""
            def _upd():
                # If we are still in indeterminate mode switch first
                if progress_bar['mode'] == 'indeterminate':
                    progress_bar.stop()
                    progress_bar.configure(mode='determinate')
                progress_var.set(max(0, min(100, int(pct))))
            top.after(0, _upd)

        def worker():
            ok = False
            msg = ""
            try:
                ok, msg = QSTAFInstaller.install_qstaf_from_zip(
                    path,
                    on_status=ui_status,
                    on_progress=ui_progress,
                    keep_temp=False,  # set True if you want to inspect temp folder
                )
            except Exception as e:
                ok, msg = False, str(e)
            finally:
                # Always run this to tidy the UI (no pop‑ups)
                def done():
                    progress_bar.stop()
                    progress_bar.configure(mode='determinate')
                    progress_var.set(100 if ok else 0)
                    if ok:
                        _log("Completed." if not msg else f"Completed: {msg}")
                    else:
                        _log(f"Failed: {msg or 'Unknown error.'}")
                top.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _pick_zip() -> None:
        filePath = filedialog.askopenfilename(
            title="Select QSTAF archive",
            filetypes=[
            ("Archives", "*.zip *.7z"),
            ("ZIP archives", "*.zip"),
            ("7z archives", "*.7z"),
            ("All files", "*.*"),
        ],
    )
        if not filePath:
            return
        if not filePath.lower().endswith((".zip", ".7z")):
            messagebox.showwarning("Unsupported file", "Please choose a .zip or .7z file.")
            return

        selected_zip.set(filePath)
        zip_label.configure(style="TLabel")  # switch from hint to normal
        _run_install(filePath)

    btn_row = ttk.Frame(Qstaf_install)
    btn_row.pack(fill="x", padx=16, pady=(0, 8))

    ttk.Button(btn_row, text="Choose archive…", command=_pick_zip, width=18)\
    .pack(side="left")

    def _clear_logs():
        log_box.configure(state="normal")
        log_box.delete("1.0", "end")
        log_box.configure(state="disabled")

    ttk.Button(btn_row, text="Clear logs", command=_clear_logs, width=12)\
    .pack(side="right")

    """
    # ── DATA MONITOR page ───────────────────────────────────────────────
    data_pg = ttk.Frame(container)
    data_pg.grid(row=0, column=0, sticky="nsew")
    pages["Data"] = data_pg
    add_nav("CPE Data Monitor", "Data")
    
    # scrollable canvas ---------------------------------------------------
    canvas   = tk.Canvas(data_pg, borderwidth=0, highlightthickness=0)
    scroll   = ttk.Scrollbar(data_pg, orient="vertical", command=canvas.yview)
    list_fr  = ttk.Frame(canvas)

    def _on_mousewheel(evt: tk.Event) -> None:
        direction = -1 if (evt.delta or evt.num == 4) > 0 else 1  # cross-platform
        canvas.yview_scroll(direction, "units")

    def _bind(_: tk.Event) -> None:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind(_: tk.Event) -> None:
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    list_fr.bind("<Enter>", _bind)
    list_fr.bind("<Leave>", _unbind)
    list_fr.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=list_fr, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # populate dynamically --------------------------------------------------

    # draw the first plot immediately
    rdp.draw_all_plots(list_fr)
    # then kick off the background refresher
    rdp.periodic_refresh(list_fr)
    """
    DataMonitorPage.create_data_monitor_page(container, pages, add_nav)


    # ── Launch ────────────────────────────────────────────────────────────────
    show("Main")
    root.mainloop()


# ───────────────────────────────────────────────────────────────────────────

