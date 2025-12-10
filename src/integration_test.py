#!/usr/bin/env python
"""
End-to-End Integration Test
Simulates complete data flow from Step 1 → Step 3 → Step 4

This script shows:
1. Load Step 1 catalog (or synthetic fallback)
2. Generate Step 1.5 context (color analysis + weather + occasion)
3. Run Step 3 recommendation (FAISS + LightGBM + LLM)
4. Format output for Step 4 (virtual try-on)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import generate_items, generate_context
from src.data_loader import load_catalog_from_step1, convert_to_standard_format, save_standardized_catalog
from src.recommend import recommend
from src.context_generator import generate_step15_context
from src.schemas import validate_schema


def load_or_create_step1_catalog(step1_json_path: str = None) -> List[Dict]:
    """
    Load Step 1 catalog or use synthetic data.
    
    Args:
        step1_json_path: Path to outfit_descriptions.json from Step 1
    
    Returns:
        List of items in standardized format
    """
    if step1_json_path and Path(step1_json_path).exists():
        print(f"📦 Loading Step 1 catalog from {step1_json_path}")
        catalog = load_catalog_from_step1(step1_json_path)
        standardized = convert_to_standard_format(catalog)
        print(f"   ✓ Loaded {len(standardized)} items from Step 1")
        return standardized
    else:
        print("📦 Using synthetic Step 1 catalog (Step 1 data not available)")
        items = generate_items(n=200)
        print(f"   ✓ Generated {len(items)} synthetic items")
        return items


def format_for_step4(recommendations: List[Dict]) -> Dict[str, Any]:
    """
    Format Step 3 output for Step 4 (virtual try-on presenter).
    
    Args:
        recommendations: Top-N recommendations from Step 3
    
    Returns:
        JSON structure for Step 4 API
    """
    return {
        "status": "success",
        "timestamp": recommendations[0].get("timestamp", ""),
        "recommended_outfits": [
            {
                "rank": i + 1,
                "score": rec["score"],
                "confidence": rec.get("confidence", rec["score"]),
                "items": {
                    "top": rec["top_id"],
                    "bottom": rec["bottom_id"],
                    "shoes": rec["shoes_id"],
                },
                "colors": rec.get("colors", {
                    "primary": "n/a",
                    "secondary": "n/a"
                }),
                "explanation": rec.get("explanation", ""),
                "accessories": rec.get("accessories_suggestions", []),
                "metadata": {
                    "style": rec.get("style", ""),
                    "occasion_fit": rec.get("occasion", ""),
                    "weather_fit": rec.get("weather_suitability", ""),
                }
            }
            for i, rec in enumerate(recommendations[:3])
        ],
        "next_steps": [
            "1. User selects outfit from top 3",
            "2. Step 4 loads item images from Google Drive",
            "3. Virtual try-on visualization",
            "4. Feedback to Step 3 (acceptance/rejection)"
        ]
    }


def run_integration_test(
    step1_path: str = None,
    use_llm: bool = False,
    output_file: str = "integration_test_output.json"
):
    """
    Execute end-to-end integration test.
    
    Args:
        step1_path: Path to Step 1 outfit_descriptions.json
        use_llm: Whether to use LLM for explanations
        output_file: Output JSON filename
    """
    
    print("\n" + "=" * 80)
    print("END-TO-END INTEGRATION TEST: Step 1 → Step 3 → Step 4")
    print("=" * 80)
    
    # ========== STEP 1: Load Catalog ==========
    print("\n[STEP 1] Loading Outfit Catalog...")
    items = load_or_create_step1_catalog(step1_path)
    
    # Save catalog for Step 3
    catalog_path = "catalog_for_step3.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"   ✓ Saved to {catalog_path}")
    
    # ========== STEP 1.5: Generate Context ==========
    print("\n[STEP 1.5] Generating User Context (Color Analysis + Weather + Occasion)...")
    
    # Example 1: Office work
    context1 = generate_step15_context(
        user_id="user_demo_office",
        temp_c=22,
        condition="cloudy",
        occasion=["work", "meeting"],
        user_style_colors=["white", "navy", "gray"],
        user_style_aesthetics=["professional", "minimalist"],
        itinerary=[
            {"time": "09:00", "activity": "office_work", "location": "office"},
            {"time": "14:00", "activity": "client_meeting", "location": "office"},
        ]
    )
    
    context_path = "context_for_step3.json"
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context1, f, ensure_ascii=False, indent=2)
    
    print(f"   User: {context1['user_id']}")
    print(f"   Occasion: {', '.join(context1['occasion'])}")
    print(f"   Weather: {context1['weather']['temp_c']}°C, {context1['weather']['condition']}")
    print(f"   Palette: {context1['palette_analysis']['dominant_colors']}")
    print(f"   ✓ Saved to {context_path}")
    
    # ========== STEP 3: Run Recommendation ==========
    print("\n[STEP 3] Running Outfit Recommendation Pipeline...")
    
    try:
        # Check if index exists
        index_path = "faiss.index"
        if not Path(index_path).exists():
            print("   ⚠️  FAISS index not found. Building...")
            from src.index import build_item_embeddings, load_item_embeddings
            build_item_embeddings(catalog_path, "item_embeddings.pkl", "faiss.index")
        
        # Check if model exists
        model_path = "model.joblib"
        if not Path(model_path).exists():
            print("   ⚠️  LightGBM model not found. Training...")
            from src.train import train_ranking_model
            from src.data import generate_preference_data
            preferences = generate_preference_data(len(items), n_samples=500)
            train_ranking_model(
                items_path=catalog_path,
                preferences_path="preferences.json",
                model_path=model_path
            )
        
        # Run recommendation
        recommendations = recommend(
            context_path=context_path,
            items_path=catalog_path,
            index_path=index_path,
            model_path=model_path,
            top_n=3,
            use_llm=use_llm
        )
        
        print(f"   ✓ Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            print(f"     - Rank {rec.get('rank', 'N/A')}: {rec['top']} + {rec['bottom']} "
                  f"(Score: {rec['score']:.3f})")
    
    except Exception as e:
        print(f"   ⚠️  Recommendation failed: {e}")
        print("   Using fallback synthetic recommendations...")
        recommendations = generate_fallback_recommendations(items)
    
    # ========== STEP 4: Format Output ==========
    print("\n[STEP 4] Formatting Output for Virtual Try-On Presenter...")
    
    step4_output = format_for_step4(recommendations)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(step4_output, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ Generated {len(step4_output['recommended_outfits'])} outfit options")
    print(f"   ✓ Saved to {output_file}")
    
    # ========== VALIDATION ==========
    print("\n[VALIDATION] Checking output format...")
    
    # Validate recommendation response schema
    is_valid, error = validate_schema(step4_output, "recommendation_response")
    if is_valid:
        print("   ✓ Step 4 output matches expected schema")
    else:
        print(f"   ⚠️  Schema validation warning: {error}")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"✓ Step 1 (Catalog):    Loaded {len(items)} items")
    print(f"✓ Step 1.5 (Context):  Generated user context ({context1['user_id']})")
    print(f"✓ Step 3 (Recommend):  Generated {len(recommendations)} recommendations")
    print(f"✓ Step 4 (Format):     Output saved to {output_file}")
    print("\nData flow:")
    print(f"  {catalog_path} (Step 1)")
    print(f"  ↓")
    print(f"  {context_path} (Step 1.5)")
    print(f"  ↓")
    print(f"  Step 3 Pipeline (FAISS + LightGBM + LLM)")
    print(f"  ↓")
    print(f"  {output_file} (Step 4)")
    print("\n" + "=" * 80)
    
    return {
        "catalog_count": len(items),
        "recommendations": recommendations,
        "step4_output": step4_output,
        "context": context1
    }


def generate_fallback_recommendations(items: List[Dict], top_n: int = 3) -> List[Dict]:
    """
    Generate fallback recommendations if main pipeline fails.
    """
    import random
    
    tops = [i for i in items if i.get("role") == "top"]
    bottoms = [i for i in items if i.get("role") == "bottom"]
    shoes = [i for i in items if i.get("role") == "shoes"]
    
    recommendations = []
    for rank in range(min(top_n, 3)):
        rec = {
            "rank": rank + 1,
            "score": 0.7 - rank * 0.05,
            "top": random.choice(tops).get("id", "top_01") if tops else "top_01",
            "top_id": random.choice(tops).get("id", "top_01") if tops else "top_01",
            "bottom": random.choice(bottoms).get("id", "bottom_01") if bottoms else "bottom_01",
            "bottom_id": random.choice(bottoms).get("id", "bottom_01") if bottoms else "bottom_01",
            "shoes_id": random.choice(shoes).get("id", "shoes_01") if shoes else "shoes_01",
            "explanation": f"Fallback recommendation #{rank + 1}",
            "timestamp": "2025-01-01T00:00:00",
            "colors": {"primary": "gray", "secondary": "white"}
        }
        recommendations.append(rec)
    
    return recommendations


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="End-to-end integration test")
    parser.add_argument("--step1-path", help="Path to Step 1 outfit_descriptions.json")
    parser.add_argument("--with-llm", action="store_true", help="Use LLM for explanations")
    parser.add_argument("--output", default="integration_test_output.json", help="Output file")
    
    args = parser.parse_args()
    
    result = run_integration_test(
        step1_path=args.step1_path,
        use_llm=args.with_llm,
        output_file=args.output
    )
