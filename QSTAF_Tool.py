import os
import tkinter as tk
from tkinter import messagebox, IntVar
import psutil
import threading
import time
import requests
import json
import datetime
from tkinter import ttk, font
import sv_ttk

# Paths
CONTROL_PATH = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
CONTROL_BAT = os.path.join(CONTROL_PATH, "Run_framework.bat")
TRAFFIC_PATH = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
TRAFFIC_BAT = os.path.join(TRAFFIC_PATH, "Run_framework.bat")
AWS_S3_PATH = r"C:\QSTAF\QSTAFpy\bin"
AWS_S3_BAT = os.path.join(AWS_S3_PATH, "aws_s3_uploder")
CONFIG_PATH = r"C:\QSTAF"
CONFIG_FILE = os.path.join(CONFIG_PATH, "app_config.json")

# Global variables
scheduler_running = False
scheduler_thread = None
status_var = None



# Make sure the directory exists
if not os.path.exists(CONFIG_PATH):
    try:
        os.makedirs(CONFIG_PATH)
    except Exception as e:
        print(f"Failed to create config directory: {e}")

# def save_settings():
#     """Save application settings to a configuration file"""
#     config = {
#         "aws_scheduler_enabled": bool(scheduler_var.get())
#     }
def save_settings(scheduler_enabled: bool):
    config = {
        "aws_scheduler_enabled": scheduler_enabled
    }
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving settings: {e}")
        # Optionally, show an error message to the user
        # messagebox.showerror("Settings Error", f"Failed to save settings: {e}")

