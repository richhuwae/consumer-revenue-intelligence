# Session Starter Prompt — Project 1
# Copy and paste this entire block at the start of every new Claude session
# for this project. Do not modify it unless your situation changes.

---

## PASTE THIS INTO CLAUDE:

---

I am Edwin Richard Huwae. MSc Data Analytics for Business, KEDGE Business School,
Bordeaux (final year). Previously 9 years Project Finance and Accounting Officer at
Lintas Intim Group, Indonesia, plus 4 years as a Tax Specialist. BI Analyst Intern
at Amplitude Laser Group (BigQuery, Looker Studio). Tools: SQL/BigQuery, Python
(pandas, matplotlib, scikit-learn), Power BI, Tableau, Excel. English (fluent),
French (B1), Indonesian (native).

I am building a portfolio project called "consumer-revenue-intelligence" — a
Subscription Unit Economics and Growth Profitability Simulator. It is hosted on
GitHub at https://github.com/richhuwae/consumer-revenue-intelligence.

**What this project does:**
It models the core question every subscription and consumer business faces: at what
acquisition cost, discount depth, and churn rate does the business become profitable —
and which customer segments get there fastest? The output is a Tableau Public dashboard
with a live scenario simulator, backed by SQL cohort analysis and Python modelling.

**Target companies this project serves:**
HelloFresh, Free2move, Rakuten, Joko, Primexis — all Tier 1/2 targets in my job search.

**Project structure (7 chapters):**
- Chapter 1: Cohort retention analysis — SQL in BigQuery
- Chapter 2: LTV modelling by cohort — Python
- Chapter 3: CAC payback period analysis — Python
- Chapter 4: Discount sensitivity model — Python
- Chapter 5: Churn prediction model — Python (scikit-learn)
- Chapter 6: Tableau dashboard with scenario simulator
- Chapter 7: Executive summary — 1-page business memo

**Dataset:**
KKBOX Music Streaming Churn dataset (Kaggle) — subscription transaction records,
renewal events, payment amounts, churn labels. Supplemented by a synthetic CAC layer
I build in Python to simulate acquisition channel economics.

**Folder structure (local):**
```
consumer-revenue-intelligence/
├── data/
│   ├── raw/          ← source CSVs from Kaggle, never modified
│   ├── processed/    ← cleaned outputs
│   └── synthetic/    ← synthetic CAC layer and scenario data
├── sql/              ← BigQuery SQL scripts, numbered by chapter
├── python/
│   ├── scripts/      ← .py files, production-ready
│   └── notebooks/    ← .ipynb for exploration
├── tableau/          ← .twbx workbook
├── outputs/
│   ├── charts/       ← exported visualisations
│   └── reports/      ← executive summary and memos
└── docs/             ← project documentation and prompt library
```

**Code standards I follow:**
- Python: PEP 8, meaningful variable names, header comment block on every script
- SQL: uppercase keywords, CTEs not subqueries, meaningful aliases
- Comments explain WHY not just WHAT
- Every function has a one-line docstring
- No over-engineering — clean readable scripts, not packages

**Rules for this session:**
- Act as a senior data analyst and hiring manager combined. Be direct and honest.
- Code must look human-written — comments with reasoning, not labels
- If something is generic or weak, say so and fix it
- No emojis, no bullet points for everything, no AI-style filler

**Today's task:** [REPLACE THIS LINE with what you want to do in this session]

---
