import tkinter as tk
from tkinter import ttk
import sv_ttk
import aws_scheduler as aws
import main_controller
import Quts_conroller  # New import for QUTS status checks


def launch_gui():
    """
    Construct and run the UI. All business logic lives in main_controller.
    """
    # Ensure admin before building any widgets
    main_controller.ensure_admin()

    # --- Window Setup ---
    root = tk.Tk()
    root.title("QSTAF System Manager")
    root.geometry("560x450")  # Reduced size to fit content better
    root.resizable(False, False)
    sv_ttk.set_theme("dark")

    # --- Styles ---
    style = ttk.Style(root)
    style.configure("Sidebar.TFrame", background="#2a2a2e")

    # Run both = Blue accent (enhanced styling)
    style.configure(
        "RunBoth.TButton",
        background="#3A7EF5",
        foreground="white",
        focuscolor="#3A7EF5",
        borderwidth=0,
    )
    style.map(
        "RunBoth.TButton",
        background=[("active", "#4A8FF6"), ("pressed", "#2A6EE5")],
    )

    # Stop all = Red accent (enhanced styling)
    style.configure(
        "StopAll.TButton",
        background="#FA5252",
        foreground="white",
        focuscolor="#FA5252",
        borderwidth=0,
    )
    style.map(
        "StopAll.TButton",
        background=[("active", "#FF6B6B"), ("pressed", "#EA4242")],
    )

    PADDING = {"padx": 12, "pady": 8}

    # --- Layout ---
    root.columnconfigure(2, weight=1)
    root.rowconfigure(0, weight=1)
    sidebar = ttk.Frame(root, style="Sidebar.TFrame")
    container = ttk.Frame(root, style="Container.TFrame")
    sidebar.grid(row=0, column=0, sticky="ns")
    container.grid(row=0, column=1, sticky="nsew")

    pages = {}
    nav_buttons = {}

    def show(page_name: str):
        pages[page_name].tkraise()
        for name, btn in nav_buttons.items():
            btn.configure(style="Accent.TButton" if name == page_name else "TButton")

    def _add_nav(text: str, key: str):
        btn = ttk.Button(sidebar, text=text, style="TButton", command=lambda k=key: show(k), width=15)
        btn.pack(fill="x", pady=6, padx=6)
        nav_buttons[key] = btn

    # --- Status Bar ---
    quts_status_var = tk.StringVar(value="QUTS: Checking…")
    scheduler_status_var = tk.StringVar(value="Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")

    footer = ttk.Frame(root)
    footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 8))

    # Left – QUTS service status (real‑time)
    ttk.Label(footer, textvariable=quts_status_var).pack(side="left")

    # Middle – AWS scheduler status
    ttk.Label(footer, textvariable=scheduler_status_var, padding=(12, 0)).pack(side="left")

    # Right – clock
    clock_lbl = ttk.Label(footer)
    clock_lbl.pack(side="right")

    import datetime

    def _tick():
        clock_lbl.config(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        root.after(1000, _tick)

    _tick()

    def _update_quts_status():
        running = Quts_conroller.is_service_running("QUTS")
        quts_status_var.set(f"QUTS: {'Running' if running else 'Stopped'}")
        # refresh every 3 seconds ‑ low overhead yet responsive
        root.after(3000, _update_quts_status)

    _update_quts_status()

    # --- Main Page ---
    main_page = ttk.Frame(container)
    main_page.grid(row=0, column=0, sticky="nsew")
    pages["Main"] = main_page
    _add_nav("Main", "Main")

    # Framework Control section
    ctrl = ttk.LabelFrame(main_page, text="Framework Control")
    ctrl.pack(fill="x", **PADDING)
    row = ttk.Frame(ctrl)
    row.pack(fill="x", **PADDING)

    # Control & Traffic buttons
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

    # Run both (blue) – Enhanced button with better styling
    ttk.Button(
        ctrl,
        text="Run both Frameworks (3 s delay)",
        command=main_controller.run_both_with_delay,
        style="RunBoth.TButton",
    ).pack(fill="x", padx=16, pady=(12, 6), ipady=10)

    # Stop all (red) – Enhanced button with better styling
    ttk.Button(
        ctrl,
        text="Stop All Frameworks",
        command=main_controller.stop_all,
        style="StopAll.TButton",
    ).pack(fill="x", padx=16, pady=(6, 12), ipady=10)

    # --- AWS S3 Uploader ---
    aws_frame = ttk.LabelFrame(main_page, text="AWS S3 Uploader")
    aws_frame.pack(fill="x", **PADDING)

    ttk.Button(
        aws_frame,
        text="Run S3 Uploader",
        command=main_controller.run_s3_uploader,
    ).pack(fill="x", padx=16, pady=8, ipady=8)

    aws_var = tk.BooleanVar(value=aws.is_enabled())

    def on_aws_toggle():
        aws.set_enabled(aws_var.get())
        scheduler_status_var.set("Scheduler: ON" if aws.is_enabled() else "Scheduler: OFF")

    ttk.Checkbutton(
        aws_frame,
        text="Auto-run daily at 4:00 PM",
        variable=aws_var,
        command=on_aws_toggle,
    ).pack(anchor="w", padx=16)

    # --- QUTS Tools Page ---
    quts_page = ttk.Frame(container)
    quts_page.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_page
    _add_nav("QUTS Tools", "QUTS")

    combo_frame = ttk.LabelFrame(quts_page, text="Restart QUTS + PCAT + QXDM")
    combo_frame.pack(fill="x", **PADDING)
    ttk.Button(
        combo_frame,
        text="Restart QUTS + PCAT + QXDM",
        command=main_controller.restart_quts_pcat_qxdm,
        width=30,
    ).pack(fill="x", **PADDING)

    single_frame = ttk.LabelFrame(quts_page, text="Restart QUTS only")
    single_frame.pack(fill="x", **PADDING)
    ttk.Button(
        single_frame,
        text="Restart QUTS only",
        command=Quts_conroller.restart_quts,
        width=30,
    ).pack(fill="x", **PADDING)

    show("Main")
    root.mainloop()


if __name__ == "__main__":
    main_controller.run_app()
