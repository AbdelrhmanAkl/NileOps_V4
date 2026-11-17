"""Calibrate Abstention Decision: Logistic Regression vs Two-Rule Gate on 5-Fold Stratified CV.
"""

import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

repo_root = Path(__file__).resolve().parent.parent.parent
cache_path = repo_root / "scratch" / "pool_features_100.json"

with open(cache_path, "r", encoding="utf-8") as f:
    records = json.load(f)

y_in_domain = np.array([0 if r["should_abstain"] else 1 for r in records])
y_abstain = 1 - y_in_domain

X = np.array([[
    r["top1_score"],
    r["margin1_2"],
    r["margin1_mean10"],
    r["lexical_support"],
] for r in records])

feature_names = ["top1_score", "margin1_2", "margin1_mean10", "lexical_support"]
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("=" * 80)
print("     COMPARING CALIBRATED ABSTENTION MODELS (5-Fold CV)")
print("=" * 80)

# 1. Sweep Logistic Regression P_threshold
best_lr = None
best_lr_score = -1

for p_cut in np.linspace(0.10, 0.45, 15):
    hit1_l, hit3_l, mrr_l, rec_l, prec_l, fa_l = [], [], [], [], [], []
    for train_idx, test_idx in skf.split(X, y_in_domain):
        X_train, y_train = X[train_idx], y_in_domain[train_idx]
        X_test = X[test_idx]
        test_recs = [records[i] for i in test_idx]
        
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        clf = LogisticRegression(class_weight="balanced", random_state=42, C=1.0)
        clf.fit(X_train_s, y_train)
        
        probs = clf.predict_proba(X_test_s)[:, 1]
        preds_abs = [1 if p < p_cut else 0 for p in probs]
        
        in_recs = [r for idx, r in enumerate(test_recs) if not r["should_abstain"]]
        out_recs = [r for idx, r in enumerate(test_recs) if r["should_abstain"]]
        
        tp = sum(1 for idx, r in enumerate(test_recs) if r["should_abstain"] and preds_abs[idx] == 1)
        fp = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and preds_abs[idx] == 1)
        
        rec = tp / len(out_recs) * 100.0 if out_recs else 0.0
        prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
        fa = fp / len(in_recs) * 100.0 if in_recs else 0.0
        
        h1 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit1"] and preds_abs[idx] == 0) / len(in_recs) * 100.0
        h3 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit3"] and preds_abs[idx] == 0) / len(in_recs) * 100.0
        
        rr = []
        for idx, r in enumerate(test_recs):
            if not r["should_abstain"]:
                rr.append(1.0 / r["rank"] if (preds_abs[idx] == 0 and r["rank"] and r["rank"] <= 3) else 0.0)
        
        hit1_l.append(h1)
        hit3_l.append(h3)
        mrr_l.append(np.mean(rr))
        rec_l.append(rec)
        prec_l.append(prec)
        fa_l.append(fa)
        
    mean_h1 = np.mean(hit1_l)
    mean_rec = np.mean(rec_l)
    mean_prec = np.mean(prec_l)
    # Target objective: balanced accuracy (Hit1 + Abstention Recall) with low False Abstention
    score = mean_h1 * 0.5 + mean_rec * 0.5
    if score > best_lr_score and mean_h1 >= 84.0 and mean_rec >= 70.0:
        best_lr_score = score
        best_lr = {
            "p_cut": p_cut,
            "hit1": (mean_h1, np.std(hit1_l)),
            "hit3": (np.mean(hit3_l), np.std(hit3_l)),
            "mrr": (np.mean(mrr_l), np.std(mrr_l)),
            "rec": (mean_rec, np.std(rec_l)),
            "prec": (mean_prec, np.std(prec_l)),
            "fa": (np.mean(fa_l), np.std(fa_l)),
        }

if best_lr:
    print(f"\n[BEST LOGISTIC REGRESSION: P_cutoff = {best_lr['p_cut']:.3f}]")
    print(f"  Hit@1:               {best_lr['hit1'][0]:.1f}% ± {best_lr['hit1'][1]:.1f}%")
    print(f"  Hit@3:               {best_lr['hit3'][0]:.1f}% ± {best_lr['hit3'][1]:.1f}%")
    print(f"  MRR:                 {best_lr['mrr'][0]:.4f} ± {best_lr['mrr'][1]:.4f}")
    print(f"  Abstention Recall:   {best_lr['rec'][0]:.1f}% ± {best_lr['rec'][1]:.1f}%")
    print(f"  Abstention Precision:{best_lr['prec'][0]:.1f}% ± {best_lr['prec'][1]:.1f}%")
    print(f"  False Abstention:    {best_lr['fa'][0]:.1f}% ± {best_lr['fa'][1]:.1f}%")


