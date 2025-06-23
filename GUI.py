"""
QSTAF System Manager – Tkinter front-end
Business logic lives in:
    • main_controller.py
    • Wifi_controller.py
    • Quts_controller.py
    • aws_scheduler.py
    • data_monitor_controller.py
"""

from __future__ import annotations          # for | typing in <3.10

# ── stdlib ──────────────────────────────────────────────────────────────────
import datetime as dt
import tkinter as tk
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# ── 3rd-party ──────────────────────────────────────────────────────────────
import sv_ttk

# ── local app modules ──────────────────────────────────────────────────────
import main_controller
import Wifi_controller
import Quts_controller
import aws_scheduler as aws
import data_monitor_controller as dmc
import plot_dynamic_render as rdp
import crash_cout_controller_v2 as cc
# ───────────────────────────────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────────────────────────────
PADDING:dict[str, int] = {"padx": 12, "pady": 8}



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
    '''
    header_frame.columnconfigure(0, weight=1)   # left column can grow
    header_frame.columnconfigure(1, weight=0)   # button – fixed
    header_frame.columnconfigure(2, weight=1)  
    '''
    for col in range(7):
       header_frame.columnconfigure(col, weight=0)
    header_frame.columnconfigure(2, weight=1)   # left side expands
    #header_frame.columnconfigure(6, weight=1) # right side expands

    def refresh_meta_mpss():
        meta = "UNKNOWN"
        mpss = "UNKNOWN"
        meta, mpss = main_controller.get_meta_mpss()
        meta_var.set(f"Meta : {meta}")
        mpss_var.set(f"MPSS : {mpss}")

    meta_var = tk.StringVar(value="Meta : ")
    mpss_var = tk.StringVar(value="MPSS : ")

    ttk.Label(header_frame, textvariable=meta_var, anchor="w") \
    .grid(row=0, column=0, sticky="w", padx=15)
    ttk.Label(header_frame, textvariable=mpss_var, anchor="w") \
    .grid(row=1, column=0, sticky="w", padx=15)

    #refresh_meta_mpss()
    ttk.Button(
        header_frame, text="Get info",
        command=refresh_meta_mpss, width=12
    ).grid(row=2, column=0, sticky="w", padx=10,pady= 5)
 
    n_dir_var  = tk.StringVar(value="—")
    n_ovn_var  = tk.StringVar(value="—")
    r_dir_var  = tk.StringVar(value="—")
    r_ovn_var  = tk.StringVar(value="—")
   
    # labels (two rows keeps width sensible)
    ttk.Label(header_frame, text="Crash:- DIR:", anchor="e") \
    .grid(row=0, column=3, sticky="e", padx=(10,5))
    ttk.Label(header_frame, textvariable=n_dir_var, anchor="w") \
    .grid(row=0, column=4, sticky="w")
    ttk.Label(header_frame, text="OVN:", anchor="e") \
    .grid(row=0, column=5, sticky="e", padx=(10,5))
    ttk.Label(header_frame, textvariable=n_ovn_var, anchor="w") \
    .grid(row=0, column=6, sticky="w", padx=10)

