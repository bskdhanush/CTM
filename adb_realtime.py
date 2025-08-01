import subprocess, threading, queue, re

def _reader(pipe, q):
    """Push each complete line from the subprocess into a queue."""
    for line in iter(pipe.readline, ''):   # until EOF
        q.put(line.rstrip('\r\n'))
    pipe.close()

def track_devices(callback):
    """
    Spawns `adb track-devices` and calls `callback(serial, state)`
    whenever a line like "<serial>\t<state>" is received.
    """
    proc = subprocess.Popen(
        ["adb", "track-devices"], stdout=subprocess.PIPE,
        text=True, bufsize=1  # line-buffered
    )

    q = queue.Queue()
    threading.Thread(target=_reader, args=(proc.stdout, q), daemon=True).start()

    header_seen = False
    while proc.poll() is None:            # loop while adb is alive
        try:
            line = q.get(timeout=0.1)
        except queue.Empty:
            continue

        if not header_seen:
            # First line is the static header
            header_seen = True
            continue

        if line.strip() == "":
            # adb sometimes sends an empty line between updates
            continue

        # Example line:  R9WN6059FJ    device
        m = re.match(r"^(\S+)\s+(\S+)$", line)
        if m:
            serial, state = m.groups()
            callback(serial, state)       # <-- your handler

def on_event(serial, state):
    print(f"{serial}: {state}")

if __name__ == "__main__":
    try:
        track_devices(on_event)
    except KeyboardInterrupt:
        print("Stopped.")
