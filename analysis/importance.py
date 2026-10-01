"""Exploratory, not pre-registered: which week-one signals the fixed model leans on.
Refits M with the configuration chosen on validation (results/test.json) on train, and permutes each feature on validation."""
import json, sys
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
sys.path.insert(0, "backtest")
import model as m

d = m.load("data/backtest")
cfg = json.load(open("results/test.json"))["params"]["m_config"]
w, y, X, _ = d["train"]
mod = HistGradientBoostingRegressor(max_iter=500, random_state=0, **cfg).fit(X, np.log(y))
wv, yv, Xv, _ = d["validation"]
r = permutation_importance(mod, Xv, np.log(yv), scoring="neg_mean_absolute_error", n_repeats=20, random_state=0)
for i in np.argsort(-r.importances_mean):
    print(f"{m.FEATURES[i]:<16} +{r.importances_mean[i]:.4f} MALE when shuffled (sd {r.importances_std[i]:.4f})")
