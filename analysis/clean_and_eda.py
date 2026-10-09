"""Part 2: pandas data wrangling and EDA over the raw source CSVs.

Reads data/orders.csv, data/customers.csv and data/products.csv directly. It
does not read the SQL database, so Part 1 and Part 2 can run in either order.
Every intermediate result the acceptance criteria refer to is printed, and
each one is also asserted, so a wrong number stops the script instead of
flowing silently into later layers.

Run from anywhere:
    python analysis/clean_and_eda.py
"""

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

# Natural key of an order: every column except order_id, which differs on the
# double-submitted rows by design.
NATURAL_KEY = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned",
]

# Part 1 Report (a) raw total, which Task 5 reconciles against.
PART1_RAW_TOTAL = 99860.20


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def order_value(df):
    """quantity * price * (1 - discount_pct/100). Needs price and a non-null discount."""
    return df["quantity"] * df["price"] * (1 - df["discount_pct"] / 100)


# --------------------------------------------------------------------------
# Task 1: load and inspect
# --------------------------------------------------------------------------
def task1_load():
    section("Task 1: Load and inspect")
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")

    print("orders.shape   :", orders.shape)
    print("customers.shape:", customers.shape)
    print("products.shape :", products.shape)
    print("\norders.dtypes:\n" + orders.dtypes.to_string())
    print("\nNull counts in raw orders:\n" + orders.isnull().sum().to_string())
    print("\norders.head():\n" + orders.head().to_string())

    assert orders.shape == (180, 9), orders.shape
    return orders, customers, products


# --------------------------------------------------------------------------
# Task 2: standardise payment_method casing
# --------------------------------------------------------------------------
def task2_payment_method(orders):
    section("Task 2: Standardise payment_method casing")
    raw_values = orders["payment_method"].unique()
    print(f"Before: {len(raw_values)} distinct raw values -> {list(raw_values)}")
    print("Before counts:\n" + orders["payment_method"].value_counts().to_string())
    assert len(raw_values) == 7, raw_values

    orders = orders.copy()
    orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

    counts = orders["payment_method"].value_counts()
    print(f"\nAfter: {orders['payment_method'].nunique()} distinct values")
    print("After counts:\n" + counts.to_string())
    assert counts.to_dict() == {"CARD": 70, "UPI": 55, "COD": 55}, counts.to_dict()
    return orders


# --------------------------------------------------------------------------
# Task 3: remove duplicate orders
# --------------------------------------------------------------------------
def task3_deduplicate(orders):
    section("Task 3: Remove duplicate orders")
    is_dup = orders.duplicated(subset=NATURAL_KEY, keep="first")
    dropped = orders[is_dup]
    print(f"Duplicate rows flagged on the natural key: {is_dup.sum()}")
    print("Dropped order_ids:", ", ".join(dropped["order_id"]))

    # Show each dropped row next to the earlier original it repeats.
    originals = orders[~is_dup].merge(dropped[NATURAL_KEY + ["order_id"]],
                                      on=NATURAL_KEY, suffixes=("_kept", "_dropped"))
    print("\nKept original -> dropped duplicate:")
    print(originals[["order_id_kept", "order_id_dropped"] + NATURAL_KEY].to_string(index=False))

    orders_clean = orders[~is_dup].reset_index(drop=True)
    print("\norders_clean.shape:", orders_clean.shape)

    assert is_dup.sum() == 5
    assert list(dropped["order_id"]) == ["O0176", "O0177", "O0178", "O0179", "O0180"]
    assert orders_clean.shape == (175, 9), orders_clean.shape
    return orders_clean, dropped


