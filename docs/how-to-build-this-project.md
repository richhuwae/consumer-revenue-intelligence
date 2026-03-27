# How to Build: Consumer Revenue Intelligence
# Step-by-step guide to completing this project from scratch
# Edwin Richard Huwae | March 2026

---

## WHAT THIS GUIDE IS

This is your working guide for building the consumer-revenue-intelligence project from
start to finish. It tells you: what to do first, what tools to use for each step, how
to structure each session, what order to build things in, and how to avoid the common
mistakes that turn portfolio projects into half-finished notebooks no one ever looks at.

The session-starter-prompt.md, prompt-library.md, and codex-prompts.md in this folder
contain the actual prompts. This document tells you WHEN and HOW to use them.

---

## BEFORE YOU WRITE A SINGLE LINE OF CODE

### Decision 1 — Dataset

The session-starter references the KKBOX Churn Prediction dataset from Kaggle. That
dataset is from a 2018 competition — the data itself is from 2015–2017. In 2026, using
it as your primary source is a risk: hiring managers who have reviewed portfolios before
will recognise it immediately, and it signals "I used the tutorial dataset."

**Recommended replacement: IBM Telco Customer Churn dataset**
- Available on Kaggle (search "IBM Telco Customer Churn")
- Clean, well-structured, subscription mechanics (monthly charges, contract type, tenure)
- Maps directly onto Free2move, HelloFresh, and Betclic unit economics questions
- Not KKBOX — hiring managers won't roll their eyes

**Alternative if you want something distinctive: Deezer or Spotify API**
- Deezer is French and has a public API — pulling real listening data is more impressive
  than downloading a CSV
- Use listening frequency, session length, and skip rates as churn proxies
- Requires API key registration (free at developers.deezer.com)
- More setup time but genuinely differentiating

**Recommendation:** Use IBM Telco for speed. Use Deezer API if you have an extra 2–3 days
and want the project to stand out more. Both work. Do not use KKBOX.

**Dataset decision — Telco column mapping:**
| Telco column | Equivalent in project |
|---|---|
| customerID | msno (user identifier) |
| tenure | months since first subscription (cohort basis) |
| MonthlyCharges | ARPU (monthly revenue per user) |
| TotalCharges | cumulative revenue |
| Contract (month-to-month / one year / two year) | subscription tier |
| Churn (Yes/No) | churn label |
| PaymentMethod | payment_method proxy |
| InternetService, OnlineSecurity etc. | product features (use for segmentation) |

The synthetic CAC layer (codex-prompts CODEX-02) remains exactly as designed —
you are adding acquisition channel and CPA data that the Telco dataset does not have.
This is still your original analytical work.

---

### Decision 2 — GitHub README now vs. later

The project is on your CV and the GitHub link is live. The README is currently the only
thing there. Before you build a single analysis, spend 30 minutes updating the README to
look like an active, serious project — not a placeholder.

**What the README should have right now, even before the code is done:**
1. One compelling paragraph: what the project is, why it exists, what question it answers
2. Project structure diagram (the folder tree)
3. Analytical chapters listed (Ch1–Ch7) with one-sentence descriptions
4. Data sources listed (IBM Telco + synthetic CAC layer)
5. Tools listed (Python, BigQuery, Tableau)
6. Status badge: "In progress — Chapters 1–2 complete" (update this as you build)

A README that describes a well-designed project in progress is not a lie. It is evidence
that you know what you are doing before you do it — which is the mark of an experienced analyst.

---

## THE BUILD ORDER

Build the chapters in this exact sequence. Do not skip ahead to the "interesting" chapters.
Each one feeds into the next.

```
WEEK 1
├── Day 1: Setup — dataset, BigQuery project, folder structure
├── Day 2-3: Chapter 1 — Cohort Retention (SQL)
└── Day 4-5: Chapter 2 — LTV Modelling (Python)

WEEK 2
├── Day 1-2: Chapter 3 — CAC Payback (Python)
├── Day 3: Chapter 4 — Discount Sensitivity (Python)
└── Day 4-5: Chapter 5 — Churn Prediction Model (Python)

WEEK 3
├── Day 1-2: Chapter 6 — Tableau Dashboard
├── Day 3: Chapter 7 — Executive Summary memo
└── Day 4-5: GitHub README polish + Tableau Public publish
```

