import tkinter as tk
from tkinter import ttk
import WifiController

PADDING:dict[str, int] = {"padx": 12, "pady": 8}
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
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Config_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    test_sel = ttk.LabelFrame(wifi_pg, text="This is to rename SSIDs before Speedtest")
    test_sel.pack(fill="x", **PADDING )# type: ignore  


    ttk.Button(
        test_sel,
        text="Set Test SSID",
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Test_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    ttk.Button(
        test_sel,
        text="Set Default SSID",
        command=lambda: WifiController.update_cpe_wifi_config(toggle_var.get(),wifi_dd.current(), "Default_SSID"),
    ).pack(fill="x", **PADDING)# type: ignore


    return wifi_pg