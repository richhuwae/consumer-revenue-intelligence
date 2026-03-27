# Codex Prompt Pack — consumer-revenue-intelligence
# Use these prompts in GitHub Copilot / OpenAI Codex / Cursor / ChatGPT
# for all code generation tasks. This saves your Claude Pro tokens for
# decisions, narrative, and review work.
#
# HOW TO USE:
# 1. Open your code editor with Copilot, OR open ChatGPT with the code model
# 2. Paste the relevant prompt below — it is self-contained
# 3. Review the output critically before using it
# 4. Bring the final code back to Claude only for review (Prompt R-1)
#
# Each prompt includes: context, schema, task, output format, and style rules.

---

## DATA CLEANING

### CODEX-01 — KKBOX data cleaning script

```
Write a Python script to clean the KKBOX Music Streaming Churn dataset.

Context:
- This is a subscription churn prediction dataset from Kaggle
- Files: transactions.csv, members.csv, user_logs.csv, train.csv (churn labels)
- The script prepares data for cohort retention analysis and LTV modelling

Tasks:
1. Load transactions.csv — parse transaction_date and membership_expire_date as datetime
2. Remove duplicate rows based on msno + transaction_date
3. Filter to transactions where payment_plan_days > 0 (exclude cancellations)
4. Create a subscription_month column: YYYY-MM from transaction_date
5. Create a cohort column: the earliest subscription_month per msno (first subscription)
6. Handle nulls: drop rows where msno or transaction_date is null
7. Load members.csv — merge on msno, keep: city, bd (age), gender, registered_via
8. Output: save cleaned dataframe to data/processed/transactions_clean.csv

Style rules:
- PEP 8 throughout
- Header comment block: project name, script purpose, author placeholder, date
- Use meaningful variable names: subscription_df not df
- Comments must explain WHY, not just WHAT
  Example: # remove payment_plan_days == 0 — these are cancellation events, not real transactions
- Every function must have a one-line docstring
- No unnecessary complexity — this is a standalone analysis script, not a package

Output: a single .py file, production-ready, with all imports at the top
```

---

### CODEX-02 — Synthetic CAC layer generator

```
Write a Python script to generate a synthetic Customer Acquisition Cost (CAC)
layer for subscription churn analysis.

Context:
- The KKBOX dataset does not include acquisition channel data
- I need to assign a synthetic acquisition channel and CPA to each user
  to simulate the economics of a real subscription business
- This is for portfolio analysis — the assumptions should be commercially
  realistic for a music/subscription platform

Schema input:
- transactions_clean.csv with columns: msno, cohort (first subscription month),
  subscription_month, payment_method_id, plan_list_price

Tasks:
1. Define a channel_mix dictionary with these channels and weights:
   - paid_search: 30%, CPA = 8.50 EUR
   - social_media: 25%, CPA = 6.20 EUR
   - organic: 20%, CPA = 0 EUR (no acquisition cost)
   - referral: 15%, CPA = 3.00 EUR
   - promo_code: 10%, CPA = 12.00 EUR (high cost, attracts deal-seekers)

2. For each unique msno in transactions_clean.csv:
   - Assign a channel using numpy random choice weighted by channel_mix
   - Assign the corresponding CPA as their acquisition_cost
   - Add a discount_flag: True if channel == promo_code, False otherwise

3. Add a realistic ARPU proxy: use plan_list_price from transactions as monthly revenue.
   For promo_code users, apply a 40% first-month discount to plan_list_price.

4. Output: save to data/synthetic/cac_layer.csv with columns:
   msno, channel, acquisition_cost, discount_flag, arpu_monthly

Style rules:
- Set a random seed (42) for reproducibility
- Header comment block with purpose and assumption notes
- Comment each assumption explicitly:
  # promo_code CPA is higher because promotional campaigns require paid media support
- PEP 8, meaningful names, one-line docstrings on functions
```

---

## CHAPTER 1 — COHORT RETENTION SQL

### CODEX-03 — Cohort retention table (BigQuery SQL)

