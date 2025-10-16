from __future__ import annotations
import os
import json
from pathlib import Path
import platform
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

from queue import Queue,Empty

import sv_ttk

import ADBController
from GUI_modules import DataMonitorPage, FzDownloadPage, HomePage, QSTAFDappInstallerPage, QutsPage, SpeedTestPage, WifiRenamePage, DeviceConfigurationPage,CrashForecastPage
import MainController
import WifiController
import QutsController
import DataMonitorController as dmc
import CrashCountController as cc
import JsonHandler as JH
from Constants import APP_CONFIG_JSON

def add_copy_support(root: tk.Tk) -> None:
    is_mac = platform.system() == 'Darwin'
    accel = 'Command-C' if is_mac else 'Control-c'

    menu = tk.Menu(root, tearoff=0)

    def label_text(w):
        try:
            txt = w.cget("text")
            if not txt:
                var = w.cget("textvariable")
                if var:
                    txt = root.getvar(var)
            return str(txt)
        except Exception:
            return ""

    def copy_from_widget(widget=None):
        w = widget or root.focus_get()
        # Enable universal copy (labels, text, entries, listbox, treeview, logs)

        if w is None:
            return
        sel = ""
        try:
            if isinstance(w, (tk.Entry, ttk.Entry)):
                sel = w.selection_get()
            elif isinstance(w, (tk.Text, ScrolledText)):
                try:
                    sel = w.get("sel.first", "sel.last")
                except Exception:
                    # fallback: copy all text (handles disabled Text/ScrolledText)
                    state = str(w.cget("state"))
                    if state == "disabled":
                        w.configure(state="normal")
                        sel = w.get("1.0", "end-1c")
                        w.configure(state="disabled")
                    else:
                        sel = w.get("1.0", "end-1c")
            elif isinstance(w, tk.Listbox):
                indices = w.curselection()
                sel = "\n".join(w.get(i) for i in indices) if indices else ""
            elif isinstance(w, ttk.Treeview):
                items = w.selection()
                rows = []
                for iid in items:
                    vals = w.item(iid, "values")
                    if vals:
                        rows.append("\t".join(map(str, vals)))
                    else:
                        rows.append(str(w.item(iid, "text")))
                sel = "\n".join(rows)
            elif isinstance(w, (ttk.Label, tk.Label)):
                sel = label_text(w)
            else:
                try:
                    sel = root.selection_get()
                except Exception:
                    sel = ""
        except Exception:
            sel = ""
        if sel:
            root.clipboard_clear()
            root.clipboard_append(sel)

    def show_menu(e):
        w = e.widget
        menu.delete(0, 'end')
        if isinstance(w, (tk.Entry, tk.Text, ttk.Entry, ScrolledText)):
            menu.add_command(label="Cut", command=lambda: w.event_generate("<<Cut>>"))
            menu.add_command(label="Copy", command=lambda: copy_from_widget(w))
            menu.add_command(label="Paste", command=lambda: w.event_generate("<<Paste>>"))
            menu.add_separator()
            menu.add_command(label="Select All", command=lambda: w.event_generate("<<SelectAll>>"))
        elif isinstance(w, (tk.Listbox, ttk.Treeview, ttk.Label, tk.Label)):
            menu.add_command(label="Copy", command=lambda: copy_from_widget(w))
        if menu.index('end') is not None:
            menu.tk_popup(e.x_root, e.y_root)

    root.bind_all(f'<{accel}>', lambda e: (copy_from_widget(), "break"))
    # Right-click context menu
    if is_mac:
        root.bind_all("<Button-2>", show_menu, add="+")
    root.bind_all("<Button-3>", show_menu, add="+")

# ───────────────────────────────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────────────────────────────
PADDING:dict[str, int] = {"padx": 12, "pady": 8}
white_accent = "#FFFFFF"
red_accent = "#E95959"


# ── Global toggle variable ─────────────────────────────────────────────────

root = None
observers = []  # Global list to track all observers
meta = ""

class JsonFileWatcher(FileSystemEventHandler):
    def __init__(self, callback, file_path_to_watch, tk_root: tk.Tk):
        self.callback = callback
        self.file_path_to_watch = str(file_path_to_watch)
        self.tk_root = tk_root

    def on_modified(self, event):
        if event.src_path == self.file_path_to_watch:
            def safe_update():
                try:
                    if self.tk_root.winfo_exists():
                        self.callback()
                except tk.TclError:
                    pass
            try:
                self.tk_root.after(0, safe_update)
                logging.info(f"JSON Watcher: File modified - {event.src_path}")
            except tk.TclError:
                pass
def start_json_file_watcher(callback, file_path_to_watch, tk_root: tk.Tk):
    obs = Observer()
    handler = JsonFileWatcher(callback, file_path_to_watch, tk_root)

    watch_dir = os.path.dirname(file_path_to_watch)
    if not os.path.exists(watch_dir):
        os.makedirs(watch_dir)

    obs.schedule(handler, watch_dir, recursive=False)
    obs.start()
    observers.append(obs)

