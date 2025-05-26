# gui.py
import tkinter as tk
from tkinter import ttk
import sv_ttk
import aws_scheduler as aws
import main_controller
import Track_process

def launch_gui():
    """
    Construct and run the UI. All business logic lives in main_controller.
    """
    # Ensure admin before building any widgets
    main_controller.ensure_admin()

    root = tk.Tk()
    root.title("QSTAF System Manager")
    root.geometry("800x500")
    root.resizable(False, False)
    sv_ttk.set_theme("dark")

    PADDING = {"padx": 12, "pady": 8}

    # Layout: sidebar + container + status bar
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    sidebar = ttk.Frame(root)
    container = ttk.Frame(root)
    sidebar.grid(row=0, column=0, sticky="ns")
    container.grid(row=0, column=1, sticky="nsew")

    pages = {}
    nav_buttons = {}

    def show(page_name: str):
        pages[page_name].tkraise()
        for name, btn in nav_buttons.items():
            btn.configure(style="Accent.TButton" if name == page_name else "TButton")

    def _add_nav(text: str, key: str):
        btn = ttk.Button(sidebar, text=text, style="TButton",
                         command=lambda k=key: show(k))
        btn.pack(fill="x", pady=2, padx=4)
        nav_buttons[key] = btn

    # Status bar with scheduler state and clock
    status_var = tk.StringVar(value="Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")
    footer = ttk.Frame(root)
    footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 8))
    ttk.Label(footer, textvariable=status_var).pack(side="left")
    clock_lbl = ttk.Label(footer)
    clock_lbl.pack(side="right")

    import datetime
    def _tick():
        clock_lbl.config(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        root.after(1000, _tick)
    _tick()

    # --- Main page ---
    main_page = ttk.Frame(container)
    main_page.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_page
    _add_nav("Main", "Main")

    # Framework Control section
    ctrl = ttk.LabelFrame(main_page, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)
    row = ttk.Frame(ctrl)
    row.pack(fill="x", **PADDING)
    ttk.Button(row, text="Control Framework",
               command=main_controller.start_control).pack(
        side="left", expand=True, fill="x", padx=(0, 6))
    ttk.Button(row, text="Traffic Framework",
               command=main_controller.start_traffic).pack(
        side="right", expand=True, fill="x", padx=(6, 0))
    ttk.Button(ctrl, text="Run both Frameworks (3 s delay)",
               command=main_controller.run_both_with_delay).pack(fill="x", **PADDING)
    ttk.Button(ctrl, text="Stop All Frameworks",
               command=main_controller.stop_all).pack(fill="x", **PADDING)

    # AWS uploader section
    aws_frame = ttk.LabelFrame(main_page, text="AWS S3 Uploader")
    aws_frame.pack(fill="x", **PADDING)
    ttk.Button(aws_frame, text="Run S3 uploader now",
               command=main_controller.run_s3_uploader).pack(fill="x", **PADDING)
    aws_var = tk.BooleanVar(value=aws.is_enabled())
    def on_aws_toggle():
        aws.set_enabled(aws_var.get())
        status_var.set("Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")
    ttk.Checkbutton(aws_frame, text="Auto-run daily at 4 PM",
                    variable=aws_var, command=on_aws_toggle).pack(anchor="w", padx=20)

    # QUTS page
    quts_page = ttk.Frame(container)
    quts_page.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_page
    _add_nav("QUTS Tools", "QUTS")
    combo_frame = ttk.LabelFrame(quts_page, text="Restart QUTS + PCAT + QXDM")
    combo_frame.pack(fill="x", **PADDING)
    ttk.Button(combo_frame, text="Restart QUTS + PCAT + QXDM",
               command=main_controller.restart_quts_pcat_qxdm).pack(fill="x", **PADDING)
    single_frame = ttk.LabelFrame(quts_page, text="Restart QUTS only")
    single_frame.pack(fill="x", **PADDING)
    ttk.Button(single_frame, text="Restart QUTS only",
               command=Track_process.restart_quts).pack(fill="x", **PADDING)

    show("Main")
    root.mainloop()

if __name__ == "__main__":
    main_controller.run_app()
