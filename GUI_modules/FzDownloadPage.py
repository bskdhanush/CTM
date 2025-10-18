import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import JsonHandler
import FzHandler

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def _get_download_path() -> str:
    return str(JsonHandler.load_cfg().get("Local_downloadPath", ""))

def create_Meta_Mpss_download(container, Pagename, device_name) -> ttk.Frame:
    print(f"Meta/Mpss selected: {device_name}")
 

    # MMdownload= ttk.Frame(container)
    # MMdownload.grid(row=0, column=0, sticky="nsew")
    # pages["MMdownload"] = MMdownload
    # add_nav("Meta/Mpss ⇩ ", "MMdownload")

    MMdownload = ttk.Frame(container)

    def get_current_files():
        try:
            items = FzHandler.list_files(device_name, Pagename)
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
        return bool(JsonHandler.load_cfg().get("Auto_download", False))

    def toggle_auto_downloader() -> None:
        cfg = JsonHandler.load_cfg()
        cfg["Auto_download"] = bool(auto_download_checkBox.get())
        JsonHandler.save_json(cfg)


    def download_selected_Meta_Mpss():
        selected_indices = file_listbox.curselection()
        if selected_indices:
            selected_item = file_listbox.get(selected_indices[0])
            print(local_path.get(),selected_item)
            FzHandler.download_file( selected_item,local_path.get())

    # Manual download section
    Selection_frame = ttk.LabelFrame(MMdownload, text=f"Select and download {Pagename} files")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='Path not selected')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="Choose download path…",
        command=lambda: browse_path(),
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

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
    refresh_table_row = tk.Frame(bottom_section)
    refresh_table_row.pack(fill="x")

    Refresh_btn = ttk.Button(refresh_table_row, text="Refresh Table", command=get_current_files)
    Refresh_btn.pack(side="left")
   
    sub_string = tk.StringVar(value="Enter a sub string to search")
   
   
    ttk.Button(
        refresh_table_row,
        text="Get Data",
        command=lambda:sub_string.get(),
    ).pack(side="right", padx=(8,8)) # type: ignore
    
    ttk.Entry(
        refresh_table_row,
        textvariable=sub_string,
        width=30
    ).pack(side="right")




    
    
    auto_download_checkBox = tk.BooleanVar(value=_is_auto_download_enabled())
    ttk.Checkbutton(
        bottom_section,
        text="Enable auto download",
        variable=auto_download_checkBox,
        command=toggle_auto_downloader
    ).pack(anchor="w", pady=(8, 0))

    # Right side: Download button
    select_btn = ttk.Button(bottom_section, text="Download", command=download_selected_Meta_Mpss)
    select_btn.pack( anchor="e")

    return MMdownload