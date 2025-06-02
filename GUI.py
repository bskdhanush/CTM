import tkinter as tk
from tkinter import ttk
import sv_ttk
import datetime
#Modules import 
import Wifi_controller
import aws_scheduler as aws
import main_controller
import Quts_controller


def launch_gui() -> None:
    """Construct and run the UI.  All business logic lives in main_controller."""
    # ── Admin check ───────────────────────────────────────────────────────────
    main_controller.ensure_admin()

    # ── Window setup ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("QSTAF System Manager")
    root.geometry("600x600")
    root.resizable(False, False)
    sv_ttk.set_theme("dark")

    # ── Styles ────────────────────────────────────────────────────────────────
    style = ttk.Style(root)
    style.configure("Sidebar.TFrame", background="#2a2a2e")

    style.configure("RunBoth.TButton",
                    background="#3A7EF5", foreground="white",
                    focuscolor="#3A7EF5", borderwidth=0)
    style.map("RunBoth.TButton",
              background=[("active", "#4A8FF6"), ("pressed", "#2A6EE5")])

    style.configure("StopAll.TButton",
                    background="#FA5252", foreground="white",
                    focuscolor="#FA5252", borderwidth=0)
    style.map("StopAll.TButton",
              background=[("active", "#FF6B6B"), ("pressed", "#EA4242")])

    PADDING = {"padx": 12, "pady": 8}

    # ── Header (NEW) ──────────────────────────────────────────────────────────
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
    ttk.Label(
    header_frame,
    text='Band Info',
    font=("Segoe UI", 12, "bold")).pack(side="left", anchor="w", padx=12, pady=(6, 4))
    
    # right‑hand column = its own frame
    right_col = ttk.Frame(header_frame)
    right_col.pack(side="right", padx=15, pady=(6, 4))   # << packed as a single block
    
    ttk.Label(right_col, text="Crash Count :‑").pack(anchor="e",padx=15)      # top
    ttk.Label(right_col, text="RDKB :‑").pack(anchor="e", pady=(2,0), padx=15)  # bottom
    
    

    # ── Grid weights ──────────────────────────────────────────────────────────
    root.columnconfigure(1, weight=1)  # column 1 = main content
    root.rowconfigure(1, weight=1)     # row 1   = sidebar + pages

    # ── Sidebar & page container ──────────────────────────────────────────────
    sidebar   = ttk.Frame(root, style="Sidebar.TFrame")
    container = ttk.Frame(root)
    sidebar.grid(row=1, column=0, sticky="ns")
    container.grid(row=1, column=1, sticky="nsew")

    pages: dict[str, ttk.Frame] = {}
    nav_buttons: dict[str, ttk.Button] = {}

    def show(page_name: str) -> None:
        """Raise the given page and highlight its nav button."""
        pages[page_name].tkraise()
       # header_var.set(page_name)                    # update header text
        for name, btn in nav_buttons.items():
            btn.configure(style="Accent.TButton" if name == page_name else "TButton")

    def _add_nav(text: str, key: str) -> None:
        btn = ttk.Button(sidebar, text=text, width=15,
                         command=lambda k=key: show(k))
        btn.pack(fill="x", pady=6, padx=6)
        nav_buttons[key] = btn

    # ── Status bar / footer ───────────────────────────────────────────────────
    quts_status_var     = tk.StringVar(value="QUTS: Checking…")
    scheduler_status_var = tk.StringVar(
        value="Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")

    footer = ttk.Frame(root)
    footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 8))

    ttk.Label(footer, textvariable=quts_status_var).pack(side="left")
    ttk.Label(footer, textvariable=scheduler_status_var, padding=(12, 0)).pack(side="left")

    clock_lbl = ttk.Label(footer)
    clock_lbl.pack(side="right")

    # live clock
    def _tick() -> None:
        clock_lbl.config(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        root.after(1000, _tick)
    _tick()

    # real‑time QUTS service monitor
    def _update_quts_status() -> None:
        running = Quts_controller.is_service_running("QUTS")
        quts_status_var.set(f"QUTS: {'Running' if running else 'Stopped'}")
        root.after(3000, _update_quts_status)
    _update_quts_status()

    # ── MAIN PAGE ─────────────────────────────────────────────────────────────
    main_page = ttk.Frame(container)
    main_page.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_page
    _add_nav("Main", "Main")

    # Framework Control section
    ctrl = ttk.LabelFrame(main_page, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)

    row = ttk.Frame(ctrl)
    row.pack(fill="x", **PADDING)

    ttk.Button(row, text="Control Framework",
               command=main_controller.start_control,
               width=18).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(row, text="Traffic Framework",
               command=main_controller.start_traffic,
               width=18).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    ttk.Button(ctrl, text="Run both Frameworks (3 s delay)",
               command=main_controller.run_both_with_delay,
               style="RunBoth.TButton").pack(fill="x", padx=16, pady=(12, 6), ipady=10)

    ttk.Button(ctrl, text="Stop All Frameworks",
               command=main_controller.stop_all,
               style="StopAll.TButton").pack(fill="x", padx=16, pady=(6, 12), ipady=10)

    # AWS S3 Uploader
    aws_frame = ttk.LabelFrame(main_page, text="AWS S3 Uploader")
    aws_frame.pack(fill="x", **PADDING)

    ttk.Button(aws_frame, text="Run S3 Uploader",
               command=main_controller.run_s3_uploader).pack(fill="x", padx=16, pady=8, ipady=8)

    aws_var = tk.BooleanVar(value=aws.is_enabled())

    def on_aws_toggle() -> None:
        aws.set_enabled(aws_var.get())
        scheduler_status_var.set("Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")

    ttk.Checkbutton(aws_frame, text="Auto‑run daily at 4 PM",
                    variable=aws_var, command=on_aws_toggle).pack(anchor="w", padx=16)

    # PCAT + QXDM launcher
    pq_frame = ttk.LabelFrame(main_page, text="PCAT_QXDM")
    pq_frame.pack(fill="x", **PADDING)
    ttk.Button(pq_frame, text="Start PCAT QXDM",
               command=main_controller.start_Pact_QXDM).pack(fill="x", padx=16, pady=8, ipady=8)

    # ── QUTS PAGE ─────────────────────────────────────────────────────────────
    quts_page = ttk.Frame(container)
    quts_page.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_page
    _add_nav("QUTS Tools", "QUTS")

    combo = ttk.LabelFrame(quts_page, text="Restart QUTS + PCAT + QXDM")
    combo.pack(fill="x", **PADDING)
    ttk.Button(combo, text="Restart QUTS + PCAT + QXDM",
               command=main_controller.restart_quts_pcat_qxdm,
               width=30).pack(fill="x", **PADDING)

    single = ttk.LabelFrame(quts_page, text="Restart QUTS only")
    single.pack(fill="x", **PADDING)
    ttk.Button(single, text="Restart QUTS only",
               command=Quts_controller.restart_quts,
               width=30).pack(fill="x", **PADDING)

    stop_all = ttk.LabelFrame(quts_page, text="Stop all Frameworks and Tools")
    stop_all.pack(fill="x", **PADDING)
    ttk.Button(stop_all, text="Stop all Tools",
               command=main_controller.stop_all_tools_Framework).pack(fill="x", **PADDING)
    
     # ── WIFI PAGE ─────────────────────────────────────────────────────────────
    wifi_config_page= ttk.Frame(container)
    wifi_config_page.grid(row=0, column=0, sticky="nsew")
    pages["Wifi Config"]=wifi_config_page
    _add_nav("Set Wifi","Wifi Config")

    # all Wifi config's 
    choices = ("3 SLO", "2G SLO + 5G-6G MLO")
    select_config= ttk.LabelFrame(wifi_config_page, text=" Select config Type")
    select_config.pack(fill="x", **PADDING)
    dropdown=ttk.Combobox(select_config, values=choices, state="readonly")
    dropdown.current(0)                                              # pre‑select first ite
    dropdown.pack(padx=20, pady=10)

    ttk.Button(select_config, text="Set config",
               command=lambda: Wifi_controller.update_cpe_wifi_config(dropdown.current())
               ).pack(fill="x", **PADDING)
    

    # ── Testing  PAGE ─────────────────────────────────────────────────────────────
    Testing_page= ttk.Frame(container)
    Testing_page.grid(row=0, column=0, sticky="nsew")
    pages["Testing_page"]=Testing_page
    _add_nav("Field Testing ","Testing_page")





    # ── Launch ────────────────────────────────────────────────────────────────
    show("Main")
    root.mainloop()


if __name__ == "__main__":
    main_controller.run_app()