# --------------------------------------------------------------------------
# Task 4: impute missing values (on the deduplicated frame)
# --------------------------------------------------------------------------
def task4_impute(orders_clean):
    section("Task 4: Impute missing values")
    orders_clean = orders_clean.copy()

    n_disc = orders_clean["discount_pct"].isnull().sum()
    print(f"discount_pct missing: {n_disc} rows -> filled with 0 (no promo code applied)")
    orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)

    n_rating = orders_clean["rating"].isnull().sum()
    rating_median = orders_clean["rating"].median()   # median skips NaN
    print(f"rating median of non-null values (deduplicated frame): {rating_median}")
    print(f"rating missing: {n_rating} rows -> filled with {rating_median}")
    orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)

    remaining = orders_clean[["discount_pct", "rating"]].isnull().sum().to_dict()
    print("Nulls remaining:", remaining)

    assert n_disc == 12 and n_rating == 15
    assert rating_median == 3.0
    assert remaining == {"discount_pct": 0, "rating": 0}
    return orders_clean


# --------------------------------------------------------------------------
# Task 5: merge and reconcile against Part 1
# --------------------------------------------------------------------------
def task5_merge_and_reconcile(orders_clean, dropped, customers, products):
    section("Task 5: Merge and reconcile against Part 1")
    merged = (orders_clean
              .merge(products, on="product_id", how="left", validate="many_to_one")
              .merge(customers, on="customer_id", how="left", validate="many_to_one"))
    assert len(merged) == 175 and merged["price"].notnull().all() and merged["city"].notnull().all()

    merged["order_value"] = order_value(merged)
    clean_total = round(merged["order_value"].sum(), 2)
    print(f"merged.shape: {merged.shape}")
    print(f"Total order_value across {len(merged)} cleaned rows: Rs {clean_total:,.2f}")

    # Independent check: value the 5 dropped rows straight from the raw rows.
    # Their discounts are all non-null, but COALESCE to 0 the same way Part 1 does.
    dropped_valued = dropped.merge(products, on="product_id", how="left")
    dropped_valued["discount_pct"] = dropped_valued["discount_pct"].fillna(0)
    dropped_valued["order_value"] = order_value(dropped_valued)
    dropped_total = round(dropped_valued["order_value"].sum(), 2)
    print("\nThe 5 dropped duplicate rows, valued independently:")
    print(dropped_valued[["order_id", "product_id", "quantity", "price",
                          "discount_pct", "order_value"]].to_string(index=False))
    print(f"Combined order_value of dropped rows: Rs {dropped_total:,.2f}")

    delta = round(PART1_RAW_TOTAL - clean_total, 2)
    print(f"\nPart 1 raw total - Part 2 clean total = Rs {PART1_RAW_TOTAL:,.2f} - "
          f"Rs {clean_total:,.2f} = Rs {delta:,.2f}")

    assert clean_total == 97358.30, clean_total
    assert dropped_total == 2501.90, dropped_total
    assert delta == dropped_total, (delta, dropped_total)

    print("\nReconciliation note:")
    print(
        f"Part 2's cleaned total of Rs {clean_total:,.2f} is Rs {delta:,.2f} lower than "
        f"Part 1 Report (a)'s raw total of Rs {PART1_RAW_TOTAL:,.2f}. That whole gap is the "
        f"5 double-submitted duplicate orders removed in Task 3 "
        f"({', '.join(dropped['order_id'])}): valued on their own, their combined "
        f"order_value is exactly Rs {dropped_total:,.2f}, equal to the delta to the paisa. "
        f"The Task 4 imputation explains none of it. Filling the 12 missing discount_pct "
        f"values with 0 gives the same result as Part 1's COALESCE(discount_pct, 0), and "
        f"rating is not part of the order_value formula, so neither step changes any "
        f"order_value."
    )
    return merged


# --------------------------------------------------------------------------
# Task 6: IQR outlier detection on quantity (flag, do not drop)
# --------------------------------------------------------------------------
def task6_iqr_outliers(merged):
    section("Task 6: IQR outlier detection on quantity")
    q1 = merged["quantity"].quantile(0.25)
    q3 = merged["quantity"].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    print(f"Q1 = {q1}, Q3 = {q3}, IQR = {iqr}, lower = {lower}, upper = {upper}")

    merged = merged.copy()
    merged["is_outlier"] = ~merged["quantity"].between(lower, upper)
    outliers = merged[merged["is_outlier"]]
    print(f"\nRows outside [{lower}, {upper}]: {len(outliers)} (flagged in is_outlier, not dropped)")
    print(outliers[["order_id", "customer_id", "product_name", "quantity",
                    "order_value", "returned"]].to_string(index=False))
    print(f"Rows kept in the dataset: {len(merged)}")

    assert (q1, q3, iqr, lower, upper) == (1.0, 2.0, 1.0, -0.5, 3.5)
    assert outliers["order_id"].tolist() == ["O0011", "O0098"]
    assert outliers["quantity"].tolist() == [25, 30]
    assert len(merged) == 175
    return merged


