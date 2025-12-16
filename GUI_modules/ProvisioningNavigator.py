# section1_page.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from GUI_modules import MetaMpssDownloadSubFrame, QSTAFDappInstallerPage
from Constants import CTM_META_DIR, CTM_MPSS_DIR,CTM_DAPP_DIR
from EndToEndDevProvsioningController import *
from JsonHandler import load_prov_json
from Threading import *

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

update_config_display=None



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
   
    if pagename == "Meta":
        dir = CTM_META_DIR
    elif pagename == "Mpss":
        dir = CTM_MPSS_DIR
    else:
        dir=""

    folderpath = filedialog.askdirectory(
        title=f"Select {pagename} folder",
        initialdir=dir
    )
    return folderpath
    
def Meta_page(parent,Pagename,device_name):
    
    status_text_Meta = tk.StringVar(value="")

    Meta_frame = MetaMpssDownloadSubFrame.create_Meta_Mpss_download(parent, Pagename, device_name,status_text_Meta)

    Selection_frame = ttk.LabelFrame(Meta_frame, text=f"Select Meta to install")
    Selection_frame.pack(fill="x", **PADDING) # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='Pls select Meta path')
    print(f"StringVar value: {local_path.get()}")  # Debug print

    label = ttk.Label(top_row, textvariable=local_path, wraplength=300)
    label.pack(side="left", padx=(10, 0), fill="x", expand=True)

    # Buttons container frame (stays on right)
    button_frame = tk.Frame(top_row)
    button_frame.pack(side="right", padx=(0, 10))

    # button2 = ttk.Button(
        # button_frame,
        # text="select Meta zip to load",
        # command=lambda: start_thread(load_meta_from_zip, "Meta install from ZIP Thread",
                                    # daemon=True, filepath=getzippath(Pagename), Pgname=Pagename,status_lable=status_text_Meta)
    # )
    # button2.pack(side="right", padx=(5, 0))

    button1 = ttk.Button(
        button_frame,
        text="Select Meta path to load",
        command=lambda: start_thread(load_meta_from_path, "Meta install Thread",
                                    daemon=True, filepath=getFolderPath(Pagename), Pgname=Pagename)
    )
    button1.pack(side="right", padx=(0, 5))
    
    Bottom_frame = ttk.Frame(Meta_frame)
    Bottom_frame.pack(fill="x", **PADDING)

   
    status_label_Meta = tk.Label(Bottom_frame, textvariable=status_text_Meta,
                            foreground="white")  # Add background color
    status_label_Meta.pack(fill="x",side="left", padx=10, pady=(30,0))
    return Meta_frame



