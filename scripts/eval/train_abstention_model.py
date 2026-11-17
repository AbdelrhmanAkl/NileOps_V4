"""Fit and Validate Calibrated Abstention Decision via 5-Fold Stratified CV.

Pool: 100 questions (70 in-domain, 30 out-of-domain).
Stratification: in_domain (0/1).
Evaluates:
1. Current baseline (threshold = 0.75)
2. Logistic Regression on [top1_score, margin1_2, margin1_mean10, lexical_support]
3. Transparent 2-signal gate
"""

import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

repo_root = Path(__file__).resolve().parent.parent.parent
cache_path = repo_root / "scratch" / "pool_features_100.json"

with open(cache_path, "r", encoding="utf-8") as f:
    records = json.load(f)

# Targets:
# For abstention: 1 = ABSTAIN (out-of-domain), 0 = ANSWER (in-domain)
y_abstain = np.array([1 if r["should_abstain"] else 0 for r in records])
# For in-domain classification: 1 = in-domain, 0 = out-of-domain
y_in_domain = 1 - y_abstain

X = np.array([[
    r["top1_score"],
    r["margin1_2"],
    r["margin1_mean10"],
    r["lexical_support"],
] for r in records])

feature_names = ["top1_score", "margin1_2", "margin1_mean10", "lexical_support"]

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("=" * 80)
print("             5-FOLD STRATIFIED CROSS-VALIDATION RESULTS")
print("=" * 80)

# -------------------------------------------------------------
# 1. BASELINE: Cosine Threshold = 0.75
# -------------------------------------------------------------
base_hit1, base_hit3, base_mrr = [], [], []
base_abs_rec, base_abs_prec = [], []
base_false_abs = []

for train_idx, test_idx in skf.split(X, y_abstain):
    test_recs = [records[i] for i in test_idx]
    
    in_d = [r for r in test_recs if not r["should_abstain"]]
    out_d = [r for r in test_recs if r["should_abstain"]]
    
    # Decisions at 0.75:
    # Abstain if top1 < 0.75
    tp = sum(1 for r in out_d if r["top1_score"] < 0.75)
    fp = sum(1 for r in in_d if r["top1_score"] < 0.75)
    fn = len(out_d) - tp
    tn = len(in_d) - fp
    
    rec = tp / len(out_d) * 100.0 if out_d else 0.0
    prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
    false_abs_rate = fp / len(in_d) * 100.0 if in_d else 0.0
    
    hit1 = sum(1 for r in in_d if r["hit1"] and r["top1_score"] >= 0.75) / len(in_d) * 100.0
    hit3 = sum(1 for r in in_d if r["hit3"] and r["top1_score"] >= 0.75) / len(in_d) * 100.0
    
    rr_list = []
    for r in in_d:
        if r["top1_score"] >= 0.75 and r["rank"]:
            rr_list.append(1.0 / r["rank"] if r["rank"] <= 3 else 0.0)
        else:
            rr_list.append(0.0)
    mrr = np.mean(rr_list) if in_d else 0.0
    
    base_hit1.append(hit1)
    base_hit3.append(hit3)
    base_mrr.append(mrr)
    base_abs_rec.append(rec)
    base_abs_prec.append(prec)
    base_false_abs.append(false_abs_rate)

print("\n[BASELINE: Absolute Cosine Threshold 0.75]")
print(f"  Hit@1:               {np.mean(base_hit1):.1f}% ± {np.std(base_hit1):.1f}%")
print(f"  Hit@3:               {np.mean(base_hit3):.1f}% ± {np.std(base_hit3):.1f}%")
print(f"  MRR:                 {np.mean(base_mrr):.4f} ± {np.std(base_mrr):.4f}")
print(f"  Abstention Recall:   {np.mean(base_abs_rec):.1f}% ± {np.std(base_abs_rec):.1f}%")
print(f"  Abstention Precision:{np.mean(base_abs_prec):.1f}% ± {np.std(base_abs_prec):.1f}%")
print(f"  False Abstention:    {np.mean(base_false_abs):.1f}% ± {np.std(base_false_abs):.1f}%")


# -------------------------------------------------------------
# 2. LOGISTIC REGRESSION ON MULTI-SIGNAL FEATURES
# -------------------------------------------------------------
lr_hit1, lr_hit3, lr_mrr = [], [], []
lr_abs_rec, lr_abs_prec = [], []
lr_false_abs = []
lr_models = []