# --------------------------------------------------------------------------
# Task 7: hypothesis - does COD have a higher return rate?
# --------------------------------------------------------------------------
def task7_cod_hypothesis(merged):
    section("Task 7: Hypothesis - does COD have a higher return rate?")
    print("Hypothesis: Cash-on-Delivery (COD) orders are returned at a higher rate than "
          "prepaid (CARD, UPI) orders, because a COD buyer has paid nothing up front "
          "and can refuse the parcel at the door at no cost.")

    by_payment = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
    by_payment["return_rate_pct"] = (by_payment["mean"] * 100).round(1)
    by_payment = by_payment.sort_values("return_rate_pct", ascending=False)
    print("\ngroupby('payment_method')['returned'].agg(['count','mean']):")
    print(by_payment.to_string())

    rates = by_payment["return_rate_pct"].to_dict()
    assert rates == {"COD": 44.4, "UPI": 18.9, "CARD": 14.7}, rates
    assert rates["COD"] > max(rates["CARD"], rates["UPI"])
    print(f"\nVerdict: CONFIRMED. COD returns at {rates['COD']}%, versus "
          f"{rates['UPI']}% for UPI and {rates['CARD']}% for CARD "
          f"({rates['COD'] / rates['CARD']:.1f}x the CARD rate).")
    return by_payment


# --------------------------------------------------------------------------
# Task 8: multi-level segmentation (payment_method x city_tier)
# --------------------------------------------------------------------------
def task8_segmentation(merged):
    section("Task 8: Multi-level segmentation - payment_method x city_tier")
    seg = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "sum", "mean"])
    seg = seg.rename(columns={"count": "orders", "sum": "returned_orders"})
    seg["return_rate_pct"] = (seg["mean"] * 100).round(1)
    seg = seg.drop(columns="mean")
    print(seg.to_string())

    top = seg["return_rate_pct"].idxmax()
    top_row = seg.loc[top]
    cod1, cod2 = seg.loc[("COD", 1)], seg.loc[("COD", 2)]
    print(f"\nHighest-risk segment: {top[0]} + Tier-{top[1]} cities at "
          f"{top_row['return_rate_pct']}% ({int(top_row['returned_orders'])} of "
          f"{int(top_row['orders'])} orders returned).")
    print(f"COD risk is not uniform across tiers: {int(cod1['orders'])} Tier-1 COD orders "
          f"return at {cod1['return_rate_pct']}%, versus {int(cod2['orders'])} Tier-2 COD "
          f"orders at {cod2['return_rate_pct']}%. The blended COD rate hides that the "
          f"problem is concentrated in Tier-2 cities.")

    assert top == ("COD", 2) and top_row["return_rate_pct"] == 54.5
    assert (int(cod1["orders"]), cod1["return_rate_pct"]) == (32, 37.5)
    assert (int(cod2["orders"]), cod2["return_rate_pct"]) == (22, 54.5)
    return seg


# --------------------------------------------------------------------------
# Task 9: correlation analysis
# --------------------------------------------------------------------------
def strength_band(r):
    a = abs(r)
    if a < 0.2:
        return "negligible"
    if a < 0.4:
        return "weak"
    if a < 0.7:
        return "moderate"
    return "strong"


