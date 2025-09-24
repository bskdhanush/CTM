import os

directory = r"C:\QSTAF\CTM_logs"
file_name = "Logs.txt"
file_path = os.path.join(directory, file_name)
def sendLog(data):
    try:
        with open(file_path, 'a') as file:
            file.write(data + "\n")  # Append data with a newline
    except Exception as e:
        print(f"Error writing to file: {e}")

# Example usage:
# send_data("Hello, World!")
# send_data("Your data here", "/path/to/your/file.txt")