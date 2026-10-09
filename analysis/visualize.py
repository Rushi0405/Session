"""Part 2, Task 11: the two charts, saved to visualizations/.

The numbers are not retyped or read from a hand-made file. This script imports
and re-runs the clean_and_eda pipeline on the raw CSVs, then plots the results
of Task 7 (return rate by payment method) and Task 10 (outlier-corrected
monthly revenue). Re-running regenerates byte-identical PNGs.

Run after clean_and_eda.py (it does not depend on that run's output, so the
order is for readability only):
    python analysis/visualize.py
"""

import contextlib
import io
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  # file output only, no display needed
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from clean_and_eda import REPO_ROOT, run_pipeline  # noqa: E402

OUT_DIR = REPO_ROOT / "visualizations"

# Chart tokens: one data hue for the highlighted mark, a muted tone for context
# marks, and neutral inks for all text (text never takes the data colour).
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
HIGHLIGHT = "#2a78d6"
MUTED = "#b8b7b0"

# Drop matplotlib's version string from the PNG so the output is byte-identical
# across runs and machines with the same library version.
PNG_METADATA = {"Software": None}


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_SECONDARY)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_return_rate_by_payment(by_payment, path):
    rates = by_payment["return_rate_pct"].sort_values(ascending=False)
    counts = by_payment["count"]
    top = rates.index[0]
    ratio = rates[top] / rates.min()

    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=SURFACE)
    style_axes(ax)
    colors = [HIGHLIGHT if m == top else MUTED for m in rates.index]
    bars = ax.bar(rates.index, rates.values, width=0.5, color=colors)
    for bar, method in zip(bars, rates.index):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{rates[method]:.1f}%", ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=TEXT_PRIMARY)

    ax.set_xticks(range(len(rates)))
    ax.set_xticklabels([f"{m}\n({counts[m]} orders)" for m in rates.index], color=TEXT_PRIMARY)
    ax.set_ylabel("Return rate (%)", color=TEXT_SECONDARY)
    ax.set_xlabel("Payment method (cleaned, 175 orders)", color=TEXT_SECONDARY)
    ax.set_ylim(0, rates.max() * 1.2)
    ax.set_title(f"{top} Returns at {rates[top]:.1f}% — {ratio:.0f}x {rates.idxmin().title()}",
                 loc="left", fontsize=14, fontweight="bold", color=TEXT_PRIMARY)

    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE, metadata=PNG_METADATA)
    plt.close(fig)


def plot_monthly_revenue_trend(monthly_corrected, path):
    months = list(monthly_corrected.index)
    values = monthly_corrected.values
    peak = monthly_corrected.idxmax()
    peak_i = months.index(peak)
    peak_label = f"{datetime.strptime(peak, '%Y-%m'):%B %Y}"

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    style_axes(ax)
    ax.plot(months, values, color=HIGHLIGHT, linewidth=2, marker="o", markersize=7,
            markerfacecolor=HIGHLIGHT, markeredgecolor=SURFACE, markeredgewidth=1.5)

    # Label only the peak and the final point, not every marker.
    for i in sorted({peak_i, len(months) - 1}):
        ax.annotate(f"₹{values[i]:,.2f}", (i, values[i]), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=10,
                    fontweight="bold" if i == peak_i else "normal", color=TEXT_PRIMARY)

    ax.set_ylim(0, values.max() * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"₹{v:,.0f}"))
    ax.set_xlabel("Month (order_date)", color=TEXT_SECONDARY)
    ax.set_ylabel("Revenue (order_value, INR)", color=TEXT_SECONDARY)
    ax.set_title(f"{peak_label} Is the True Revenue Peak (Outliers Excluded)",
                 loc="left", fontsize=14, fontweight="bold", color=TEXT_PRIMARY, pad=24)
    ax.text(0, 1.02, "Outlier-corrected: bulk orders O0011 and O0098 removed from January",
            transform=ax.transAxes, fontsize=9, color=TEXT_SECONDARY, va="bottom")

    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE, metadata=PNG_METADATA)
    plt.close(fig)


def main():
    # Re-run the pipeline quietly; its full printed audit trail belongs to
    # clean_and_eda.py. Its assertions still run, so a wrong number stops here too.
    with contextlib.redirect_stdout(io.StringIO()):
        results = run_pipeline()

    OUT_DIR.mkdir(exist_ok=True)
    p1 = OUT_DIR / "return_rate_by_payment.png"
    p2 = OUT_DIR / "monthly_revenue_trend.png"
    plot_return_rate_by_payment(results["by_payment"], p1)
    plot_monthly_revenue_trend(results["monthly_corrected"], p2)
    print(f"Saved {p1.relative_to(REPO_ROOT)}")
    print(f"Saved {p2.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