# 2. Sweep Two-Rule Gate
# Rule: Answer IF:
#   (top1 >= T_HIGH and margin1_2 >= M_MIN)
#   OR (top1 >= T_LOW and lexical_support >= L_MIN)
# Otherwise Abstain.

best_gate = None
best_gate_score = -1

for t_high in [0.80, 0.81, 0.82, 0.83]:
    for m_min in [0.015, 0.020, 0.025, 0.030]:
        for t_low in [0.75, 0.76, 0.77, 0.78]:
            for l_min in [0.08, 0.10, 0.12, 0.15]:
                hit1_l, hit3_l, mrr_l, rec_l, prec_l, fa_l = [], [], [], [], [], []
                for train_idx, test_idx in skf.split(X, y_in_domain):
                    test_recs = [records[i] for i in test_idx]
                    in_recs = [r for r in test_recs if not r["should_abstain"]]
                    out_recs = [r for r in test_recs if r["should_abstain"]]
                    
                    preds_abs = []
                    for r in test_recs:
                        t1 = r["top1_score"]
                        m12 = r["margin1_2"]
                        lex = r["lexical_support"]
                        
                        is_ans = (t1 >= t_high and m12 >= m_min) or (t1 >= t_low and lex >= l_min)
                        preds_abs.append(0 if is_ans else 1)
                        
                    tp = sum(1 for idx, r in enumerate(test_recs) if r["should_abstain"] and preds_abs[idx] == 1)
                    fp = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and preds_abs[idx] == 1)
                    
                    rec = tp / len(out_recs) * 100.0 if out_recs else 0.0
                    prec = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
                    fa = fp / len(in_recs) * 100.0 if in_recs else 0.0
                    
                    h1 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit1"] and preds_abs[idx] == 0) / len(in_recs) * 100.0
                    h3 = sum(1 for idx, r in enumerate(test_recs) if not r["should_abstain"] and r["hit3"] and preds_abs[idx] == 0) / len(in_recs) * 100.0
                    
                    rr = []
                    for idx, r in enumerate(test_recs):
                        if not r["should_abstain"]:
                            rr.append(1.0 / r["rank"] if (preds_abs[idx] == 0 and r["rank"] and r["rank"] <= 3) else 0.0)
                    
                    hit1_l.append(h1)
                    hit3_l.append(h3)
                    mrr_l.append(np.mean(rr))
                    rec_l.append(rec)
                    prec_l.append(prec)
                    fa_l.append(fa)
                    
                mean_h1 = np.mean(hit1_l)
                mean_rec = np.mean(rec_l)
                mean_prec = np.mean(prec_l)
                score = mean_h1 * 0.5 + mean_rec * 0.5
                if score > best_gate_score and mean_h1 >= 84.0 and mean_rec >= 70.0:
                    best_gate_score = score
                    best_gate = {
                        "params": (t_high, m_min, t_low, l_min),
                        "hit1": (mean_h1, np.std(hit1_l)),
                        "hit3": (np.mean(hit3_l), np.std(hit3_l)),
                        "mrr": (np.mean(mrr_l), np.std(mrr_l)),
                        "rec": (mean_rec, np.std(rec_l)),
                        "prec": (mean_prec, np.std(prec_l)),
                        "fa": (np.mean(fa_l), np.std(fa_l)),
                    }

if best_gate:
    gp = best_gate["params"]
    print(f"\n[BEST TWO-RULE GATE: T_HIGH={gp[0]}, M_MIN={gp[1]}, T_LOW={gp[2]}, L_MIN={gp[3]}]")
    print(f"  Hit@1:               {best_gate['hit1'][0]:.1f}% ± {best_gate['hit1'][1]:.1f}%")
    print(f"  Hit@3:               {best_gate['hit3'][0]:.1f}% ± {best_gate['hit3'][1]:.1f}%")
    print(f"  MRR:                 {best_gate['mrr'][0]:.4f} ± {best_gate['mrr'][1]:.4f}")
    print(f"  Abstention Recall:   {best_gate['rec'][0]:.1f}% ± {best_gate['rec'][1]:.1f}%")
    print(f"  Abstention Precision:{best_gate['prec'][0]:.1f}% ± {best_gate['prec'][1]:.1f}%")
    print(f"  False Abstention:    {best_gate['fa'][0]:.1f}% ± {best_gate['fa'][1]:.1f}%")
