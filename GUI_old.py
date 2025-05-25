import tkinter as tk
from tkinter import ttk
import sv_ttk               # optional dark‑mode theme (pip install sv-ttk)
import datetime

# Business‑logic modules — NO GUI code inside them
import inndivudal_controller.aws_scheduler as aws          # new, handles config + scheduling
import main_controller               # your existing framework helpers
import Track_process                 # existing QUTS helpers

# ------------------------------------------------------------------
# Root window
# ------------------------------------------------------------------
root = tk.Tk()
main_controller.ensure_admin()       # still needed for elevated ops
root.title("QSTAF System Manager")
root.geometry("700x500")
root.resizable(False, False)
sv_ttk.set_theme("dark")            # comment out if not using sv‑ttk

PADDING = {"padx": 12, "pady": 6}

# ------------------------------------------------------------------
# Framework Control section
# ------------------------------------------------------------------
ctrl_frame = ttk.LabelFrame(root, text="Framework Control")
ctrl_frame.pack(fill="x", **PADDING)

row = ttk.Frame(ctrl_frame)
row.pack(fill="x", **PADDING)

ttk.Button(row, text="Control Framework",  command=main_controller.start_control).pack(side="left", expand=True, fill="x", padx=(0, 6))

ttk.Button(row, text="Traffic Framework",  command=main_controller.start_traffic).pack(side="right", expand=True, fill="x", padx=(6, 0))

ttk.Button(
    ctrl_frame,
    text="Run both Frameworks (3 s delay)",
    command=main_controller.run_both_with_delay,
).pack(fill="x", **PADDING)

ttk.Button(
    ctrl_frame,
    text="Stop All Frameworks",
    command=main_controller.stop_all,
).pack(fill="x", **PADDING)


# ------------------------------------------------------------------
# AWS S3 uploader section (toggle + run‑now)
# ------------------------------------------------------------------
aws_frame = ttk.LabelFrame(root, text="AWS S3 Uploader")
aws_frame.pack(fill="x", **PADDING)

# --- Run‑now button ----------------------------------------------------

def run_s3_now():
    aws.run_now()

ttk.Button(
    aws_frame,
    text="Run S3 uploader now",
    command=run_s3_now,
).pack(fill="x", **PADDING)

# --- Auto‑run toggle ---------------------------------------------------
aws_var = tk.BooleanVar(value=aws.is_enabled())

status_var = tk.StringVar(
    value="Scheduler: ON" if aws_var.get() else "Scheduler: OFF"
)

def on_aws_toggle():
    enabled = aws_var.get()
    aws.set_enabled(enabled)
    status_var.set("Scheduler: ON" if enabled else "Scheduler: OFF")

ttk.Checkbutton(
    aws_frame,
    text="Auto‑run daily at 4 PM",
    variable=aws_var,
    command=on_aws_toggle,
).pack(anchor="w", padx=20)


# ------------------------------------------------------------------
# QUTS / PCAT / QXDM helpers
# ------------------------------------------------------------------
quts_frame = ttk.LabelFrame(root, text="QUTS / PCAT / QXDM")
quts_frame.pack(fill="x", **PADDING)

ttk.Button(
    quts_frame,
    text="Restart QUTS + PCAT + QXDM",
    command=main_controller.restart_quts_pcat_qxdm,
).pack(fill="x", **PADDING)

stand_frame = ttk.LabelFrame(root, text="Restart QUTS (stand‑alone)")
stand_frame.pack(fill="x", **PADDING)

ttk.Button(
    stand_frame,
    text="Restart QUTS only",
    command=Track_process.restart_quts,
).pack(fill="x", **PADDING)

# ------------------------------------------------------------------
# Footer (scheduler status + live clock)
# ------------------------------------------------------------------
footer = ttk.Frame(root)
footer.pack(fill="x", padx=12, pady=(8, 10))

ttk.Label(footer, textvariable=status_var).pack(side="left")
clock_lbl = ttk.Label(footer)
clock_lbl.pack(side="right")


def _tick():
    clock_lbl.config(text=datetime.datetime.now().strftime("%Y‑%m‑%d  %H:%M:%S"))
    root.after(1000, _tick)

_tick()

# ------------------------------------------------------------------
# Start Tk loop
# ------------------------------------------------------------------
root.mainloop()
