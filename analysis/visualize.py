# =====================================================================
# Part 2 - Task 11: Two visualizations
# =====================================================================
# How to run (from the main repo folder):
#     python analysis/clean_and_eda.py     <- run this first (once): it saves the cleaned CSVs
#     python analysis/visualize.py         <- then this: it only reads the cleaned data and draws
#
# The charts are made from analysis/cleaned_data/orders_merged_clean.csv, which
# clean_and_eda.py writes. No number is typed in by hand: every value on the
# charts is calculated below from that cleaned file.
# Both charts are saved in the visualizations/ folder.

import os
import sys

import matplotlib
matplotlib.use("Agg")              # save charts to files (no window needed)
import matplotlib.pyplot as plt
import pandas as pd

CLEANED_FILE = "analysis/cleaned_data/orders_merged_clean.csv"

# Stop with a clear message if Part 2 has not been run yet
if not os.path.exists(CLEANED_FILE):
    print(f"ERROR: {CLEANED_FILE} not found.")
    print("Run 'python analysis/clean_and_eda.py' first - it creates the cleaned CSV files.")
    sys.exit(1)

# Load the cleaned analysis table (175 orders, with order_value, is_outlier and year_month)
merged = pd.read_csv(CLEANED_FILE)
print(f"Loaded {CLEANED_FILE}: {merged.shape}")

# Create the output folder if it does not exist yet
os.makedirs("visualizations", exist_ok=True)


# ---------------------------------------------------------------------
# Chart 1: Return rate by payment method (bar chart)
# ---------------------------------------------------------------------
# Return rate per payment method = share of orders with returned = 1 (same as Task 7)
# Sorted from highest to lowest. Expected: COD 44.4, UPI 18.9, CARD 14.7
rates = (merged.groupby("payment_method")["returned"].mean() * 100).round(1)
rates = rates.sort_values(ascending=False)
print("\nReturn rate by payment method (%):")
print(rates)

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
print("Saved visualizations/return_rate_by_payment.png")


# ---------------------------------------------------------------------
# Chart 2: Monthly revenue trend, outlier-corrected (line chart)
# ---------------------------------------------------------------------
# Monthly revenue WITHOUT the outlier orders (same as Task 10, version 2)
# Expected peak: 2026-03 = 20318.90
monthly = merged[merged["is_outlier"] == False].groupby("year_month")["order_value"].sum().round(2)
print("\nMonthly revenue, outliers excluded:")
print(monthly)

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