```
Write a BigQuery Standard SQL query to compute monthly cohort retention rates
for a subscription dataset.

Input table: `transactions_clean` with columns:
- msno STRING — unique user identifier
- subscription_month STRING — format 'YYYY-MM', the month of this transaction
- cohort STRING — format 'YYYY-MM', the user's first subscription month

Task:
1. CTE cohort_sizes: count distinct msno per cohort
2. CTE cohort_activity: for each cohort, count distinct msno active in each
   subsequent month (month_number = 0, 1, 2, ... 11)
   - month_number is the integer difference in months between subscription_month
     and cohort month
   - Only include month_number 0 through 11
3. Final SELECT: join cohort_sizes and cohort_activity, compute:
   - retention_rate = active_users / cohort_size (as FLOAT64, 2 decimal places)
   - Include columns: cohort, month_number, cohort_size, active_users, retention_rate
4. Order by cohort ASC, month_number ASC

Style rules:
- All SQL keywords UPPERCASE
- Use CTEs, not nested subqueries
- Alias tables with meaningful short names (cs for cohort_sizes, ca for cohort_activity)
- Add a comment above each CTE explaining its purpose in one line
- No redundant columns in intermediate CTEs
```

---

### CODEX-04 — LTV by cohort SQL (BigQuery)

```
Write a BigQuery Standard SQL query to compute cumulative customer LTV per cohort.

Input tables:
- `transactions_clean`: msno, subscription_month, cohort, plan_list_price (monthly revenue proxy)
- `cac_layer`: msno, channel, acquisition_cost, arpu_monthly, discount_flag

Task:
1. CTE monthly_revenue: join the two tables on msno, compute:
   - For discount_flag = TRUE and month_number = 0: revenue = arpu_monthly * 0.6
     (40% first-month discount applied)
   - For all other rows: revenue = arpu_monthly
2. CTE cohort_monthly_ltv: per cohort and month_number, compute avg revenue per user
3. CTE cumulative_ltv: compute running sum of avg_revenue by cohort up to each month
   (use SUM OVER PARTITION BY cohort ORDER BY month_number ROWS UNBOUNDED PRECEDING)
4. Final output columns: cohort, month_number, avg_monthly_revenue, cumulative_ltv_90d,
   cumulative_ltv_180d, cumulative_ltv_365d
   (flag these with CASE WHEN month_number <= 2/5/11)

Style rules:
- All SQL keywords UPPERCASE
- CTEs with single-line purpose comments
- Meaningful aliases
- Handle NULL join results with COALESCE where appropriate
```

---

## CHAPTER 2 — LTV MODELLING (Python)

### CODEX-05 — LTV modelling script

```
Write a Python script to compute and visualise customer LTV by cohort.

Input files:
- data/processed/transactions_clean.csv
- data/synthetic/cac_layer.csv

Columns available:
- msno, cohort, subscription_month, plan_list_price, channel,
  acquisition_cost, arpu_monthly, discount_flag

Tasks:
1. Function compute_cohort_ltv(df):
   - Input: merged dataframe
   - For each msno, compute cumulative revenue at months 3, 6, 12
   - Apply discount (arpu * 0.6) for month 0 if discount_flag is True
   - Return dataframe: msno, cohort, channel, ltv_90d, ltv_180d, ltv_365d

2. Function plot_ltv_curves(ltv_df):
   - Plot average LTV over time (month 0 to 11) for each cohort
   - One line per cohort, colour-coded
   - X axis: month number (0-11), Y axis: cumulative LTV in EUR
   - Clean styling: no gridlines on top/right, muted colours, legend outside plot
   - Save to outputs/charts/ltv_curves.png at 150dpi

3. Function plot_ltv_by_channel(ltv_df):
   - Bar chart: average 12-month LTV by acquisition channel
   - Horizontal bars, sorted descending by ltv_365d
   - Annotate each bar with the LTV value
   - Save to outputs/charts/ltv_by_channel.png at 150dpi

Style rules:
- PEP 8, meaningful variable names (cohort_ltv_df not df2)
- Header comment block: project, purpose, author placeholder, date
- Comment the discount logic clearly:
  # month 0 revenue reduced for promo users — they paid less to acquire
- Matplotlib style: use plt.style.use('seaborn-v0_8-whitegrid') or similar
  clean style; avoid default matplotlib aesthetics
- All chart labels in title case, axis labels in sentence case
- main() function that runs everything in sequence
```

