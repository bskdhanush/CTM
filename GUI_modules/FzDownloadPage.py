import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import customtkinter as ctk

from JsonHandler import load_cfg,load_prov_json, save_json
import FzHandler

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def _get_download_path() -> str:
    return str(load_cfg().get("Local_downloadPath", ""))

def create_Meta_Mpss_download(container, Pagename, device_name) -> ttk.Frame:
    
    # MMdownload= ttk.Frame(container)
    # MMdownload.grid(row=0, column=0, sticky="nsew")
    # pages["MMdownload"] = MMdownload
    # add_nav("Meta/Mpss ⇩ ", "MMdownload")

    MMdownload = ttk.Frame(container)

    def get_current_files(sub_string):
        try:
            items = FzHandler.list_files(device_name, Pagename, sub_string)
            file_listbox.delete(0, tk.END)
            for item in items:
                file_listbox.insert(tk.END, item["name"])
        except Exception as e:
            print(f'Exception during list_files: {e}')
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


    def _is_auto_download_enabled() -> bool:
        #print("entered auto download check")
        return bool(load_cfg().get("Auto_download", False))

    def toggle_auto_downloader() -> None:
        cfg = load_cfg()
        cfg["Auto_download"] = bool(auto_download_checkBox.get())
        save_json(cfg)


    def download_selected_Meta_Mpss():
        selected_indices = file_listbox.curselection()
        if selected_indices:
            selected_item = file_listbox.get(selected_indices[0])
            print(local_path.get(),selected_item)
            FzHandler.download_file( selected_item,load_prov_json().get(f"{Pagename}_path"))

    # Manual download section
    Selection_frame = ttk.LabelFrame(MMdownload, text=f"Select and download {Pagename} files")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value=f'Downlaod Path:- C:\CTM\{Pagename}')
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

    Refresh_btn = ttk.Button(refresh_btn_row, text="Refresh Table", command=lambda:get_current_files(""))
    Refresh_btn.pack(side="left")

   
   
    ttk.Button(
        refresh_btn_row,
        text="Get Data",
        command=lambda:get_current_files(entry.get()),
    ).pack(side="right", padx=(8,8)) # type: ignore
    
    entry = ctk.CTkEntry(
    refresh_btn_row,
    placeholder_text="Type substring here...",
    width=200,
    height=30,
    corner_radius=6
)
    entry.pack(side="right", padx=5)
    

    download_btn_row = tk.Frame(bottom_section)
    download_btn_row.pack(fill="x", pady=(10,0))

    auto_download_checkBox = tk.BooleanVar(value=_is_auto_download_enabled())
    ttk.Checkbutton(
        download_btn_row,
        text="Enable auto download",
        variable=auto_download_checkBox,
        command=toggle_auto_downloader
    ).pack(side='left', pady=(8, 0))

    # Right side: Download button
    select_btn = ttk.Button(download_btn_row, text="Download", command=download_selected_Meta_Mpss)
    select_btn.pack( side='right')

    return MMdownload