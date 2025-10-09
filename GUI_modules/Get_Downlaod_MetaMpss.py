import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import JsonHandler
import Metapull_fst

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def _get_download_path() -> str:
    return str(JsonHandler.load_cfg().get("Local_downloadPath", ""))





def create_Meta_Mpss_downlaod(container, Pagename, device_name) -> ttk.Frame:
    print(f"Meta/Mpss selected: {device_name}")

    items = Metapull_fst.list_files("Kobuk", Pagename)

    # MMdownload= ttk.Frame(container)
    # MMdownload.grid(row=0, column=0, sticky="nsew")
    # pages["MMdownload"] = MMdownload
    # add_nav("Meta/Mpss ⇩ ", "MMdownload")

    MMdownload = ttk.Frame(container)

   

    def browse_path():
        # Open directory selection dialog
        selected_path = filedialog.askdirectory(title="Select Folder")
        if not selected_path:
            local_path.set(selected_path) # Return default if no selection
            print(f"Not selected: {selected_path}" )
        else:
            local_path.set(selected_path)
            print(f"Selected path: {selected_path}")


    def _is_auto_downlaod_enabled() -> bool:
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
            Metapull_fst.download_file( selected_item,local_path.get())

        



    # Manula download section
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

   
    if items is None:
        print("No items found on the server.")
        items = []

    for item in items:
        print(f"Found item: {item}")
        file_listbox.insert(tk.END, item["name"])

    

    # Centered download button below the list
    separator = ttk.Separator(Selection_frame, orient='horizontal')
    separator.pack(fill='x', padx=100, pady=(12,0))


    select_btn = ttk.Button(Selection_frame, text="Download", command=download_selected_Meta_Mpss)
    select_btn.pack(pady=(15, 10))
    select_btn.pack_configure(anchor="center")

    auto_download_checkBox = tk.BooleanVar(value=_is_auto_downlaod_enabled())

    ttk.Checkbutton(
    Selection_frame,
    text="Enable auto download",
    variable=auto_download_checkBox,
    command=toggle_auto_downloader
    ).pack(side="left", padx=16)
                

    return MMdownload