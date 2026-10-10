# Mamaearth Returns-vs-Margin Pipeline

**SQL → Python (pandas) → GenAI (Gemini).** This is an end-to-end pipeline that checks whether product returns are eating into Mamaearth's margins, and explains the answer in plain business language.

---

## Contents
1. [The problem we are solving](#1-the-problem-we-are-solving)
2. [Key results at a glance](#2-key-results-at-a-glance)
3. [How the pipeline works](#3-how-the-pipeline-works)
4. [Repository structure](#4-repository-structure)
5. [Requirements](#5-requirements)
6. [Getting started (step by step)](#6-getting-started-step-by-step)
7. [Part 1: SQL relational layer and reporting](#7-part-1--sql-relational-layer--reporting)
8. [Part 2: Python data wrangling and EDA](#8-part-2--python-data-wrangling--eda)
9. [Part 3: GenAI insight narrator](#9-part-3--genai-insight-narrator)
10. [Methods and tools used](#10-methods-and-tools-used)
11. [Data-quality issues and how they are handled](#11-data-quality-issues-and-how-they-are-handled)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. The problem we are solving

**Scenario.** I'm a Data Analyst on Mamaearth's Growth Analytics team. The team suspects that **returns are eating into margins on a subset of orders**, but nobody has built the pipeline to prove it end to end.

**Business questions:**
- What is the **true revenue** once data errors (duplicate orders, missing values, typing inconsistencies) are cleaned out?
- Which orders are returned most often: does **Cash on Delivery (COD)** return more than prepaid (Card, UPI)?
- Where exactly is the return problem concentrated? For example, **which payment method in which city tier**?
- Do **discounts** reduce returns?
- Which month was really the **best month for revenue**, once one-off bulk orders are set aside?
- What should the **regional ops and finance heads** do about it? They need an answer they can act on without reading a notebook.

**What we built:** three connected layers.

| Layer | Folder | Job |
|---|---|---|
| 1. SQL relational store | `sql/` | Load the raw orders into SQLite and answer 9 business report queries |
| 2. Python analysis | `analysis/` | Clean the data, test hypotheses, find patterns, draw 2 charts, and export the verified numbers |
| 3. GenAI narrative | `narrator/` | Turn the verified numbers into a Situation–Complication–Resolution (SCR) business brief using Gemini, with a fully offline fallback |

**Ground rule:** no layer reports a number it did not calculate itself or receive from the layer before it. Nothing is typed in by hand, not in the charts, the JSON or the AI prompt.

---

## 2. Key results at a glance

| Question | Answer | Source |
|---|---|---|
| Raw revenue (all 180 order rows) | **₹99,860.20** | Part 1 Report (a); recalculated in Part 2 |
| True revenue after cleaning (175 orders) | **₹97,358.30** | Part 2 Task 5 |
| Why the two differ | **₹2,501.90** = exactly the 5 double-submitted duplicate orders (O0176–O0180) | Part 2 Task 5 |
| Return rate by payment method | **COD 44.4%**, UPI 18.9%, CARD 14.7%. COD returns about 3× as often as Card. | Part 2 Task 7 |
| Highest-risk segment | **COD orders in Tier-2 cities: 54.5%** returned (vs 37.5% for COD in Tier-1) | Part 2 Task 8 |
| Do discounts reduce returns? | **No.** The correlation is negligible (r = −0.09). | Part 2 Task 9 |
| Best revenue month | **March 2026, ₹20,318.90.** January (₹29,582.10) only looked best because of 2 bulk outlier orders. | Part 2 Task 10 |

**Recommendation (in the narrative):**
- Target COD orders in Tier-2 cities first: confirm them before dispatch and offer an incentive to pay in advance.
- Fix the double-submit bug at checkout.
- Report revenue only after removing duplicate orders.
- Review bulk orders separately.

---

## 3. How the pipeline works

```
 data/*.csv  (raw, never edited by hand)
     │
     ├──────────────▶ PART 1: SQL (SQLite)
     │                 sql/schema.sql    → create tables
     │                 sql/seed_data.sql → load raw rows (blank cells → NULL)
     │                 sql/reports.sql   → 9 reports; Report (a) raw total = 99,860.20
     │                                                      │
     │                                         must MATCH   │  (cross-check)
     ▼                                                      ▼
 PART 2: Python (pandas)   analysis/clean_and_eda.py
     clean → merge → reconcile with Part 1 → outliers → hypotheses → trend
     │
     ├──▶ analysis/visualize.py ──▶ visualizations/*.png  (2 charts)
     │
     └──▶ narrator/findings.json  (verified numbers, written by code)
                │
                ▼
 PART 3: GenAI   narrator/generate_narrative.py
     ├─ Gemini API (when a free GEMINI_API_KEY is set)  → narrator/sample_output.txt
     └─ Offline template (no key, no internet)
     → SCR narrative + automatic check that 5 key figures are present
```

**How each layer feeds the next:**
- **Part 1 → Part 2.** The brief requires Part 2 to read the raw CSVs, not the database, so Parts 1 and 2 can run in any order. Part 2 recalculates Part 1's raw total from the same rows and gets the same **₹99,860.20**. It then shows that the gap to its cleaned total is exactly the duplicates it removed. If the Part 1 database (`mamaearth.db`) exists, Part 2 also runs the SQL total itself and prints **MATCH**.
- **Part 2 → Part 3.** The final step of `clean_and_eda.py` writes **`narrator/findings.json`**. The narrator reads only this file. The Gemini prompt and the offline template take every number from it, so new data gives a new narrative automatically.

---

## 4. Repository structure

```
<repo>/
├── README.md                  ← this guide
├── requirements.txt           ← Python packages to install
├── sql/
│   ├── schema.sql             ← Part 1 Task 1: CREATE TABLE customers, products, orders
│   ├── seed_data.sql          ← Part 1 Task 2: INSERT all rows from the CSVs (re-runnable)
│   └── reports.sql            ← Part 1 Task 3: reports (a)–(i), each with its real output above it
├── data/
│   ├── customers.csv          ← 45 customers  (customer_id, name, city, city_tier, signup_date, acquisition_source)
│   ├── products.csv           ← 16 products   (product_id, product_name, category, price in INR)
│   └── orders.csv             ← 180 orders    (order_id, customer_id, product_id, order_date, quantity,
│                                                discount_pct, payment_method, rating, returned)
├── analysis/
│   ├── clean_and_eda.py       ← Part 2 Tasks 1–10, then writes narrator/findings.json
│   └── visualize.py           ← Part 2 Task 11: the 2 charts
├── visualizations/
│   ├── return_rate_by_payment.png   ← bar chart: return rate by payment method
│   └── monthly_revenue_trend.png    ← line chart: monthly revenue, outliers excluded
└── narrator/
    ├── findings.json          ← verified numbers from Part 2 (generated, never hand-typed)
    ├── generate_narrative.py  ← Part 3: Gemini SCR narrative + offline fallback + accuracy checker
    └── sample_output.txt      ← one real Gemini run, saved and checked
```

---

## 5. Requirements

| What | Version | Why |
|---|---|---|
| **Python** | 3.9 or newer | Runs Parts 2 and 3 |
| **pandas** | ≥ 2.0 | Data cleaning and analysis |
| **matplotlib** | ≥ 3.7 | Charts |
| **google-genai** | ≥ 1.0 | Gemini API client (`from google import genai`). Only needed for the online path. |
| **SQLite** (`sqlite3` command-line tool) | any recent version | Runs Part 1 |
| **Gemini API key** | **optional**, free | From Google AI Studio. Without a key, Part 3 runs fully offline. |
| **Git** | any | To clone the repo (or use GitHub's **Code → Download ZIP**) |

**Free path:** Google AI Studio issues a **free** Gemini API key with a free usage tier. Use that, and never a paid-only key. Part 3 also has a fully offline fallback, so the whole pipeline can be run and graded with **no API key, no cost and no internet**.

---

## 6. Getting started (step by step)

Choose **one** way to run it: on your own computer (Option A) or in Google Colab (Option B). Run every command from the **main repo folder**.

### Option A: on your own computer

**Step 1. Get the code and install the packages**
```bash
git clone <this-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

**Step 2. Install the SQLite command-line tool, if you don't have it** (check with `sqlite3 --version`)
- **Windows:** download "sqlite-tools" from sqlite.org/download.html, unzip it, and add the folder to your PATH.
- **macOS:** already installed. Otherwise run `brew install sqlite`.
- **Linux:** `sudo apt-get install sqlite3`

**Step 3. Run Part 1 (SQL)**
```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 -header -column mamaearth.db < sql/reports.sql
```

**Step 4. Run Part 2 (Python analysis)**
```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

**Step 5. Run Part 3 (GenAI narrative)**
```bash
# Without a key (offline template), works straight away:
python narrator/generate_narrative.py

# With a free Gemini key (set it as an environment variable, never inside a file):
export GEMINI_API_KEY="your-key-here"        # macOS / Linux
set GEMINI_API_KEY=your-key-here             # Windows (Command Prompt)
$env:GEMINI_API_KEY="your-key-here"          # Windows (PowerShell)
python narrator/generate_narrative.py
```

### Option B: in Google Colab (nothing to install locally)
Open a new notebook at colab.research.google.com and run these cells:
```python
!git clone <this-repo-url>
%cd <repo-folder>
!pip install -q -r requirements.txt
!apt-get -qq install -y sqlite3 > /dev/null
```
```python
# Part 1
!sqlite3 mamaearth.db < sql/schema.sql
!sqlite3 mamaearth.db < sql/seed_data.sql
!sqlite3 -header -column mamaearth.db < sql/reports.sql
```
```python
# Part 2
!python analysis/clean_and_eda.py
!python analysis/visualize.py
```
```python
# Part 3: optional key from Colab Secrets (the key icon on the left; turn on notebook access)
import os
from google.colab import userdata
os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")   # use your secret's name; skip this cell to run offline
!python narrator/generate_narrative.py
```

### How you know it worked
| Step | You should see |
|---|---|
| Part 1 | Report (a): `180  99860.20  554.78`. Every report matches the `-- Output:` comment above it in `sql/reports.sql`. |
| Part 2 | `Rs 97358.30`, `Difference : 2501.90`, `CONFIRMED`, `COD + Tier-2 cities at 54.5%`, `Highest month: 2026-03`, and (if Part 1 ran first) `MATCH`. |
| Charts | Two PNG files in `visualizations/` |
| Part 3 | A narrative with **Situation / Complication / Resolution**, then **5 × `[PASS]`** |

Everything is deterministic. Running the same steps again gives exactly the same numbers, the same `findings.json` and identical charts.

---

## 7. Part 1: SQL relational layer and reporting

**Tool:** SQLite. **Files:** `sql/schema.sql`, `sql/seed_data.sql`, `sql/reports.sql`

**Task 1: Schema.** Three tables with data types, `PRIMARY KEY`, `NOT NULL`, `DEFAULT 0` (on `returned`) and `FOREIGN KEY ... REFERENCES` links from orders to customers and products. `discount_pct` and `rating` are deliberately **nullable**, because an order can have no promo code or no rating yet.

**Task 2: Seed data.** The file holds `INSERT` statements generated row by row from the CSVs and is safe to re-run. Blank CSV cells load as real **`NULL`**, not empty strings. Row counts: **45 / 16 / 180**.

**Task 3: Reports**, all run on the **raw** data. Each query's exact output is pasted above it.

| # | SQL technique | Question | Result |
|---|---|---|---|
| a | `JOIN`, `SUM`, `AVG`, `COALESCE` | Orders, revenue and average order value (NULL discount = 0%) | 180 · ₹99,860.20 · ₹554.78 |
| b | `COUNT(*)` vs `COUNT(col)` | How many orders have no rating? | 180 vs 165 → **15 unrated** |
| c | `LEFT JOIN` + `NOT IN` | Customers with zero orders (two independent ways) | Both return **C045 Vihaan** |
| d | `GROUP BY` + `HAVING` | Cities with return rate above 20% | Jaipur 42.1% · Lucknow 30.6% · Bangalore 24.2% |
| e | `ORDER BY` + `LIMIT` / `OFFSET` | Top 5 customers by spend; then ranks 3–5 | C043 Reyansh ₹12,920.00 leads; OFFSET 2 returns C008, C011, C042 |
| f | Three-table `JOIN` | Orders and revenue by category | Haircare ₹44,956.10 · Skincare ₹27,346.00 · Babycare ₹16,805.00 · PersonalCare ₹10,753.10 |
| g | `LIKE` | Customers whose name starts with "A" | 10 customers |
| h | `DISTINCT` | Acquisition sources | Ad, Organic, Referral, Social |
| i | `ALTER TABLE` + `UPDATE ... CASE` | Add `loyalty_tier`: Gold for Tier-1 cities, else Silver | Gold 28 · Silver 17 |

---

## 8. Part 2: Python data wrangling and EDA

**Tools:** Python, pandas, matplotlib. **Files:** `analysis/clean_and_eda.py`, `analysis/visualize.py`
This part reads the **raw CSVs directly** and prints every intermediate result.

| # | Task | Method | Result |
|---|---|---|---|
| 1 | Load and inspect | `pd.read_csv`, `.shape`, `.isnull().sum()` | orders `(180, 9)`; 12 missing discounts, 15 missing ratings |
| 2 | Standardise casing | `.str.strip().str.upper()` | 7 spellings → 3 values: CARD 70, UPI 55, COD 55 |
| 3 | Remove duplicates | `.duplicated(subset=[all columns except order_id], keep="first")` | 5 dropped (O0176–O0180) → `(175, 9)` |
| 4 | Fill missing values | `.fillna(0)` for discount; `.median()` for rating | median rating 3.0; no nulls left |
| 5 | Merge and reconcile | `.merge()`; order value = qty × price × (1 − discount/100) | ₹97,358.30. The gap of ₹2,501.90 to Part 1 is exactly the 5 duplicates. |
| 6 | Outliers | IQR rule: Q1 = 1, Q3 = 2, limits −0.5 to 3.5 | O0011 (qty 25) and O0098 (qty 30) **flagged** in `is_outlier`, not dropped |
| 7 | COD hypothesis | `groupby("payment_method")["returned"].agg(["count","mean"])` | COD 44.4% vs UPI 18.9% vs CARD 14.7% → **Confirmed** |
| 8 | Segmentation | `groupby(["payment_method","city_tier"])` | Highest risk: **COD + Tier-2, 54.5%** (Tier-1 COD 37.5%) |
| 9 | Correlation | `.corr()` with strength bands (negligible / weak / moderate / strong) | All 6 pairs negligible; "discounts reduce returns" **Busted** (r = −0.09) |
| 10 | Outlier-corrected trend | `pd.to_datetime`, monthly sums with and without outliers | January leads only because of the bulk orders; **March (₹20,318.90) is the true peak** |
| 11 | Two charts | matplotlib (`visualize.py`) | `return_rate_by_payment.png`, `monthly_revenue_trend.png` |
| — | Export | `json.dump` | Writes `narrator/findings.json` for Part 3 |

---

## 9. Part 3: GenAI insight narrator

**Tools:** Google Gemini API (`google-genai`, model `gemini-3.1-flash-lite`, free tier). **File:** `narrator/generate_narrative.py`

| Task | What the code does |
|---|---|
| 1. `findings.json` | Written by the last step of `clean_and_eda.py`. Holds the 7 required figures, plus extra context and a note on where the numbers came from. |
| 2. `generate_scr_narrative(findings)` | Calls `client.models.generate_content(...)`. A separate **system instruction** sets the role ("senior data analyst writing for Mamaearth's regional ops and finance heads"), the three labelled sections (Situation, Complication, Resolution), and the rule that **every number must come from the findings with the same value**. The user prompt is built from the `findings` dict, with no hardcoded numbers. |
| 3. Parameters and errors | `temperature=0.0`, because this is a factual report, not creative writing. `max_output_tokens=2048`. `timeout=30000` milliseconds (30 s). Wrapped in `try/except`, it always returns a dict: `{"status": "success", "narrative", "tokens"}` or `{"status": "error", "narrative": None, "message"}`. |
| 4. Offline fallback | `generate_scr_narrative_offline(findings)` fills the same three sections from an f-string template, with no key and no internet. It's used automatically when there is no key or when the Gemini call fails. |
| 5. Accuracy checker | `check_numeric_accuracy()` prints PASS or FAIL for each of the 5 required figures: **97,358.30**, **44.4**, **54.5**, **2,501.90**, and **March + 20,318.90**. It also warns if the narrative contains any number not found in `findings.json`. |
| Sample | A successful Gemini run is saved to `narrator/sample_output.txt`, and the checker runs on that saved file. |

**API key safety:** the key is only read from the `GEMINI_API_KEY` environment variable, or from Colab Secrets. It is never written into code or committed to the repo.

---

## 10. Methods and tools used

| Area | Tools | Methods |
|---|---|---|
| Data storage and reporting | **SQLite**, SQL | Relational schema (primary and foreign keys, constraints), `JOIN`s, aggregation, `GROUP BY`/`HAVING`, `LEFT JOIN` vs `NOT IN` cross-check, ranking with `LIMIT`/`OFFSET`, `ALTER`/`UPDATE ... CASE` |
| Data cleaning | **Python**, **pandas** | Text standardisation, duplicate detection on a natural key, imputation (0 for discount, median for rating), merging, reconciliation against SQL |
| Exploratory analysis | pandas | Hypothesis testing with group rates, multi-level segmentation, Pearson correlation with strength bands, IQR outlier detection, time series by month |
| Visualisation | **matplotlib** | Sorted bar chart with value labels; line chart with the peak labelled |
| GenAI | **Google Gemini API** (`google-genai`) | System instructions, prompts built from data, parameter locking (temperature, token limit, timeout), structured error handling, deterministic offline fallback, automatic number checking |
| Pipeline design | JSON, environment variables, Git | Each layer passes verified numbers to the next. Results are reproducible. No hardcoded numbers or secrets. |

---

## 11. Data-quality issues and how they are handled

All cleaning happens in Python code. **The source CSVs are never edited by hand.**

| Issue in the raw data | How it is handled |
|---|---|
| Blank `discount_pct` (12) and `rating` (15) cells | SQL stores them as `NULL`. pandas fills discount with 0 (no promo code) and rating with the median (3.0). |
| `payment_method` typed 7 different ways (COD/cod, Card/card/CARD, UPI/upi) | Standardised to 3 upper-case values |
| 5 double-submitted orders (O0176–O0180) | Detected on every column except `order_id`, then dropped |
| 2 bulk orders (quantities 25 and 30) | Flagged as outliers with the IQR rule, **kept** in the data, and excluded only from the corrected monthly trend |

**Pitfalls avoided:**
- SQL uses `/ 100.0`, not `/ 100`, because whole-number division would turn every discount into 0.
- Duplicates are removed **before** missing values are filled.
- Outliers are found **before** the monthly trend.
- `findings.json` is always written by code.
- The Gemini timeout is in milliseconds.

---

## 12. Troubleshooting

| Problem | Fix |
|---|---|
| `sqlite3: command not found` | Install SQLite (section 6, Step 2). In Colab: `!apt-get -qq install -y sqlite3` |
| `duplicate column name: loyalty_tier` | Report (i) already ran. Re-run `schema.sql` and `seed_data.sql`, then `reports.sql`. |
| `FileNotFoundError: data/orders.csv` | Run the commands from the **main repo folder**, not from inside `analysis/` |
| `narrator/findings.json not found` | Run `python analysis/clean_and_eda.py` first. Its last step creates the file. |
| Narrator says "using the offline template" | No `GEMINI_API_KEY` is set. This is expected without a key. Set the key to use Gemini. |
| `Gemini call failed: ... API key not valid` / `429 quota` | Check the key, or wait a minute for the free-tier limit. The script falls back to the offline narrative automatically. |
| `ModuleNotFoundError: google` | Run `pip install -r requirements.txt`. This is only needed for the Gemini path. |
