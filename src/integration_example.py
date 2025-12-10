"""
Simple end-to-end integration example for the Outfit Recommendation System.

This demonstrates the complete data flow:
1. Input: User context from Person 2 (mock_context)
2. Processing: Outfit retrieval and selection
3. Output: JSON for Person 4 (Virtual Try-On Presenter)

Example outputs are saved to files for inspection.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mock_context import get_beach_wedding_context, get_office_meeting_context, select_context
from src.data_loader import CatalogLoader
from src.recommend_interface import OutfitRecommender, RecommendationOutput


def demonstrate_input_formats():
    """
    Demonstrate the input formats from Person 2 (Context Collector).
    
    These are mock contexts since Person 2 hasn't delivered real data yet.
    """
    print("\n" + "=" * 70)
    print("STEP 1: INPUT FORMATS (from Person 2 - Context Collector)")
    print("=" * 70)
    
    print("\n📋 Beach Wedding Context (Example 1):")
    context1 = get_beach_wedding_context()
    print(json.dumps(context1, ensure_ascii=False, indent=2))
    
    print("\n📋 Office Meeting Context (Example 2):")
    context2 = get_office_meeting_context()
    print(json.dumps(context2, ensure_ascii=False, indent=2))
    
    # Save for reference
    with open("context_example_beach.json", "w", encoding="utf-8") as f:
        json.dump(context1, f, ensure_ascii=False, indent=2)
    
    with open("context_example_office.json", "w", encoding="utf-8") as f:
        json.dump(context2, f, ensure_ascii=False, indent=2)
    
    print("\n✓ Context examples saved to context_example_*.json")
    return context1, context2


def demonstrate_catalog_loading():
    """
    Demonstrate catalog loading (from Person 1 - Catalog Builder).
    
    Shows how to load and search the outfit descriptions.
    """
    print("\n" + "=" * 70)
    print("STEP 2: CATALOG LOADING (from Person 1 - Catalog Builder)")
    print("=" * 70)
    
    try:
        # Try to load actual catalog
        loader = CatalogLoader(catalog_path="items.json")
        print(f"\n✓ Loaded catalog with {loader.catalog_size} items")
        
        # Show statistics
        stats = loader.get_stats()
        print(f"\nCatalog Statistics:")
        print(f"  - Total items: {stats['total_items']}")
        print(f"  - Unique colors: {stats['unique_colors']}")
        print(f"  - Unique materials: {stats['unique_materials']}")
        print(f"  - Unique styles: {stats['unique_styles']}")
        print(f"  - Has embeddings: {stats['has_embeddings']}")
        
        # Show first few items
        print(f"\n📦 First 3 items in catalog:")
        for item in loader.get_all()[:3]:
            print(f"\n  ID: {item.get('item_id')}")
            print(f"  Title: {item.get('title')}")
            print(f"  Color: {item.get('color')}")
            print(f"  Material: {item.get('material')}")
            print(f"  Style: {item.get('style')}")
        
        return loader
    
    except FileNotFoundError as e:
        print(f"\n⚠️  Catalog file not found: {e}")
        print("Please ensure items.json exists in the root directory")
        return None


def demonstrate_recommendation_process(context: Dict[str, Any], loader=None):
    """
    Demonstrate the recommendation process.
    
    Shows the complete pipeline: Retrieve → Reason → Output.
    """
    print("\n" + "=" * 70)
    print("STEP 3: RECOMMENDATION PROCESS (Outfit Planner)")
    print("=" * 70)
    
    try:
        # Initialize recommender
        recommender = OutfitRecommender(catalog_path="items.json")
        
        print(f"\n🔍 Input Context:")
        print(f"  User Query: {context.get('user_query')}")
        print(f"  Occasion: {context.get('occasion', {}).get('type')}")
        print(f"  Temperature: {context.get('weather', {}).get('temperature_c')}°C")
        print(f"  Style Preferences: {context.get('user_profile', {}).get('style_preferences')}")
        
        # Generate recommendation
        print(f"\n⚙️  Processing recommendation...")
        output = recommender.recommend(context=context, top_k=5)
        
        print(f"✓ Recommendation generated!")
        print(f"  Selected Item: {output.selected_outfit_filename}")
        print(f"  Confidence: {output.confidence_score:.2%}")
        
        return output
    
    except Exception as e:
        print(f"\n❌ Recommendation failed: {e}")
        return None


def demonstrate_output_formats(output: RecommendationOutput):
    """
    Demonstrate the output format for Person 4 (Virtual Try-On Presenter).
    
    This is the final JSON that Person 4 will receive.
    """
    print("\n" + "=" * 70)
    print("STEP 4: OUTPUT FORMAT (for Person 4 - Virtual Try-On Presenter)")
    print("=" * 70)
    
    output_dict = output.to_dict()
    
    print("\n📤 Complete Recommendation Output (JSON):")
    print(json.dumps(output_dict, ensure_ascii=False, indent=2))
    
    # Highlight key fields
    print(f"\n🔑 Key Fields for Person 4:")
    print(f"\n1️⃣  selected_outfit_filename: {output.selected_outfit_filename}")
    print(f"   → Which image file to show (from Person 1's catalog)")
    
    print(f"\n2️⃣  reasoning: {output.reasoning[:100]}...")
    print(f"   → Why this outfit was selected (explanation to user)")
    
    print(f"\n3️⃣  vton_prompt (first 150 chars):")
    print(f"   {output.vton_prompt[:150]}...")
    print(f"   → For Stable Diffusion virtual try-on generation")
    
    print(f"\n4️⃣  confidence_score: {output.confidence_score:.2%}")
    print(f"   → How confident are we in this recommendation")
    
    return output_dict


def save_complete_example():
    """
    Generate and save a complete example for documentation.
    """
    print("\n" + "=" * 70)
    print("SAVING COMPLETE EXAMPLE")
    print("=" * 70)
    
    # Load beach wedding context
    context = get_beach_wedding_context()
    
    try:
        recommender = OutfitRecommender(catalog_path="items.json")
        output = recommender.recommend(context=context)
        output_dict = output.to_dict()
    except Exception as e:
        print(f"Using fallback example due to: {e}")
        output_dict = {
            "selected_outfit_filename": "12.jpg",
            "selected_outfit_id": "outfit_12",
            "reasoning": "這件淡藍色雪紡洋裝非常適合海邊婚禮，顏色符合Summer Mute色調，且材質透氣適合30度高溫。",
            "vton_prompt": "A photorealistic image of an elegant woman wearing a light blue chiffon dress (flowing silhouette, romantic style), standing gracefully on a beach, sunny lighting, professional photography, cinematic, ultra high quality",
            "negative_prompt": "ugly, distorted, blurry, low quality",
            "confidence_score": 0.87,
            "fashion_notes": "完美詮釋Summer Mute色彩季型。傘形剪裁修飾梨形身材。得體展現半正式場合的優雅氣質。",
            "generated_at": "2025-12-10T12:00:00"
        }
    
    # Save complete example
    with open("complete_example_input_output.json", "w", encoding="utf-8") as f:
        complete_example = {
            "scenario": "beach_wedding",
            "input_context": context,
            "output_recommendation": output_dict,
            "description": "Complete example of input from Person 2 and output for Person 4"
        }
        json.dump(complete_example, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Complete example saved to complete_example_input_output.json")
    return output_dict


def main():
    """Run the complete demonstration."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  OUTFIT RECOMMENDATION SYSTEM - INTEGRATION EXAMPLE           ║")
    print("║  Demonstrating Input/Output Format Specifications             ║")
    print("╚" + "=" * 68 + "╝")
    
    # Step 1: Show input formats from Person 2
    context1, context2 = demonstrate_input_formats()
    
    # Step 2: Show catalog loading from Person 1
    loader = demonstrate_catalog_loading()
    
    # Step 3: Show recommendation process
    output = demonstrate_recommendation_process(context1, loader)
    
    if output:
        # Step 4: Show output format for Person 4
        output_dict = demonstrate_output_formats(output)
        
        # Save complete example
        save_complete_example()
    
    print("\n" + "=" * 70)
    print("✓ Integration example completed!")
    print("=" * 70)
    print("\nFiles generated:")
    print("  - context_example_beach.json: Input from Person 2 (beach scenario)")
    print("  - context_example_office.json: Input from Person 2 (office scenario)")
    print("  - recommendation_output.json: Output for Person 4 (from recommend_interface.py)")
    print("  - complete_example_input_output.json: Full input/output example")
    print("\nNext steps:")
    print("  1. Replace mock contexts with real data from Person 2")
    print("  2. Provide Person 1's catalog as items.json + embeddings NPY")
    print("  3. Run main_recommend() to get recommendations")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
