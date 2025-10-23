# section1_page.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from GUI_modules import MetaMpssDownloadSubFrame, QSTAFDappInstallerPage
import EndToEndDevProvsioningController
from JsonHandler import load_prov_json
from Threading import *

PADDING:dict[str, int] = {"padx": 12, "pady": 8}


def getzippath(pagenme):
        filepath = QSTAFDappInstallerPage._pick_zip(pagenme)
        return filepath

def getFilePath(label_var, identifier):
        filepath = filedialog.askopenfilename(
            title=f"Select {identifier} path",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            label_var.set(filepath)
        return filepath

def getFolderPath(pagename):
    from Constants import CTM_META_DIR, CTM_MPSS_DIR
    if pagename == "Meta":
        dir = CTM_META_DIR
    elif pagename == "MPSS":
        dir = CTM_MPSS_DIR
    else :
         dir = "~"
    folderpath = filedialog.askdirectory(
        title=f"Select {pagename} folder",
        initialdir=dir
    )
    return folderpath
    
def Meta_page(parent,Pagename,device_name):

    Meta_frame = MetaMpssDownloadSubFrame.create_Meta_Mpss_download(parent, Pagename, device_name)

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
        text="Select Meta path to load",
        command=lambda: start_thread(EndToEndDevProvsioningController.load_meta_from_path,"Meta install Thread",
                                     daemon=True, filepath=getFolderPath(Pagename))
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    button = ttk.Button(
        top_row,
        text="select Meta zip to load",
        command=lambda:start_thread(EndToEndDevProvsioningController.load_meta_from_zip,"Meta install from ZIP Thread",
                                    daemon=True, filepath=getzippath(Pagename))
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    return Meta_frame



def Mpss_page(parent,Pagename,device_name) -> ttk.Frame:
    Mpss_frame= MetaMpssDownloadSubFrame.create_Meta_Mpss_download(parent, Pagename, device_name)
    Selection_frame = ttk.LabelFrame(Mpss_frame, text=f"Select MPSS to install")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='MPSS not selected')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="Select MPSS path to load",
        command=lambda: start_thread(EndToEndDevProvsioningController.load_mpss_from_path,"MPSS install Thread",
                                     daemon=True, filepath=getFolderPath(Pagename))
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    button = ttk.Button(
        top_row,
        text="Select MPSS zip to load",
        command=lambda:start_thread(EndToEndDevProvsioningController.load_mpss_from_zip,"MPSS install from ZIP Thread",
                                    daemon=True, filepath=getzippath(Pagename))
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    return Mpss_frame


def QCN_page(parent, Pagename, device_name) -> ttk.LabelFrame:
    QCN_frame = ttk.LabelFrame(parent, text=f"Select QCN to install")
    QCN_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(QCN_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))


    button = ttk.Button(
        top_row,
        text="Load QCN",
        command=lambda:start_thread(EndToEndDevProvsioningController.load_qcn, "QCN install Thread", daemon=True)
    )
    button.pack(fill="x", padx=(0, 10))
    
    return QCN_frame
    
def MBN_page(parent, Pagename, device_name)-> ttk.LabelFrame :
    Choices = ["TMO", "ATT", "VZW"]

    MBN_frame = ttk.LabelFrame(parent, text=f"Select MBN to install")
    MBN_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(MBN_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    dropdown_var = ttk.Combobox(top_row, values=Choices, state="readonly")
    dropdown_var.pack(expand=True, fill="x", padx=6, pady=6)
    dropdown_var.current(0)  # Set default selection
    

    button = ttk.Button(
        top_row,
        text="Activate MBN",
        command=lambda:start_thread(EndToEndDevProvsioningController.activate_mbn, "MBNs install Thread", daemon=True, operator=dropdown_var.get())
    )
    button.pack(fill="x", padx=(0, 10))

    # button = ttk.Button(
        # top_row,
        # text="Deactivate MBN",
        # command=lambda:EndToEndDevProvsioningController.deactivate_mbn(dropdown_var.get()),
    # )
    # button.pack(fill="x", padx=(0, 10))
    
    return MBN_frame
    
def NV_page(parent, Pagename, device_name)-> ttk.LabelFrame :
    NV_frame = ttk.LabelFrame(parent, text=f"Select NV's to install")
    NV_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(NV_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))


    button = ttk.Button(
        top_row,
        text="Load NV",
        command=lambda:start_thread(EndToEndDevProvsioningController.write_nv, "NVs install Thread", daemon=True)
    )
    button.pack(fill="x", padx=(0, 10))
    
    return NV_frame

def Full_Provisioning_page(parent, Pagename, device_name)-> ttk.LabelFrame :
    Full_Provisioning_frame = ttk.LabelFrame(parent, text=f"Full Provisioning")
    Full_Provisioning_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Full_Provisioning_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))


    button = ttk.Button(
        top_row,
        text="Full Provisioning",
        command=lambda:start_thread(EndToEndDevProvsioningController.full_provisioning, "Full Provisioning Thread", daemon=True)
    )
    button.pack(fill="x", padx=(0, 10))
    
    return Full_Provisioning_frame


def FOTA_page(parent, Pagename, device_name) -> ttk.LabelFrame:

    FOTA_frame = ttk.LabelFrame(parent, text=f"FOTA")
    FOTA_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(FOTA_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='FOTA zip not selected')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", anchor="w", padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="FOTA",
        command=lambda: start_thread(EndToEndDevProvsioningController.load_fota,"Fota Thread" ,daemon=True, filepath=getzippath(local_path))
    )
    button.pack(fill="x", padx=(0, 10))

    return FOTA_frame
    
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


    