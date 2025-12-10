import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import joblib
from sklearn.metrics.pairwise import cosine_similarity

# Import LLM tools
try:
    from src.llm_chain import OutfitExplainer, create_explanation_tools
    HAS_LLM = True
except ImportError:
    HAS_LLM = False
    OutfitExplainer = None

MODEL_NAME = "all-MiniLM-L6-v2"


def load_items(path="items.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_index(path="./data/items.index"):
    return faiss.read_index(path)


def embed_text(texts):
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    return emb


def retrieve_candidates(ctx, items, index, top_k=10):
    # embed context
    txt = f"preferences: {ctx['preferences']}. occasion: {ctx['occasion']}. weather: {ctx['weather']}"
    ctx_emb = embed_text([txt])[0]
    D, I = index.search(np.array([ctx_emb]), top_k)
    idxs = I[0].tolist()
    candidates = [items[i] for i in idxs]
    return candidates, ctx_emb


def assemble_outfits(candidates):
    # simple greedy assembly: ensure top+bottom+shoes
    tops = [c for c in candidates if c['role'] == 'top']
    bottoms = [c for c in candidates if c['role'] == 'bottom']
    shoes = [c for c in candidates if c['role'] == 'shoes']
    outfits = []
    for t in tops[:5]:
        for b in bottoms[:5]:
            for s in shoes[:5]:
                outfits.append([t, b, s])
    return outfits


def featurize_combo_for_model(combo, ctx):
    # mimic features from train.py
    color_match = len([it['color'] for it in combo]) - len(set([it['color'] for it in combo]))
    style_match = sum(1 for it in combo if it['style'] in ctx['preferences']['styles']) / len(combo)
    temp = ctx['weather']['temp_c']
    if temp <= 10:
        season = 'winter'
    elif temp <= 18:
        season = 'fall'
    elif temp <= 24:
        season = 'spring'
    else:
        season = 'summer'
    season_match = sum(1 for it in combo if it['season'] == season) / len(combo)
    avg_pop = sum(it.get('popularity', 0) for it in combo) / len(combo)
    return [color_match, style_match, season_match, avg_pop, 0.0]


def explain_outfit(combo, ctx):
    reasons = []
    reasons.append(f"This set matches your preferred style ({', '.join(ctx['preferences']['styles'])}).")
    reasons.append(f"Colors: {', '.join([it['color'] for it in combo])} — balanced and suitable for the occasion.")
    reasons.append(f"Materials and seasonality: {', '.join([it['season'] for it in combo])} — suitable for {ctx['weather']['temp_c']}°C.")
    return reasons


def recommend(context_path="context.json", items_path="items.json", index_path="./data/items.index", model_path="model.joblib", top_n=3, use_llm=False):
    items = load_items(items_path)
    index = load_index(index_path)
    with open(context_path, 'r', encoding='utf-8') as f:
        ctx = json.load(f)
    candidates, ctx_emb = retrieve_candidates(ctx, items, index, top_k=50)
    outfits = assemble_outfits(candidates)
    # load model
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    else:
        model = None
    
    # Initialize LLM if requested and available
    explainer = None
    if use_llm and HAS_LLM:
        try:
            explainer = OutfitExplainer()
        except ValueError as e:
            print(f"Warning: Could not initialize LLM: {e}")
    
    scored = []
    for o in outfits:
        feats = featurize_combo_for_model(o, ctx)
        score = model.predict([feats])[0] if model is not None else (feats[1] * 0.5 + feats[2] * 0.3 + feats[0] * 0.2)
        scored.append((score, o))
    scored.sort(key=lambda x: x[0], reverse=True)
    recs = []
    for rank, (s, o) in enumerate(scored[:top_n], start=1):
        if explainer:
            reasons = explainer.explain_outfit(o, ctx['occasion'][0], ctx['weather'], ctx['preferences']['styles'])
            reasons = [r.strip() for r in reasons.split('\n') if r.strip().startswith('•')]
            accessories = explainer.suggest_accessories(o[0]['color'], o[1]['color'], ctx['occasion'][0], ctx['preferences']['styles'][0])
        else:
            reasons = explain_outfit(o, ctx)
            accessories = []
        
        recs.append({
            "rank": rank,
            "overall_score": float(s),
            "items": [{"role": it['role'], "item_id": it['item_id'], "title": it['title'], "color": it['color'], 'image_url': ''} for it in o],
            "reasons": reasons,
            "accessory_suggestions": accessories,
        })
    out = {"user_id": ctx['user_id'], "timestamp": ctx['date_time'], "recommendations": recs}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    import sys
    use_llm = "--with-llm" in sys.argv
    recommend(use_llm=use_llm)
