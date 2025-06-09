# ── data_monitor_controller.py ───────────────────────────────────────────────
"""
Business‑logic helpers for the Data‑Monitor page.

Changes in this version
––––––––––––––––––––––––
• Always use C:\QSTAF\logs\temp_data.csv as the sole data source.
• get_data_paths() now returns a single‑element list (or empty if missing).
"""

from io import BytesIO
from pathlib import Path
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt

# Fixed data‑file location
LOG_DIR   = Path(r"C:\QSTAF\logs")
TEMP_CSV  = LOG_DIR / "temp_data.csv"

def get_data_paths() -> list[Path]:
    """Return [TEMP_CSV] if present, otherwise an empty list."""
    if TEMP_CSV.exists():
        return [TEMP_CSV]
    print(f"[WARN] {TEMP_CSV} not found.")
    return []

def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load CSV/Excel into a DataFrame (auto‑detects CSV vs Excel)."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path, engine="openpyxl")  # handles .xls/.xlsx

def make_plot_figure(path: Path, figsize: tuple[int, int] = (4, 2)):
    """
    Build and return a matplotlib Figure showing the first numeric column
    from *path*.  Caller embeds the Figure in Tk.
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

'''
def make_plot_thumbnail(path: Path,
                        size: tuple[int, int] = (400, 200)) -> Image.Image:
    """
    Return a Pillow image (PNG) of the plot resized to *size* pixels.

    *size* is interpreted in pixels.  Internally we render at 100 dpi so
    width = size[0]/100 inches and height = size[1]/100 inches.
    """
    # Build the plot
    fig = make_plot_figure(path,
                           figsize=(size[0] / 100, size[1] / 100))  # inches @100 dpi

    # Save the figure into an in‑memory buffer
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)                       # free the figure
    buf.seek(0)

    # Load with Pillow and resize exactly to *size*
    img = Image.open(buf).resize(size, Image.LANCZOS)
    return img

# Quick manual test (python data_monitor_controller.py)
if __name__ == "__main__":
    for p in get_data_paths():
        make_plot_figure(p)
'''