def launch_gui() -> None:
    """Construct and run the UI."""
    global root 

    # ── Window ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("CPE Test Manager V3.0")
    root.geometry("1024x768")
    root.resizable(True, True)
    sv_ttk.set_theme("dark")
    add_copy_support(root)

    # ── Styles ──────────────────────────────────────────────────────────
    style = ttk.Style(root)
    style.configure("Sidebar.TFrame", background="#2a2a2e")

    # ── header (mini) ───────────────────────────────────────────────────────
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=4)

    for col in range(7):
       header_frame.columnconfigure(col, weight=0)
    header_frame.columnconfigure(1, weight=1)   # left side expands
    
    meta_var = tk.StringVar(value="Meta : ")
    mpss_var = tk.StringVar(value="MPSS : ")

    ttk.Label(header_frame, textvariable=meta_var,  anchor="w") \
        .grid(row=0, column=0, sticky="w", padx=15)
    ttk.Label(header_frame, textvariable=mpss_var,  anchor="w") \
        .grid(row=1, column=0, sticky="w", padx=15)

    def refresh_meta_mpss() -> None:
        meta, mpss = MainController.get_meta_mpss()
        meta_var.set(f"Meta : {meta or 'UNKNOWN'}")
        mpss_var.set(f"MPSS : {mpss or 'UNKNOWN'}")
    refresh_meta_mpss()

    ttk.Button(
        header_frame, text="Get Build info",
        command=refresh_meta_mpss, width=12
    ).grid(row=2, column=0, sticky="w", padx=10, pady=5)

    # --- reboot button (centre-left, on its own row) ----------------------------
    ttk.Button(
        header_frame, text="Restart Device", width=12,
        command=lambda: WifiController.run_command("adb root && adb reboot")
    ).grid(row=2, column=2, sticky="w", padx=10, pady=5)

    # --- crash counters (hard-right) -------------------------------------------
    def Reset_label():
        crash_lbl.config(foreground=white_accent)
        crash_text_lbl.configure(foreground=white_accent)
        crash_var.set("0")

        RDKB_lbl.configure(foreground=white_accent)
        RDKB_text_lbl.configure(foreground=white_accent)
        RDKB_var.set("0")
        cc.rest_counter()


    crash_var  = tk.StringVar(value="—")
    RDKB_var   = tk.StringVar(value="—")

    crash_text_lbl = ttk.Label(header_frame, text="Device Crashes:", anchor="e")
    crash_text_lbl.grid(row=0, column=3, sticky="e", padx=(10, 5))
    crash_lbl = ttk.Label(header_frame, textvariable=crash_var, anchor="w")
    crash_lbl.grid(row=0, column=4, sticky="w")

    RDKB_text_lbl = ttk.Label(header_frame, text="RDKB Crashes:",  anchor="e")
    RDKB_text_lbl.grid(row=1, column=3, sticky="e", padx=(10, 5))
    RDKB_lbl = ttk.Label(header_frame, textvariable=RDKB_var, anchor="w")
    RDKB_lbl.grid(row=1, column=4, sticky="w")

    ttk.Button(
        header_frame, text="Reset Counter", width=12,
        command=Reset_label
    ).grid(row=2, column=3, columnspan=2, sticky="e", padx=20, pady=5)


    def check_crash_queue():
        try:
            while True:
                update = crash_update_queue.get_nowait()
                
                # Update based on crash type
                if update['type'] in ['crash', 'normalcrash']:
                    crash_var.set(str(update['count']))
                    if update['count'] > 0:
                        crash_lbl.config(foreground=red_accent)
                        crash_text_lbl.configure(foreground=red_accent)
                elif update['type'] == 'rdkbcrash':
                    RDKB_var.set(str(update['count']))
                    if update['count'] > 0:
                        RDKB_lbl.configure(foreground=red_accent)
                        RDKB_text_lbl.configure(foreground=red_accent)
                        
        except Empty:
            pass
        finally:
            # Check queue again after 100ms
            if root is not None:
                try:
                    if root.winfo_exists():
                        root.after(100, check_crash_queue)
                except tk.TclError:
                    pass
    check_crash_queue()

    # ── Grid weights ─────────────────────────────────────────────────────
    root.columnconfigure(1, weight=1)  # column 1 = main content
    root.rowconfigure(1, weight=1)     # row 1   = sidebar  pages

    # ── Sidebar & container ───────────────────────────────────────────────
    sidebar   = ttk.Frame(root, style="Sidebar.TFrame")
    container = ttk.Frame(root)
    sidebar.grid(row=1, column=0, sticky="ns")
    container.grid(row=1, column=1, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    pages: dict[str, ttk.Frame] = {}
    nav_btns: dict[str, ttk.Button] = {}

    def show(page: str) -> None:
        pages[page].tkraise()
        for name, btn in nav_btns.items():
            btn.configure(style="Accent.TButton" if name == page else "TButton")

    def add_nav(text: str, key: str) -> None:
        btn = ttk.Button(sidebar, text=text, width=15, command=lambda k=key: show(k))
        btn.pack(fill="x", pady=6, padx=6)
        nav_btns[key] = btn


    # ── Footer / status bar ───────────────────────────────────────────────
    footer = ttk.Frame(root)
    footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 8))

    # give each of 4 columns equal weight
    footer.columnconfigure(0, weight=0)
    footer.columnconfigure(1, weight=1)
    footer.columnconfigure(2, weight=1)
    footer.columnconfigure(3, weight=0)

    # --- vars ---
    adb_var       = tk.StringVar(value="ADB ID: --")
    quts_stat_var = tk.StringVar(value="QUTS: Checking…")
    center_var    = tk.StringVar(value="Internet status")
    version_text  = f"QSTAF VERSION: {MainController.get_qstaf_version()}"

    # --- widgets in desired order ---
    adb_label = ttk.Label(footer, textvariable=adb_var)
    quts_label = tk.Label(
        footer,
        textvariable=quts_stat_var,
        font=("TkDefaultFont", 10, "bold"),
    )
    internet_label = tk.Label(
        footer,
        textvariable=center_var,
        font=("Segoe UI", 12),
        fg="white",
        anchor="center",
    )
    version_label = ttk.Label(footer, text=version_text)

    # --- grid them evenly ---
    adb_label.grid(    row=0, column=0, sticky="w",  padx=5)
    quts_label.grid(   row=0, column=1, sticky="ew", padx=5)
    internet_label.grid(   row=0, column=2, sticky="ew", padx=5)
    version_label.grid(  row=0, column=3, sticky="e",  padx=5)

    def update_label():
        try:
            with open(ADBController.json_path, "r") as f:
                data = json.load(f)
            adb_id = data.get("ADB ID", "--")
            adb_var.set(f"ADB ID: {adb_id}")
        except (FileNotFoundError, json.JSONDecodeError):
            adb_id = "--"

    update_label()
    start_json_file_watcher(update_label,Path(ADBController.json_path), root)

    def update_internet_status():
        status = dmc.get_internet_status()
        if status == 1:
            center_var.set("Internet status: GOOD")
            internet_label.configure(foreground="green", font=("Segoe UI", 14))
        elif status == 0:
            center_var.set("Internet status: DOWN")
            internet_label.configure(foreground="red", font=("Segoe UI", 14))
        else:
            center_var.set("Internet status")
            internet_label.configure(foreground="white", font=("Segoe UI", 12))
        
        # Safety check before scheduling next update
        if root is not None:
            try:
                if root.winfo_exists():
                    root.after(5000, update_internet_status)
            except tk.TclError:
                pass
    update_internet_status()

    def _update_quts() -> None:
        running = QutsController.is_service_running("QUTS")
        quts_stat_var.set(f"QUTS: {'Running' if running else 'Stopped'}")
        quts_label.config(fg=white_accent if running else red_accent)
        
        # Safety check before scheduling next update
        if root is not None:
            try:
                if root.winfo_exists():
                    root.after(3_000, _update_quts)
            except tk.TclError:
                pass
    _update_quts()

    # ── MAIN PAGE ────────────────────────────────────────────────────────────
    HomePage.create_Home_Page(container, pages, add_nav, root)


    # ── QUTS page ────────────────────────────────────────────────────────────
    QutsPage.create_Quts_Page(container, pages, add_nav)

    # ── WIFI CONFIG page ─────────────────────────────────────────────────────
    WifiRenamePage.create_wifi_renaming_page(container, pages, add_nav)

    # ── Speed test page ──────────────────────────────────────────────────────
    SpeedTestPage.create_speed_Test_page(container, pages, add_nav)

    # ── QSTAF installer page ─────────────────────────────────────────────────
    QSTAFDappInstallerPage. create_Qstaf_dapp_install_page(container, pages, add_nav)

    # ── CPE data monitor page ────────────────────────────────────────────────
    DataMonitorPage.create_data_monitor_page(container, pages, add_nav)

     # ── CPE config monitor page ────────────────────────────────────────────────
    DeviceConfigurationPage.create_device_Configuaration_page(container, pages, add_nav, meta_var.get().split(': ')[1])
    
     # ── CPE config monitor page ────────────────────────────────────────────────

    CrashForecastPage.create_crash_forecat_page(container,pages ,add_nav)



  
    # ── Launch ──────────────────────────────────────────────────────────────
    show("Main")

    def on_closing():
        global observers
        for obs in observers:
            try:
                obs.stop()
                obs.join(timeout=1)  # Wait max 1 second
            except Exception as e:
                logging.error(f"Error stopping observer: {e}")
        observers.clear()
        if root is not None:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


# ───────────────────────────────────────────────────────────────────────────

