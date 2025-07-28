"""
QSTAF System Manager – Tkinter front-end
Business logic lives in:
    • MainController.py
    • WifiController.py
    • QutsController.py
    • AwsScheduler.py
    • DataMonitorController.py
"""

from __future__ import annotations          # for | typing in <3.10

# ── stdlib ──────────────────────────────────────────────────────────────────
from functools import partial
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

# ── 3rd-party ──────────────────────────────────────────────────────────────
import sv_ttk

# ── local app modules ──────────────────────────────────────────────────────
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
import RealTimeDataController

# ───────────────────────────────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────────────────────────────
PADDING:dict[str, int] = {"padx": 12, "pady": 8}
white_accent = "#FFFFFF"
red_accent  = "#E95959"



def launch_gui() -> None:
    """Construct and run the UI."""

    # ── Window ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("CPE Test Manager")
    root.geometry("1024x768")
    root.resizable(True, True)
    sv_ttk.set_theme("dark")

    # ── Styles ──────────────────────────────────────────────────────────
    style = ttk.Style(root)
    style.configure("Sidebar.TFrame", background="#2a2a2e")


    # ── header (mini) ───────────────────────────────────────────────────────
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)

    for col in range(7):
       header_frame.columnconfigure(col, weight=0)
    header_frame.columnconfigure(2, weight=1)   # left side expands
    
    RFband_info= tk.StringVar(value="Band Combo : ")
    SNR_values = tk.StringVar(value= "Channel Conditions : ")

    
    def display_real_time_rf_data():
        time.sleep(20)
        while True:
            rf_band, rsrp = RealTimeDataController.get_current_rfband_rsrp()
            root.after(0, lambda: RFband_info.set(f"Band Combo: {rf_band}"))
            root.after(0, lambda: SNR_values.set(f"Channel Conditions: {rsrp}"))
            time.sleep(1)

    t3 = threading.Thread(
    target=display_real_time_rf_data,
    daemon=True)
    t3.start()

    ttk.Label(header_frame, textvariable=RFband_info, anchor="w") \
    .grid(row=0, column=0, sticky="w", padx=15)
    ttk.Label(header_frame, textvariable=SNR_values, anchor="w") \
    .grid(row=1, column=0, sticky="w", padx=15)

 
    crash_var  = tk.StringVar(value="—")
    RDKB_var  = tk.StringVar(value="—")
   
    # labels (two rows keeps width sensible)
    crash_text_lbl =ttk.Label(header_frame, text="Device Crashes:", anchor="e") 
    crash_text_lbl.grid(row=0, column=3, sticky="e", padx=(10,5))
    crash_lbl = ttk.Label(header_frame, textvariable=crash_var, anchor="w")
    crash_lbl.grid(row=0, column=4, sticky="w")

    RDKB_text_lbl= ttk.Label(header_frame, text="RDKB Crashes:", anchor="e") 
    RDKB_text_lbl.grid(row=1, column=3, sticky="e", padx=(10,5))
    RDKB_lbl = ttk.Label(header_frame, textvariable=RDKB_var, anchor="w")
    RDKB_lbl.grid(row=1, column=4, sticky="w")
    
    ttk.Button(
    header_frame,text="Reset Counter",command=cc.rest_counter,width=12)\
    .grid(row=2,column=3,columnspan=4,sticky="e",padx=20,pady=5)

    # ­—----- start the app_JSON watcher ­-----—
    class ConfigHandler(FileSystemEventHandler):
        def __init__(self, callback):
            self.callback = callback

        def on_modified(self, event):
            # only react if *that* JSON file changed
            if event.src_path == str(cc.CONFIG_PATH):
                # schedule the UI update on the Tk main thread
                root.after(0, self.callback)

    def start_config_watcher(callback):
        obs = Observer()
        handler = ConfigHandler(callback)
        obs.schedule(handler, str(cc.CONFIG_PATH.parent), recursive=False)
        obs.start()
        # keep it running in background
        threading.Thread(target=obs.join, daemon=True).start()
   
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
    start_config_watcher(load_counters)


    # ── Grid weights ─────────────────────────────────────────────────────
    root.columnconfigure(1, weight=1)  # column 1 = main content
    root.rowconfigure(1, weight=1)     # row 1   = sidebar + pages

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
    
    footer.columnconfigure(0, weight=0)   # QUTS
    footer.columnconfigure(1, weight=0)   # Scheduler
    footer.columnconfigure(2, weight=1)   # Internet (will expand & center)
    footer.columnconfigure(3, weight=0) 

    quts_stat_var = tk.StringVar(value="QUTS: Checking…")
    sched_stat_var = tk.StringVar(
        value="Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF"
    )

    quts_label = tk.Label(
    footer,
    textvariable=quts_stat_var,
    font=("TkDefaultFont", 10, "bold"))
    quts_label.grid(row=0, column=0, sticky="w")

    sched_label = ttk.Label(footer, textvariable=sched_stat_var)
    sched_label.grid(row=0, column=1, sticky="w", padx=(12,0))

    def update_internet_status():
        status = dmc.get_internet_status()
        if status == 1:
            center_var.set("Internet status: GOOD")
            center_lbl.configure(foreground="green", font=("Segoe UI", 14) )

        elif status == 0:
            center_var.set("Internet status: DOWN")
            center_lbl.configure(foreground="red",font=("Segoe UI", 14))

        else:
            center_var.set("Internet status")
            center_lbl.configure(foreground="white",font=("Segoe UI", 12))
            
        root.after(5000, update_internet_status)

    center_var = tk.StringVar(value="Internet status")
    center_lbl = tk.Label(
    footer,
    textvariable=center_var,
    font=("Segoe UI", 12),
    fg="white",           # default color
    anchor="center",)
    center_lbl.grid(row=0, column=2, sticky="ew")

    root.after(0, update_internet_status)

    version_lbl = ttk.Label(
    footer,
    text=f"QSTAF VERSION: {MainController.get_qstaf_version()}")
    version_lbl.grid(row=0, column=3, sticky="e", padx=10)

    def _update_quts() -> None:
        running = QutsController.is_service_running("QUTS")
        quts_stat_var.set(f"QUTS: {'Running' if running else 'Stopped'}")

        quts_label.config(
            fg=white_accent if running else red_accent)
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
    start_config_watcher(update_timestamps)


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
        sched_stat_var.set("Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")

    ttk.Checkbutton(
        aws_fr,
        text="Auto-run daily at 4 PM",
        variable=aws_var,
        command=_toggle_aws,
    ).pack(anchor="w", padx=16)




    # get devices build info
    Build_info= ttk.LabelFrame(main_pg, text="GET build info")
    Build_info.pack(fill="x",**PADDING) #type: ignore

    def refresh_meta_mpss():
        meta = "UNKNOWN"
        mpss = "UNKNOWN"
        meta, mpss = MainController.get_meta_mpss()
        meta_var.set(f"Meta : {meta}")
        mpss_var.set(f"MPSS : {mpss}")

    meta_var = tk.StringVar(value="Meta : ")
    mpss_var = tk.StringVar(value="MPSS : ")

    ttk.Label(Build_info, textvariable=meta_var, anchor="w") \
    .grid(row=0, column=0, sticky="w", padx=15)
    ttk.Label(Build_info, textvariable=mpss_var, anchor="w") \
    .grid(row=1, column=0, sticky="w", padx=15)

    refresh_meta_mpss()
    ttk.Button(
        Build_info, text="Get Build info",
        command=refresh_meta_mpss, width=12
    ).grid(row=2, column=0, sticky="w", padx=10,pady= 5)



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
    add_nav("Set Wifi (RDKB)", "Wifi")

    CHOICES = ("3 SLO", "2G SLO + 5G-6G MLO")
    wifi_sel = ttk.LabelFrame(wifi_pg, text="Select config type for RDKB TMO")
    wifi_sel.pack(fill="x", **PADDING)# type: ignore


    wifi_dd = ttk.Combobox(wifi_sel, values=CHOICES, state="readonly")
    wifi_dd.current(0)
    wifi_dd.pack(padx=20, pady=10)

    ttk.Button(
        wifi_sel,
        text="Set config",
        command=lambda: MainController.set_wifi_config(wifi_dd.current()),
    ).pack(fill="x", **PADDING)# type: ignore


    # ── TESTING page ─────────────────────────────────────────────────────
    test_pg = ttk.Frame(container)
    test_pg.grid(row=0, column=0, sticky="nsew")
    pages["Testing"] = test_pg
    add_nav("Rename SSIDs", "Testing")

    test_sel = ttk.LabelFrame(test_pg, text="This is to rename SSIDs before Speedtest for RKDB")
    test_sel.pack(fill="x", **PADDING)# type: ignore  


    test_dd = ttk.Combobox(test_sel, values=CHOICES, state="readonly")
    test_dd.current(0)
    test_dd.pack(padx=20, pady=10)

    ttk.Button(
        test_sel,
        text="Set Test SSID",
        command=lambda: WifiController.update_cpe_wifi_config(test_dd.current(), "_"),
    ).pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        test_sel,
        text="Set Default SSID",
        command=lambda: WifiController.update_cpe_wifi_config(test_dd.current(), ""),
    ).pack(fill="x", **PADDING)# type: ignore

    SpeedTest = ttk.LabelFrame(test_pg, text="Start speed test")
    SpeedTest.pack(fill="x", **PADDING)# type: ignore  

    ttk.Button(
        SpeedTest,
        text="Start Speed Test",
        command=MainController.SpeedTest,
    ).pack(fill="x", **PADDING)# type: ignore

    # ── Speed Test Data table ───────────────────────────────────────────

    SpeedTest_table = ttk.LabelFrame(test_pg, text="Speed Test Data")
    SpeedTest_table.pack(fill="both", expand=True, **PADDING) # type: ignore

    COLUMNS = ("TimeStamp", "Dl", "UL", "adbid")

    tree = ttk.Treeview(
    SpeedTest_table,
    columns=COLUMNS,
    show="headings",
    height=4   # ≤4 rows visible; more will scroll
    )

