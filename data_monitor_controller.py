# data_monitor.py
from pathlib import Path

def get_pic_paths():
    """
    Return a list of 5 placeholder images.
    Replace this logic later with whatever produces real data.
    """
    root = Path(__file__).parent / "dummy_pics"          # <app>/dummy_pics/
    return [root / f"pic{i}.png" for i in range(1, 6)]
