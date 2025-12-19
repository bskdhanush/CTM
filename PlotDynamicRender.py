import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # type: ignore

import CopyCsv
import DataMonitorController as dmc

# keep this at module scope so state survives between calls
# one dict per logical plot instance
plot_refs: list[dict] = []

PLOT_FUNCS = [
    dmc.traffic_plots,
    dmc.rf_band_plot,
    dmc.ipa_thruput_plot,
    dmc.wifi_clients_plot,
    dmc.data_call_state_plot,
    dmc.channel_conditions_plot,
]


def init_plots(parent_frame):
    """
    Create figures/canvases/toolbars once and remember update callbacks.
    Call exactly once from DataMonitorPage after creating list_fr.
    """
    if plot_refs:
        return  # already initialized

    # initial CSV load
    CopyCsv.copy_csv_main()

    for plot_fn in PLOT_FUNCS:
        try:
            # New API: expect (fig or [fig], update_fn) from controller
            result = plot_fn(figsize=(7, 4))
        except TypeError:
            # Old API: just a Figure or list of Figures
            result = plot_fn(figsize=(7, 4))

        fig = None
        update_fn = None

        if isinstance(result, tuple) and len(result) == 2:
            fig, update_fn = result
        else:
            fig = result

        if not fig:
            continue

        figs = fig if isinstance(fig, list) else [fig]

        for f in figs:
            canv = FigureCanvasTkAgg(f, master=parent_frame)
            canv.draw()
            canv.get_tk_widget().pack(anchor="center", pady=6)

            toolbar = NavigationToolbar2Tk(canv, parent_frame, pack_toolbar=False)
            toolbar.update()
            toolbar.pack(anchor="center", pady=(0, 6))

            plot_refs.append(
                {
                    "fig": f,
                    "canvas": canv,
                    "toolbar": toolbar,
                    "update": update_fn,
                    "plot_fn": plot_fn,
                }
            )


def refresh_plots():
    """
    Update existing plot contents without recreating Tk widgets.
    """
    # still does disk work, but no Tk widget churn
    CopyCsv.copy_csv_main()

    for plot in plot_refs:
        fig = plot["fig"]
        canvas = plot["canvas"]
        update_fn = plot["update"]
        plot_fn = plot["plot_fn"]

        try:
            if callable(update_fn):
                # controller updates artists in-place
                update_fn(fig)
            else:
                # fallback: clear and let controller redraw into same Figure
                for ax in fig.get_axes():
                    ax.cla()
                # if controller exposes a pure "redraw" helper, call it here:
                try:
                    plot_fn.redraw(fig)  # type: ignore[attr-defined]
                except Exception:
                    # Otherwise rely on update_fn being added later
                    pass

            canvas.draw_idle()
        except Exception as e:
            print(f"Exception during refresh of {plot_fn}: {e}")


def periodic_refresh(parent_frame, interval_secs: int = 120):
    """
    Tk-based scheduler, no while True / extra GUI thread.
    """

    def _tick():
        refresh_plots()
        parent_frame.after(interval_secs * 1000, _tick)

    parent_frame.after(interval_secs * 1000, _tick)
