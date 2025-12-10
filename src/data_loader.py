"""
Data loader and converter for Step 1 (Catalog Builder) output.
Expects outfit_descriptions.json from the Catalog Builder.
"""

import json
from typing import List, Dict, Any


def load_catalog_from_step1(json_path: str) -> List[Dict[str, Any]]:
    """
    Load outfit catalog from Step 1 output (outfit_descriptions.json).
    
    Args:
        json_path: Path to outfit_descriptions.json from Step 1
    
    Returns:
        List of outfit items with standardized fields for Step 3
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        step1_data = json.load(f)
    
    items = []
    for idx, outfit in enumerate(step1_data):
        # Map Step 1 fields to our standardized schema
        item = {
            "item_id": f"outfit_{idx}",
            "category": outfit.get("category", ""),  # Upper, Lower, Dress, Set
            "subcategory": outfit.get("subcategory", ""),
            "title": outfit.get("complete_description", outfit.get("subcategory", f"Outfit {idx}")),
            "role": _map_category_to_role(outfit.get("category", "")),
            "color": outfit.get("color_primary", ""),
            "color_secondary": outfit.get("color_secondary", ""),
            "colors": [outfit.get("color_primary", "")] + 
                     ([outfit.get("color_secondary", "")] if outfit.get("color_secondary") else []),
            "pattern": outfit.get("pattern", ""),
            "material": outfit.get("material", ""),
            "style": outfit.get("style_aesthetic", ""),
            "fit": outfit.get("fit_silhouette", ""),
            "sleeve_length": outfit.get("sleeve_length", ""),
            "length": outfit.get("length", ""),
            "description": outfit.get("complete_description", ""),
            "raw_metadata": outfit,  # Keep original for reference
        }
        items.append(item)
    
    return items


def _map_category_to_role(category: str) -> str:
    """Map Step 1 category to our role field."""
    category_lower = category.lower()
    if "upper" in category_lower:
        return "top"
    elif "lower" in category_lower:
        return "bottom"
    elif "dress" in category_lower:
        return "dress"
    elif "set" in category_lower:
        return "set"
    else:
        return "other"


def convert_to_standard_format(step1_catalog: List[Dict]) -> List[Dict]:
    """
    Convert Step 1 items to standard format for recommender.
    
    Args:
        step1_catalog: Output from load_catalog_from_step1()
    
    Returns:
        Items in standardized schema format
    """
    standardized = []
    for item in step1_catalog:
        std_item = {
            "item_id": item["item_id"],
            "title": item["title"],
            "role": item["role"],
            "color": item["color"],
            "colors": item["colors"],
            "style": item["style"],
            "material": item["material"],
            "pattern": item["pattern"],
            "fit": item["fit"],
            "description": item["description"],
            "category": item["category"],
            "subcategory": item["subcategory"],
            "sleeve_length": item.get("sleeve_length", ""),
            "length": item.get("length", ""),
            "available": True,
            "popularity": 0.5,  # Default; can be updated based on usage
            "image_url": "",  # To be filled with actual image URLs
        }
        standardized.append(std_item)
    
    return standardized


def save_standardized_catalog(items: List[Dict], output_path: str):
    """Save standardized catalog to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example usage (when Step 1 data is available)
    try:
        catalog = load_catalog_from_step1("outfit_descriptions.json")
        standardized = convert_to_standard_format(catalog)
        save_standardized_catalog(standardized, "catalog_standardized.json")
        print(f"✓ Loaded {len(catalog)} outfits from Step 1")
        print(f"✓ Converted to {len(standardized)} standardized items")
    except FileNotFoundError:
        print("outfit_descriptions.json not found. Using synthetic data instead.")