def task9_correlation(merged):
    section("Task 9: Correlation analysis")
    cols = ["rating", "returned", "discount_pct", "quantity"]
    corr = merged[cols].corr()
    print("Correlation matrix (Pearson, 175 cleaned rows):")
    print(corr.round(3).to_string())

    print("\nBands: negligible |r| 0-0.19, weak 0.2-0.39, moderate 0.4-0.69, strong 0.7-1.0")
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            pairs.append({"pair": f"{a} vs {b}", "r": round(r, 3), "band": strength_band(r)})
            print(f"  {a:>12} vs {b:<12} r = {r:+.3f}  -> {strength_band(r)}")

    r_disc_ret = corr.loc["discount_pct", "returned"]
    print(f"\nHypothesis 'higher discounts reduce returns': BUSTED. discount_pct vs returned "
          f"r = {r_disc_ret:+.2f}, which is negligible. The sign is negative, but the "
          f"relationship is too weak to support the claim.")

    assert len(pairs) == 6 and all(p["band"] == "negligible" for p in pairs), pairs
    assert round(r_disc_ret, 2) == -0.09, r_disc_ret
    return corr, pairs


# --------------------------------------------------------------------------
# Task 10: outlier-corrected monthly time series
# --------------------------------------------------------------------------
def task10_monthly_trend(merged):
    section("Task 10: Outlier-corrected monthly revenue")
    merged = merged.copy()
    merged["order_date"] = pd.to_datetime(merged["order_date"])
    merged["year_month"] = merged["order_date"].dt.strftime("%Y-%m")

    with_outliers = merged.groupby("year_month")["order_value"].sum().round(2)
    corrected = merged[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)

    print("(1) Monthly order_value INCLUDING the 2 outlier orders:")
    print(with_outliers.map("{:,.2f}".format).to_string())
    print(f"    Highest month: {with_outliers.idxmax()}")
    print("\n(2) Monthly order_value EXCLUDING the 2 outlier orders (outlier-corrected):")
    print(corrected.map("{:,.2f}".format).to_string())
    print(f"    Highest month: {corrected.idxmax()}")

    out = merged[merged["is_outlier"]]
    desc = " and ".join(f"{r.order_id} ({r.quantity} units, Rs {r.order_value:,.2f}) on "
                        f"{r.order_date:%Y-%m-%d}" for r in out.itertuples())
    print(f"\nJanuary's apparent lead is an artifact. Both bulk orders landed in January: "
          f"{desc}. Remove them and January drops from Rs {with_outliers['2026-01']:,.2f} to "
          f"Rs {corrected['2026-01']:,.2f}, and March (Rs {corrected['2026-03']:,.2f}) is the "
          f"genuine peak month. This is why outliers are flagged in Task 6 before the time "
          f"series is built here, not after.")

    assert with_outliers.idxmax() == "2026-01" and with_outliers["2026-01"] == 29582.10
    assert with_outliers["2026-06"] == 11615.40
    assert corrected.to_dict() == {
        "2026-01": 11637.10, "2026-02": 13195.50, "2026-03": 20318.90,
        "2026-04": 9495.30, "2026-05": 13151.10, "2026-06": 11615.40,
    }, corrected.to_dict()
    assert corrected.idxmax() == "2026-03"
    assert sorted(out["order_id"]) == ["O0011", "O0098"]
    return with_outliers, corrected


def run_pipeline():
    """Run Tasks 1-10 in order and return every result later layers use."""
    orders, customers, products = task1_load()
    orders = task2_payment_method(orders)
    orders_clean, dropped = task3_deduplicate(orders)
    orders_clean = task4_impute(orders_clean)
    merged = task5_merge_and_reconcile(orders_clean, dropped, customers, products)
    merged = task6_iqr_outliers(merged)
    by_payment = task7_cod_hypothesis(merged)
    segments = task8_segmentation(merged)
    corr, corr_pairs = task9_correlation(merged)
    monthly_raw, monthly_corrected = task10_monthly_trend(merged)
    return {
        "merged": merged,
        "dropped": dropped,
        "by_payment": by_payment,
        "segments": segments,
        "corr": corr,
        "corr_pairs": corr_pairs,
        "monthly_raw": monthly_raw,
        "monthly_corrected": monthly_corrected,
    }


if __name__ == "__main__":
    run_pipeline()
