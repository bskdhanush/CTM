import logging
import threading

def start_thread(target_func, thread_name, daemon=True):
    """Start a thread with exception handling that logs thread name"""
    def wrapper():
        try:
            target_func()
        except Exception as e:
            # Log exception with thread name
            current_thread = threading.current_thread()
            error_msg = f"Exception in thread '{current_thread.name}': {type(e).__name__}: {e}"
            print(error_msg)
            logging.exception(f"Thread '{current_thread.name}' failed")
    
    thread = threading.Thread(
        target=wrapper,
        daemon=daemon,
        name=thread_name
    )
    thread.start()
    return thread


def thread_lock():
    return threading.Lock()


def thread_event():
    return threading.Event()