---

## CHAPTER 3 — CAC PAYBACK (Python)

### CODEX-06 — CAC payback period script

```
Write a Python script to calculate CAC payback period by acquisition channel.

Input file: output from LTV modelling — ltv_by_user.csv with columns:
msno, cohort, channel, acquisition_cost, monthly_revenue_m0 through monthly_revenue_m11

Task:
1. Function compute_payback_period(row):
   - Input: a single row (one user)
   - Compute cumulative revenue month by month
   - Return the first month where cumulative_revenue >= acquisition_cost
   - If never reached in 11 months, return None (user never pays back)

2. Function summarise_payback(df):
   - Apply compute_payback_period across all users
   - Group by channel, compute:
     - avg_payback_months: mean payback period (exclude None)
     - pct_never_payback: % of users who never reach payback within 11 months
     - ltv_cac_ratio: average 12-month LTV / average CAC per channel
   - Return summary dataframe

3. Function plot_payback_summary(summary_df):
   - Grouped bar chart: avg_payback_months and pct_never_payback side by side per channel
   - Add a horizontal reference line at LTV/CAC = 3.0 (healthy threshold)
   - Save to outputs/charts/cac_payback.png

Style rules:
- PEP 8
- Handle the None case explicitly — comment why:
  # None means the customer churned before recovering their acquisition cost
  # This is the most commercially dangerous segment
- Vectorised operations with pandas where possible, not row-by-row loops
- Header comment block with purpose
- main() function
```

---

## CHAPTER 4 — DISCOUNT SENSITIVITY (Python)

### CODEX-07 — Discount sensitivity model

```
Write a Python script to model LTV sensitivity to acquisition discount depth.

Context:
- I want to understand how offering deeper discounts at acquisition affects
  12-month LTV and whether the discount is NPV-positive

Assumptions to implement:
- Base ARPU: use arpu_monthly from cac_layer.csv (average across users)
- Monthly churn rates by discount tier (calibrated from cohort data):
  - 0% discount: 8% monthly churn
  - 20% discount: 10% monthly churn
  - 40% discount: 13% monthly churn
  - 60% discount: 18% monthly churn
- Discount reduces month-0 revenue only
- CAC for discounted campaigns: use promo_code CPA = 12.00 EUR

Task:
1. Function compute_scenario_ltv(arpu, churn_rate, discount_pct, months=12):
   - Compute LTV over 12 months with given churn rate
   - Month 0 revenue = arpu * (1 - discount_pct)
   - Subsequent months: arpu * (1 - churn_rate)^month
   - Return cumulative LTV at month 12

2. Function build_sensitivity_table():
   - Run compute_scenario_ltv for each discount tier (0%, 20%, 40%, 60%)
   - Add columns: discount_pct, ltv_12m, cac, net_value (ltv - cac), ltv_cac_ratio
   - Return dataframe

3. Function plot_sensitivity(sensitivity_df):
   - Line chart: LTV and CAC on same axis against discount depth
   - Shade the region where net_value < 0 in light red
   - Add a vertical dashed line at the break-even discount depth
   - Save to outputs/charts/discount_sensitivity.png

Style rules:
- Comment every assumption explicitly:
  # churn rates calibrated from KKBOX cohort data — promo users churn ~2x faster
- PEP 8, meaningful names
- Header comment block
- main() function
```

---

## CHAPTER 5 — CHURN PREDICTION (Python / scikit-learn)

### CODEX-08 — Feature engineering script

