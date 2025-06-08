# ── data_monitor_controller.py ───────────────────────────────────────────────
"""
Business‑logic helpers for the Data‑Monitor page:
  • locate CSV / Excel files under C:\QSTAF\logs
  • build a matplotlib Figure for each file
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Folder that holds log spreadsheets
LOG_DIR = Path(r"C:\QSTAF\logs")        # <-- updated

# Acceptable file patterns (add more if needed)
_PATTERNS = ("*.csv", "*.xls*", "*.xlsx")

def get_data_paths() -> list[Path]:
    """Return every CSV / Excel file in LOG_DIR (sorted by name)."""
    paths: list[Path] = []
    for pat in _PATTERNS:
        paths.extend(LOG_DIR.glob(pat))
    return sorted(paths)


def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load *path* into a DataFrame, auto‑detecting CSV vs Excel."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path, engine="openpyxl")  # handles .xls/.xlsx


def make_plot_figure(path: Path, figsize: tuple[int, int] = (4, 2)):
    """
    Build and return a matplotlib Figure showing the first numeric column from
    *path* (CSV/Excel).  Caller embeds the Figure in Tk.
    """
    try:
        df = _load_dataframe(path)
        y  = df.select_dtypes("number").iloc[:, 0]
    except Exception as exc:
        print(f"[WARN] {path.name}: {exc} — using dummy data")
        y = [0, 1, 0]

    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    ax.plot(y)
    ax.set_title(path.stem, fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig
