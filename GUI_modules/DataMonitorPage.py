import tkinter as tk
from tkinter import ttk
import PlotDynamicRender as rdp


def create_data_monitor_page(container, pages, add_nav):
    """
    Create and return the DATA MONITOR page with navigation registration.
    
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

    # populate dynamically ----
    # draw the first plot immediately
    rdp.draw_all_plots(list_fr)
    # then kick off the background refresher
    rdp.periodic_refresh(list_fr)
    
    return data_pg