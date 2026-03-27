# Prompt Library — consumer-revenue-intelligence
# Use these prompts in Claude sessions throughout the project.
# Always paste the session-starter-prompt.md content FIRST,
# then add the relevant prompt from this library as "Today's task."
#
# CLAUDE vs CODEX split is marked on each prompt.
# Rule: Use Codex for code generation. Use Claude for decisions,
# narrative, review, and anything requiring business judgment.

---

## SETUP & DATA

### PROMPT S-1 — Dataset download and schema understanding [CLAUDE]
```
Today's task: I need to set up the KKBOX Churn Prediction dataset from Kaggle.
Walk me through exactly which files to download, what each file contains,
and what the key columns are that I will need for cohort retention analysis,
LTV modelling, and churn prediction. Give me a plain-English schema summary
I can keep in a reference file. Do not write code yet — I want to understand
the data structure first before doing anything.
```

### PROMPT S-2 — Synthetic CAC layer design [CLAUDE]
```
Today's task: I need to design the synthetic CAC (Customer Acquisition Cost)
layer for this project. Since the KKBOX dataset does not contain acquisition
channel data, I need to create a realistic synthetic layer. Help me design
a channel mix table with realistic CPA (cost per acquisition) assumptions
for a music/subscription business: paid search, social, organic, referral,
and promo code. I want this to feel like real analyst work — not arbitrary
numbers. Walk me through your reasoning for each assumption before we build it.
```

### PROMPT S-3 — Data quality audit [CLAUDE]
```
Today's task: Before building anything, I want to audit the KKBOX dataset
for data quality issues. I have loaded the raw CSVs. Help me think through:
what null values, duplicates, date inconsistencies, and edge cases should I
expect in subscription transaction data? What are the most dangerous quality
issues that would silently corrupt a cohort retention analysis if not caught?
Give me a checklist to work through before I pass anything to the cleaning script.
```

---

## CHAPTER 1 — COHORT RETENTION (SQL)

### PROMPT 1-A — Cohort logic design [CLAUDE]
```
Today's task: Chapter 1 — Cohort Retention Analysis. Before I write any SQL,
I want to make sure the cohort logic is correct. Walk me through how to define
a subscription cohort correctly in the KKBOX dataset: what constitutes a user's
first subscription month, how to handle users with gaps in their subscription
history, and what edge cases could produce incorrect retention percentages.
I want to understand the logic before touching BigQuery.
```

### PROMPT 1-B — Cohort SQL review [CLAUDE]
```
Today's task: I have written (or Codex has generated) the cohort retention SQL.
Please review it as a senior analyst. Check for: incorrect cohort definitions,
off-by-one errors in month calculations, division by zero risks, and any logic
that would silently produce wrong results. Then tell me what the output table
should look like — column names, data types, example rows — so I know what
to expect when I run it.
```

### PROMPT 1-C — Retention heatmap interpretation [CLAUDE]
```
Today's task: I have run the cohort retention SQL and have the output table.
Help me interpret what I am seeing. What patterns should I look for in a
subscription retention heatmap? What would indicate a seasonality problem,
a product quality issue, or a promotional acquisition problem? I want to
understand what story this data is telling before I build the visualisation.
```

---

## CHAPTER 2 — LTV MODELLING (Python)

### PROMPT 2-A — LTV model design [CLAUDE]
```
Today's task: Chapter 2 — LTV Modelling by Cohort. Help me design the LTV
calculation approach. I want to compute 90-day, 180-day, and 12-month LTV
per cohort using the retention curves from Chapter 1. Walk me through the
formula: how does cumulative LTV compound across months, how do I handle
cohorts that are not yet 12 months old (right-censoring), and what is the
cleanest way to structure this in pandas? Decision first, code later.
```

### PROMPT 2-B — LTV output review [CLAUDE]
```
Today's task: I have built the LTV model and have cohort LTV curves.
Review the outputs with me. Do the numbers look commercially realistic
for a subscription business? What would cause LTV to be implausibly high
or low? Help me sanity-check the results before I present them as findings.
Then help me write 3-4 sentences of analytical commentary that explains
what the LTV curves tell us — written for a growth director, not a data scientist.
```

---

## CHAPTER 3 — CAC PAYBACK (Python)

### PROMPT 3-A — CAC payback design [CLAUDE]
```
Today's task: Chapter 3 — CAC Payback Period Analysis. I need to calculate
the average month at which each acquisition channel recoups its CAC. Walk me
through the logic: how do I find the exact month where cumulative LTV crosses
CAC for each user, how do I average this across a cohort, and how do I handle
users who never reach payback within the observation window? I want to get the
methodology right before generating code.
```

### PROMPT 3-B — Payback findings narrative [CLAUDE]
```
Today's task: I have the CAC payback period results by channel. Help me write
the analytical narrative for this section — 1 paragraph, written as if I am
presenting findings to a Head of Growth. It should state the key finding
(which channel pays back fastest, which is at risk), include specific numbers,
and end with a clear implication for the business. No data science jargon.
```

---

