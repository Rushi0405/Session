# =====================================================================
# Part 2: Data cleaning and EDA (Tasks 1-10)
# =====================================================================
# How to run (from the main repo folder):
#     python analysis/clean_and_eda.py
#
# This script reads the raw CSV files in data/ directly with pandas.
# It does NOT use the SQL database, so Part 1 and Part 2 can run in any order.
# Every result is printed. The "Expected:" comments show the answer from the brief.

import pandas as pd


# ---------------------------------------------------------------------
# Task 1: Load and inspect the data
# ---------------------------------------------------------------------
print("========== Task 1: Load and inspect ==========")

# Read the three CSV files into DataFrames
orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")

# Check the size of each table (rows, columns)
# Expected: orders.shape = (180, 9)
print("orders shape   :", orders.shape)
print("customers shape:", customers.shape)
print("products shape :", products.shape)

# Look at the first 5 orders
print("\nFirst 5 rows of orders:")
print(orders.head())

# Count missing values in each column of orders
print("\nMissing values in orders:")
print(orders.isnull().sum())


# ---------------------------------------------------------------------
# Task 2: Standardize payment_method casing
# ---------------------------------------------------------------------
# The same method is typed in different ways: COD/cod, Card/card/CARD, UPI/upi
print("\n========== Task 2: Standardize payment_method ==========")

# Before cleaning: 7 different spellings
print("Before:", list(orders["payment_method"].unique()))
print("Number of distinct values before:", orders["payment_method"].nunique())

# Remove extra spaces and convert everything to UPPER CASE
orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

# After cleaning: only 3 values remain
# Expected counts: CARD 70, UPI 55, COD 55
print("\nAfter:", list(orders["payment_method"].unique()))
print("Number of distinct values after:", orders["payment_method"].nunique())
print(orders["payment_method"].value_counts())


# ---------------------------------------------------------------------
# Task 3: Remove duplicate orders
# ---------------------------------------------------------------------
# Some orders were submitted twice: same values in every column except order_id.
print("\n========== Task 3: Remove duplicates ==========")

# Columns that describe an order (everything except order_id)
key_columns = ["customer_id", "product_id", "order_date", "quantity",
               "discount_pct", "payment_method", "rating", "returned"]

# Mark a row as duplicate if the same order appeared before it (keep the first one)
is_duplicate = orders.duplicated(subset=key_columns, keep="first")

# Expected: 5 duplicates -> O0176, O0177, O0178, O0179, O0180
dropped_rows = orders[is_duplicate]
print("Number of duplicate rows:", is_duplicate.sum())
print("Dropped order_ids:", list(dropped_rows["order_id"]))

# Keep only the rows that are NOT duplicates
orders_clean = orders[~is_duplicate].copy()

# Expected shape: (175, 9)
print("Shape after removing duplicates:", orders_clean.shape)


# ---------------------------------------------------------------------
# Task 4: Fill missing values (on the data without duplicates)
# ---------------------------------------------------------------------
print("\n========== Task 4: Fill missing values ==========")

# discount_pct: missing means no promo code was used, so fill with 0
# Expected: 12 missing
print("Missing discount_pct:", orders_clean["discount_pct"].isnull().sum())
orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)

# rating: find the median of the existing ratings, then fill the missing ones with it
# Expected: median = 3.0, 15 missing
rating_median = orders_clean["rating"].median()
print("Median rating:", rating_median)
print("Missing rating:", orders_clean["rating"].isnull().sum())
orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)

# Check: no missing values should be left (both should be 0)
print("\nMissing values after filling:")
print(orders_clean[["discount_pct", "rating"]].isnull().sum())


# ---------------------------------------------------------------------
# Task 5: Merge tables and match the total with Part 1 (SQL)
# ---------------------------------------------------------------------
print("\n========== Task 5: Merge and reconcile ==========")

