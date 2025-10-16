import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import WifiController
from Threading import *

PADDING:dict[str, int] = {"padx": 12, "pady": 8}

def show_loading_popup(parent, msg="Processing..."):
    """Show a modal loading popup"""
    loading = tk.Toplevel(parent)
    loading.title("Please Wait")
    loading.geometry("250x120")
    loading.transient(parent)
    loading.grab_set()
    loading.resizable(False, False)
    
    # Center the popup
    loading.update_idletasks()
    x = (loading.winfo_screenwidth() // 2) - (250 // 2)
    y = (loading.winfo_screenheight() // 2) - (120 // 2)
    loading.geometry(f"250x120+{x}+{y}")
    
    ttk.Label(loading, text=msg, font=("Arial", 10)).pack(pady=20)
    
    # Add a progress bar for visual feedback
    progress = ttk.Progressbar(loading, mode='indeterminate')
    progress.pack(pady=10, padx=20, fill='x')
    progress.start(10)
    
    loading.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
    return loading

def hide_loading_popup(loading_popup):
    """Hide the loading popup"""
    if loading_popup and loading_popup.winfo_exists():
        loading_popup.destroy()

def run_wifi_command_with_loading(parent, func, msg, success_msg="Operation completed successfully!"):
    """Run a WiFi command in background thread with loading popup"""
    loading_popup = show_loading_popup(parent, msg)
    
    def worker():
        try:
            func()  # Execute the actual WiFi command
            #parent.after(0, lambda: messagebox.showinfo("Success", success_msg))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            parent.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            parent.after(0, lambda: hide_loading_popup(loading_popup))
    
    start_thread(worker,"WIFI Renaming Thread", daemon=True)


def create_wifi_renaming_page(container, pages, add_nav):

    # ── WiFi Renaming page ─────────────────────────────────────────────────────
    wifi_pg = ttk.Frame(container)
    wifi_pg.grid(row=0, column=0, sticky="nsew")
    pages["Wifi"] = wifi_pg
    add_nav("Set/Rename WIFI", "Wifi")

        # ── Toggle Options ────────────────────────────────────────────────────

    toggle_fr = ttk.LabelFrame(wifi_pg, text="Toggle Options")
    toggle_fr.pack(fill="x", **PADDING) # type: ignore

    
    OWRT_CHOICES = ("3 SLO", "2G-5G MLO", "3 MLO")
    RDKB_CHOICES = ("3 SLO", "2G SLO + 5G-6G MLO")
    Kobuk_CHOICES = ("2G SLO", "5G SLO", "6G SLO", "2G-5G MLO", "3 MLO")

    toggle_var = tk.StringVar(value="OWRT")

    # Two radiobuttons share the same StringVar, so only one can be “on” at a time


    ttk.Radiobutton(
        toggle_fr,
        text="OWRT (ATT)",
        variable=toggle_var,
        value="OWRT",
    ).pack(side="left", expand=True, fill="x", padx=6, pady=6)

    ttk.Radiobutton(
        toggle_fr,
        text="RDKB (TMO)",
        variable=toggle_var,
        value="RDKB",
    ).pack(side="left", expand=True, fill="x", padx=6, pady=6)
   
    ttk.Radiobutton(
        toggle_fr,
        text="Kobuk",
        variable=toggle_var,
        value="Kobuk",
    ).pack(side="left", expand=True, fill="x", padx=6, pady=6)



    wifi_sel = ttk.LabelFrame(wifi_pg, text="Select Config Type" )
    wifi_sel.pack(fill="x", **PADDING)# type: ignore

    wifi_dd = ttk.Combobox(wifi_sel, state="readonly")
    wifi_dd.pack(padx=20, pady=10)

    def _update_choices(*_):
        if toggle_var.get() == "OWRT":
           choices = OWRT_CHOICES
        elif toggle_var.get() == "RDKB":
            choices = RDKB_CHOICES
        elif toggle_var.get() == "Kobuk":
            choices = Kobuk_CHOICES
        else:
            choices = []
        wifi_dd.configure(values=choices)
        # Set current value to first choice if not in choices
        cur = wifi_dd.get()
        wifi_dd.set(cur if cur in choices and cur else choices[0])

    toggle_var.trace_add("write", _update_choices)
    _update_choices() 


    ttk.Button(
    wifi_sel,
    text="Set config",
    command=lambda: run_wifi_command_with_loading(
        wifi_pg,
        lambda: WifiController.update_cpe_wifi_config(toggle_var.get(), wifi_dd.current(), "Config_SSID"),
        "Applying WiFi Configuration...",
        "WiFi configuration applied successfully!"
    ),
    ).pack(fill="x", **PADDING)# type: ignore


    test_sel = ttk.LabelFrame(wifi_pg, text="This is to rename SSIDs before Speedtest")
    test_sel.pack(fill="x", **PADDING )# type: ignore  


    ttk.Button(
    test_sel,
    text="Set Test SSID",
    command=lambda: run_wifi_command_with_loading(
        wifi_pg,
        lambda: WifiController.update_cpe_wifi_config(toggle_var.get(), wifi_dd.current(), "Test_SSID"),
        "Setting Test SSID...",
        "Test SSID configured successfully!"
    ),
    ).pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
    test_sel,
    text="Set Default SSID",
    command=lambda: run_wifi_command_with_loading(
        wifi_pg,
        lambda: WifiController.update_cpe_wifi_config(toggle_var.get(), wifi_dd.current(), "Default_SSID"),
        "Restoring Default SSID...",
        "Default SSID restored successfully!"
    ),
    ).pack(fill="x", **PADDING)# type: ignore


    return wifi_pg