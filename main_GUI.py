# main_GUI.py (Updated)
import tkinter as tk
from tkinter import ttk, font, IntVar, messagebox
import threading
import datetime
import time
import sv_ttk
import sys
import traceback

from inndivudal_controller.Track_process import ensure_admin, restart_quts_pcat_qxdm
from QSTAF_Tool import (
    run_control_framework, run_traffic_framework, run_aws_s3_uploader,
    run_both_frameworks, load_settings, save_settings
)

# Global Exception Handler
def global_exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print("Unhandled exception:", error_msg)
    messagebox.showerror("Application Crash", error_msg)

sys.excepthook = global_exception_hook

# === Initialization ===
ensure_admin()
root = tk.Tk()
root.title("QSTAF System Manager")
root.geometry("600x520")
root.resizable(False, False)
sv_ttk.set_theme("dark")

padx = 25
pady = 15

status_var = tk.StringVar(value="Ready")
scheduler_var = IntVar()
scheduler_thread = None

def update_status(msg):
    if status_var:
        status_var.set(msg)
        root.update_idletasks()

# === Fonts ===
main_font = font.nametofont("TkDefaultFont").copy()
main_font.configure(size=10)
title_font = font.nametofont("TkDefaultFont").copy()
title_font.configure(size=16, weight="bold")

# === Title ===
ttk.Label(ttk.Frame(root), text="QSTAF System Manager", font=title_font).pack(padx=padx, pady=pady)

content_frame = ttk.Frame(root)
content_frame.pack(fill="both", expand=True, padx=padx, pady=10)

# === Framework Section ===
section1 = ttk.LabelFrame(content_frame, text="Framework Control")
section1.pack(fill="x", pady=10)

btns1 = ttk.Frame(section1)
btns1.pack(fill="x", padx=padx, pady=pady)
ttk.Button(btns1, text="Control Framework", command=run_control_framework).grid(row=0, column=0, padx=5, sticky="ew")
ttk.Button(btns1, text="Traffic Framework", command=run_traffic_framework).grid(row=0, column=1, padx=5, sticky="ew")
ttk.Button(btns1, text="Run both Frameworks (3s delay)", command=run_both_frameworks).grid(row=1, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="ew")
btns1.columnconfigure((0,1), weight=1)

ttk.Button(section1, text="Stop All Frameworks", style="Accent.TButton", command=lambda: print("TODO: kill_all_processes()")).pack(fill="x", padx=padx, pady=(0, pady))

# === AWS Section ===
section2 = ttk.LabelFrame(content_frame, text="AWS S3 Uploader")
section2.pack(fill="x", pady=10)

aws_frame = ttk.Frame(section2)
aws_frame.pack(fill="x", padx=padx, pady=pady)
ttk.Button(aws_frame, text="Run S3 Uploader", command=run_aws_s3_uploader).pack(fill="x", pady=(0, 10))

def toggle_aws_scheduler():
    global scheduler_thread
    enabled = scheduler_var.get() == 1
    if enabled:
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
        update_status("AWS Scheduler activated")
    else:
        update_status("AWS Scheduler deactivated")
    save_settings(enabled)

ttk.Checkbutton(aws_frame, text="Auto-run daily at 4:00 PM", variable=scheduler_var, command=toggle_aws_scheduler).pack(side=tk.LEFT)

# === QUTS / PCAT / QXDM Section ===
section3 = ttk.LabelFrame(content_frame, text="QUTS / PCAT / QXDM")
section3.pack(fill="x", pady=10)
ttk.Button(section3, text="Restart QUTS + PCAT + QXDM", command=lambda: restart_quts_pcat_qxdm(callback=update_status)).pack(fill="x", padx=padx, pady=pady)

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

# === Load saved settings ===
settings = load_settings()
if settings.get("aws_scheduler_enabled"):
    scheduler_var.set(1)
    toggle_aws_scheduler()

# === Launch GUI ===
root.mainloop()