# ── RDKB counters in cols 3–6 (row 1) ───────────────────────────────────
    ttk.Label(header_frame, text="RDKB:- DIR:", anchor="e") \
    .grid(row=1, column=3, sticky="e", padx=(10,5))
    ttk.Label(header_frame, textvariable=r_dir_var, anchor="w") \
    .grid(row=1, column=4, sticky="w")
    ttk.Label(header_frame, text="OVN:", anchor="e") \
    .grid(row=1, column=5, sticky="e", padx=(10,5))
    ttk.Label(header_frame, textvariable=r_ovn_var, anchor="w") \
    .grid(row=1, column=6, sticky="w", padx=10)
    
    ttk.Button(
    header_frame,text="Reset Counter",command=cc.rest_counter,width=12)\
    .grid(row=2,column=3,columnspan=4,sticky="e",padx=20,pady=5)

    # ­—----- start the JSON watcher ­-----—
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
        cfg = cc.load_config()
        n_dir_var.set(str(cfg.get("crash_day_counter",   0)))
        n_ovn_var.set(str(cfg.get("crash_night_counter", 0)))
        r_dir_var.set(str(cfg.get("rdkbcrash_day_counter",   0)))
        r_ovn_var.set(str(cfg.get("rdkbcrash_night_counter", 0)))

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

    quts_stat_var = tk.StringVar(value="QUTS: Checking…")
    sched_stat_var = tk.StringVar(
        value="Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF"
    )

    quts_label = tk.Label(
    footer,
    textvariable=quts_stat_var,
    font=("TkDefaultFont", 10, "bold"))
    quts_label.pack(side="left")

    ttk.Label(footer, textvariable=sched_stat_var, padding=(12, 0)).pack(side="left")

    clock_lbl = ttk.Label(footer)
    clock_lbl.pack(side="right")

    def _tick() -> None:
        clock_lbl.config(text=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        root.after(1_000, _tick)

    def _update_quts() -> None:
        running = Quts_controller.is_service_running("QUTS")
        quts_stat_var.set(f"QUTS: {'Running' if running else 'Stopped'}")
        white_accent = "#FFFFFF"
        red_accent  = "#E95959"

        quts_label.config(
        fg=white_accent if running else red_accent)
        root.after(3_000, _update_quts)

    _tick()
    _update_quts()

    # ── MAIN PAGE ─────────────────────────────────────────────────────────
    main_pg = ttk.Frame(container)
    main_pg.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_pg
    add_nav("Main", "Main")

    # Framework control
    ctrl = ttk.LabelFrame(main_pg, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)# type: ignore
 # type: ignore

    row = ttk.Frame(ctrl)
    row.pack(fill="x", **PADDING)# type: ignore
# type: ignore


    ttk.Button(
        row,
        text="Control Framework",
        command=main_controller.start_control,
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row,
        text="Traffic Framework",
        command=main_controller.start_traffic,
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    run_btn = tk.Button(
    ctrl,
    text="Run both Frameworks (3 s delay)",
    command=main_controller.run_both_with_delay,
    bg="#2A2A2A",            # normal background
    activebackground="#006EA5",
    fg="white",              # text color
    activeforeground="white",
    bd=0,                    # no border
    relief="flat")
    run_btn.pack(fill="x", padx=16, pady=(12, 6), ipady=10)

    stop_btn = tk.Button(
    ctrl,
    text="Stop All Frameworks",
    command=main_controller.stop_all,
    bg="#FA5252",
    activebackground="#910000",
    fg="white",
    activeforeground="white",
    bd=0,
    relief="flat",
)
    stop_btn.pack(fill="x", padx=16, pady=(6, 12), ipady=10)

    # AWS S3 uploader
    aws_fr = ttk.LabelFrame(main_pg, text="AWS S3 Uploader")
    aws_fr.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        aws_fr,
        text="Run S3 Uploader",
        command=main_controller.run_s3_uploader,
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

    # ── QUTS page ────────────────────────────────────────────────────────
    quts_pg = ttk.Frame(container)
    quts_pg.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_pg
    add_nav("QUTS Tools", "QUTS")

    combo = ttk.LabelFrame(quts_pg, text="Restart QUTS + PCAT + QXDM")
    combo.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        combo,
        text="Restart QUTS + PCAT + QXDM",
        command=main_controller.restart_quts_pcat_qxdm,
        width=30,
    ).pack(fill="x", **PADDING)# type: ignore


    single = ttk.LabelFrame(quts_pg, text="Restart QUTS only")
    single.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        single,
        text="Restart QUTS only",
        command=Quts_controller.restart_quts,
        width=30,
    ).pack(fill="x", **PADDING)# type: ignore


    # PCAT + QXDM launcher
    pq_fr = ttk.LabelFrame(quts_pg, text="PCAT_QXDM")
    pq_fr.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        pq_fr,
        text="Start PCAT QXDM",
        command=main_controller.start_Pact_QXDM,
    ).pack(fill="x", padx=16, pady=8, ipady=8)


    stop_all = ttk.LabelFrame(quts_pg, text="Stop all Tools")
    stop_all.pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        stop_all,
        text="Stop all Tools",
        command=main_controller.stop_all_tools_Framework,
    ).pack(fill="x", **PADDING)# type: ignore


    # ── WIFI CONFIG page ────────────────────────────────────────────────
    wifi_pg = ttk.Frame(container)
    wifi_pg.grid(row=0, column=0, sticky="nsew")
    pages["Wifi"] = wifi_pg
    add_nav("Set Wifi", "Wifi")

    CHOICES = ("3 SLO", "2G SLO + 5G-6G MLO")
    wifi_sel = ttk.LabelFrame(wifi_pg, text="Select config type")
    wifi_sel.pack(fill="x", **PADDING)# type: ignore


    wifi_dd = ttk.Combobox(wifi_sel, values=CHOICES, state="readonly")
    wifi_dd.current(0)
    wifi_dd.pack(padx=20, pady=10)

    ttk.Button(
        wifi_sel,
        text="Set config",
        command=lambda: main_controller.set_wifi_config(wifi_dd.current()),
    ).pack(fill="x", **PADDING)# type: ignore


    # ── TESTING page ─────────────────────────────────────────────────────
    test_pg = ttk.Frame(container)
    test_pg.grid(row=0, column=0, sticky="nsew")
    pages["Testing"] = test_pg
    add_nav("SpeedTest", "Testing")

    test_sel = ttk.LabelFrame(test_pg, text="Select config type")
    test_sel.pack(fill="x", **PADDING)# type: ignore


    test_dd = ttk.Combobox(test_sel, values=CHOICES, state="readonly")
    test_dd.current(0)
    test_dd.pack(padx=20, pady=10)

    ttk.Button(
        test_sel,
        text="Set Test SSID",
        command=lambda: Wifi_controller.update_cpe_wifi_config(test_dd.current(), "_"),
    ).pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        test_sel,
        text="Set Default SSID",
        command=lambda: Wifi_controller.update_cpe_wifi_config(test_dd.current(), ""),
    ).pack(fill="x", **PADDING)# type: ignore


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
    main_controller.run_app()