def load_settings():
    """Load application settings from configuration file"""
    default_config = {
        "aws_scheduler_enabled": False  # Default setting if file doesn't exist
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_config
    else:
        return default_config

def run_bat_as_admin(bat_path, working_dir):
    """Run a batch file with admin privileges"""
    try:
        # Create a temporary VBS script to elevate privileges
        vbs_content = f'''
        Set objShell = CreateObject("WScript.Shell")
        Set UAC = CreateObject("Shell.Application")
        
        ' Change to the working directory first
        objShell.CurrentDirectory = "{working_dir}"
        
        ' Execute the batch file with admin privileges
        UAC.ShellExecute "cmd.exe", "/k cd /d {working_dir} & {os.path.basename(bat_path)}", "", "runas", 1
        '''
        
        # Write the VBS script to a temporary file
        temp_vbs = os.path.join(os.environ['TEMP'], 'run_as_admin.vbs')
        with open(temp_vbs, 'w') as f:
            f.write(vbs_content)
        
        # Execute the VBS script
        os.system(f'wscript.exe "{temp_vbs}"')
        
        # Clean up
        os.remove(temp_vbs)
        
        # Update status
        update_status(f"Running {os.path.basename(bat_path)}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run the script:\n{e}")

def run_control_framework():
    """Run the Control framework"""
    run_bat_as_admin(CONTROL_BAT, CONTROL_PATH)

def run_traffic_framework():
    """Run the Traffic framework"""
    run_bat_as_admin(TRAFFIC_BAT, TRAFFIC_PATH)

def run_aws_s3_uploader(new_terminal=True, as_admin=False):
    """Run the AWS S3 uploader batch file in a new terminal window"""
    import subprocess
    import platform
    
    system = platform.system()
    
    if new_terminal:
        if system == "Windows":
            # Open a new command prompt and run the batch file
            cmd = f'start cmd.exe /k "{AWS_S3_BAT}"'
            subprocess.run(cmd, cwd=AWS_S3_PATH, shell=True)
        elif system == "Darwin":  # macOS
            # Open a new Terminal window and run the batch file
            cmd = f'open -a Terminal "{AWS_S3_BAT}"'
            subprocess.run(cmd, cwd=AWS_S3_PATH, shell=True)
        elif system == "Linux":
            # Open a new terminal window (e.g., gnome-terminal, xterm) and run the batch file
            cmd = f'gnome-terminal -- bash -c "{AWS_S3_BAT}; read -p \'Press Enter to close\'"'
            # Alternative for other terminals: xterm, konsole, etc.
            # cmd = f'xterm -e "bash -c \'{AWS_S3_BAT}; read -p \"Press Enter to close\"\'\"'
            subprocess.run(cmd, cwd=AWS_S3_PATH, shell=True)
    else:
        # Original behavior - run in current process
        if as_admin:
            run_bat_as_admin(AWS_S3_BAT, AWS_S3_PATH)
        else:
            subprocess.run([AWS_S3_BAT], cwd=AWS_S3_PATH, shell=True)

    # Update status bar
    update_status("AWS S3 uploader executed manually")
    
def run_both_frameworks():
    """Run both frameworks with a delay between them"""
    def execute():
        # Run Control framework first
        run_bat_as_admin(CONTROL_BAT, CONTROL_PATH)
        
        # Wait for delay - no popup confirmation
        time.sleep(2.5)
        
        # Run Traffic framework
        run_bat_as_admin(TRAFFIC_BAT, TRAFFIC_PATH)
    
    # Start in a new thread to prevent GUI freezing
    threading.Thread(target=execute, daemon=True).start()
    update_status("Starting both frameworks with 2.5s delay...")

def is_chrome_running():
    """Check if Chrome is running"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ['chrome.exe', 'googlechrome.exe']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def find_chrome_debugging_port():
    """Try to find an existing Chrome debugging port"""
    try:
        response = requests.get("http://localhost:9222/json/version", timeout=1)
        if response.status_code == 200:
            return 9222
    except:
        pass
    
    # Try other common debugging ports
    for port in [9223, 9224, 9225]:
        try:
            response = requests.get(f"http://localhost:{port}/json/version", timeout=1)
            if response.status_code == 200:
                return port
        except:
            continue
            
    return None

def close_all_chrome_tabs(close_chrome=True):
    """Close all Chrome tabs using Chrome's debugging protocol"""
    if not is_chrome_running():
        return 0
        
    debug_port = find_chrome_debugging_port()
    closed_count = 0
    
    if debug_port:
        try:
            # Get all tabs
            response = requests.get(f"http://localhost:{debug_port}/json/list", timeout=2)
            tabs = json.loads(response.text)
            
            # Filter to keep only page type tabs
            page_tabs = [tab for tab in tabs if tab['type'] == 'page']
            
            # Close all tabs
            for tab in page_tabs:
                tab_id = tab['id']
                requests.get(f"http://localhost:{debug_port}/json/close/{tab_id}", timeout=2)
                closed_count += 1
            
            # If we want to close Chrome completely
            if close_chrome:
                time.sleep(0.5)  # Give tabs time to close
                kill_chrome_instances(traffic_only=False)
                
            return closed_count
        except Exception as e:
            print(f"Failed to close tabs via debugging: {e}")
    
    # If debugging not available, use process termination
    killed = kill_chrome_instances(traffic_only=False)
    return killed

def kill_chrome_instances(traffic_only=True):
    """Kill Chrome processes"""
    killed_count = 0
    try:
        # Look for Chrome processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if it's a Chrome process
                if proc.info['name'] and proc.info['name'].lower() in ['chrome.exe', 'googlechrome.exe']:
                    # If traffic_only is True, check command line for traffic-related indicators
                    if traffic_only:
                        cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                        traffic_indicators = [
                            'traffic_laptop', 
                            'qstaf',
                            # Add more indicators as needed
                        ]
                        
                        if any(indicator in cmdline for indicator in traffic_indicators):
                            proc.kill()
                            killed_count += 1
                    else:
                        # Kill all Chrome processes
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"Error killing Chrome: {e}")
    
    return killed_count

def kill_framework_processes(framework_type="all"):
    """Kill processes associated with the specified framework(s)"""
    
    # First close Chrome tabs when stopping Traffic or All frameworks
    if framework_type == "traffic" or framework_type == "all":
        if is_chrome_running():
            # Close all Chrome tabs and exit Chrome completely
            close_all_chrome_tabs(close_chrome=True)
    
    # List of common processes related to the frameworks
    target_processes = ['python.exe', 'cmd.exe', 'java.exe', 'conhost.exe']
    
    killed_count = 0
    search_terms = []
    
    # Determine which processes to kill based on framework_type
    if framework_type == "control" or framework_type == "all":
        search_terms.append("control_laptop")
    if framework_type == "traffic" or framework_type == "all":
        search_terms.append("traffic_laptop")
    
    # Add general QSTAF term to catch other related processes
    search_terms.append("qstaf")
    
    # First attempt - find and kill all processes with matching search terms
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if process name matches any target
            if proc.info['name'] and proc.info['name'].lower() in target_processes:
                # Check if cmdline contains any reference to our search terms
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                if any(term in cmdline for term in search_terms):
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            print(f"Error killing process: {e}")
    
    # Second attempt - if framework_type is "traffic", find any remaining cmd.exe 
    # processes that might have been spawned by the traffic framework
    if framework_type == "traffic" or framework_type == "all":
        # Wait a brief moment to allow processes to terminate
        time.sleep(0.5)
        
        # Check for any remaining command prompts that might be from Traffic
        # This is a more aggressive approach that might also catch command prompts
        # that appear to be related to Traffic based on timing
        traffic_start_time = time.time() - 3600  # Look for processes started in the last hour
        
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'cmd.exe':
                    # If the command prompt was created after our traffic_start_time
                    if proc.info['create_time'] > traffic_start_time:
                        # Additional check: Try to get window title if possible
                        try:
                            import win32gui
                            import win32process
                            
                            def get_window_title(pid):
                                def callback(hwnd, hwnds):
                                    if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                                        if found_pid == pid:
                                            hwnds.append(hwnd)
                                    return True
                                
                                hwnds = []
                                win32gui.EnumWindows(callback, hwnds)
                                
                                for hwnd in hwnds:
                                    title = win32gui.GetWindowText(hwnd).lower()
                                    if any(term in title for term in ['traffic', 'qstaf', 'run_framework']):
                                        return title
                                return None
                            
                            window_title = get_window_title(proc.pid)
                            if window_title:
                                proc.kill()
                                killed_count += 1
                        except:
                            # If we can't check the window title, make a best guess
                            # based on timing or just kill it as a precaution
                            proc.kill()
                            killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                print(f"Error in second-pass process killing: {e}")
    
    update_status(f"Killed {killed_count} processes related to {framework_type} framework")

def kill_control_processes():
    """Kill only Control framework processes"""
    kill_framework_processes("control")

def kill_traffic_processes():
    """Kill only Traffic framework processes"""
    kill_framework_processes("traffic")

def kill_all_processes():
    """Kill all framework processes"""
    kill_framework_processes("all")

def update_status(message):
    """Update the status bar with a message"""
    status_var.set(message)

def aws_scheduler_loop():
    """Loop function for the AWS scheduler"""
    global scheduler_running
    
    while scheduler_running:
        now = datetime.datetime.now()
        
        # Check if it's 4:00 PM
        if now.hour == 16 and now.minute == 0 and 0 <= now.second < 10:
            update_status("Running scheduled AWS S3 upload (4:00 PM)")
            run_aws_s3_uploader()
            
            # Sleep for 50 seconds to avoid multiple triggers in the same minute
            time.sleep(50)
        
        # Check every 5 seconds
        time.sleep(5)

def toggle_aws_scheduler():
    """Toggle the AWS scheduler on/off"""
    global scheduler_running, scheduler_thread
    
    if scheduler_var.get() == 1:  # If checkbox is checked
        scheduler_running = True
        scheduler_thread = threading.Thread(target=aws_scheduler_loop, daemon=True)
        scheduler_thread.start()
        update_status("AWS Scheduler activated - Will run at 4:00 PM daily")
    else:
        scheduler_running = False
        update_status("AWS Scheduler deactivated")
    
    # Save settings whenever the toggle changes
    save_settings()