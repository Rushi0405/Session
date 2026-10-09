# Mamaearth Returns-vs-Margin Pipeline

Mamaearth's Growth Analytics team suspects that returns are eating into margins on a subset of orders. This repository checks that end to end in three connected layers:

1. **SQL layer.** A SQLite store of the raw orders, plus nine report queries.
2. **Python analysis layer.** pandas cleans the data, tests hypotheses and saves two charts. Its last step writes the verified numbers to `narrator/findings.json`.
3. **GenAI narrative layer.** Gemini turns `findings.json` into a Situation–Complication–Resolution brief for the regional ops and finance heads. An offline template does the same when there is no API key.

**Rule followed throughout:** no layer reports a number it did not calculate itself or receive from the layer before it. Nothing is typed in by hand.

---

## Repository structure

```
<repo>/
├── README.md                  <- you are here: structure, run order, data flow
├── requirements.txt           <- Python packages (pandas, matplotlib, google-genai)
├── sql/
│   ├── schema.sql             <- Part 1 Task 1: creates customers, products, orders
│   ├── seed_data.sql          <- Part 1 Task 2: loads the 3 CSVs (blank cells -> NULL)
│   └── reports.sql            <- Part 1 Task 3: reports (a)-(i), each output pasted above it
├── data/
│   ├── customers.csv          <- raw source data (45 rows), never edited by hand
│   ├── products.csv           <- raw source data (16 rows)
│   └── orders.csv             <- raw source data (180 rows)
├── analysis/
│   ├── clean_and_eda.py       <- Part 2 Tasks 1-10, then writes narrator/findings.json
│   └── visualize.py           <- Part 2 Task 11: draws the 2 charts
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json          <- verified numbers, written by clean_and_eda.py
    ├── generate_narrative.py  <- Part 3: Gemini SCR narrative + offline fallback + checker
    └── sample_output.txt      <- one real Gemini run, saved and checked
```

---

## How the layers connect

```
data/*.csv ──▶ sql/seed_data.sql ──▶ SQLite ──▶ sql/reports.sql
   │                                              Report (a) raw total = 99,860.20
   │                                                        │ must match
   ▼                                                        ▼
analysis/clean_and_eda.py  (reads the raw CSVs directly; recalculates the raw total = 99,860.20)
   │  cleans: duplicates removed, missing values filled, outliers flagged
   │  results: 97,358.30 | COD 44.4% | COD + Tier-2 54.5% | true peak March 20,318.90
   ├──▶ analysis/visualize.py ──▶ visualizations/*.png
   └──▶ narrator/findings.json ──▶ narrator/generate_narrative.py
                                        ├─ Gemini (when GEMINI_API_KEY is set)
                                        └─ offline template (no key, no network)
                                        ──▶ narrative + 5-figure accuracy check
```

- **Part 1 → Part 2.** As the brief requires, Part 2 reads the raw CSVs, not the database, so Parts 1 and 2 can run in either order. Part 2 recalculates Part 1's raw total from the same 180 rows and gets the same **99,860.20**. It then shows that the **2,501.90** gap to its cleaned total is exactly the 5 duplicate orders it removed. If `mamaearth.db` exists, Part 2 also runs the SQL total and prints `MATCH`.
- **Part 2 → Part 3.** The last step of `clean_and_eda.py` writes `narrator/findings.json` from its own variables. The narrator reads only that file. Both the Gemini prompt and the offline template take every number from it, so a different `findings.json` produces a different narrative.

---

## Run order (top to bottom reproduces every number)

### Step 0: setup (once)
```bash
git clone <this-repo-url>
cd <repo>
pip install -r requirements.txt
```
You also need the `sqlite3` command-line tool. In Google Colab: `!apt-get -qq install -y sqlite3`.
Run every command from the main repo folder.

### Step 1: SQL layer (Part 1)
```bash
sqlite3 mamaearth.db < sql/schema.sql            # create the 3 tables
sqlite3 mamaearth.db < sql/seed_data.sql         # load the data (re-runnable)
sqlite3 -header -column mamaearth.db < sql/reports.sql   # run reports (a)-(i)
```
Expected results:
- **Load:** 45 customers, 16 products, 180 orders.
- **Report (a):** 180 orders, revenue **99860.20**, average order value **554.78**.
- **Other reports:** each report's output is pasted as a comment above its query in `sql/reports.sql`.

Report (i) runs `ALTER TABLE`. To run `reports.sql` again, re-run the first two commands first.

### Step 2: analysis layer (Part 2)
```bash
python analysis/clean_and_eda.py     # Tasks 1-10, prints every result, then writes narrator/findings.json
python analysis/visualize.py         # Task 11, saves the 2 charts in visualizations/
```
`clean_and_eda.py` prints each task's result. Its final step writes **`narrator/findings.json`**, which uses the Task 5 reconciliation and the Task 7, 8 and 10 results. Key results:

