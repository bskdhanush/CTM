import subprocess
import json
import os

# Path to the JSON file
json_path = r"C:\QSTAF\CTM_logs\adb_ID.json"

# Ensure directory exists
os.makedirs(os.path.dirname(json_path), exist_ok=True)

# Store last known "ADB ID" value
last_adb_id = None

def save_to_json(adb_id):
    data = {"ADB ID": adb_id}
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)
    #print(f"[INFO] Updated ADB ID → {adb_id}")

def run_adb_track_devices():
    global last_adb_id
    cmd = ["adb", "track-devices"]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #print("[INFO] Tracking devices... (Press Ctrl+C to stop)")

    header_skipped = False

    for line in process.stdout: # type: ignore
        line = line.strip()
        if not line:
            continue
        
        # Skip first "List of devices attached"
        if not header_skipped and line.lower().startswith("list of devices"):
            header_skipped = True
            continue

        devices = []
        if "\t" in line:
            serial, state = line.split("\t", 1)
            if state.strip() == "device":
                # Remove first 4 characters
                trimmed_serial = serial.strip()[4:]
                devices.append(trimmed_serial)

        adb_id = devices[0] if devices else "--"

        if adb_id != last_adb_id:
            last_adb_id = adb_id
            save_to_json(adb_id)

if __name__ == "__main__":
    try:
        run_adb_track_devices()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped tracking.")
