import threading
import time
import queue
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk # type: ignore
import CopyCsv
import DataMonitorController as dmc

# Global state for plot management
plot_refs = []  # [(fig, canvas, toolbar, plot_func), ...]
data_queue = queue.Queue()
refresh_active = False
refresh_thread = None

PLOT_FUNCS = [
    dmc.traffic_plots,
    dmc.rf_band_plot,
    dmc.ipa_thruput_plot,
    dmc.wifi_clients_plot,
    dmc.data_call_state_plot,
    dmc.channel_conditions_plot,
]

def init_plots(parent_frame):
    """Initialize all plots once - no more destroy/recreate cycle"""
    global plot_refs
    
    # Clear any existing plots first
    clear_plots()
    
    print("Initializing plots...")
    
    # Copy CSV data once for initial setup
    try:
        CopyCsv.copy_csv_main()
    except Exception as e:
        print(f"Error copying CSV: {e}")
    
    for plot_fn in PLOT_FUNCS:
        try:
            # Create initial figure(s)
            fig_result = plot_fn(figsize=(7, 4))
            if not fig_result:
                continue
                
            # Handle both single figures and lists of figures
            if not isinstance(fig_result, list):
                fig_result = [fig_result]
            
            for fig in fig_result:
                if fig is None:
                    continue
                    
                # Create canvas and toolbar
                canvas = FigureCanvasTkAgg(fig, master=parent_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(anchor="center", pady=6)
                
                toolbar = NavigationToolbar2Tk(canvas, parent_frame, pack_toolbar=False)
                toolbar.update()
                toolbar.pack(anchor="center", pady=(0, 6))
                
                # Store references for later updates
                plot_refs.append((fig, canvas, toolbar, plot_fn))
                
        except Exception as e:
            print(f'Exception during {plot_fn.__name__}: {e}')
    
    print(f"Initialized {len(plot_refs)} plots")

def clear_plots():
    """Clean up existing plots"""
    global plot_refs
    
    for fig, canvas, toolbar, _ in plot_refs:
        try:
            canvas.get_tk_widget().destroy()
            toolbar.destroy()
            plt.close(fig)
        except Exception as e:
            print(f"Error clearing plot: {e}")
    
    plot_refs.clear()

def update_plots_fast():
    """Fast plot update - only refresh data, keep widgets alive"""
    global plot_refs

    if not plot_refs:
        print("No plots to update")
        return

    print("Updating plots...")

    for fig, canvas, toolbar, plot_fn in plot_refs:
        try:
            # Clear and reuse existing figure
            fig.clear()

            # Call the plot function with existing figure
            plot_fn(figsize=(7, 4), fig=fig)

            # Format x-axis for all axes inside fig
            for ax in fig.get_axes():
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
                fig.autofmt_xdate()
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            # Redraw on canvas
            canvas.draw_idle()

        except Exception as e:
            print(f'Exception updating {plot_fn.__name__}: {e}')

    print("Plot update complete")

def background_data_worker():
    """Background thread that processes data and queues UI updates"""
    global refresh_active
    
    while refresh_active:
        try:
            # Copy CSV data in background
            CopyCsv.copy_csv_main()
            
            # Signal that data is ready for UI update
            data_queue.put('update_ready')
            
        except Exception as e:
            print(f"Error in background worker: {e}")
            data_queue.put('error')
        
        # Wait for next cycle
        time.sleep(60)  # 60 second interval

def check_data_queue(parent_frame):
    """Check for background data updates and trigger UI refresh"""
    global refresh_active
    
    if not refresh_active:
        return
    
    try:
        while True:
            message = data_queue.get_nowait()
            if message == 'update_ready':
                # Trigger fast plot update on UI thread
                update_plots_fast()
            elif message == 'error':
                print("Background data processing error")
    except queue.Empty:
        pass
    
    # Schedule next check
    if refresh_active:
        parent_frame.after(1000, lambda: check_data_queue(parent_frame))  # Check every 1 second

def start_periodic_refresh(parent_frame, interval_secs=60):
    """Start the optimized periodic refresh system"""
    global refresh_active, refresh_thread
    
    if refresh_active:
        print("Refresh already active")
        return
    
    print(f"Starting periodic refresh every {interval_secs} seconds")
    refresh_active = True
    
    # Start background data processing thread
    refresh_thread = threading.Thread(target=background_data_worker, daemon=True)
    refresh_thread.start()
    
    # Start UI queue checker
    check_data_queue(parent_frame)

def stop_periodic_refresh():
    """Stop the periodic refresh"""
    global refresh_active
    
    print("Stopping periodic refresh")
    refresh_active = False

def periodic_refresh(parent_frame, interval_secs=60):
    """Legacy function - now uses optimized approach"""
    start_periodic_refresh(parent_frame, interval_secs)

# Convenience function for manual refresh
def manual_refresh():
    """Trigger a manual refresh of all plots"""
    try:
        CopyCsv.copy_csv_main()
        update_plots_fast()
    except Exception as e:
        print(f"Error in manual refresh: {e}")