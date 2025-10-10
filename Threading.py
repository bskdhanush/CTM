import threading

def start_thread(target_func, daemon=True):
    threading.Thread(
        target=target_func,
        daemon=daemon
    ).start()

def thread_lock():
    return threading.Lock()

def thread_event():
    return threading.Event()
