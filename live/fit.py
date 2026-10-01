"""Freeze the tested methods for live use: the same train-only fit that results/test.json scored.

  python live/fit.py    # writes models/methods.pkl, after checking it reproduces the test MALE exactly

Not refitted on more data: the live record has to grade the model that passed, not a different one.
"""
import json, os, pickle, sys
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import sklearn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backtest"))
import model as m  # noqa: E402

res = json.load(open("results/test.json"))
cfg = res["params"]["m_config"]
d = m.load("data/backtest")
w, y, X, _ = d["train"]
b2 = float(np.median(y / w))
b, a = np.polyfit(np.log(w), np.log(y), 1)
M = HistGradientBoostingRegressor(max_iter=500, random_state=0, **cfg).fit(X, np.log(y))

wt, yt, Xt, _ = d["test"]
got = m.male(np.exp(M.predict(Xt)), yt)
assert abs(got - res["male"]["M"]) < 1e-12, (got, res["male"]["M"])
assert abs(b2 - res["params"]["b2_ratio"]) < 1e-12

os.makedirs("models", exist_ok=True)
with open("models/methods.pkl", "wb") as f:
    pickle.dump({"M": M, "b2_ratio": b2, "b3": (float(a), float(b)), "b1_ratio": m.B1_RATIO,
                 "features": m.FEATURES, "sklearn": sklearn.__version__, "test_commit": res["commit"]}, f)
print(f"saved; reproduces test MALE {got:.6f}; sklearn {sklearn.__version__}")