# Join orders with products (to get price) and customers (to get city, city_tier)
merged = orders_clean.merge(products, on="product_id").merge(customers, on="customer_id")

# Value of each order after discount
merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)

# Expected: 97358.30 across 175 rows
clean_total = round(merged["order_value"].sum(), 2)
print("Merged shape:", merged.shape)
print(f"Total order value (cleaned data): Rs {clean_total:.2f}")

# Part 1 (SQL Report a) total, calculated on the raw data that still has duplicates
part1_total = 99860.20
difference = round(part1_total - clean_total, 2)
print(f"\nPart 1 total : {part1_total:.2f}")
print(f"Part 2 total : {clean_total:.2f}")
print(f"Difference   : {difference:.2f}")

# Check: calculate the value of the 5 dropped duplicate rows separately
dropped_with_price = dropped_rows.merge(products, on="product_id")
dropped_with_price["order_value"] = (dropped_with_price["quantity"] * dropped_with_price["price"]
                                     * (1 - dropped_with_price["discount_pct"] / 100))
dropped_total = round(dropped_with_price["order_value"].sum(), 2)
print("\nThe 5 dropped duplicate rows:")
print(dropped_with_price[["order_id", "quantity", "price", "discount_pct", "order_value"]])
print(f"Value of dropped duplicates: {dropped_total:.2f}")   # Expected: 2501.90

# Reconciliation note
print("\nReconciliation note:")
print(f"The cleaned total (Rs {clean_total:,.2f}) is Rs {difference:,.2f} lower than the Part 1 raw "
      f"total (Rs {part1_total:,.2f}). This difference comes only from the 5 duplicate orders removed "
      f"in Task 3 (O0176-O0180). Their combined value is exactly Rs {dropped_total:,.2f}. "
      f"Filling missing values in Task 4 did not change the total: a missing discount filled with 0 "
      f"is the same as SQL's COALESCE(discount_pct, 0), and rating is not used to calculate order value.")


# ---------------------------------------------------------------------
# Task 6: Find outliers in quantity using the IQR method
# ---------------------------------------------------------------------
# We only FLAG the outliers with a new column. We do not delete them.
print("\n========== Task 6: IQR outliers ==========")

# Quartiles and IQR
# Expected: Q1 = 1.0, Q3 = 2.0, IQR = 1.0, lower = -0.5, upper = 3.5
Q1 = merged["quantity"].quantile(0.25)
Q3 = merged["quantity"].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
print("Q1 =", Q1, " Q3 =", Q3, " IQR =", IQR)
print("Lower limit =", lower, " Upper limit =", upper)

# True if quantity is outside the limits
merged["is_outlier"] = (merged["quantity"] < lower) | (merged["quantity"] > upper)

# Expected: 2 outliers -> O0011 (quantity 25) and O0098 (quantity 30)
print("\nOutlier orders:")
print(merged[merged["is_outlier"]][["order_id", "order_date", "quantity", "order_value"]])
print("Rows still in the data:", len(merged))


# ---------------------------------------------------------------------
# Task 7: Hypothesis - do COD orders have a higher return rate?
# ---------------------------------------------------------------------
print("\n========== Task 7: COD return hypothesis ==========")
print("Hypothesis: COD (Cash on Delivery) orders are returned more often than CARD or UPI orders.")

# count = number of orders, mean = share of orders returned (returned is 0 or 1)
payment_summary = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
payment_summary["return_rate_%"] = (payment_summary["mean"] * 100).round(1)
payment_summary = payment_summary.sort_values("return_rate_%", ascending=False)

# Expected: COD 44.4%, UPI 18.9%, CARD 14.7%
print(payment_summary)

cod_rate = payment_summary.loc["COD", "return_rate_%"]
card_rate = payment_summary.loc["CARD", "return_rate_%"]
upi_rate = payment_summary.loc["UPI", "return_rate_%"]
print(f"\nResult: CONFIRMED - COD return rate is {cod_rate}%, compared with "
      f"UPI {upi_rate}% and CARD {card_rate}% (about {cod_rate / card_rate:.0f}x Card).")


