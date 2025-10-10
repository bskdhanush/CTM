import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import datetime as dt
import QSTAFInstaller,DappInstaller
from Threading import *

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def _pick_zip() -> str:
        filePath = filedialog.askopenfilename(
            title="Select QSTAF archive",
            filetypes=[
            ("Archives", "*.zip *.7z"),
            ("ZIP archives", "*.zip"),
            ("7z archives", "*.7z"),
            ("All files", "*.*"),
        ],
    )
        if not filePath:
            return ""
        if not filePath.lower().endswith((".zip", ".7z")):
            messagebox.showwarning("Unsupported file", "Please choose a .zip or .7z file.")
            return ""
        return filePath


def create_Qstaf_dapp_install_page(container, pages, add_nav):
# ── QSTAF update page ─────────────────────────────────────────────────────
    QSTAF_pg = ttk.Frame(container)
    QSTAF_pg.grid(row=0, column=0, sticky="nsew")
    pages["QSTAF"] = QSTAF_pg
    add_nav("Dapp/QSTAF Install", "QSTAF")
    # avaible_ver=gr.get_all_tags()

    # ver_sel = ttk.LabelFrame(QSTAF_pg, text="select the version and download")
    # ver_sel.pack(fill="x", **PADDING)# type: ignore  

    # select_ver = ttk.Combobox(ver_sel, values=avaible_ver, state="readonly")
    # select_ver.current(0)
    # select_ver.pack(padx=20, pady=10)
    # selected_zip = tk.StringVar(value="No file selected")

    # ttk.Button(
        # ver_sel,
        # text="Download",
        # command=lambda:gr.download_asset_by_tag(avaible_ver[select_ver.current()], "."),
    # ).pack(fill="x", **PADDING)# type: ignore


    Qstaf_install = ttk.LabelFrame(QSTAF_pg, text="Select and install QSTAF")
    Qstaf_install.pack(fill="x", **PADDING)  # type: ignore

# Path label (with hint style)
    selected_zip = tk.StringVar(value='No file selected — click "Choose archive…"')
    style = ttk.Style()
    style.configure("Hint.TLabel", foreground="#6b7280")

    zip_label = ttk.Label(
        Qstaf_install,
        textvariable=selected_zip,
        anchor="w",
        style="Hint.TLabel",
    )
    zip_label.pack(fill="x", **PADDING)  # type: ignore

# --- Progress  Logs ----------------------------------------------------------
    progress_var = tk.IntVar(value=0)
    progress_bar = ttk.Progressbar(Qstaf_install, maximum=100, variable=progress_var, mode="determinate")
    progress_bar.pack(fill="x", padx=16, pady=(0, 8))

    log_box = ScrolledText(Qstaf_install, height=10, wrap="word", state="disabled")
    log_box.pack(fill="both", expand=False, padx=16, pady=(0, 12))

    def _log(msg: str):
            ts = dt.datetime.now().strftime("%H:%M:%S")  # type: ignore
            log_box.configure(state="normal")
            log_box.insert("end", f"[{ts}] {msg}\n")
            log_box.see("end")
            log_box.configure(state="disabled")

    def _run_install(path: str) -> None:
        """Run QSTAF installer asynchronously and update GUI elements."""
        # Reset UI and start indeterminate progress
        progress_var.set(0)
        progress_bar.configure(mode="indeterminate")
        progress_bar.start(10)
        _log(f"Starting install for: {path}")

        top = QSTAF_pg.winfo_toplevel()

        def ui_status(msg: str):
            # Schedule status log update on the Tk main thread
            top.after(0, lambda: _log(msg))

        def ui_progress(pct: int):
            """Update determinate progress bar from 0‑100."""
            def _upd():
                # If we are still in indeterminate mode switch first
                if progress_bar['mode'] == 'indeterminate':
                    progress_bar.stop()
                    progress_bar.configure(mode='determinate')
                progress_var.set(max(0, min(100, int(pct))))
            top.after(0, _upd)

        def worker():
            ok = False
            msg = ""
            try:
                ok, msg = QSTAFInstaller.install_qstaf_from_zip(
                    path,
                    on_status=ui_status,
                    on_progress=ui_progress,
                    keep_temp=False,  # set True if you want to inspect temp folder
                )
            except Exception as e:
                ok, msg = False, str(e)
            finally:
                # Always run this to tidy the UI (no pop‑ups)
                def done():
                    progress_bar.stop()
                    progress_bar.configure(mode='determinate')
                    progress_var.set(100 if ok else 0)
                    if ok:
                        _log("Completed." if not msg else f"Completed: {msg}")
                    else:
                        _log(f"Failed: {msg or 'Unknown error.'}")
                top.after(0, done)

        start_thread(target=worker, daemon=True)

    def getSetQstafZipPath():
        filePath = _pick_zip()
        selected_zip.set(filePath)
        zip_label.configure(style="TLabel")  # switch from hint to normal
        _run_install(filePath)

    btn_row = ttk.Frame(Qstaf_install)
    btn_row.pack(fill="x", padx=16, pady=(0, 8))

    ttk.Button(btn_row, text="Choose archive…", command=getSetQstafZipPath, width=18)\
    .pack(side="left")

    def _clear_logs():
        log_box.configure(state="normal")
        log_box.delete("1.0", "end")
        log_box.configure(state="disabled")

    ttk.Button(btn_row, text="Clear logs", command=_clear_logs, width=12)\
    .pack(side="right")


   #--- Isntall Dapp --------------------------------------------------------------
    Dapp_install = ttk.LabelFrame(QSTAF_pg, text="Select and install Dapp")
    Dapp_install.pack(fill="x", **PADDING)  # type: ignore

    selected_Dapp_zip = tk.StringVar(value='No file selected — click "Choose archive…"')
    style = ttk.Style()
    style.configure("Hint.TLabel", foreground="#6b7280")

    tk.Label(Dapp_install, 
             text="Note: Make sure the device is connected via ADB before installing Dapp.", 
             fg="red",
             font=("Arial", 12),
             anchor="w"
             ).pack(fill="x", **PADDING) # type: ignore

    zip_Dapp_label = ttk.Label(
        Dapp_install,
        textvariable=selected_Dapp_zip,
        anchor="w",
        style="Hint.TLabel",
    )
    zip_Dapp_label.pack(fill="x", **PADDING)  # type: ignore

    

    def getSetDappZipPath():
        filePath = _pick_zip()
        selected_Dapp_zip.set(filePath)
        zip_Dapp_label.configure(style="TLabel")  # switch from hint to normal
        DappInstaller.InstallDapp(filePath)

    ttk.Button(Dapp_install, text="Choose archive… /Install", command=getSetDappZipPath, width=20)\
    .pack(fill="x", **PADDING)  # type: ignore  




    
    return QSTAF_pg