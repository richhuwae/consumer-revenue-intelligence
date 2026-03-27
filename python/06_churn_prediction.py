"""
Consumer Revenue Intelligence — Step 06
Churn Prediction Model

What this script does:
  Builds a machine learning model to predict which subscribers are likely to
  churn within the next 30 days. This enables proactive retention efforts
  before revenue is lost.

  The model uses features that would be available before churn occurs:
    - Subscription tier (free_trial, monthly, annual)
    - Months active to date
    - Monthly revenue
    - Acquisition channel
    - Genre preference
    - Engagement metrics (sessions per month, audio features)

  Key outputs:
    - data/processed/churn_model_features.csv   (feature matrix)
    - data/processed/churn_model_results.csv    (predictions and probabilities)
    - outputs/charts/churn_feature_importance.png (top predictors of churn)
    - outputs/charts/churn_confusion_matrix.png   (model performance)
    - outputs/charts/churn_roc_curve.png          (ROC-AUC curve)

Run after: python3 python/05_discount_sensitivity.py
Usage:     python3 python/06_churn_prediction.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, roc_auc_score,
    precision_recall_curve, average_precision_score, precision_score,
    recall_score, ConfusionMatrixDisplay
)

# ── Paths ─────────────────────────────────────────────────────────────────────
INPUT_USERS   = "data/synthetic/users.csv"
OUTPUT_FEAT   = "data/processed/churn_model_features.csv"
OUTPUT_PRED   = "data/processed/churn_model_results.csv"
OUT_FEAT_IMP  = "outputs/charts/churn_feature_importance.png"
OUT_CM        = "outputs/charts/churn_confusion_matrix.png"
OUT_ROC       = "outputs/charts/churn_roc_curve.png"
OUT_PR        = "outputs/charts/churn_pr_curve.png"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

BRAND_BLUE = "#1F4E79"
ACCENT_RED = "#D9534F"
ACCENT_GREEN = "#5CB85C"

np.random.seed(42)

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_USERS)
print(f"Loaded {len(df):,} users")
print(f"Churn rate: {df['churned'].mean():.1%}")

# ── Feature engineering ───────────────────────────────────────────────────────
print("\nEngineering features...")

# Create feature matrix
features = df.copy()

# Categorical features to encode
categorical_cols = ['tier', 'acquisition_channel', 'genre_preference']
label_encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    features[col + '_encoded'] = le.fit_transform(features[col].astype(str))
    label_encoders[col] = le

# Numerical features (already available)
numerical_cols = [
    'avg_energy', 'avg_valence', 'avg_danceability',
    'sessions_per_month', 'cpa_eur', 'monthly_revenue_eur',
    'months_active'
]

# Select final feature set
feature_cols = [col + '_encoded' for col in categorical_cols] + numerical_cols
X = features[feature_cols]
y = features['churned']

print(f"Feature matrix shape: {X.shape}")
print(f"Features: {feature_cols}")

# ── Train-test split ─────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTraining set: {len(X_train):,} users")
print(f"Test set: {len(X_test):,} users")

# ── Train Random Forest model ────────────────────────────────────────────────
print("\nTraining Random Forest model...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=50,
    min_samples_leaf=25,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)

# ── Train Logistic Regression (baseline) ─────────────────────────────────────
print("Training Logistic Regression baseline...")
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train, y_train)

# ── Model evaluation ─────────────────────────────────────────────────────────
print("\n--- Model Performance ---")

# Random Forest predictions
rf_pred = rf_model.predict(X_test)
rf_prob = rf_model.predict_proba(X_test)[:, 1]

# Logistic Regression predictions
lr_pred = lr_model.predict(X_test)
lr_prob = lr_model.predict_proba(X_test)[:, 1]

# Classification reports
print("\nRandom Forest Classification Report:")
print(classification_report(y_test, rf_pred, target_names=['Active', 'Churned']))

print("\nLogistic Regression Classification Report:")
print(classification_report(y_test, lr_pred, target_names=['Active', 'Churned']))

# ROC-AUC scores
rf_roc_auc = roc_auc_score(y_test, rf_prob)
lr_roc_auc = roc_auc_score(y_test, lr_prob)
print(f"\nROC-AUC Score:")
print(f"  Random Forest:     {rf_roc_auc:.4f}")
print(f"  Logistic Regression: {lr_roc_auc:.4f}")

# Precision-Recall AUC
rf_ap = average_precision_score(y_test, rf_prob)
lr_ap = average_precision_score(y_test, lr_prob)
print(f"\nAverage Precision Score:")
print(f"  Random Forest:     {rf_ap:.4f}")
print(f"  Logistic Regression: {lr_ap:.4f}")

# ── Feature importance ───────────────────────────────────────────────────────
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n--- Top 10 Most Important Features ---")
print(feature_importance.head(10).to_string(index=False))

# Save predictions
results = X_test.copy()
results['actual_churned'] = y_test
results['rf_predicted_churned'] = rf_pred
results['rf_churn_probability'] = rf_prob
results['lr_churn_probability'] = lr_prob
results.to_csv(OUTPUT_PRED, index=False)
print(f"\nPredictions saved: {OUTPUT_PRED}")

# Save feature matrix
X.to_csv(OUTPUT_FEAT, index=False)
print(f"Feature matrix saved: {OUTPUT_FEAT}")

# ── Chart 1: Feature Importance ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))

top_features = feature_importance.head(10)
colors = [BRAND_BLUE if i % 2 == 0 else ACCENT_GREEN for i in range(len(top_features))]

bars = ax.barh(range(len(top_features)), top_features['importance'].values, color=colors)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'].values)
ax.set_xlabel('Feature Importance', fontsize=11)
ax.set_title('Top 10 Features Predicting Customer Churn', fontsize=13, fontweight='bold')
ax.invert_yaxis()
ax.grid(axis='x', linestyle='--', alpha=0.3)

for bar, val in zip(bars, top_features['importance'].values):
    ax.text(val + 0.002, bar.get_y() + bar.get_height()/2, 
            f'{val:.3f}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig(OUT_FEAT_IMP, dpi=150, bbox_inches='tight')
plt.close()
print(f"Feature importance chart saved: {OUT_FEAT_IMP}")

# ── Chart 2: Confusion Matrix ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Random Forest confusion matrix
cm_rf = confusion_matrix(y_test, rf_pred)
disp_rf = ConfusionMatrixDisplay(confusion_matrix=cm_rf, display_labels=['Active', 'Churned'])
disp_rf.plot(ax=axes[0], cmap='Blues', values_format='d')
axes[0].set_title(f'Random Forest\nAccuracy: {(rf_pred == y_test).mean():.1%}', fontweight='bold')

# Logistic Regression confusion matrix
cm_lr = confusion_matrix(y_test, lr_pred)
disp_lr = ConfusionMatrixDisplay(confusion_matrix=cm_lr, display_labels=['Active', 'Churned'])
disp_lr.plot(ax=axes[1], cmap='Blues', values_format='d')
axes[1].set_title(f'Logistic Regression\nAccuracy: {(lr_pred == y_test).mean():.1%}', fontweight='bold')

plt.tight_layout()
plt.savefig(OUT_CM, dpi=150, bbox_inches='tight')
plt.close()
print(f"Confusion matrix saved: {OUT_CM}")

# ── Chart 3: ROC Curves ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7))

# Random Forest ROC
fpr_rf, tpr_rf, _ = roc_curve(y_test, rf_prob)
ax.plot(fpr_rf, tpr_rf, linewidth=2, label=f'Random Forest (AUC = {rf_roc_auc:.3f})', color=BRAND_BLUE)

# Logistic Regression ROC
fpr_lr, tpr_lr, _ = roc_curve(y_test, lr_prob)
ax.plot(fpr_lr, tpr_lr, linewidth=2, label=f'Logistic Regression (AUC = {lr_roc_auc:.3f})', color=ACCENT_GREEN)

# Diagonal line (random classifier)
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier', alpha=0.5)

ax.set_xlabel('False Positive Rate', fontsize=11)
ax.set_ylabel('True Positive Rate', fontsize=11)
ax.set_title('ROC Curves: Churn Prediction Models', fontsize=13, fontweight='bold')
ax.legend(loc='lower right', fontsize=10)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_ROC, dpi=150, bbox_inches='tight')
plt.close()
print(f"ROC curve saved: {OUT_ROC}")

# ── Chart 4: Precision-Recall Curves ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7))

# Random Forest PR curve
precision_rf, recall_rf, _ = precision_recall_curve(y_test, rf_prob)
ax.plot(recall_rf, precision_rf, linewidth=2, 
        label=f'Random Forest (AP = {rf_ap:.3f})', color=BRAND_BLUE)

# Logistic Regression PR curve
precision_lr, recall_lr, _ = precision_recall_curve(y_test, lr_prob)
ax.plot(recall_lr, precision_lr, linewidth=2,
        label=f'Logistic Regression (AP = {lr_ap:.3f})', color=ACCENT_GREEN)

# Baseline (proportion of positive class)
baseline = y_test.mean()
ax.axhline(y=baseline, color='red', linestyle='--', linewidth=1, 
           label=f'Baseline ({baseline:.1%})', alpha=0.7)

ax.set_xlabel('Recall', fontsize=11)
ax.set_ylabel('Precision', fontsize=11)
ax.set_title('Precision-Recall Curves: Churn Prediction Models', fontsize=13, fontweight='bold')
ax.legend(loc='upper right', fontsize=10)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_PR, dpi=150, bbox_inches='tight')
plt.close()
print(f"Precision-Recall curve saved: {OUT_PR}")

# ── Business insights ────────────────────────────────────────────────────────
print("\n" + "="*70)
print("CHURN PREDICTION MODEL — BUSINESS INSIGHTS")
print("="*70)

print("\nTop 3 predictors of churn:")
for i, row in feature_importance.head(3).iterrows():
    feature_name = row['feature']
    if '_encoded' in feature_name:
        feature_name = feature_name.replace('_encoded', '')
    print(f"  {i+1}. {feature_name}: {row['importance']:.3f}")

print(f"\nModel Performance:")
print(f"  Random Forest ROC-AUC:     {rf_roc_auc:.3f}")
print(f"  Random Forest Precision:   {precision_score(y_test, rf_pred):.3f}")
print(f"  Random Forest Recall:      {recall_score(y_test, rf_pred):.3f}")

print(f"\nBusiness Application:")
print(f"  At 50% probability threshold, the model would flag")
print(f"  {(rf_prob[y_test == 1] > 0.5).mean():.1%} of at-risk users for retention campaigns")
print(f"  Precision at this threshold: {precision_score(y_test, rf_pred):.1%}")

print("\nRecommendations:")
print("  1. Use model to identify high-risk subscribers 30 days before churn")
print("  2. Target retention offers to users with churn probability > 0.5")
print("  3. Focus retention efforts on users with:")
print("     - Low monthly revenue (price-sensitive)")
print("     - Low engagement (sessions_per_month < 5)")
print("     - Free trial users approaching conversion point")
print("  4. A/B test retention interventions on the highest-risk segment")
print("="*70)