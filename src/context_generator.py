"""
Step 1.5 Context Generator
Simulates input from:
- Personal Style (color analysis)
- Context Collector (weather, occasion, itinerary)
"""

import json
from datetime import datetime
from typing import Dict, List, Any


def generate_step15_context(
    user_id: str = "user_001",
    date: str = None,
    temp_c: int = 22,
    humidity: int = 60,
    condition: str = "sunny",
    occasion: List[str] = None,
    user_style_colors: List[str] = None,
    user_style_aesthetics: List[str] = None,
    itinerary: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate Step 1.5 output (simulated color analysis + context).
    
    Args:
        user_id: User identifier
        date: Date string (default: today)
        temp_c: Temperature in Celsius
        humidity: Humidity percentage
        condition: Weather condition (sunny, cloudy, rainy, snowy, etc.)
        occasion: List of occasions (work, date, casual, gym, party, etc.)
        user_style_colors: List of preferred colors (from color analysis)
        user_style_aesthetics: List of preferred aesthetics/styles
        itinerary: List of planned activities with times
    
    Returns:
        Context JSON matching Step 1.5 output format
    """
    
    if date is None:
        date = datetime.now().isoformat()
    
    if occasion is None:
        occasion = ["casual_walk"]
    
    if user_style_colors is None:
        user_style_colors = ["white", "navy", "beige"]
    
    if user_style_aesthetics is None:
        user_style_aesthetics = ["casual", "minimalist"]
    
    if itinerary is None:
        itinerary = [
            {
                "time": "09:00",
                "activity": "office_work",
                "location": "office"
            },
            {
                "time": "12:30",
                "activity": "lunch_meeting",
                "location": "cafe"
            }
        ]
    
    context = {
        "user_id": user_id,
        "date_time": date,
        "location": "taipei",  # TODO: Get from geolocation
        
        # From Step 1.5 Part A: Color Analysis
        "palette_analysis": {
            "dominant_colors": user_style_colors,  # e.g., ["white", "navy", "beige"]
            "seasonal_palette": _classify_seasonal_palette(user_style_colors),
            "skin_tone": "neutral",  # Can be determined by color analysis
            "undertone": "cool"  # warm, cool, neutral
        },
        
        # From Step 1.5 Part B: Context Collector
        "weather": {
            "temp_c": temp_c,
            "humidity": humidity,
            "condition": condition,  # sunny, cloudy, rainy, snowy, windy
            "uv_index": _estimate_uv_index(condition, temp_c),
            "wind_speed_kmh": 10  # Default; can be fetched from weather API
        },
        
        # User preferences for this day
        "preferences": {
            "styles": user_style_aesthetics,  # e.g., ["casual", "minimalist"]
            "colors": user_style_colors,
            "avoid": ["neon", "bright_patterns"],  # Can be set by user
            "fit_pref": "regular"
        },
        
        # Today's planned occasions and activities
        "occasion": occasion,
        "itinerary": itinerary,
        
        # User demographics (relatively static)
        "demographics": {
            "age": 28,
            "gender": "female"
        },
        
        # Recently worn items (to avoid repetition)
        "last_worn_history": []
    }
    
    return context


def _classify_seasonal_palette(colors: List[str]) -> str:
    """
    Classify seasonal color palette based on dominant colors.
    
    Spring: pastels, soft colors
    Summer: bright, light colors
    Fall: earth tones, warm colors
    Winter: cool, deep colors
    """
    color_lower = [c.lower() for c in colors]
    
    spring_colors = ["pink", "peach", "mint", "lavender", "light"]
    summer_colors = ["white", "yellow", "light_blue", "bright"]
    fall_colors = ["orange", "brown", "rust", "olive", "gold"]
    winter_colors = ["navy", "black", "burgundy", "deep", "cool"]
    
    spring_score = sum(1 for c in color_lower if any(sc in c for sc in spring_colors))
    summer_score = sum(1 for c in color_lower if any(sc in c for sc in summer_colors))
    fall_score = sum(1 for c in color_lower if any(sc in c for sc in fall_colors))
    winter_score = sum(1 for c in color_lower if any(sc in c for sc in winter_colors))
    
    scores = {
        "spring": spring_score,
        "summer": summer_score,
        "fall": fall_score,
        "winter": winter_score
    }
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "neutral"


def _estimate_uv_index(condition: str, temp_c: int) -> float:
    """Estimate UV index based on condition."""
    base_uv = {
        "sunny": 8,
        "cloudy": 3,
        "rainy": 1,
        "snowy": 2,
        "windy": 5,
    }.get(condition.lower(), 4)
    
    # Adjust for temperature (higher temp = more sun exposure)
    if temp_c > 25:
        base_uv += 1
    elif temp_c < 5:
        base_uv -= 1
    
    return max(0, min(11, base_uv))


def generate_multiple_contexts(count: int = 5) -> List[Dict[str, Any]]:
    """
    Generate multiple diverse context examples for testing.
    """
    scenarios = [
        {
            "user_id": "user_001",
            "temp_c": 22,
            "condition": "sunny",
            "occasion": ["work", "casual"],
            "user_style_colors": ["white", "navy", "beige"],
            "user_style_aesthetics": ["minimal", "professional"],
        },
        {
            "user_id": "user_002",
            "temp_c": 28,
            "condition": "sunny",
            "occasion": ["date", "casual_walk"],
            "user_style_colors": ["pink", "white", "cream"],
            "user_style_aesthetics": ["romantic", "casual"],
        },
        {
            "user_id": "user_003",
            "temp_c": 5,
            "condition": "cloudy",
            "occasion": ["office", "meeting"],
            "user_style_colors": ["black", "gray", "burgundy"],
            "user_style_aesthetics": ["formal", "modern"],
        },
        {
            "user_id": "user_004",
            "temp_c": 15,
            "condition": "rainy",
            "occasion": ["casual", "shopping"],
            "user_style_colors": ["olive", "brown", "cream"],
            "user_style_aesthetics": ["boho", "earthy"],
        },
        {
            "user_id": "user_005",
            "temp_c": 35,
            "condition": "sunny",
            "occasion": ["beach", "casual_walk"],
            "user_style_colors": ["white", "light_blue", "yellow"],
            "user_style_aesthetics": ["sporty", "casual"],
        },
    ]
    
    return [generate_step15_context(**scenario) for scenario in scenarios[:count]]


if __name__ == "__main__":
    # Generate example contexts
    print("=" * 70)
    print("STEP 1.5 CONTEXT EXAMPLES (Color Analysis + Context Collector)")
    print("=" * 70)
    
    contexts = generate_multiple_contexts(3)
    for ctx in contexts:
        print(f"\n{ctx['user_id']}: {ctx['date_time']}")
        print(f"  Weather: {ctx['weather']['temp_c']}°C, {ctx['weather']['condition']}")
        print(f"  Occasion: {', '.join(ctx['occasion'])}")
        print(f"  Colors: {', '.join(ctx['palette_analysis']['dominant_colors'])}")
        print(f"  Styles: {', '.join(ctx['preferences']['styles'])}")
        print(f"  Palette: {ctx['palette_analysis']['seasonal_palette']}")
    
    # Save one as example
    example_ctx = generate_step15_context(
        user_id="user_demo",
        temp_c=20,
        condition="sunny",
        occasion=["work", "coffee_meeting"],
        user_style_colors=["white", "navy", "beige"],
        user_style_aesthetics=["minimalist", "professional"],
        itinerary=[
            {"time": "09:00", "activity": "office_work", "location": "office"},
            {"time": "14:00", "activity": "coffee_meeting", "location": "cafe"},
        ]
    )
    
    with open("step15_context_example.json", "w", encoding="utf-8") as f:
        json.dump(example_ctx, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved example context to step15_context_example.json")
