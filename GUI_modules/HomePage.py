import tkinter as tk
from tkinter import ttk
from functools import partial

import AwsScheduler as aws
import GUI
from JsonHandler import load_json, save_json
import MainController
from Constants import APP_CONFIG_JSON

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_Home_Page(container, pages, add_nav, root):
    main_pg = ttk.Frame(container)
    main_pg.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_pg
    add_nav("Main", "Main")

    # Framework control
    ctrl = ttk.LabelFrame(main_pg, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)# type: ignore
    control_ts_var = tk.StringVar(value="Control: Not started")
    traffic_ts_var = tk.StringVar(value="Traffic: Not started")
    control_reset_timer_var = tk.StringVar(value="none")
    traffic_idle_timer_var = tk.StringVar(value="none")
    traffic_test_timer_var = tk.StringVar(value="none")


    def update_timestamps(mode):
        cfg = load_json()
        if mode == "control":
            cts = cfg.get("control_start_timestamp")
            control_ts_var.set(f"Control started at: {cts}" if cts else "Control: Not started")
        elif mode == "traffic":
            tts = cfg.get("traffic_start_timestamp")
            traffic_ts_var.set(f"Traffic started at: {tts}" if tts else "Traffic: Not started")
        else:
            cts = cfg.get("control_start_timestamp")
            control_ts_var.set(f"Control started at: {cts}" if cts else "Control: Not started")
            tts = cfg.get("traffic_start_timestamp")
            traffic_ts_var.set(f"Traffic started at: {tts}" if tts else "Traffic: Not started")

    update_timestamps("")
    #GUI.start_json_file_watcher(update_timestamps, APP_CONFIG_JSON, root)

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

    left_frame = ttk.Frame(row_relaunch)
    left_frame.pack(side="left", fill="x", expand=True)

    right_frame = ttk.Frame(row_relaunch)
    right_frame.pack(side="right", fill="x", expand=True)
    
    ttk.Button(
        row,
        text="Launch Control Framework",
        command=lambda:update_timestamps(MainController.start_framework("control")), 
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row,
        text="Launch Traffic Framework",
        command=lambda:update_timestamps(MainController.start_framework("traffic")), 
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    ttk.Button(
        row_s,
        text="Stop Control Framework",
        command=lambda:update_timestamps(MainController.stop_framework("control")),
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        row_s,
        text="Stop Traffic Framework",
        command=lambda:update_timestamps(MainController.stop_framework("traffic")),
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

    app_cfg = load_json()
    control_reset_timer_value = app_cfg.get("control_reset_timer", " ")
    control_reset_timer_var = tk.StringVar(value=control_reset_timer_value)
    ttk.Entry(
        left_frame,
        textvariable=control_reset_timer_var,
        width=4
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        left_frame,
        text="Update Control Relaunch Timer (in mins)",
        command=lambda: update_control_reset_timer_var()
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)

    def update_control_reset_timer_var() -> None:
        try:
            new_count = int(control_reset_timer_var.get())
        except ValueError:
            return
        cfg = load_json()
        cfg["control_reset_timer"] = new_count
        save_json(cfg)
        update_timestamps("")


    app_cfg = load_json()
    traffic_idle_timer_value = app_cfg.get("traffic_idle_timer", " ")
    traffic_idle_timer_var = tk.StringVar(value=traffic_idle_timer_value)
    ttk.Entry(
        right_frame,
        textvariable=traffic_idle_timer_var,
        width=4
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        right_frame,
        text="Update Idle Timer",
        command=lambda: update_traffic_idle_timer_var()
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)
    
    def update_traffic_idle_timer_var() -> None:
        try:
            new_count = int(traffic_idle_timer_var.get())
        except ValueError:
            return
        cfg = load_json()
        cfg["traffic_idle_timer"] = new_count
        save_json(cfg)
        traffic_idle_timer_var.set(f"{new_count}")
        update_timestamps("")


    app_cfg = load_json()
    traffic_test_timer_value = app_cfg.get("traffic_test_timer", " ")
    traffic_test_timer_var = tk.StringVar(value=traffic_test_timer_value)
    ttk.Entry(
        right_frame,
        textvariable=traffic_test_timer_var,
        width=4
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        right_frame,
        text="Update Test Timer",
        command=lambda: update_traffic_test_timer_var()
    ).pack(side="left", expand=False, fill="x", padx=(0, 6), ipady=6)
    
    def update_traffic_test_timer_var() -> None:
        try:
            new_count = int(traffic_test_timer_var.get())
        except ValueError:
            return
        cfg = load_json()
        cfg["traffic_test_timer"] = new_count
        save_json(cfg)
        traffic_test_timer_var.set(f"{new_count}")
        update_timestamps("")



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
    
    return main_pg