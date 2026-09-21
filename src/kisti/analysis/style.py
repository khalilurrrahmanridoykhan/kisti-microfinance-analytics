"""Chart style shared by every figure.

Colours come from a validated palette (worst all-pairs colour-vision difference 9.2, worst
normal-vision difference 24.0 for the first three slots, checked with the dataviz validator).
One hue carries a single measure; further categories take the next slot in fixed order.
Text is always ink, never a series colour, and every figure is backed by a CSV table.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
# Categorical slots in fixed order: blue, orange, aqua, yellow, magenta, green.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
BLUE = SERIES[0]
ORANGE = SERIES[1]
SEQ_LIGHT = "#cde2fb"


def setup() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "text.color": INK,
            "font.size": 9,
            "legend.frameon": False,
            "lines.linewidth": 2,
        }
    )


def save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def caption(fig, text: str, y: float = -0.07) -> None:
    """A one-line note under the plot: what is measured and over which MFIs."""
    fig.text(0.0, y, text, fontsize=8, color=INK_2, ha="left", va="top", wrap=True)


def rounded_bars(ax, y, widths, height=0.42, color=BLUE, left=None):
    """Horizontal bars grown from one baseline."""
    return ax.barh(y, widths, height=height, color=color, left=left, edgecolor="none")
