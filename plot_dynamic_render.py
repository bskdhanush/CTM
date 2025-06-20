import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk # type: ignore
import copy_csv
import data_monitor_controller as dmc

# keep this at module scope so state survives between calls
plot_refs: list[tuple[plt.Figure, FigureCanvasTkAgg, NavigationToolbar2Tk]] = [] # type: ignore


PLOT_FUNCS = [
    dmc.process_traffic_csv,
    dmc.rf_band_plot,
    dmc.ipa_thruput_plot,
    dmc.wifi_clients_plot,
    dmc.data_call_state_plot,
    dmc.channel_conditions_plot,
]

def clear_plots():
    """Destroy existing canvases & toolbars, close figures, and clear refs."""
    for fig, canv, toolbar in plot_refs:
        canv.get_tk_widget().destroy()
        toolbar.destroy()
        plt.close(fig)
    plot_refs.clear()

def draw_all_plots(parent_frame):
    """
    Runs each plot function in PLOT_FUNCS, embeds its Figure in parent_frame,
    and retains the (fig, canvas, toolbar) in plot_refs.
    """
    copy_csv.copy_csv_main()
    for plot_fn in PLOT_FUNCS:
        try:
            fig = plot_fn(figsize=(7, 4))
            if not fig:
                continue

            canv = FigureCanvasTkAgg(fig, master=parent_frame)
            canv.draw()
            canv.get_tk_widget().pack(anchor="center", pady=6)

            toolbar = NavigationToolbar2Tk(canv, parent_frame, pack_toolbar=False)
            toolbar.update()
            toolbar.pack(anchor="center", pady=(0, 6))

            plot_refs.append((fig, canv, toolbar))
        except Exception as e:
            print(f'Exception during {plot_fn}')


def periodic_refresh(parent_frame, interval_secs = 120):
    """
    Every interval_secs seconds:
      1) copy updated CSV
      2) clear old plots
      3) draw ALL plots (throughput, wifi_clients, channel_conditions)
    """
    def _worker():
        while True:
            time.sleep(interval_secs)
            parent_frame.after(0, clear_plots)
            parent_frame.after(0, lambda: draw_all_plots(parent_frame))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