for fold, (train_idx, test_idx) in enumerate(skf.split(X, y_in_domain), 1):
    X_train, y_train = X[train_idx], y_in_domain[train_idx]
    X_test = X[test_idx]
    test_recs = [records[i] for i in test_idx]
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    clf = LogisticRegression(class_weight="balanced", random_state=42)
    clf.fit(X_train_scaled, y_train)
    lr_models.append((clf, scaler))
    
    # Predict probability of being in-domain
    probs_in = clf.predict_proba(X_test_scaled)[:, 1]
    
    # Calibrated decision threshold: say P(in_domain) >= 0.50 => Answer, else Abstain
    preds_abstain = [1 if p < 0.50 else 0 for p in probs_in]
    
    in_d_indices = [idx for idx, r in enumerate(test_recs) if not r["should_abstain"]]
    out_d_indices = [idx for idx, r in enumerate(test_recs) if r["should_abstain"]]
    
    tp = sum(1 for idx in out_d_indices if preds_abstain[idx] == 1)
    fp = sum(1 for idx in in_d_indices if preds_abstain[idx] == 1)
    fn = len(out_d_indices) - tp
    tn = len(in_d_indices) - fp
    
    rec = tp / len(out_d_indices) * 100.0 if out_d_indices else 0.0
    prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
    false_abs_rate = fp / len(in_d_indices) * 100.0 if in_d_indices else 0.0
    
    hit1 = sum(1 for idx in in_d_indices if test_recs[idx]["hit1"] and preds_abstain[idx] == 0) / len(in_d_indices) * 100.0
    hit3 = sum(1 for idx in in_d_indices if test_recs[idx]["hit3"] and preds_abstain[idx] == 0) / len(in_d_indices) * 100.0
    
    rr_list = []
    for idx in in_d_indices:
        r = test_recs[idx]
        if preds_abstain[idx] == 0 and r["rank"]:
            rr_list.append(1.0 / r["rank"] if r["rank"] <= 3 else 0.0)
        else:
            rr_list.append(0.0)
    mrr = np.mean(rr_list) if in_d_indices else 0.0
    
    lr_hit1.append(hit1)
    lr_hit3.append(hit3)
    lr_mrr.append(mrr)
    lr_abs_rec.append(rec)
    lr_abs_prec.append(prec)
    lr_false_abs.append(false_abs_rate)

print("\n[MULTI-SIGNAL LOGISTIC REGRESSION (P >= 0.50)]")
print(f"  Hit@1:               {np.mean(lr_hit1):.1f}% ± {np.std(lr_hit1):.1f}%")
print(f"  Hit@3:               {np.mean(lr_hit3):.1f}% ± {np.std(lr_hit3):.1f}%")
print(f"  MRR:                 {np.mean(lr_mrr):.4f} ± {np.std(lr_mrr):.4f}")
print(f"  Abstention Recall:   {np.mean(lr_abs_rec):.1f}% ± {np.std(lr_abs_rec):.1f}%")
print(f"  Abstention Precision:{np.mean(lr_abs_prec):.1f}% ± {np.std(lr_abs_prec):.1f}%")
print(f"  False Abstention:    {np.mean(lr_false_abs):.1f}% ± {np.std(lr_false_abs):.1f}%")


# Fit full model to inspect global parameters
full_scaler = StandardScaler()
X_full_scaled = full_scaler.fit_transform(X)
full_clf = LogisticRegression(class_weight="balanced", random_state=42)
full_clf.fit(X_full_scaled, y_in_domain)

print("\n[GLOBAL FITTED LOGISTIC REGRESSION PARAMETERS]")
print(f"  Intercept: {full_clf.intercept_[0]:.4f}")
for name, coef, m, s in zip(feature_names, full_clf.coef_[0], full_scaler.mean_, full_scaler.scale_):
    print(f"  {name:<16}: coef = {coef:+.4f} | mean = {m:.4f} | scale = {s:.4f}")


# -------------------------------------------------------------
# 3. TRANSPARENT TWO-RULE GATE
# -------------------------------------------------------------
# Gate Rule:
# ANSWER if:
#   top1_score >= T_HIGH (e.g. 0.83 - high semantic confidence answers unconditionally)
#   OR (top1_score >= T_MID and (lexical_support >= L_MIN or margin1_mean10 >= M_MIN))
# Otherwise ABSTAIN.

