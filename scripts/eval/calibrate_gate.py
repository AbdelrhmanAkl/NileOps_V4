"""Refined Multi-Signal Gate Sweep with Margin1_Mean10.
"""

import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold

repo_root = Path(__file__).resolve().parent.parent.parent
cache_path = repo_root / "scratch" / "pool_features_100.json"

with open(cache_path, "r", encoding="utf-8") as f:
    records = json.load(f)

y_in_domain = np.array([0 if r["should_abstain"] else 1 for r in records])
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

candidates = []

for t_high in [0.80, 0.81, 0.82]:
    for m12_min in [0.010, 0.015, 0.020]:
        for m10_min in [0.015, 0.020, 0.025]:
            for t_low in [0.76, 0.77, 0.78]:
                for l_min in [0.06, 0.08, 0.10]:
                    hit1_l, hit3_l, mrr_l, rec_l, prec_l, fa_l = [], [], [], [], [], []
                    for train_idx, test_idx in skf.split(records, y_in_domain):
                        test_recs = [records[i] for i in test_idx]
                        in_recs = [r for r in test_recs if not r["should_abstain"]]
                        out_recs = [r for r in test_recs if r["should_abstain"]]
                        
                        preds_abs = []
                        for r in test_recs:
                            t1 = r["top1_score"]
                            m12 = r["margin1_2"]
                            m10 = r["margin1_mean10"]
                            lex = r["lexical_support"]
                            
                            is_ans = (t1 >= t_high and m12 >= m12_min and m10 >= m10_min) or (t1 >= t_low and lex >= l_min)
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
                    candidates.append({
                        "params": (t_high, m12_min, m10_min, t_low, l_min),
                        "hit1": (mean_h1, np.std(hit1_l)),
                        "hit3": (np.mean(hit3_l), np.std(hit3_l)),
                        "mrr": (np.mean(mrr_l), np.std(mrr_l)),
                        "rec": (mean_rec, np.std(rec_l)),
                        "prec": (mean_prec, np.std(prec_l)),
                        "fa": (np.mean(fa_l), np.std(fa_l)),
                    })

# Filter candidates where Hit@1 >= 85.0% and Abstention Recall >= 80.0%
viable = [c for c in candidates if c["hit1"][0] >= 85.0 and c["rec"][0] >= 80.0]
if not viable:
    viable = [c for c in candidates if c["hit1"][0] >= 84.0 and c["rec"][0] >= 75.0]

sorted_viable = sorted(viable, key=lambda x: x["hit1"][0] * 0.5 + x["rec"][0] * 0.5, reverse=True)

print("Top 5 Calibrated Gate Configurations:")
for i, c in enumerate(sorted_viable[:5], 1):
    p = c["params"]
    print(f"\n#{i}: T_HIGH={p[0]}, M12_MIN={p[1]}, M10_MIN={p[2]}, T_LOW={p[3]}, L_MIN={p[4]}")
    print(f"   Hit@1:               {c['hit1'][0]:.1f}% ± {c['hit1'][1]:.1f}%")
    print(f"   Hit@3:               {c['hit3'][0]:.1f}% ± {c['hit3'][1]:.1f}%")
    print(f"   MRR:                 {c['mrr'][0]:.4f} ± {c['mrr'][1]:.4f}")
    print(f"   Abstention Recall:   {c['rec'][0]:.1f}% ± {c['rec'][1]:.1f}%")
    print(f"   Abstention Precision:{c['prec'][0]:.1f}% ± {c['prec'][1]:.1f}%")
    print(f"   False Abstention:    {c['fa'][0]:.1f}% ± {c['fa'][1]:.1f}%")