| Task | Result |
|---|---|
| 2. Payment-method casing | 7 raw values → 3 (CARD 70, UPI 55, COD 55) |
| 3. Duplicates removed | 5 (O0176–O0180) → 175 rows |
| 4. Missing values | 12 discounts → 0; 15 ratings → median 3.0 |
| 5. Cleaned revenue | **97,358.30**; gap to raw total **2,501.90** = the 5 duplicates |
| 6. IQR outliers (flagged, not dropped) | O0011 (qty 25), O0098 (qty 30) |
| 7. Return rate by payment | COD **44.4%**, UPI 18.9%, CARD 14.7% → hypothesis **Confirmed** |
| 8. Highest-risk segment | COD + Tier-2 cities **54.5%** (vs COD Tier-1 37.5%) |
| 9. Correlations | all 6 pairs negligible; "higher discounts reduce returns" **Busted** (r = -0.09) |
| 10. Monthly revenue | January 29,582.10 looks highest only because of the 2 bulk orders; outlier-corrected, **March 20,318.90** is the true peak |

Both scripts are deterministic. Re-running them gives identical numbers, the same `findings.json` and identical PNGs.

### Step 3: narrative layer (Part 3)

**Option A: with a free Gemini API key**
1. Get a free key from Google AI Studio (aistudio.google.com → Get API key). Use the free tier and never a paid-only key.
2. Put the key in an environment variable. Never put it in a file in this repo.
   ```bash
   export GEMINI_API_KEY="your-key-here"          # macOS / Linux
   set GEMINI_API_KEY=your-key-here               # Windows (cmd)
   python narrator/generate_narrative.py
   ```
   In Google Colab, store the key under **Secrets** (the key icon), then run:
   ```python
   import os
   from google.colab import userdata
   os.environ["GEMINI_API_KEY"] = userdata.get("SY_API_KEY")   # use your secret's name
   !python narrator/generate_narrative.py
   ```
3. A successful Gemini run is saved to `narrator/sample_output.txt`, and the checker runs on that saved file.

**Option B: no key at all (fully offline)**
```bash
python narrator/generate_narrative.py
```
With no `GEMINI_API_KEY`, the script uses `generate_scr_narrative_offline()`. This fills a template from `findings.json`, makes no network call and needs no setup. The script also falls back to this path if the Gemini call fails for any reason, such as a bad key, no network, a quota limit or a timeout.

**What the narrator does**

| Brief requirement | How `generate_narrative.py` meets it |
|---|---|
| Task 2: `generate_scr_narrative(findings)` | Uses `from google import genai` and `client.models.generate_content(...)`. A separate `system_instruction` fixes the role (senior data analyst writing for ops and finance heads), the three labelled sections (Situation, Complication, Resolution) and the rule that every number must come from the findings. The user prompt is built from the `findings` dict. |
| Task 3: parameter locking | `temperature=0.0`, because this is a factual report. `max_output_tokens=2048` is set explicitly. `HttpOptions(timeout=30000)` is in milliseconds, so 30 seconds. The whole call is in `try/except` and returns `{"status": "success", "narrative", "tokens"}` or `{"status": "error", "narrative": None, "message"}`. |
| Task 4: offline fallback | `generate_scr_narrative_offline(findings)` is an f-string template with the same three sections and the same return shape. It uses no key and no network. |
| Task 5: accuracy checker | `check_numeric_accuracy()` prints PASS or FAIL for each of the 5 figures: **97,358.30**, **44.4**, **54.5**, **2,501.90**, and **March + 20,318.90**. It removes commas before comparing. It's a hard pass/fail on the offline path, and it also runs on the saved `sample_output.txt`. |
| Extra | Warns if the narrative contains any number that isn't in `findings.json`. |

---

## Data-quality issues handled (all in Python code, never by editing the CSVs)

| Issue | Where | How |
|---|---|---|
| Blank `discount_pct` and `rating` cells | `seed_data.sql`, `clean_and_eda.py` Task 4 | Loaded as SQL `NULL`. In pandas, discount is filled with 0 and rating with the median (3.0). |
| Inconsistent `payment_method` casing | Task 2 | `.str.strip().str.upper()` |
| 5 double-submitted orders | Task 3 | `.duplicated(subset=<every column except order_id>, keep="first")` |
| 2 bulk-quantity outliers | Task 6 | IQR rule; flagged in `is_outlier`, never dropped |

Pitfalls avoided:
- SQL divides by `100.0`, not `100`, to avoid integer division.
- Duplicates are removed before missing values are filled.
- Outliers are flagged before the monthly trend is calculated.
- `findings.json` is always written by code.
- The API key is only ever read from an environment variable.
