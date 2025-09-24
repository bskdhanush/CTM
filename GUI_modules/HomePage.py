import tkinter as tk
from tkinter import ttk
from functools import partial

import AwsScheduler as aws
import GUI
import JsonHandler as JH
import MainController


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
    GUI.start_json_file_watcher(update_timestamps, JH.get_json_path(), root)


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
    
    return main_pg