**Rule:** Finish one chapter before starting the next. A complete Chapter 1 with clean
output is worth more than five half-built chapters. When a hiring manager looks at your
GitHub, they will know immediately if a project is finished vs. abandoned mid-way.

---

## HOW TO RUN EACH SESSION

Every working session follows this structure:

**Step 1 — Open a new Claude chat**
Copy the entire contents of `session-starter-prompt.md` and paste it as your first message.
Replace the `[TODAY'S TASK]` line at the bottom with what you are doing.

**Step 2 — Use the right tool for the right task**
- CLAUDE prompt → paste into Claude (decisions, design, interpretation, narrative)
- CODEX prompt → paste into GitHub Copilot, Cursor, or ChatGPT with code model

**Step 3 — Build, review, save**
- Generate code with CODEX
- Review with Prompt R-1 in Claude before committing to GitHub
- Save outputs to the correct folder
- Commit to GitHub after each chapter

**Step 4 — Update the README status badge**
After each chapter: update the README to reflect current progress.
"In progress — Chapter 1 complete, Chapter 2 in progress"

---

## CHAPTER BY CHAPTER INSTRUCTIONS

### SETUP — Before Chapter 1

**Tools needed:**
- Python 3.10+ with pip
- Google BigQuery account (free tier is sufficient — 1TB queries/month free)
- Tableau Public (free account at public.tableau.com)
- GitHub account (repo already exists at github.com/richhuwae/consumer-revenue-intelligence)

**Steps:**
1. Download IBM Telco Customer Churn dataset from Kaggle (one CSV file, ~7000 rows)
   Save to: `data/raw/telco_churn.csv`
2. Create a Google Cloud project (free) and enable BigQuery API
3. Install Python dependencies using CODEX-10 to generate requirements.txt, then `pip install -r requirements.txt`
4. In Claude, run Prompt S-1 to understand the dataset schema before touching anything
5. Run Prompt S-2 to design the synthetic CAC layer assumptions
6. Run Prompt S-3 to plan your data quality audit

**Expected time:** 2–3 hours including BigQuery setup

---

### CHAPTER 1 — Cohort Retention Analysis (SQL)

**What you are building:** A retention table showing what % of customers from each
acquisition cohort are still active at months 1, 2, 3, 6, 12. This is the foundation
that everything else builds on.

**How to build it:**
1. Run Prompt 1-A in Claude to design the cohort logic before writing SQL
2. Run CODEX-03 in Codex to generate the BigQuery SQL query
3. Load `telco_churn.csv` into BigQuery (upload CSV → create table)
4. Run the SQL — review the output table
5. Run Prompt 1-B in Claude to review the SQL logic
6. Run Prompt 1-C in Claude to interpret the retention patterns you see
7. Export the output table to `data/processed/cohort_retention.csv`

**Expected output:** A table with columns: cohort, month_number, cohort_size, active_users,
retention_rate. A heatmap visualisation of retention by cohort (you can generate this in
Python or Tableau — do it in Python first for the GitHub repo).

**Common mistake:** Defining the cohort incorrectly — make sure a user's cohort is their
FIRST subscription month, not their most recent. Prompt 1-A covers this.

**Expected time:** 4–6 hours

---

### CHAPTER 2 — LTV Modelling (Python)

**What you are building:** Customer Lifetime Value by cohort and acquisition channel.
How much revenue does the average customer generate over 3 months, 6 months, 12 months?
Which channels produce higher-value customers?

**How to build it:**
1. Run CODEX-02 to build the synthetic CAC layer — this assigns each customerID an
   acquisition channel and CPA. Save to `data/synthetic/cac_layer.csv`
2. Run Prompt 2-A in Claude to design the LTV calculation approach
3. Run CODEX-05 to generate the Python LTV modelling script
4. Run Prompt 2-B in Claude to review the output and write the analytical commentary
5. Save charts to `outputs/charts/`