# Headings + column options
    tree.heading("TimeStamp",    text="TimeStamp")
    tree.heading("Dl", text="DL")
    tree.heading("UL", text="UL")
    tree.heading("adbid",     text="ADB ID")

    tree.column("TimeStamp", width=170, anchor="w")
    tree.column("Dl",        width=80,  anchor="e")
    tree.column("UL",        width=80,  anchor="e")
    tree.column("adbid",     width=120, anchor="w")

# Grid the tree + scrollbar
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll = ttk.Scrollbar(SpeedTest_table, orient="vertical", command=tree.yview)
    vscroll.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=vscroll.set)

    
    SpeedTest_table.columnconfigure(0, weight=1)

    def load_data_table():
        """Read JSON list and (re)populate the table."""
        data = JH.load_json().get("SpeedTestData", [])   # <-- adjust key to your JSON
    # Clear
        for row in data:
            tree.insert(
            "",
            "end",
            values=(
                row.get("TimeStamp", ""),
                row.get("Dl", ""),
                row.get("UL", ""),
                row.get("adbid", "")
            )
        )
    # initial fill
    load_data_table()

    # ── QSTAF update page ─────────────────────────────────────────────────────
    QSTAF_pg = ttk.Frame(container)
    QSTAF_pg.grid(row=0, column=0, sticky="nsew")
    pages["QSTAF"] = QSTAF_pg
    add_nav("Install QSTAF", "QSTAF")
    avaible_ver=gr.get_all_tags()

    ver_sel = ttk.LabelFrame(QSTAF_pg, text="select the version and download")
    ver_sel.pack(fill="x", **PADDING)# type: ignore  

    select_ver = ttk.Combobox(ver_sel, values=avaible_ver, state="readonly")
    select_ver.current(0)
    select_ver.pack(padx=20, pady=10)
    selected_zip = tk.StringVar(value="No file selected")

    ttk.Button(
        ver_sel,
        text="Download",
        command=lambda:gr.download_asset_by_tag(avaible_ver[select_ver.current()], "."),
    ).pack(fill="x", **PADDING)# type: ignore


    Qstaf_install = ttk.LabelFrame(QSTAF_pg, text="select the version and download")
    Qstaf_install.pack(fill="x", **PADDING)# type: ignore

    def _pick_zip() -> None:
        filePath = filedialog.askopenfilename(
        title="Select QSTAF .zip",
        filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")]
        )
        if filePath:
            selected_zip.set(filePath)
            QSTAFInstaller.isntallQSTAF(filePath)
            

    ttk.Label(
        Qstaf_install,
        textvariable=selected_zip,
        anchor="w",
        style="Hint.TLabel"  # type: ignore
    ).pack(fill="x", padx=16)


    ttk.Button(
        Qstaf_install,
        text="Choose ZIP…",
        command=_pick_zip,
    ).pack(fill="x", **PADDING)  # type: ignore

    
   



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



    # ── Launch ────────────────────────────────────────────────────────────────
    show("Main")
    root.mainloop()


# ───────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MainController.run_app()
