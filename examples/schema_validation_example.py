#!/usr/bin/env python
"""
Example: Validate recommendation request/response against JSON schemas.
Run: python examples/schema_validation_example.py
"""

import json
import sys
from src.schemas import validate_schema

# Example 1: Valid recommendation request
valid_request = {
    "user_id": "user_demo",
    "weather": {
        "temp_c": 22,
        "humidity": 60,
        "condition": "sunny"
    },
    "occasion": ["casual_walk", "coffee_meet"],
    "preferences": {
        "styles": ["casual", "smart-casual"],
        "colors": ["white", "navy"]
    },
    "palette_analysis": {
        "dominant_colors": ["white", "navy"],
        "seasonal_palette": "spring"
    },
    "demographics": {
        "age": 28,
        "gender": "female"
    },
    "last_worn_history": ["item_5", "item_12"],
    "top_n": 3,
    "use_llm": True
}

# Example 2: Valid recommendation response
valid_response = {
    "request_id": "req_20251210_001",
    "user_id": "user_demo",
    "timestamp": "2025-12-10T09:00:00Z",
    "context_summary": {
        "temp_c": 22,
        "condition": "sunny",
        "occasion": ["casual_walk"],
        "preferences": {
            "styles": ["casual", "smart-casual"],
            "colors": ["white", "navy"]
        }
    },
    "recommendations": [
        {
            "rank": 1,
            "outfit_id": "outfit_demo_1",
            "overall_score": 0.92,
            "confidence": 0.88,
            "items": [
                {
                    "role": "top",
                    "item_id": "item_42",
                    "title": "白色棉質短袖襯衫",
                    "color": "white",
                    "style": "casual",
                    "material": "cotton",
                    "match_score": 0.95,
                    "image_url": "https://example.com/item_42.jpg"
                },
                {
                    "role": "bottom",
                    "item_id": "item_67",
                    "title": "卡其色亞麻褲",
                    "color": "khaki",
                    "style": "casual",
                    "material": "linen",
                    "match_score": 0.90,
                    "image_url": "https://example.com/item_67.jpg"
                },
                {
                    "role": "shoes",
                    "item_id": "item_89",
                    "title": "米色皮質樂福鞋",
                    "color": "beige",
                    "style": "casual",
                    "material": "leather",
                    "match_score": 0.88,
                    "image_url": "https://example.com/item_89.jpg"
                }
            ],
            "suitability": {
                "temp_ok": True,
                "weather_ok": True,
                "occasion_ok": True,
                "weather_explanation": "棉麻混紡材質透氣性佳，適合 22°C 溫和天氣"
            },
            "reasons": [
                "• 簡潔白色襯衫搭配中性卡其褲，展現都市休閒風格",
                "• 全身色彩偏淡，清爽適合陽光咖啡約會",
                "• 布料輕薄透氣，完美應對春夏季節"
            ],
            "accessory_suggestions": [
                "棕色皮質腰帶",
                "金色簡約手錶"
            ],
            "color_harmony": {
                "harmony_score": 0.92,
                "notes": "白色主調搭配卡其和米色形成溫暖中性的配色"
            },
            "visual_preview_url": "https://example.com/preview/outfit_1.png"
        }
    ],
    "metadata": {
        "retrieval_time_ms": 45,
        "ranking_time_ms": 120,
        "llm_time_ms": 890,
        "total_time_ms": 1055,
        "candidates_retrieved": 50,
        "candidates_assembled": 125,
        "llm_model": "gpt-3.5-turbo",
        "ranking_model": "lightgbm_v1",
        "embedding_model": "all-MiniLM-L6-v2"
    },
    "exposure_control": {
        "max_recs": 3,
        "diversity_penalty": 0.15,
        "freshness_weight": 0.1
    }
}

# Example 3: Invalid request (missing required field)
invalid_request_missing_field = {
    "user_id": "user_demo",
    # Missing "weather" field
    "occasion": ["casual_walk"]
}

# Example 4: Invalid request (wrong type)
invalid_request_wrong_type = {
    "user_id": "user_demo",
    "weather": {
        "temp_c": "22",  # Should be integer, not string
        "condition": "sunny"
    },
    "occasion": ["casual_walk"]
}


def test_schema_validation():
    """Test schema validation."""
    print("\n" + "="*70)
    print("JSON SCHEMA VALIDATION TESTS")
    print("="*70)
    
    test_cases = [
        ("Valid Request", valid_request, "recommendation_request", True),
        ("Valid Response", valid_response, "recommendation_response", True),
        ("Invalid Request (Missing Field)", invalid_request_missing_field, "recommendation_request", False),
        ("Invalid Request (Wrong Type)", invalid_request_wrong_type, "recommendation_request", False),
    ]
    
    for test_name, data, schema_name, should_pass in test_cases:
        is_valid, error_msg = validate_schema(data, schema_name)
        
        status = "✓ PASS" if is_valid == should_pass else "✗ FAIL"
        print(f"\n{status} | {test_name}")
        
        if is_valid:
            print(f"  Schema: {schema_name} ✓ Valid")
        else:
            if should_pass:
                print(f"  Error: {error_msg}")
            else:
                print(f"  Expected validation error: {error_msg[:80]}...")
    
    print("\n" + "="*70)
    print("SCHEMA DOCUMENTATION")
    print("="*70)
    
    print("""
Available schemas:

1. item
   - Clothing item with metadata (color, style, material, season, etc.)
   - Required fields: item_id, title, role, color, style

2. weather_context
   - Weather condition and environment
   - Required fields: temp_c, condition

3. user_context
   - User preferences, occasion, and session context
   - Required fields: user_id, weather, occasion

4. outfit_recommendation
   - Single outfit with items, score, and explanation
   - Required fields: rank, outfit_id, items, overall_score

5. recommendation_request
   - API request format for getting recommendations
   - Required fields: user_id, weather, occasion

6. recommendation_response
   - API response format with top-N recommendations
   - Required fields: request_id, user_id, timestamp, recommendations

Usage:
    from src.schemas import validate_schema
    is_valid, error_msg = validate_schema(data, "recommendation_request")
    if not is_valid:
        print(f"Validation error: {error_msg}")
""")


if __name__ == "__main__":
    test_schema_validation()