def Mpss_page(parent, Pagename, device_name) -> ttk.Frame:
    
    status_text_mpss = tk.StringVar(value="")
    
    Mpss_frame = MetaMpssDownloadSubFrame.create_Meta_Mpss_download(parent, Pagename, device_name,status_text_mpss)
    Selection_frame = ttk.LabelFrame(Mpss_frame, text=f"Select MPSS to install")
    Selection_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(Selection_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    # Create StringVar at parent level so it persists
    local_path = tk.StringVar(value='Pls selcect MPSS path')
    ttk.Label(top_row, textvariable=local_path).pack(side="left",expand=True, padx=(10, 0))

    button = ttk.Button(
        top_row,
        text="Select MPSS path to load",
        command=lambda: start_thread(load_mpss_from_path,"MPSS install Thread",daemon=True,filepath=getFolderPath(Pagename),Pgname=Pagename,
          #  text_var=local_path   Pass the StringVar to the thread
        )
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    # button = ttk.Button(
        # top_row,
        # text="Select MPSS zip to load",
        # command=lambda: start_thread(
            # load_mpss_from_zip,
            # "MPSS install from ZIP Thread",
            # daemon=True,
            # filepath=getzippath(Pagename),
            # Pgname=Pagename,
            # status_lable=status_text_mpss
           # # text_var=local_path   Pass the StringVar to the thread
        # )
    # )
    # button.pack(side="right", anchor="e", padx=(0, 10))
    
    
    Bottom_frame = ttk.Frame(Mpss_frame)
    Bottom_frame.pack(fill="x", **PADDING)


    status_label_mpss = tk.Label(Bottom_frame, textvariable=status_text_mpss,
                            foreground="white")  # Add background color
    status_label_mpss.pack(fill="x",side="left", padx=10, pady=(30,0))
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
        command=lambda:start_thread(load_qcn, "QCN install Thread", daemon=True)
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
        command=lambda:start_thread(activate_mbn, "MBNs install Thread", daemon=True, operator=dropdown_var.get() ,Pgname=Pagename)
    )
    button.pack(fill="x", padx=(0, 10))

    # button = ttk.Button(
        # top_row,
        # text="Deactivate MBN",
        # command=lambda:deactivate_mbn(dropdown_var.get()),
    # )
    # button.pack(fill="x", padx=(0, 10))
    
    return MBN_frame
    
def NV_page(parent, Pagename, device_name) -> ttk.LabelFrame:
    NV_frame = ttk.LabelFrame(parent, text=f"Current NV's Config")
    NV_frame.pack(fill="x", **PADDING)  # type: ignore
    
    # Create Treeview for table display
    tree_frame = tk.Frame(NV_frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create Treeview with columns
    tree = ttk.Treeview(tree_frame, columns=("NV Item", "Value"), show="headings", height=8)
    tree.grid(row=0, column=0, sticky="nsew")
    
    # Add vertical scrollbar
    scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar_y.set)
    
    # Add horizontal scrollbar
    scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    tree.configure(xscrollcommand=scrollbar_x.set)
    
    # Configure grid weights so the treeview expands
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    # Define column headings
    tree.heading("NV Item", text="NV Item")
    tree.heading("Value", text="Value")
    
    # Define column widths - increased for long values
    tree.column("NV Item", width=150, anchor="w", stretch=False)
    tree.column("Value", width=700, anchor="w", stretch=True)  # Allow stretching for long values
    
    def get_NVForConnectedDevice():
        # Clear all existing rows in the table
        tree.delete(*tree.get_children())
        config = get_device_config_txt()
        print(config)
        
        # Display NV items in table
        if not config:
            # Insert "No device Connected" message
            tree.insert("", "end", values=("No device Connected", ""))
        else:
            # Insert each NV item as a row
            for key, value in config.items():
                if key == "NV":
                    # Handle list of NV items
                    if isinstance(value, list):
                        for nv_entry in value:
                            # Parse "Item=453 Value=0" format
                            if "Item=" in nv_entry and "Value=" in nv_entry:
                                try:
                                    # Split to extract Item number and Value
                                    item_part = nv_entry.split("Value=")[0].strip()
                                    value_part = nv_entry.split("Value=")[1].strip()
                                    item_num = item_part.replace("Item=", "").strip()
                                    tree.insert("", "end", values=(item_num, value_part))
                                except:
                                    # Fallback if parsing fails
                                    tree.insert("", "end", values=("NV", nv_entry))
                            else:
                          
                                tree.insert("", "end", values=("NV", nv_entry))
                    else:
                        # Single NV item (shouldn't happen with updated parser, but just in case)
                        if "Item=" in value and "Value=" in value:
                            try:
                                item_part = value.split("Value=")[0].strip()
                                value_part = value.split("Value=")[1].strip()
                                item_num = item_part.replace("Item=", "").strip()
                                tree.insert("", "end", values=(f"Item {item_num}", value_part))
                            except:
                                tree.insert("", "end", values=("NV", value))
                        else:
                            tree.insert("", "end", values=("NV", value))
    
    # For initial run
    get_NVForConnectedDevice()
    
    RefreshTableButtonFrame = ttk.Frame(NV_frame)
    RefreshTableButtonFrame.pack(fill="x", **PADDING)  # type: ignore
    
    button = ttk.Button(
        RefreshTableButtonFrame,
        text="Refresh NV Table",
        command=lambda: get_NVForConnectedDevice()
    )
    button.pack(fill="x", padx=(0, 10))
    
    separator_frame = tk.Frame(NV_frame)
    separator_frame.pack(fill="x", padx=10, pady=10)
    ttk.Separator(separator_frame, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    

    cfg = load_prov_json()
    script_path = cfg.get("provisioning_path", "Configuration file not found")
    if script_path !="Configuration file not found":
        # Ensures the return value is treated as a string
        script_path = "NV Config file Path:- "+script_path + "/QCN/" + "ADB_ID"

    print(script_path)

    
    # NV Path display row
    row = tk.Frame(NV_frame)
    row.pack(side='top', fill='x', padx=5, pady=5)

    ttk.Label(row, text=script_path).pack(side='left', padx=5)
    
    

    # Call update function to populate the label
    
    
    separator_frame2 = tk.Frame(NV_frame)
    separator_frame2.pack(fill="x", padx=10, pady=10)
    ttk.Separator(separator_frame2, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(NV_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))
    
    button = ttk.Button(
        top_row,
        text="Load NV",
        command=lambda: start_thread(write_nv, "NVs install Thread", daemon=True)
    )
    button.pack(fill="x", padx=(0, 10))
    
    

    
    return NV_frame


def EFS_page(parent, Pagename, device_name) -> ttk.LabelFrame:

    EFS_frame = ttk.LabelFrame(parent, text=f"EFS")
    EFS_frame.pack(fill="x", **PADDING)  # type: ignore

    # First row: label (left), button (right) in a horizontal frame
    top_row = tk.Frame(EFS_frame)
    top_row.pack(fill="x", padx=10, pady=(10, 0))

    local_path = tk.StringVar(value='Select dev:')
    label = ttk.Label(top_row, textvariable=local_path)
    label.pack(side="left", padx=(10, 0))
    

    ttk.Label(top_row,
              text="Select Device:"
              ).pack(side="left",padx=(10,0))
    
    toggle_var = tk.StringVar(value="")
    
    ttk.Radiobutton(
        top_row,
        text="Kobuk",
        variable=toggle_var,
        value="Kobuk",
    ).pack(side="right", fill="x", padx=6, pady=6)

  
    ttk.Radiobutton(
        top_row,
        text="SDx75",
        variable=toggle_var,
        value="SDx75",
    ).pack(side="right",  fill="x", padx=6, pady=6)
    
    
    EFS_selection_row = tk.Frame(EFS_frame)
    EFS_selection_row.pack(fill="x", padx=10, pady=(10, 0))
    
    meta_checkbox_var = tk.IntVar()

    # Checkbox
    meta_checkbox = tk.Checkbutton(
        Meta_row,
        selectcolor="black",
        variable=meta_checkbox_var
    )
    meta_checkbox.pack(side="left", padx=(10, 5))

    # Label next to checkbox
    ttk.Label(Meta_row, text="Select META:").pack(side="left", padx=(0, 10))
    
    
    
   

    return EFS_frame


def Full_Provisioning_page(parent, Pagename, device_name)-> ttk.LabelFrame :
    status_text_FullPov= tk.StringVar(value="")
    
    Full_Provisioning_frame = ttk.LabelFrame(parent, text=f"Full Provisioning")
    Full_Provisioning_frame.pack(fill="x", **PADDING)  # type: ignore
         

    # Meta selection section 
    Meta_row= tk.Frame(Full_Provisioning_frame)
    Meta_row.pack(fill="x", padx=10, pady=10)

    # to store checkbox state
    meta_checkbox_var = tk.IntVar()

    # Checkbox
    meta_checkbox = tk.Checkbutton(
        Meta_row,
        selectcolor="black",
        variable=meta_checkbox_var
    )
    meta_checkbox.pack(side="left", padx=(10, 5))

    # Label next to checkbox
    ttk.Label(Meta_row, text="Select META:").pack(side="left", padx=(0, 10))
    
    button = ttk.Button(
        Meta_row,
        text="Select Meta folder",
        command=lambda: update_txt_display_lables(0)
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    # button = ttk.Button(
        # Meta_row,
        # text="select Meta zip file",
        # command=lambda: update_txt_display_lables(1)
    # )
    # button.pack(side="right", anchor="e", padx=(0, 10))


    # Mpss selection section
    Mpss_row= tk.Frame(Full_Provisioning_frame)
    Mpss_row.pack(fill="x", padx=10, pady=10)

    # to store checkbox state
    mpss_checkbox_var = tk.IntVar()

    # Checkbox
    mpss_checkbox = tk.Checkbutton(
        Mpss_row,
        selectcolor="black",
        variable=mpss_checkbox_var
    )
    mpss_checkbox.pack(side="left", padx=(10, 5))

    ttk.Label(Mpss_row,
              text="Select MPSS:"
              ).pack(side="left", padx=(0, 10))
    
    button = ttk.Button(
        Mpss_row,
        text="Select Mpss folder",
        command=lambda: update_txt_display_lables(2)
    )
    button.pack(side="right", anchor="e", padx=(0, 10))

    # button = ttk.Button(
        # Mpss_row,
        # text="select Mpss zip file",
        # command=lambda: update_txt_display_lables(3)
    # )
    # button.pack(side="right", anchor="e", padx=(0, 10))


    # MBN selection section
    MBN_row= tk.Frame(Full_Provisioning_frame)
    MBN_row.pack(fill="x", padx=10, pady=10)

    ttk.Label(MBN_row,
              text="Select MBN:"
              ).pack(side="left",padx=(10,0))
    
    toggle_var = tk.StringVar(value="TMO")
    
    ttk.Radiobutton(
        MBN_row,
        text="ATT",
        variable=toggle_var,
        value="ATT",
    ).pack(side="right", fill="x", padx=6, pady=6)

  
    ttk.Radiobutton(
        MBN_row,
        text="VZW",
        variable=toggle_var,
        value="VZW",
    ).pack(side="right",  fill="x", padx=6, pady=6)
   
 
    ttk.Radiobutton(
        MBN_row,
        text="TMO",
        variable=toggle_var,
        value="TMO",
    ).pack(side="right", fill="x", padx=6, pady=6)


    def on_toggle_change(*args):
        activate_mbn(toggle_var.get() ,Pgname="")
        update_config_display()

    toggle_var.trace_add("write", on_toggle_change)

    #display current selected meta and mpss

    separator_frame = tk.Frame(Full_Provisioning_frame)
    separator_frame.pack(fill="x", padx=10, pady=10)

    ttk.Separator(separator_frame, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(0, 5))
    ttk.Label(separator_frame, text="Configuration Details", font=("Arial", 10, "bold")).pack(side="left")
    ttk.Separator(separator_frame, orient="horizontal").pack(side="left", fill="x", expand=True, padx=(5, 0))

    Current_Config_display_row = tk.Frame(Full_Provisioning_frame)
    Current_Config_display_row.pack(fill="x", padx=10, pady=10)

    

   # Initialize StringVars once (at the top level)
    meta_var = tk.StringVar()
    mpss_var = tk.StringVar()
    mbn_var = tk.StringVar()
    imei_var = tk.StringVar()

    # Create labels once (during UI setup)

    ttk.Label(Current_Config_display_row, textvariable=meta_var).grid(row=0, column=0, sticky="w", padx=10, pady=2)
    ttk.Label(Current_Config_display_row, textvariable=mpss_var).grid(row=1, column=0, sticky="w", padx=10, pady=2)
    ttk.Label(Current_Config_display_row, textvariable=mbn_var).grid(row=2, column=0, sticky="w", padx=10, pady=2)
    ttk.Label(Current_Config_display_row, textvariable=imei_var).grid(row=3, column=0, sticky="w", padx=10, pady=2)

    # Update function just changes the StringVar values
    def update_config_display():
        meta_mpss_config = get_data_Meta_Mpss_txt()
        config = get_device_config_txt()

        from WifiController import get_meta_build_info
        meta_build = get_meta_build_info()

        if isinstance(meta_build, str) and 'kobuk' in meta_build.lower():
            meta_var.set(f"Meta selected :- {meta_mpss_config.get('DE9.0_KOBUK_META', 'N/A')}")
            mpss_var.set(f"MPSS selected :- {meta_mpss_config.get('DE9.0_KOBUK_MPSS', 'N/A')}")
            mbn_var.set(f"MBN selected  :- {meta_mpss_config.get('MBN_SW', 'N/A')}")
            imei_var.set(f"IMEI :- {config.get('IMEI', 'N/A')}")

        elif isinstance(meta_build, str) and 'pinnacles' in meta_build.lower():
            meta_var.set(f"Meta selected :- {meta_mpss_config.get('DE7.0_PINNACLES_META', 'N/A')}")
            mpss_var.set(f"MPSS selected :- {meta_mpss_config.get('DE7.0_PINNACLES_MPSS', 'N/A')}")
            mbn_var.set(f"MBN selected  :- {meta_mpss_config.get('MBN_SW', 'N/A')}")
            imei_var.set(f"IMEI :- {config.get('IMEI', 'N/A')}")

        else:
            meta_var.set(f"Meta selected :- UNKNOWN (Bad device state)")
            mpss_var.set(f"MPSS selected :- UNKNOWN (Bad device state)")
            mbn_var.set(f"MBN selected  :- {meta_mpss_config.get('MBN_SW', 'N/A')}")
            imei_var.set(f"IMEI :- {config.get('IMEI', 'N/A')}")


    # Initial call
    update_config_display()


    def update_txt_display_lables(value: int):
        if value == 0:
            start_thread(load_meta_from_path, "Meta update txt Thread", 
                        daemon=True, filepath=getFolderPath("Meta"), Pgname="",
                        callback=update_config_display)
        elif value == 1:
            start_thread(load_meta_from_zip, "Meta update txt ZIP Thread",
                        daemon=True, filepath=getzippath("Meta"), Pgname="",status_lable=status_text_FullPov,
                        callback=update_config_display)
        elif value == 2:
            start_thread(load_mpss_from_path, "Mpss update txt Thread",
                        daemon=True, filepath=getFolderPath("Mpss"), Pgname="",
                        callback=update_config_display)
        elif value == 3:
            start_thread(load_mpss_from_zip, "Meta update txt ZIP Thread",
                        daemon=True, filepath=getzippath("Mpss"), Pgname="",status_lable=status_text_FullPov,
                        callback=update_config_display)

        


   # Full prov button 
    bottom_row = tk.Frame(Full_Provisioning_frame)
    bottom_row.pack(fill="x", padx=10, pady=(10, 0))


    button = ttk.Button(
        bottom_row,
        text="Full Provisioning",
        command=lambda:start_thread(
            full_provisioning,
            "Full Provisioning Thread",
            daemon=True,
            meta_selection=meta_checkbox_var.get(),
            mpss_selection=mpss_checkbox_var.get()
        )
    )
    button.pack(fill="x", padx=(0, 10))
     
    Bottom_frame = ttk.Frame(Full_Provisioning_frame)
    Bottom_frame.pack(fill="x", **PADDING)


    status_label_mpss = tk.Label(Bottom_frame, textvariable=status_text_FullPov,
                            foreground="white")  # Add background color
    status_label_mpss.pack(fill="x",side="left", padx=10, pady=(30,0))
    
    
    
    return Full_Provisioning_frame



'''
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
        command=lambda: start_thread(load_fota,"Fota Thread" ,daemon=True, filepath=getzippath(local_path))
    )
    button.pack(fill="x", padx=(0, 10))

    return FOTA_frame
'''
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


    