# ---------------------------------------------------------------------
# Task 8: Segmentation by payment method and city tier
# ---------------------------------------------------------------------
print("\n========== Task 8: Payment method x city tier ==========")

# Return rate for every (payment_method, city_tier) combination
segment = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"])
segment["return_rate_%"] = (segment["mean"] * 100).round(1)
print(segment)

# Find the segment with the highest return rate
# Expected: COD + Tier-2 at 54.5%
highest = segment["return_rate_%"].idxmax()
print(f"\nHighest-risk segment: {highest[0]} + Tier-{highest[1]} cities "
      f"at {segment.loc[highest, 'return_rate_%']}%")

# Compare COD in Tier-1 vs Tier-2 cities
cod_tier1 = segment.loc[("COD", 1)]
cod_tier2 = segment.loc[("COD", 2)]
print(f"COD Tier-1: {int(cod_tier1['count'])} orders, return rate {cod_tier1['return_rate_%']}%")
print(f"COD Tier-2: {int(cod_tier2['count'])} orders, return rate {cod_tier2['return_rate_%']}%")
print("So COD risk is not the same everywhere: it is concentrated in Tier-2 cities.")


# ---------------------------------------------------------------------
# Task 9: Correlation analysis
# ---------------------------------------------------------------------
# Strength bands: negligible 0-0.19, weak 0.2-0.39, moderate 0.4-0.69, strong 0.7-1.0
print("\n========== Task 9: Correlation ==========")

columns = ["rating", "returned", "discount_pct", "quantity"]
corr_matrix = merged[columns].corr()
print(corr_matrix.round(3))


# Function that gives the strength band of a correlation value
def get_band(r):
    r = abs(r)
    if r < 0.2:
        return "negligible"
    elif r < 0.4:
        return "weak"
    elif r < 0.7:
        return "moderate"
    else:
        return "strong"


# Print every pair once (6 pairs). Expected: all are negligible
print("\nPairwise correlations:")
for i in range(len(columns)):
    for j in range(i + 1, len(columns)):
        r = corr_matrix.loc[columns[i], columns[j]]
        print(f"{columns[i]} vs {columns[j]}: r = {r:.3f} -> {get_band(r)}")

r_discount = corr_matrix.loc["discount_pct", "returned"]
print(f"\nHypothesis 'higher discounts reduce returns': BUSTED "
      f"(r = {r_discount:.2f}, which is {get_band(r_discount)}).")


# ---------------------------------------------------------------------
# Task 10: Monthly revenue, with and without the outliers
# ---------------------------------------------------------------------
print("\n========== Task 10: Monthly revenue ==========")

# Convert order_date to a date and take the year-month (e.g. 2026-01)
merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.strftime("%Y-%m")

# (1) Monthly revenue including the 2 outlier orders
# Expected: 2026-01 = 29582.10 is the highest month
monthly_with = merged.groupby("year_month")["order_value"].sum().round(2)
print("(1) Monthly revenue INCLUDING outliers:")
for month, value in monthly_with.items():
    print(month, f"{value:.2f}")
print("Highest month:", monthly_with.idxmax())

# (2) Monthly revenue excluding the 2 outlier orders
# Expected: 2026-03 = 20318.90 is the highest month
monthly_without = merged[merged["is_outlier"] == False].groupby("year_month")["order_value"].sum().round(2)
print("\n(2) Monthly revenue EXCLUDING outliers:")
for month, value in monthly_without.items():
    print(month, f"{value:.2f}")
print("Highest month:", monthly_without.idxmax())

print("\nConclusion: January only looks like the best month because both bulk orders were placed "
      "in January (O0011 on 2026-01-28 and O0098 on 2026-01-10). After removing them, "
      "March is the real peak month. That is why we found outliers (Task 6) before this step.")
