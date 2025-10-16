import threading

def start_thread(target_func, thread_name, daemon=True):
    threading.Thread(
        target=target_func,
        daemon=daemon,
        name=thread_name
    ).start()

def thread_lock():
    return threading.Lock()

def thread_event():
    return threading.Event()
