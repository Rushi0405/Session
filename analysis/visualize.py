# =====================================================================
# Part 2 - Task 11: Two visualizations
# =====================================================================
# How to run (from the main repo folder, after clean_and_eda.py):
#     python analysis/visualize.py
#
# The charts use the results calculated in clean_and_eda.py.
# "import clean_and_eda" runs that script again from the raw CSV files,
# so no number is typed in by hand. (Its printed output appears again first.)
# Both charts are saved in the visualizations/ folder.

import os

import matplotlib
matplotlib.use("Agg")              # save charts to files (no window needed)
import matplotlib.pyplot as plt
import pandas as pd

import clean_and_eda as eda        # gives us eda.payment_summary and eda.monthly_without

# Create the output folder if it does not exist yet
os.makedirs("visualizations", exist_ok=True)


# ---------------------------------------------------------------------
# Chart 1: Return rate by payment method (bar chart)
# ---------------------------------------------------------------------
# payment_summary is already sorted from highest to lowest return rate (Task 7)
rates = eda.payment_summary["return_rate_%"]
cod_rate = rates["COD"]
card_rate = rates["CARD"]

# Highlight COD in blue, other methods in grey
colors = ["#2a78d6" if method == "COD" else "#b8b7b0" for method in rates.index]

plt.figure(figsize=(7, 5))
plt.bar(rates.index, rates.values, color=colors, width=0.5)

# Write the exact percentage on top of each bar
for i, value in enumerate(rates.values):
    plt.text(i, value + 1, f"{value}%", ha="center", fontsize=12, fontweight="bold")

# Title states the finding, e.g. "COD Returns at 44.4% - 3x Card"
plt.title(f"COD Returns at {cod_rate}% — {cod_rate / card_rate:.0f}x Card", fontsize=14, fontweight="bold")
plt.xlabel("Payment method")
plt.ylabel("Return rate (%)")
plt.ylim(0, rates.max() * 1.2)
plt.savefig("visualizations/return_rate_by_payment.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nSaved visualizations/return_rate_by_payment.png")


# ---------------------------------------------------------------------
# Chart 2: Monthly revenue trend, outlier-corrected (line chart)
# ---------------------------------------------------------------------
# We use monthly_without (Task 10), NOT the version inflated by the 2 bulk orders
monthly = eda.monthly_without
peak_month = monthly.idxmax()                                   # e.g. "2026-03"
peak_name = pd.to_datetime(peak_month).strftime("%B %Y")        # e.g. "March 2026"

plt.figure(figsize=(8, 5))
plt.plot(monthly.index, monthly.values, marker="o", linewidth=2, color="#2a78d6")

# Label the peak month with its value
plt.annotate(f"Rs {monthly.max():,.2f}", (peak_month, monthly.max()),
             textcoords="offset points", xytext=(0, 10), ha="center", fontweight="bold")

# Title names the real peak month
plt.title(f"{peak_name} Is the Peak Revenue Month (Outliers Excluded)", fontsize=14, fontweight="bold")
plt.xlabel("Month")
plt.ylabel("Revenue (INR)")
plt.ylim(0, monthly.max() * 1.2)
plt.grid(axis="y", alpha=0.3)
plt.savefig("visualizations/monthly_revenue_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved visualizations/monthly_revenue_trend.png")
