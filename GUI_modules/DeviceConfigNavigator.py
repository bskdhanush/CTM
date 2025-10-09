# section1_page.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from GUI_modules import Get_Downlaod_MetaMpss, QSTAFDappInstallerPage
import EndToEndDevProvsioningController

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def Meta_page(parent,Pagename,device_name):

    Meta_frame=Get_Downlaod_MetaMpss.create_Meta_Mpss_downlaod(parent, Pagename, device_name)

    Selection_frame = ttk.LabelFrame(Meta_frame, text=f"Select Meta to install")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='Meta not selected')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="select Meta file",
        command=lambda:getzippath(),
    )
    button.pack(side="right", anchor="e", padx=(0, 10))


    def getzippath():
        filepath = QSTAFDappInstallerPage._pick_zip()
        local_path.set(filepath)
        # unzip the file and set the path in end to end device script
        EndToEndDevProvsioningController.set_meta_file_path(filepath)




    return Meta_frame



def Mpss_page(parent,Pagename,device_name) -> ttk.Frame:
    Mpss_frame= Get_Downlaod_MetaMpss.create_Meta_Mpss_downlaod(parent, Pagename, device_name)
    Selection_frame = ttk.LabelFrame(Mpss_frame, text=f"Select Meta to install")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='Meta not selected')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="select Meta file",
        command=lambda:getzippath(),
    )
    button.pack(side="right", anchor="e", padx=(0, 10))


    def getzippath():
        filepath = QSTAFDappInstallerPage._pick_zip()
        local_path.set(filepath)
        # unzip the file and set the path in end to end device script
        EndToEndDevProvsioningController.set_mpss_file_path(filepath)


    return Mpss_frame






"""
    Returns a frame containing:
      - An entry showing selected text file path
      - A 'Browse...' button to choose a .txt file
    
    fr = ttk.Frame(parent)
    fr.columnconfigure(0, weight=1)

    file_var = tk.StringVar(value="No file selected")
    entry = ttk.Entry(fr, textvariable=file_var)
    entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

    def choose_file():
        path = filedialog.askopenfilename(
            title="Select a text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            file_var.set(path)

    browse_btn = ttk.Button(fr, text="Browse…", command=choose_file)
    browse_btn.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
    """


    