**Expected outputs:**
- `ltv_curves.png` — LTV over time by cohort (line chart)
- `ltv_by_channel.png` — 12-month LTV by acquisition channel (bar chart)
- `data/processed/ltv_by_user.csv` — user-level LTV table

**Expected time:** 4–6 hours

---

### CHAPTER 3 — CAC Payback Period (Python)

**What you are building:** For each acquisition channel, how many months does it take
on average to recover the cost of acquiring the customer? And what % of customers from
each channel never reach payback?

**How to build it:**
1. Run Prompt 3-A in Claude to design the payback logic
2. Run CODEX-06 to generate the CAC payback script
3. Run Prompt 3-B in Claude to write the commercial narrative of your findings

**Expected outputs:**
- `cac_payback.png` — payback period and never-payback % by channel
- `data/processed/payback_summary.csv`
- One paragraph of commercial narrative (save in `outputs/reports/ch3_narrative.md`)

**Expected time:** 3–4 hours

---

### CHAPTER 4 — Discount Sensitivity (Python)

**What you are building:** Does giving customers a discount at acquisition hurt long-term LTV?
At what discount depth does the offer become NPV-negative? This is the most commercially
interesting analysis in the project — it directly answers the "are we buying customers or
renting them?" question.

**How to build it:**
1. Run Prompt 4-A in Claude to design the sensitivity model and validate assumptions
2. Run CODEX-07 to generate the discount sensitivity script
3. Run Prompt 4-B in Claude to write the "so what" analysis

**Expected outputs:**
- `discount_sensitivity.png` — LTV vs. CAC across discount depths, with break-even line
- `data/processed/sensitivity_table.csv`
- Two paragraphs of commercial analysis (save in `outputs/reports/ch4_narrative.md`)

**Expected time:** 3–4 hours

---

### CHAPTER 5 — Churn Prediction Model (Python)

**What you are building:** A machine learning model that predicts which customers are
most likely to churn. This is the "data science" chapter that shows technical depth.
The business value: if you can predict churn, you can intervene before it happens.

**How to build it:**
1. Run Prompt 5-A in Claude to decide which features to engineer and why
2. Run CODEX-08 to generate the feature engineering script
3. Run CODEX-09 to generate the model training and evaluation script
4. Run Prompt 5-B in Claude to interpret the results as a business finding

**Expected outputs:**
- `roc_curve.png` — ROC curve comparison (logistic regression vs. random forest)
- `feature_importance.png` — top 8 features by importance
- `model_evaluation.txt` — plain text evaluation report
- `churn_model.pkl` — saved model
- One paragraph of business interpretation (save in `outputs/reports/ch5_narrative.md`)

**Expected time:** 6–8 hours (this is the most complex chapter)

---

### CHAPTER 6 — Tableau Dashboard

**What you are building:** An interactive Tableau Public dashboard with three views:
cohort retention heatmap, unit economics summary (LTV vs. CAC by channel), and a
scenario simulator with parameter sliders (CAC, ARPU, churn rate → LTV, payback, ratio).

**How to build it:**
1. Run Prompt 6-A in Claude to design the dashboard layout before opening Tableau
2. Run CODEX from prompt-library 5-B to prepare dashboard-ready CSV exports
3. Open Tableau Public — connect to the CSV files
4. Build the three views following the design brief
5. Run Prompt 6-B in Claude to verify the scenario simulator formula logic
6. Publish to Tableau Public — copy the public link

**Expected output:** Live Tableau Public link — add this to the GitHub README immediately
after publishing. This is the most visually impressive deliverable in the project.

**Expected time:** 6–8 hours

---

### CHAPTER 7 — Executive Summary

**What you are building:** A 1-page business memo addressed to "Head of Growth" that
presents 3 findings with specific numbers and 2 clear recommendations. This is what
proves you can communicate analysis, not just build it.

**How to build it:**
1. Collect your key numbers from Chapters 1–5 (retention at month 6, best-performing
   channel by LTV, CAC payback period, break-even discount depth, model AUC)
2. Run Prompt 7-A in Claude — paste in your numbers and get the draft
3. Edit it to sound like you, not like AI. The Human-Like Test: would you say this out loud?
4. Save as `outputs/reports/executive_summary.md` and also export to PDF