## CHAPTER 4 — DISCOUNT SENSITIVITY (Python)

### PROMPT 4-A — Discount model design [CLAUDE]
```
Today's task: Chapter 4 — Discount Sensitivity Analysis. I want to model how
different discount depths (0%, 20%, 40%, 60% off first period) affect LTV.
Help me think through the assumptions I need: how do I model lower initial ARPU
for discounted users, how do I calibrate a retention penalty for promo-acquired
users using my cohort data, and what is the right way to compute a break-even
discount depth? Walk me through the logic and the key assumptions before I build.
```

### PROMPT 4-B — Sensitivity table interpretation [CLAUDE]
```
Today's task: I have the discount sensitivity output table. Help me write the
"so what" for this analysis in 2 paragraphs: first paragraph states the finding
(at what discount level does the offer become NPV-negative), second paragraph
frames this as a specific recommendation to a growth team running acquisition
campaigns. This should feel like real analyst work — specific, commercial, direct.
```

---

## CHAPTER 5 — CHURN PREDICTION (Python / scikit-learn)

### PROMPT 5-A — Feature engineering decisions [CLAUDE]
```
Today's task: Chapter 5 — Churn Prediction Model. Before building the model,
I need to decide on features. Based on the KKBOX dataset columns available,
help me select and engineer the 6-8 most predictive features for 30-day churn
prediction. For each feature, explain the business logic — why would a finance
professional believe this variable predicts churn? I want every feature to have
a business rationale, not just statistical correlation.
```

### PROMPT 5-B — Model results interpretation [CLAUDE]
```
Today's task: I have trained the churn model (logistic regression + random forest).
The results are: [PASTE YOUR METRICS HERE — AUC, precision, recall, feature importances].
Help me interpret these results as a business finding, not a model report. What does
this AUC mean in practical terms? Which features are most important and what does
that tell us about why customers churn? Write 1 paragraph of business interpretation
suitable for the executive summary.
```

---

## CHAPTER 6 — TABLEAU DASHBOARD

### PROMPT 6-A — Dashboard structure and UX design [CLAUDE]
```
Today's task: Chapter 6 — Tableau Dashboard. Before I open Tableau, help me
design the dashboard layout and user experience. I want three views: a cohort
retention heatmap, a unit economics summary (LTV vs. CAC by channel), and a
scenario simulator with parameter sliders. For each view, describe: what goes
on each axis, what the colour encoding should be, what a user should be able
to do with it, and what the most important thing they should understand in
under 10 seconds is. I want a design brief, not a tutorial.
```

### PROMPT 6-B — Scenario simulator logic [CLAUDE]
```
Today's task: I am building the scenario simulator in Tableau. The sliders are:
CAC (€), average monthly ARPU (€), and monthly churn rate (%). The calculated
outputs should be: projected 12-month LTV, payback period in months, and
LTV/CAC ratio. Help me verify the Tableau calculated field formulas for each
of these three outputs. Write the formula logic clearly — I will translate it
into Tableau syntax myself.
```

---

## CHAPTER 7 — EXECUTIVE SUMMARY

### PROMPT 7-A — Executive summary draft [CLAUDE]
```
Today's task: Chapter 7 — Executive Summary. I have completed the analysis.
The key findings are: [PASTE YOUR 3-4 KEY NUMBERS HERE].

Write a 1-page executive memo (400-500 words) addressed to "Head of Growth"
at a subscription business. Structure: (1) the business question, (2) what
the data shows — 3 specific findings with numbers, (3) what it means —
2 clear business recommendations, (4) limitations and what would improve
the analysis with more data. Tone: confident, commercial, direct. Written
as Edwin the analyst, not as a student documenting a project.
```

---

## GITHUB & PRESENTATION

### PROMPT G-1 — README final review [CLAUDE]
```
Today's task: My project is complete. Review the GitHub README at
https://github.com/richhuwae/consumer-revenue-intelligence and tell me:
is the opening paragraph compelling enough to make a hiring manager read
further? Is the project description specific enough, or does it sound generic?
Does it pass the human-like test — would a real analyst have written this?
Give me specific edits, not general feedback.
```

### PROMPT G-2 — Website project card copy [CLAUDE]
```
Today's task: I need to write the project card copy for my personal website
(edwinrichardhuwae.com) for this project. I need: a title (max 8 words),
a subtitle (max 15 words), and a 2-sentence description (max 40 words total).
The audience is a hiring manager who has 3 seconds. It must make them click.
Write 3 versions ranked by how likely they are to generate a click.
```

---

## CODE REVIEW

### PROMPT R-1 — Full project code review [CLAUDE]
```
Today's task: Full code review of the project before I publish to GitHub.
I am going to paste each script one at a time. For each one, review:
(1) does the code look human-written or AI-generated? Flag any patterns
that give it away, (2) are the comments explaining reasoning or just narrating
the obvious? (3) are there any logic errors or edge cases that would break
in production? (4) would a senior analyst at HelloFresh or Free2move be
impressed by this, or would they find it unremarkable? Be harsh.
```
