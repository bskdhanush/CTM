import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import MainController
import JsonHandler as JH

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def create_speed_Test_page(container, pages, add_nav):
    SpeedTest_page = ttk.Frame(container)
    SpeedTest_page.grid(row=0, column=0, sticky="nsew")
    pages["Testing"] = SpeedTest_page
    add_nav("SpeedTest", "Testing")

    
    SpeedTest = ttk.LabelFrame(SpeedTest_page, text="Start speed test")
    SpeedTest.pack(fill="x", **PADDING)# type: ignore  

    ttk.Label(
    SpeedTest,
    text="Enter the number of iterations:",
    anchor="w"
    ).pack(side="left", fill="x", expand=True,padx=(20, 0))

    iterationCount = tk.StringVar(value="1")
    ttk.Entry(
        SpeedTest,
        textvariable=iterationCount,
        width=4
    ).pack(side="left", padx=(8, 0))

    def get_iteration_count():
        try:
            return int(iterationCount.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for iteration count.")
            return None

    ttk.Button(
        SpeedTest,
        text="Start Speed Test",
        command=lambda:MainController.SpeedTest(get_iteration_count(), load_data_table),
    ).pack(fill="x", **PADDING)# type: ignore

    # ── Speed Test Data table ───────────────────────────────────────────
    
    SpeedTest_table = ttk.LabelFrame(SpeedTest_page, text="Speed Test Data")
    SpeedTest_table.pack(fill="both", expand=True, **PADDING)  # type: ignore

    # Make the LabelFrame act like a grid container
    SpeedTest_table.rowconfigure(0, weight=0)   # table row grows
    SpeedTest_table.columnconfigure(0, weight=1)

    COLUMNS = ("DL", "UL", "Band Info","Location","TimeStamp","adbid")  # include Location

    tree = ttk.Treeview(
        SpeedTest_table,
        columns=COLUMNS,
        show="headings",
        height=4,  # visible rows
    )

    # Headings
    tree.heading("TimeStamp", text="TimeStamp")
    tree.heading("DL",        text="DL (Mbps)")
    tree.heading("UL",        text="UL (Mbps)")
    tree.heading("adbid",     text="ADB ID")
    tree.heading("Location",    text="Location")
    tree.heading("Band Info",    text="Band Info")

    # Column widths; set some stretch=False so total width exceeds widget -> enables X scroll
    tree.column("TimeStamp", width=170, anchor="center", stretch=False)
    tree.column("DL",        width=120, anchor="center", stretch=False)
    tree.column("UL",        width=120, anchor="center", stretch=False)
    tree.column("adbid",     width=140, anchor="center", stretch=False)
    tree.column("Location",    width=180, anchor="center", stretch=True)
    tree.column("Band Info",    width=180, anchor="center", stretch=True)

    # Scrollbars
    vscroll = ttk.Scrollbar(SpeedTest_table, orient="vertical",   command=tree.yview)
    hsb     = ttk.Scrollbar(SpeedTest_table, orient="horizontal", command=tree.xview)

    # Wire scrollbars to the tree
    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hsb.set)

    # Layout (tree row 0, hsb row 1, button row 2; vscroll spans rows 0-1)
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns", rowspan=2)
    hsb.grid(row=1, column=0, sticky="ew")

    # Refresh button BELOW the hscrollbar (row 2)
    ttk.Button(
        SpeedTest_table,
        text="Refresh Data",
        command=lambda: (MainController.get_all_speedtest_results(), load_data_table()),
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 0))


    def load_data_table():
        """Read JSON list and (re)populate the table."""
        data = JH.load_json().get("SpeedTestData", []) 
        tree.delete(*tree.get_children())  # <-- adjust key to your JSON
    # Clear
        for row in data:
            tree.insert(
            "",
            "end",
            values=(
                row.get("DL", ""),
                row.get("UL", ""),
                row.get("BAND", ""),
                row.get("LOCATION", ""),
                row.get("TIMESTAMP", ""),
                row.get("ADBID", "")
            )
        )
    # initial fill
    load_data_table()

    return SpeedTest_page
    