def evaluate_gate(t_high=0.83, t_mid=0.77, l_min=0.08, m_min=0.02):
    gate_hit1, gate_hit3, gate_mrr = [], [], []
    gate_abs_rec, gate_abs_prec = [], []
    gate_false_abs = []
    
    for train_idx, test_idx in skf.split(X, y_abstain):
        test_recs = [records[i] for i in test_idx]
        in_d = [r for r in test_recs if not r["should_abstain"]]
        out_d = [r for r in test_recs if r["should_abstain"]]
        
        preds_abstain = []
        for r in test_recs:
            top1 = r["top1_score"]
            lex = r["lexical_support"]
            m10 = r["margin1_mean10"]
            
            # Decision rule:
            is_answer = (top1 >= t_high) or (top1 >= t_mid and (lex >= l_min or m10 >= m_min))
            preds_abstain.append(0 if is_answer else 1)
            
        tp = sum(1 for idx, r in enumerate(test_recs) if r["should_abstain"] and preds_abstain[idx] == 1)
        fp = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and preds_abstain[idx] == 1)
        fn = sum(1 for idx, r in enumerate(test_recs) if r["should_abstain"] and preds_abstain[idx] == 0)
        tn = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and preds_abstain[idx] == 0)
        
        rec = tp / len(out_d) * 100.0 if out_d else 0.0
        prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
        false_abs_rate = fp / len(in_d) * 100.0 if in_d else 0.0
        
        hit1 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit1"] and preds_abstain[idx] == 0) / len(in_d) * 100.0
        hit3 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit3"] and preds_abstain[idx] == 0) / len(in_d) * 100.0
        
        rr_list = []
        for idx, r in enumerate(test_recs):
            if not r["should_abstain"]:
                if preds_abstain[idx] == 0 and r["rank"]:
                    rr_list.append(1.0 / r["rank"] if r["rank"] <= 3 else 0.0)
                else:
                    rr_list.append(0.0)
        mrr = np.mean(rr_list) if in_d else 0.0
        
        gate_hit1.append(hit1)
        gate_hit3.append(hit3)
        gate_mrr.append(mrr)
        gate_abs_rec.append(rec)
        gate_abs_prec.append(prec)
        gate_false_abs.append(false_abs_rate)
        
    return {
        "hit1": (np.mean(gate_hit1), np.std(gate_hit1)),
        "hit3": (np.mean(gate_hit3), np.std(gate_hit3)),
        "mrr": (np.mean(gate_mrr), np.std(gate_mrr)),
        "abs_rec": (np.mean(gate_abs_rec), np.std(gate_abs_rec)),
        "abs_prec": (np.mean(gate_abs_prec), np.std(gate_abs_prec)),
        "false_abs": (np.mean(gate_false_abs), np.std(gate_false_abs)),
    }

# Sweep P(in_domain) threshold for Logistic Regression
print("\n" + "=" * 80)
print("             LOGISTIC REGRESSION THRESHOLD SWEEP (5-Fold CV)")
print("=" * 80)
print(f"{'P_cutoff':<8} | {'Hit@1':<14} | {'Hit@3':<14} | {'MRR':<16} | {'Abs Recall':<14} | {'Abs Prec':<14} | {'False Abs':<14}")
print("-" * 80)

