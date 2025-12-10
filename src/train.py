import itertools
import random
import os
import json
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import lightgbm as lgb


def color_match_score(items):
    # simple heuristic: if any two items share same color -> +1
    colors = [it["color"] for it in items]
    return len(colors) - len(set(colors))


def style_match_score(items, pref_styles):
    styles = [it["style"] for it in items]
    return sum(1 for s in styles if s in pref_styles) / max(1, len(styles))


def season_match_score(items, target_temp):
    # map temp to likely season
    if target_temp <= 10:
        season = "winter"
    elif target_temp <= 18:
        season = "fall"
    elif target_temp <= 24:
        season = "spring"
    else:
        season = "summer"
    return sum(1 for it in items if it["season"] == season) / len(items)


def create_candidates(items, context, max_cand: int = 200):
    # sample random outfits (top+bottom+shoes) for training
    tops = [it for it in items if it["role"] == "top"]
    bottoms = [it for it in items if it["role"] == "bottom"]
    shoes = [it for it in items if it["role"] == "shoes"]
    combos = []
    for _ in range(max_cand):
        combo = [random.choice(tops), random.choice(bottoms), random.choice(shoes)]
        combos.append(combo)
    return combos


def featurize_combo(combo, ctx_emb=None, item_embs=None):
    # simple features
    feat = {}
    feat["color_match"] = color_match_score(combo)
    feat["style_match_pref"] = style_match_score(combo, ctx_emb.get("styles", []))
    feat["season_match"] = season_match_score(combo, ctx_emb.get("temp_c", 20))
    feat["avg_popularity"] = sum(it.get("popularity", 0) for it in combo) / len(combo)
    # embedding similarity if provided
    if item_embs is not None and ctx_emb.get("embed") is not None:
        avg_item = np.mean(item_embs, axis=0)
        feat["ctx_item_sim"] = float(cosine_similarity([avg_item], [ctx_emb["embed"]])[0][0])
    else:
        feat["ctx_item_sim"] = 0.0
    return feat


def build_training_data(items, contexts):
    # contexts: list of context dicts
    X = []
    y = []
    for ctx in contexts:
        combos = create_candidates(items, ctx, max_cand=100)
        for combo in combos:
            # heuristic label: weighted sum of features
            s_color = color_match_score(combo)
            s_style = style_match_score(combo, ctx["preferences"]["styles"])
            s_season = season_match_score(combo, ctx["weather"]["temp_c"])
            score = 0.4 * s_style + 0.3 * s_season + 0.3 * (s_color / 2.0)
            f = featurize_combo(combo, ctx_emb={
                "styles": ctx["preferences"]["styles"],
                "temp_c": ctx["weather"]["temp_c"]
            })
            X.append(list(f.values()))
            y.append(score)
    X = np.array(X)
    y = np.array(y)
    return X, y


def train_and_save(items_path="items.json", ctx_path="context.json", out_model="model.joblib"):
    import json
    with open(items_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    with open(ctx_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)
    # create several context variations for training
    contexts = [ctx]
    for i in range(10):
        c = ctx.copy()
        c["weather"] = c["weather"].copy()
        c["weather"]["temp_c"] = random.randint(5, 30)
        contexts.append(c)

    X, y = build_training_data(items, contexts)
    dtrain = lgb.Dataset(X, label=y)
    params = {"objective": "regression", "metric": "l2", "verbose": -1}
    bst = lgb.train(params, dtrain, num_boost_round=50)
    joblib.dump(bst, out_model)
    print("Saved model to", out_model)


if __name__ == "__main__":
    train_and_save()
