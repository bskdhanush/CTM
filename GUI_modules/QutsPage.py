import tkinter as tk
from tkinter import ttk

import MainController
import QutsController

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
def create_Quts_Page(container, pages, add_nav):
    # ── Quts page ─────────────────────────────────────────────────────
    quts_pg = ttk.Frame(container)
    quts_pg.grid(row=0, column=0, sticky="nsew")
    pages["QUTS"] = quts_pg
    add_nav("QUTS Tools", "QUTS")

    # Select which tools to manage (side-by-side)
    tools_fr = ttk.LabelFrame(quts_pg, text="Select Tools")
    tools_fr.pack(fill="x", **PADDING) # type: ignore

    quts_var = tk.BooleanVar(value=False)
    pcat_var = tk.BooleanVar(value=True)
    qxdm_var = tk.BooleanVar(value=False)

    # Use a little inner frame so the LabelFrame text stays above
    inner = ttk.Frame(tools_fr)
    inner.pack(padx=10, pady=6, fill="x")

    ttk.Checkbutton(inner, text="QUTS Service", variable=quts_var)\
        .grid(row=0, column=0, padx=8, pady=4, sticky="w")
    ttk.Checkbutton(inner, text="PCAT", variable=pcat_var)\
        .grid(row=0, column=1, padx=8, pady=4, sticky="w")
    ttk.Checkbutton(inner, text="QXDM", variable=qxdm_var)\
        .grid(row=0, column=2, padx=8, pady=4, sticky="w")

    # Start/Stop buttons
    btn_fr = ttk.Frame(quts_pg)
    btn_fr.pack(fill="x", **PADDING) # type: ignore

    def start_selected_tools():
        if quts_var.get() and pcat_var.get() and qxdm_var.get():
            MainController.start_all()
        else:
            if quts_var.get():
                QutsController.start_quts()
            if pcat_var.get():
                MainController.start_Pact_only()
            if qxdm_var.get():
                MainController.start_QXDM_only()

    def stop_selected_tools():
        if quts_var.get():
            QutsController.stop_quts()
        if pcat_var.get():
            MainController.stop_pcat_only()
        if qxdm_var.get():
            MainController.stop_qxdm_only()

    ttk.Button(
        btn_fr,
        text="Start",
        command=start_selected_tools,
        width=18,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)

    ttk.Button(
        btn_fr,
        text="Stop",
        command=stop_selected_tools,
        width=18,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=6)

    return quts_pg
