import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict

MODEL_NAME = "all-MiniLM-L6-v2"


def build_item_embeddings(items: List[Dict], save_dir: str = "./data") -> None:
    os.makedirs(save_dir, exist_ok=True)
    texts = [f"{it['title']}. {it['description']}" for it in items]
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    # normalize for inner-product similarity
    faiss.normalize_L2(emb)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    faiss.write_index(index, os.path.join(save_dir, "items.index"))
    np.save(os.path.join(save_dir, "items_emb.npy"), emb)


def load_index(path: str = "./data/items.index"):
    return faiss.read_index(path)


def embed_texts(texts: List[str]):
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    return emb


if __name__ == "__main__":
    import json
    with open("items.json", "r", encoding="utf-8") as f:
        items = json.load(f)
    build_item_embeddings(items, save_dir="./data")
