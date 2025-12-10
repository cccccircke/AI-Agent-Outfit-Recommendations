import random
import json
from typing import List, Dict

ROLES = ["top", "bottom", "outer", "shoes", "accessory"]
STYLES = ["casual", "formal", "sporty", "boho", "street", "smart-casual"]
COLORS = ["white", "black", "navy", "khaki", "brown", "beige", "olive", "red", "green"]
MATERIALS = ["cotton", "linen", "wool", "polyester", "leather"]
PATTERNS = ["plain", "stripe", "floral", "check"]
SEASONS = ["spring", "summer", "fall", "winter"]


def _rand_choice(lst):
    return random.choice(lst)


def generate_items(n: int = 200, seed: int = 42) -> List[Dict]:
    random.seed(seed)
    items = []
    for i in range(n):
        role = _rand_choice(ROLES)
        style = _rand_choice(STYLES)
        color = _rand_choice(COLORS)
        material = _rand_choice(MATERIALS)
        pattern = _rand_choice(PATTERNS)
        season = _rand_choice(SEASONS)
        title = f"{color} {material} {role}"
        desc = f"A {style}, {pattern} {role} in {color} made of {material}. Suitable for {season}."
        items.append({
            "item_id": f"item_{i}",
            "role": role,
            "title": title,
            "description": desc,
            "color": color,
            "style": style,
            "material": material,
            "pattern": pattern,
            "season": season,
            "available": True,
            "popularity": random.random(),
        })
    return items


def generate_context(seed: int = 1) -> Dict:
    random.seed(seed)
    temp_c = random.randint(5, 30)
    humidity = random.randint(20, 90)
    pref_styles = random.sample(STYLES, k=1)
    occasion = random.choice(["work", "date", "coffee", "gym", "party", "outdoor_walk"])
    palette = random.sample(COLORS, k=2)
    ctx = {
        "user_id": "user_demo",
        "date_time": "2025-12-10T09:00:00Z",
        "location": "demo_city",
        "weather": {"temp_c": temp_c, "humidity": humidity, "condition": "sunny"},
        "preferences": {"styles": pref_styles, "colors": palette},
        "occasion": [occasion],
        "palette_analysis": {"dominant_colors": palette, "seasonal_palette": None},
        "demographics": {"age": 30, "gender": "female"},
        "last_worn_history": [],
    }
    return ctx


def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    items = generate_items(200)
    ctx = generate_context()
    save_json("items.json", items)
    save_json("context.json", ctx)
