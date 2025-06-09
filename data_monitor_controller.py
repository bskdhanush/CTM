# ── data_monitor_controller.py ───────────────────────────────────────────────
"""
Business‑logic helpers for the Data‑Monitor page.

What’s new?
-----------
• get_data_paths() now returns *all* CSV / Excel files in C:\QSTAF\logs
• make_plot_figure() auto‑chooses bar, scatter, or line based on columns
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------- constants
LOG_DIR   = Path(r"C:\QSTAF\logs")               # root of your log folder
_PATTERNS = ("*.csv", "*.xls*", "*.xlsx")        # recognised file types

# ----------------------------------------------------------------- helpers
def get_data_paths() -> list[Path]:
    """
    Return every matching CSV / Excel file in *LOG_DIR* (sorted by name).
    """
    paths: list[Path] = []
    for pat in _PATTERNS:
        paths.extend(LOG_DIR.glob(pat))

    if not paths:
        print(f"[WARN] No data files found in {LOG_DIR}")
    return sorted(paths)

def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load *path* into a DataFrame (CSV vs Excel handled automatically)."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path, engine="openpyxl")

# ----------------------------------------------------------------- plotting
def make_plot_figure(path: Path, figsize: tuple[int, int] = (4, 2)):
    """
    Build a matplotlib Figure appropriate for the file’s columns:

    • “Category”, “Value”  → bar chart
    • “X”, “Y”             → scatter (dot) plot
    • otherwise            → first numeric column as a line chart
    """
    try:
        df = _load_dataframe(path)
    except Exception as exc:
        print(f"[WARN] {path.name}: {exc} — using dummy data")
        import numpy as np
        df = pd.DataFrame({"dummy": np.arange(10)})

    fig, ax = plt.subplots(figsize=figsize, dpi=100)

    if {"Category", "Value"}.issubset(df.columns):
        ax.bar(df["Category"], df["Value"])
    elif {"X", "Y"}.issubset(df.columns):
        ax.scatter(df["X"], df["Y"])
    else:
        y = df.select_dtypes("number").iloc[:, 0]
        ax.plot(y)

    ax.set_title(path.stem, fontsize=8)
    fig.tight_layout()
    return fig
