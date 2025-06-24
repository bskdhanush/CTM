
import psutil

def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

def stop_all_tests(mode: str):
    found = False
    if mode=="control": 
        keywords = [" control ","aws_control_",]
        print("control loop")
    else :
        keywords = [
        " traffic ", "aws_traffic", 
        "pinghandler", "iperf", "ping"]
        print("traffic loop")


    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']).lower()
            if any(keyword in cmdline for keyword in keywords):
                kill_process_and_children(proc.info['pid'])
                found = True
        except Exception:
            continue
 
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == 'chrome.exe':
                kill_process_and_children(proc.info['pid'])
                found = True
        except Exception:
            continue

    return found
   
