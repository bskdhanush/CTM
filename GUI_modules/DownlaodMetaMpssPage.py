import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

PADDING:dict[str, int] = {"padx": 12, "pady": 8}





def create_Meta_Mpss_downlaod(container, pages, add_nav):

    MMdownload= ttk.Frame(container)
    MMdownload.grid(row=0, column=0, sticky="nsew")
    pages["MMdownload"] = MMdownload
    add_nav("Meta/Mpss ⇩ ", "MMdownload")

    download_frame = ttk.LabelFrame(MMdownload, text="Download Meta/Mpss")
    download_frame.pack(fill="x", **PADDING) # type: ignore

    path_lable  = tk.StringVar(value='Path not selected')
    ttk.Label(
        download_frame,
        textvariable=path_lable,
        anchor="w",
        style="Hint.TLabel",
    ).pack(side="left", fill="x", expand=True,padx=(20, 0))  # type: ignore

    ttk.Button(
        download_frame,
        text="Choose download path…",
        command=lambda: browse_path(),
    ).pack(fill="x", **PADDING)  # type: ignore


    def browse_path():
        # Open directory selection dialog
        selected_path = filedialog.askdirectory(title="Select Folder")
        if not selected_path:
            path_lable.set(selected_path) # Return default if no selection
            print(f"Not selected: {selected_path}" )
        else:
            path_lable.set(selected_path)
            print(f"Selected path: {selected_path}")


   
    