**Expected time:** 2–3 hours

---

## GITHUB WORKFLOW

**Repository:** github.com/richhuwae/consumer-revenue-intelligence

**Commit after each chapter.** Never commit a chapter mid-build. Commit when it is done.
Use clear commit messages:
- `Add Chapter 1: cohort retention SQL and output table`
- `Add Chapter 2: LTV modelling by cohort and channel`

**Never commit:**
- Raw data files (add `data/raw/` to .gitignore)
- API keys or credentials
- The `.pkl` model file if it is large — add to .gitignore, describe how to reproduce it

**Update the README status line after every commit.**

---

## HOW TO TALK ABOUT THIS PROJECT IN INTERVIEWS

You will be asked about this project before it is finished. That is fine.
Here is how to talk about it at each stage of completion:

**While building (nothing in repo yet except README):**
> "I'm actively building a subscription unit economics project. The full analytical framework
> is designed — cohort retention, LTV by channel, CAC payback, discount sensitivity, and a
> churn prediction model. I'm working through the chapters now. Let me walk you through the
> methodology."
Then walk through the 5 analytical layers. Fluency here matters more than finished code.

**Chapters 1–2 complete:**
> "I've completed the cohort retention and LTV analysis. The early findings show [specific
> insight]. I'm now building the CAC payback layer. The Tableau dashboard comes last."
Point them to the GitHub repo and walk through the SQL and Python output.

**All chapters complete:**
> "The project is complete — here is the Tableau Public link. Let me walk you through
> the key finding: [specific number and business implication]."
Lead with the finding, not the methodology.

---

## ADAPTING THE PROJECT FOR SPECIFIC COMPANIES

The project is designed to be universal. Here is how to frame it per company:

| Company | What to emphasise | What to say |
|---|---|---|
| **Free2move** | CAC payback, retention by tier, discount sensitivity | "I modelled the same question your subscription fleet faces — at what acquisition cost and churn rate does a usage-based subscription become profitable?" |
| **HelloFresh** | Discount sensitivity (promo-acquired cohorts), retention curves | "The discount sensitivity analysis maps directly to promotional meal-kit offers — I found the break-even discount depth beyond which acquisition becomes NPV-negative." |
| **Betclic** | Churn prediction model, channel LTV comparison | "The churn model identifies which players are most at risk of churning — the same logic applies to player lifetime value in gaming." |
| **Rakuten** | LTV by channel, loyalty cohort comparison | "I segmented LTV by acquisition channel, which maps to how Rakuten tracks member engagement across Club R tiers." |
| **Primexis** | The pipeline and automation angle | "I built the end-to-end pipeline — SQL in BigQuery, Python modelling, Tableau dashboard — automating what a finance team would previously do manually in Excel." |
| **CMA CGM** | Not directly applicable — use maritime-trade-intelligence project instead | Don't force this one. The Telco-based project is a weaker fit for CMA CGM. |

---

## PROMPT REFERENCE — QUICK LOOKUP

| Chapter | Claude Prompt | Codex Prompt |
|---|---|---|
| Setup | S-1, S-2, S-3 | CODEX-01, CODEX-02 |
| Ch1 Cohort Retention | 1-A, 1-B, 1-C | CODEX-03 |
| Ch2 LTV | 2-A, 2-B | CODEX-04, CODEX-05 |
| Ch3 CAC Payback | 3-A, 3-B | CODEX-06 |
| Ch4 Discount Sensitivity | 4-A, 4-B | CODEX-07 |
| Ch5 Churn Model | 5-A, 5-B | CODEX-08, CODEX-09 |
| Ch6 Dashboard | 6-A, 6-B | — |
| Ch7 Executive Summary | 7-A | — |
| GitHub | G-1, G-2 | — |
| Review | R-1 | — |

Full prompts are in:
- `docs/prompt-library.md` — all Claude prompts
- `docs/codex-prompts.md` — all Codex/Copilot code generation prompts
- `docs/session-starter-prompt.md` — paste at start of every new Claude session

---

*Last updated: March 2026*
*Build this project before applying to Free2move, HelloFresh, Betclic, Rakuten.*