for p_cut in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]:
    sw_hit1, sw_hit3, sw_mrr = [], [], []
    sw_abs_rec, sw_abs_prec, sw_false_abs = [], [], []
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y_in_domain), 1):
        X_train, y_train = X[train_idx], y_in_domain[train_idx]
        X_test = X[test_idx]
        test_recs = [records[i] for i in test_idx]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        clf = LogisticRegression(class_weight="balanced", random_state=42)
        clf.fit(X_train_scaled, y_train)
        
        probs_in = clf.predict_proba(X_test_scaled)[:, 1]
        preds_abstain = [1 if p < p_cut else 0 for p in probs_in]
        
        in_d_indices = [idx for idx, r in enumerate(test_recs) if not r["should_abstain"]]
        out_d_indices = [idx for idx, r in enumerate(test_recs) if r["should_abstain"]]
        
        tp = sum(1 for idx in out_d_indices if preds_abstain[idx] == 1)
        fp = sum(1 for idx in in_d_indices if preds_abstain[idx] == 1)
        
        rec = tp / len(out_d_indices) * 100.0 if out_d_indices else 0.0
        prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
        false_abs_rate = fp / len(in_d_indices) * 100.0 if in_d_indices else 0.0
        
        hit1 = sum(1 for idx in in_d_indices if test_recs[idx]["hit1"] and preds_abstain[idx] == 0) / len(in_d_indices) * 100.0
        hit3 = sum(1 for idx in in_d_indices if test_recs[idx]["hit3"] and preds_abstain[idx] == 0) / len(in_d_indices) * 100.0
        
        rr_list = []
        for idx in in_d_indices:
            r = test_recs[idx]
            if preds_abstain[idx] == 0 and r["rank"]:
                rr_list.append(1.0 / r["rank"] if r["rank"] <= 3 else 0.0)
            else:
                rr_list.append(0.0)
        mrr = np.mean(rr_list) if in_d_indices else 0.0
        
        sw_hit1.append(hit1)
        sw_hit3.append(hit3)
        sw_mrr.append(mrr)
        sw_abs_rec.append(rec)
        sw_abs_prec.append(prec)
        sw_false_abs.append(false_abs_rate)
        
    print(f"{p_cut:<8.2f} | {np.mean(sw_hit1):.1f}% ± {np.std(sw_hit1):.1f}% | {np.mean(sw_hit3):.1f}% ± {np.std(sw_hit3):.1f}% | {np.mean(sw_mrr):.4f} ± {np.std(sw_mrr):.4f} | {np.mean(sw_abs_rec):.1f}% ± {np.std(sw_abs_rec):.1f}% | {np.mean(sw_abs_prec):.1f}% ± {np.std(sw_abs_prec):.1f}% | {np.mean(sw_false_abs):.1f}% ± {np.std(sw_false_abs):.1f}%")

# Broader sweep for Transparent Two-Rule Gate
print("\n" + "=" * 80)
print("             TRANSPARENT TWO-RULE GATE GRID SEARCH")
print("=" * 80)
all_gate_results = []
for t_high in [0.81, 0.82, 0.83, 0.84]:
    for t_mid in [0.74, 0.75, 0.76, 0.77]:
        for l_min in [0.01, 0.03, 0.05, 0.08]:
            for m_min in [0.01, 0.015, 0.02]:
                res = evaluate_gate(t_high, t_mid, l_min, m_min)
                all_gate_results.append(((t_high, t_mid, l_min, m_min), res))

# Sort by F1 of abstention + Hit@1
sorted_gates = sorted(all_gate_results, key=lambda x: (x[1]["hit1"][0] >= 85.0, x[1]["abs_rec"][0] + x[1]["hit1"][0]), reverse=True)
top = sorted_gates[0]
bp = top[0]
br = top[1]
print(f"Top Gate Params: t_high={bp[0]}, t_mid={bp[1]}, l_min={bp[2]}, m_min={bp[3]}")
print(f"  Hit@1:               {br['hit1'][0]:.1f}% ± {br['hit1'][1]:.1f}%")
print(f"  Hit@3:               {br['hit3'][0]:.1f}% ± {br['hit3'][1]:.1f}%")
print(f"  MRR:                 {br['mrr'][0]:.4f} ± {br['mrr'][1]:.4f}")
print(f"  Abstention Recall:   {br['abs_rec'][0]:.1f}% ± {br['abs_rec'][1]:.1f}%")
print(f"  Abstention Precision:{br['abs_prec'][0]:.1f}% ± {br['abs_prec'][1]:.1f}%")
print(f"  False Abstention:    {br['false_abs'][0]:.1f}% ± {br['false_abs'][1]:.1f}%")

print("\nTop 5 Gate Param Candidates:")
for p, r in sorted_gates[:5]:
    print(f"  t_high={p[0]}, t_mid={p[1]}, l_min={p[2]}, m_min={p[3]} -> Hit@1: {r['hit1'][0]:.1f}%, AbsRec: {r['abs_rec'][0]:.1f}%, AbsPrec: {r['abs_prec'][0]:.1f}%, FalseAbs: {r['false_abs'][0]:.1f}%")

