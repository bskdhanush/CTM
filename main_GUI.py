import os
import tkinter as tk
from tkinter import ttk, font, messagebox, IntVar
import threading
import datetime
import psutil
import subprocess
import time
import json
import sv_ttk

from Track_process import ensure_admin, restart_quts_pcat_qxdm
from QSTAF_Tool import (
    run_control_framework, run_traffic_framework, run_aws_s3_uploader,
    run_both_frameworks, kill_all_processes, load_settings, save_settings
)

# === Initialization ===
ensure_admin()

root = tk.Tk()
root.title("QSTAF System Manager")
root.geometry("600x520")
root.resizable(False, False)
sv_ttk.set_theme("dark")

padx = 25
pady = 15

status_var = tk.StringVar()
status_var.set("Ready")

def update_status(msg):
    status_var.set(msg)
    root.update_idletasks()

# === Fonts ===
main_font = font.nametofont("TkDefaultFont").copy()
main_font.configure(size=10)
title_font = font.nametofont("TkDefaultFont").copy()
title_font.configure(size=16, weight="bold")

# === Title ===
title_frame = ttk.Frame(root)
title_frame.pack(fill="x", padx=padx, pady=pady)
ttk.Label(title_frame, text="QSTAF System Manager", font=title_font).pack()

content_frame = ttk.Frame(root)
content_frame.pack(fill="both", expand=True, padx=padx, pady=10)

# === Framework Control Section ===
section_frame1 = ttk.LabelFrame(content_frame, text="Framework Control")
section_frame1.pack(fill="x", pady=10)

btn_frame1 = ttk.Frame(section_frame1)
btn_frame1.pack(fill="x", padx=padx, pady=pady)

ttk.Button(btn_frame1, text="Control Framework", command=run_control_framework).grid(row=0, column=0, padx=5, sticky="ew")
ttk.Button(btn_frame1, text="Traffic Framework", command=run_traffic_framework).grid(row=0, column=1, padx=5, sticky="ew")
ttk.Button(btn_frame1, text="Run both Frameworks (3s delay)", command=run_both_frameworks).grid(row=1, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="ew")
btn_frame1.columnconfigure(0, weight=1)
btn_frame1.columnconfigure(1, weight=1)

stop_frame = ttk.Frame(section_frame1)
stop_frame.pack(fill="x", padx=padx, pady=(0, pady))
ttk.Button(stop_frame, text="Stop All Frameworks", command=kill_all_processes, style="Accent.TButton").pack(fill="x")

# === AWS Section ===
section_frame2 = ttk.LabelFrame(content_frame, text="AWS S3 Uploader")
section_frame2.pack(fill="x", pady=10)

aws_frame = ttk.Frame(section_frame2)
aws_frame.pack(fill="x", padx=padx, pady=pady)
ttk.Button(aws_frame, text="Run S3 Uploader", command=run_aws_s3_uploader).pack(fill="x", pady=(0, 10))

# Scheduler
scheduler_var = IntVar()
def toggle_aws_scheduler():
    global scheduler_thread
    scheduler_running = scheduler_var.get() == 1
    if scheduler_running:
        def aws_scheduler_loop():
            while scheduler_var.get():
                now = datetime.datetime.now()
                if now.hour == 16 and now.minute == 0 and 0 <= now.second < 10:
                    update_status("Running scheduled AWS S3 upload (4:00 PM)")
                    run_aws_s3_uploader()
                    time.sleep(50)
                time.sleep(5)
        scheduler_thread = threading.Thread(target=aws_scheduler_loop, daemon=True)
        scheduler_thread.start()
        update_status("AWS Scheduler activated - Will run at 4:00 PM daily")
    else:
        update_status("AWS Scheduler deactivated")
    save_settings()

ttk.Checkbutton(aws_frame, text="Auto-run daily at 4:00 PM", variable=scheduler_var, command=toggle_aws_scheduler).pack(side=tk.LEFT)

# === QUTS/PCAT/QXDM Section ===
section_frame3 = ttk.LabelFrame(content_frame, text="QUTS / PCAT / QXDM")
section_frame3.pack(fill="x", pady=10)

quts_frame = ttk.Frame(section_frame3)
quts_frame.pack(fill="x", padx=padx, pady=pady)

def on_restart_apps():
    restart_quts_pcat_qxdm(callback=update_status)

ttk.Button(quts_frame, text="Restart QUTS + PCAT + QXDM", command=on_restart_apps).pack(fill="x")

# === Footer ===
status_frame = ttk.Frame(root)
status_frame.pack(side=tk.BOTTOM, fill="x", padx=padx, pady=pady)

ttk.Label(status_frame, textvariable=status_var, anchor="w").pack(side=tk.LEFT)

time_var = tk.StringVar()
def update_time():
    time_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
    root.after(1000, update_time)
update_time()

ttk.Label(status_frame, textvariable=time_var).pack(side=tk.RIGHT)

# === Load Scheduler Settings ===
settings = load_settings()
if settings.get("aws_scheduler_enabled"):
    scheduler_var.set(1)
    toggle_aws_scheduler()

# === Launch ===
root.mainloop()
