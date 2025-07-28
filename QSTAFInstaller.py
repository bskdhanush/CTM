import threading
from tkinter import ttk, filedialog, messagebox

def isntallQSTAF(filePAth):
    if not filePAth:
        print("File path is empty.")
        return
    
    return 0