```
Write a Python script to engineer features for churn prediction from the
KKBOX dataset.

Input files:
- data/processed/transactions_clean.csv
- data/processed/user_logs_clean.csv (if available, else skip)
- data/synthetic/cac_layer.csv
- train.csv (churn labels: msno, is_churn)

Features to engineer per msno:
1. subscription_age_months: number of months since cohort date to last transaction
2. days_to_expire: membership_expire_date - last transaction_date
3. payment_method_id: most frequent payment method (mode)
4. plan_list_price: most recent plan price
5. total_transactions: count of all transactions in history
6. auto_renew_rate: proportion of transactions where is_auto_renew = 1
7. channel: from cac_layer (acquisition channel)
8. discount_flag: from cac_layer (binary)
9. arpu_trend: difference between last 3 months ARPU and first 3 months ARPU
   (negative = declining spend, positive = growing)
10. churn_label: from train.csv

Task:
- Merge all features on msno
- Handle nulls: fill numeric nulls with median, categorical with mode
- Output: data/processed/features.csv — one row per msno, all features + label

Style rules:
- PEP 8, meaningful names
- Comment the business logic for each feature:
  # days_to_expire: users close to expiry with no renewal are at highest risk
- Header comment block
- main() function
```

---

### CODEX-09 — Churn model training and evaluation script

```
Write a Python script to train and evaluate a churn prediction model.

Input: data/processed/features.csv
Target: churn_label (binary 0/1)

Features (all except msno and churn_label):
subscription_age_months, days_to_expire, payment_method_id, plan_list_price,
total_transactions, auto_renew_rate, channel, discount_flag, arpu_trend

Tasks:
1. Preprocessing:
   - One-hot encode: payment_method_id, channel
   - Scale numeric features with StandardScaler
   - Train/test split: 80/20, stratified on churn_label, random_state=42

2. Train two models:
   a. Logistic Regression (max_iter=1000)
   b. Random Forest (n_estimators=100, max_depth=6, random_state=42)

3. Evaluate both models:
   - ROC-AUC score
   - Precision, recall, F1 (classification_report)
   - Confusion matrix
   - Feature importances (Random Forest) — top 8 features, horizontal bar chart
   - ROC curve comparison plot for both models on same axes

4. Save outputs:
   - outputs/charts/roc_curve.png
   - outputs/charts/feature_importance.png
   - outputs/reports/model_evaluation.txt — plain text summary of both models

5. Save best model (by AUC) to python/scripts/churn_model.pkl using joblib

Style rules:
- PEP 8
- Comment the model choice rationale:
  # Logistic regression as interpretable baseline — coefficients have business meaning
  # Random forest to capture non-linear interactions in payment behaviour
- Separate functions: preprocess_data(), train_models(), evaluate_models(), save_outputs()
- main() calls all functions in sequence
- Header comment block
```

---

## UTILITY

### CODEX-10 — Project requirements.txt generator

```
Write a requirements.txt file for this Python project.

The project uses:
- pandas for data manipulation
- numpy for numerical operations
- matplotlib and seaborn for visualisation
- scikit-learn for machine learning (logistic regression, random forest, preprocessing)
- joblib for model serialisation
- google-cloud-bigquery for BigQuery connection (optional)

Rules:
- Pin major and minor version but not patch (e.g. pandas==2.1.*)
- Add a comment above each package group explaining what it is used for
- Group packages: data, visualisation, machine learning, cloud, utilities
- Include python-dotenv for environment variable management
```

---

## NOTES ON USING CODEX EFFECTIVELY

1. Always provide the exact column names and data types in your prompt.
   Codex cannot guess your schema — give it the schema.

2. Specify the output format explicitly (file path, column names, chart dimensions).
   This prevents you having to rewrite code to fit your folder structure.

3. The style rules at the bottom of each prompt are non-negotiable.
   If Codex ignores them, add "strictly follow the style rules above" at the end.

4. After generating code with Codex, always bring it to Claude (Prompt R-1)
   for a review pass before pushing to GitHub. Code correctness is one thing;
   whether it looks like real analyst work is another.

5. Do not use Codex for:
   - Deciding what features to engineer (use Prompt 5-A in Claude)
   - Writing the executive summary (use Prompt 7-A in Claude)
   - Interpreting model results (use Prompt 5-B in Claude)
   - Designing the Tableau dashboard (use Prompt 6-A in Claude)
