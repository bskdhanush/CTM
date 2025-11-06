import logging
import time
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import customtkinter as ctk
import schedule

from JsonHandler import load_cfg,load_prov_json, save_json
from AutoDownloader import checK_for_new_meta,checK_for_new_CSV
import FzHandler
from Threading import start_thread

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

_job: schedule.Job | None = None
_loop_started = False
mtimeList=[]

# def _get_download_path() -> str:
#     return str(load_cfg().get("Local_downloadPath", ""))

def create_Meta_Mpss_download(container, Pagename, device_name, download_status_label_update) -> ttk.Frame:
    
    # MMdownload= ttk.Frame(container)
    # MMdownload.grid(row=0, column=0, sticky="nsew")
    # pages["MMdownload"] = MMdownload
    # add_nav("Meta/Mpss ⇩ ", "MMdownload")

    MMdownload = ttk.Frame(container)

    def get_current_files(pattern):
        mtimeList.clear()
        try:
            items = FzHandler.list_files(device_name, Pagename, pattern)
            file_listbox.delete(0, tk.END)
            for item in items:
                mtimeList.append(item['mtime'])
                file_listbox.insert(tk.END, item['name'])
            #print(f'timestamps: {mtimeList}')
        except Exception as e:
            print(f'Exception during list_files: {e}')
            items = []
        return items
        


    def browse_path():
        # Open directory selection dialog
        selected_path = filedialog.askdirectory(title="Select Folder")
        if not selected_path:
            local_path.set(selected_path) # Return default if no selection
            print(f"Not selected: {selected_path}" )
        else:
            local_path.set(selected_path)
            print(f"Selected path: {selected_path}")
    
    def check_for_updates():
        # Your code here
        print("Checking for updates...")
        checK_for_new_CSV(download_status_label_update)
        checK_for_new_meta(device_name,download_status_label_update)
        


    def _reschedule(enable: bool) -> None:
        """(Re)create or cancel the 30-min job."""
        global _job
        if _job:
            print("Removing the jobs")
            schedule.cancel_job(_job)
            _job = None
        if enable:
            print("Scheduling 30-min interval job")
            _job = schedule.every(30).minutes.do(check_for_updates)

    def _loop() -> None:
        """Background thread that drives `schedule`."""
        while True:
            schedule.run_pending()
            time.sleep(1)

    def _start_loop_once() -> None:
        global _loop_started
        if not _loop_started:
            start_thread(_loop,"META auto download Thresf", daemon=True)
            _loop_started = True

    def is_enabled() -> bool:
        return bool(load_cfg().get("Auto_download", False))

    def set_enabled(enable: bool) -> None:
        cfg = load_cfg()
        cfg["Auto_download"] = bool(enable)
        save_json(cfg)
        _reschedule(enable)

    def on_checkbox():
        set_enabled(auto_download_checkBox.get())


    def download_selected_Meta_Mpss():
        from Constants import CTM_META_DIR, CTM_MPSS_DIR, CTM_BASE_DIR
        selected_indices = file_listbox.curselection()
        local_dir = None
        if Pagename == 'Meta':
            local_dir = CTM_META_DIR
        if Pagename == 'Mpss':
            local_dir = CTM_MPSS_DIR

        if selected_indices:
            selected_item = file_listbox.get(selected_indices[0])
            print(local_path.get(),selected_item)
            if selected_item and selected_item.lower() == 'crashrenamingmetainfo.csv':
                local_dir = CTM_BASE_DIR
            if local_dir:
                try:
                    FzHandler.download_file(selected_item, local_dir, Pagename,download_status_label_update, mtimeList[0])
                except Exception as e:
                    print(f"printing from subpage file {e}")
            else:
                print('No valid destination path to download')

    # Manual download section
    Selection_frame = ttk.LabelFrame(MMdownload, text=f"Select and download {Pagename} files")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value=f'Download Path:- C:\CTM\{Pagename}') # type: ignore
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    # button = ttk.Button(
    #     top_row,
    #     text="Choose download path…",
    #     command=lambda: browse_path(),
    # )
    # button.pack(side="right", anchor="e", padx=(0, 10))

    # Separator below the row
    separator = ttk.Separator(Selection_frame, orient='horizontal')
    separator.pack(fill='x', padx=40, pady=(12, 12))

    # Frame for listbox and scrollbar (center)
    list_container = tk.Frame(Selection_frame)
    list_container.pack(fill="x", padx=20)

    file_listbox = tk.Listbox(
        list_container, height=5, activestyle='dotbox', font=('Segoe UI', 10),
        borderwidth=0, highlightthickness=0
    )
    file_listbox.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=file_listbox.yview)
    scrollbar.pack(side="right", fill="y")

    file_listbox.config(yscrollcommand=scrollbar.set)

    # Separator above buttons
    separator = ttk.Separator(Selection_frame, orient='horizontal')
    separator.pack(fill='x', padx=100, pady=(12, 0))

    # Bottom section with buttons and checkbox
    bottom_section = tk.Frame(Selection_frame)
    bottom_section.pack(fill="x", padx=16, pady=(15, 10))

    # Left side: Refresh button and checkbox in a vertical frame
    refresh_btn_row = tk.Frame(bottom_section)
    refresh_btn_row.pack(fill="x")

    # Refresh_btn = ttk.Button(refresh_btn_row, text="Refresh Table", command=lambda:get_current_files(""))
    # Refresh_btn.pack(side="left")

    entry = ctk.CTkEntry(
        refresh_btn_row,
        placeholder_text="Pattern to search...",
        width=200,
        height=30,
        corner_radius=6
    )
    entry.pack(side="left", padx=5)

   
   
    ttk.Button(
        refresh_btn_row,
        text="Get Data",
        command=lambda:get_current_files(entry.get()),
    ).pack(side="right", padx=(8,8)) # type: ignore
    
   
    

    download_btn_row = tk.Frame(bottom_section)
    download_btn_row.pack(fill="x", pady=(10,0))


    if Pagename=="Meta":

        auto_download_checkBox = tk.BooleanVar(value=is_enabled())
        ttk.Checkbutton(
            download_btn_row,
            text="Enable auto download",
            variable=auto_download_checkBox,
            command=on_checkbox
        ).pack(side='left', pady=(8, 0))

    # Right side: Download button
    select_btn = ttk.Button(download_btn_row, 
                            text="Download", 
                            command=lambda:start_thread(download_selected_Meta_Mpss,"Download Thread for FZ",
                                     daemon=True,))
    select_btn.pack( side='right')

    _reschedule(is_enabled())

    
   # _start_loop_once()

    return MMdownload