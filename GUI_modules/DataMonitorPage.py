import tkinter as tk
from tkinter import ttk
import PlotDynamicRender as rdp


def create_data_monitor_page(container, pages, add_nav):
    """
    Create and return the DATA MONITOR page with navigation registration.
    Uses optimized plotting system for smooth refresh without UI stuttering.
    
    Args:
    container: The parent container (ttk.Frame) where this page will be placed
    pages: Dictionary to store page references
    add_nav: Function to add navigation button
    
    Returns:
    ttk.Frame: The configured DATA MONITOR page frame
    """
    # ── DATA MONITOR page ────
    data_pg = ttk.Frame(container)
    data_pg.grid(row=0, column=0, sticky="nsew")
    pages["Data"] = data_pg
    add_nav("CPE Data Monitor", "Data")
    
    # Create control frame for refresh controls
    control_frame = ttk.Frame(data_pg)
    control_frame.pack(fill="x", padx=10, pady=5)
    interval_var = tk.StringVar(value="60")
    """
    # Add refresh controls
    ttk.Label(control_frame, text="Refresh Interval (seconds):").pack(side="left", padx=5)
    
    interval_var = tk.StringVar(value="60")
    interval_entry = ttk.Entry(control_frame, textvariable=interval_var, width=10)
    interval_entry.pack(side="left", padx=5)
      
    def update_interval():
        try:
            new_interval = int(interval_var.get())
            if new_interval < 10:
                new_interval = 10  # Minimum 10 seconds
                interval_var.set("10")
            
            # Restart refresh with new interval
            rdp.stop_periodic_refresh()
            rdp.start_periodic_refresh(list_fr, new_interval)
            status_label.config(text=f"Refresh interval updated to {new_interval}s")
        except ValueError:
            status_label.config(text="Invalid interval - using default 60s")
            interval_var.set("60")
    
    def manual_refresh():
        status_label.config(text="Refreshing...")
        data_pg.after(100, lambda: [rdp.manual_refresh(), status_label.config(text="Manual refresh complete")])
    
    def start_refresh():
        try:
            interval = int(interval_var.get())
            rdp.start_periodic_refresh(list_fr, interval)
            status_label.config(text=f"Auto-refresh started ({interval}s interval)")
        except ValueError:
            status_label.config(text="Invalid interval")
    
    def stop_refresh():
        rdp.stop_periodic_refresh()
        status_label.config(text="Auto-refresh stopped")

    
    
    # Control buttons
    ttk.Button(control_frame, text="Update Interval", command=update_interval).pack(side="left", padx=5)
    ttk.Button(control_frame, text="Manual Refresh", command=manual_refresh).pack(side="left", padx=5)
    ttk.Button(control_frame, text="Start Auto-Refresh", command=start_refresh).pack(side="left", padx=5)
    ttk.Button(control_frame, text="Stop Auto-Refresh", command=stop_refresh).pack(side="left", padx=5)
   
    """
    # Status label
    status_label = ttk.Label(control_frame, text="Ready", foreground="green")
    status_label.pack(side="right", padx=10)
    
    # Separator
    ttk.Separator(data_pg, orient="horizontal").pack(fill="x", pady=5)
    
    # scrollable canvas ----
    canvas = tk.Canvas(data_pg, borderwidth=0, highlightthickness=0)
    scroll = ttk.Scrollbar(data_pg, orient="vertical", command=canvas.yview)
    list_fr = ttk.Frame(canvas)

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
    
    # Initialize plots once and start refresh system
    def initialize_page():
        status_label.config(text="Initializing plots...")
        data_pg.after(100, lambda: [
            rdp.init_plots(list_fr),
            rdp.start_periodic_refresh(list_fr, int(interval_var.get())),
            status_label.config(text="Plots initialized - auto-refresh active")
        ])
    
    # Initialize after a short delay to ensure UI is ready
    data_pg.after(500, initialize_page)
   
    
    # Cleanup function for when page is destroyed
    def cleanup():
        rdp.stop_periodic_refresh()
        rdp.clear_plots()
    
    # Bind cleanup to page destruction
    data_pg.bind("<Destroy>", lambda e: cleanup())
    
    return data_pg