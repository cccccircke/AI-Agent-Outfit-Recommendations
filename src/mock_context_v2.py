"""
Enhanced Mock Context Generator (Part 2 Simulation)
Provides realistic input scenarios for outfit recommendation testing.

This module simulates what Part 2 (Context Collector) would provide:
- User query (natural language)
- Weather conditions
- User profile (personal color, style preferences, body type)
- Occasion details
- Constraints
"""

import json
from datetime import datetime
from typing import Dict, Any, Literal


def get_base_context() -> Dict[str, Any]:
    """Return base context structure for all scenarios."""
    return {
        "user_id": "",
        "timestamp": datetime.now().isoformat(),
        "user_query": "",
        "weather": {
            "temperature_c": 20,
            "condition": "Mild",
            "humidity_percent": 60,
            "description": ""
        },
        "user_profile": {
            "gender": "Female",
            "age": 30,
            "personal_color": "Neutral",
            "color_preferences": [],
            "dislike_colors": [],
            "style_preferences": [],
            "dislike_styles": [],
            "body_type": "Rectangle",
            "fit_preferences": []
        },
        "occasion": {
            "type": "Casual",
            "location": "Indoor",
            "formality": "Casual",
            "time_of_day": "Afternoon",
            "dress_code": "Casual"
        },
        "constraints": {
            "breathable": False,
            "avoid_heavy_materials": False,
            "sun_protection": False,
            "wrinkle_resistant": False
        }
    }


def get_beach_wedding_context() -> Dict[str, Any]:
    """
    Scenario: Beach wedding guest (coastal, sunny, warm)
    Personal Color: Summer Soft
    """
    ctx = get_base_context()
    ctx.update({
        "user_id": "user_beach_wedding_001",
        "user_query": "週末要去海邊參加婚禮，需要優雅但輕盈的裝扮，要展現Summer Soft色調的氣質",
        "weather": {
            "temperature_c": 32,
            "condition": "Sunny",
            "humidity_percent": 75,
            "description": "晴朗炎熱，海風明顯，紫外線強"
        },
        "user_profile": {
            "gender": "Female",
            "age": 32,
            "personal_color": "Summer Soft",
            "color_preferences": ["light blue", "mint green", "beige", "cream"],
            "dislike_colors": ["deep colors", "dark tones"],
            "style_preferences": ["Elegant", "Romantic", "Breathable"],
            "dislike_styles": ["Sporty", "Heavy", "Dark"],
            "body_type": "Hourglass",
            "fit_preferences": ["Fitted", "Flowing"]
        },
        "occasion": {
            "type": "Wedding Guest (Beach)",
            "location": "Beach",
            "formality": "Semi-formal",
            "time_of_day": "Afternoon",
            "dress_code": "Elegant Casual"
        },
        "constraints": {
            "breathable": True,
            "avoid_heavy_materials": True,
            "sun_protection": True,
            "max_temperature": 35
        }
    })
    return ctx


def get_office_meeting_context() -> Dict[str, Any]:
    """
    Scenario: Important business meeting (professional environment)
    Personal Color: Autumn Deep
    """
    ctx = get_base_context()
    ctx.update({
        "user_id": "user_office_meeting_001",
        "user_query": "重要客戶會議，需要專業得體、展現Autumn Deep色調的商務穿搭",
        "weather": {
            "temperature_c": 18,
            "condition": "Cloudy",
            "humidity_percent": 60,
            "description": "秋季涼爽，室內外溫差不大"
        },
        "user_profile": {
            "gender": "Female",
            "age": 35,
            "personal_color": "Autumn Deep",
            "color_preferences": ["burgundy", "navy", "camel", "cream"],
            "dislike_colors": ["bright pink", "neon"],
            "style_preferences": ["Professional", "Minimalist", "Elegant"],
            "dislike_styles": ["Casual", "Sporty"],
            "body_type": "Pear",
            "fit_preferences": ["Tailored", "Straight"]
        },
        "occasion": {
            "type": "Business Meeting",
            "location": "Office",
            "formality": "Formal",
            "time_of_day": "Morning",
            "dress_code": "Business Professional"
        },
        "constraints": {
            "breathable": False,
            "wrinkle_resistant": True,
            "professionalism": True,
            "min_temperature": 15
        }
    })
    return ctx


def get_casual_date_context() -> Dict[str, Any]:
    """
    Scenario: Weekend casual date (relaxed, outdoor)
    Personal Color: Spring Light
    """
    ctx = get_base_context()
    ctx.update({
        "user_id": "user_casual_date_001",
        "user_query": "週末約會，輕鬆但精緻，展現Spring Light明亮色調的魅力",
        "weather": {
            "temperature_c": 22,
            "condition": "Pleasant",
            "humidity_percent": 50,
            "description": "春天宜人，陽光充足"
        },
        "user_profile": {
            "gender": "Female",
            "age": 28,
            "personal_color": "Spring Light",
            "color_preferences": ["white", "soft pink", "light yellow", "soft green"],
            "dislike_colors": ["muddy colors"],
            "style_preferences": ["Casual", "Elegant", "Chic"],
            "dislike_styles": ["Overly formal", "Sportswear"],
            "body_type": "Apple",
            "fit_preferences": ["Fitted top", "Flowy bottom"]
        },
        "occasion": {
            "type": "Casual Date",
            "location": "Outdoor/Café",
            "formality": "Casual",
            "time_of_day": "Afternoon",
            "dress_code": "Smart Casual"
        },
        "constraints": {
            "breathable": True,
            "avoid_heavy_materials": False,
            "sun_protection": False
        }
    })
    return ctx


def get_formal_dinner_context() -> Dict[str, Any]:
    """
    Scenario: Formal evening dinner (elegant, sophisticated)
    Personal Color: Winter Clear
    """
    ctx = get_base_context()
    ctx.update({
        "user_id": "user_formal_dinner_001",
        "user_query": "晚宴盛典，展現Winter Clear冷色調的高級優雅",
        "weather": {
            "temperature_c": 16,
            "condition": "Clear",
            "humidity_percent": 40,
            "description": "冬夜清爽，室內有空調"
        },
        "user_profile": {
            "gender": "Female",
            "age": 38,
            "personal_color": "Winter Clear",
            "color_preferences": ["black", "white", "deep blue", "burgundy"],
            "dislike_colors": ["warm tones", "muted colors"],
            "style_preferences": ["Sophisticated", "Elegant", "Timeless"],
            "dislike_styles": ["Casual", "Trendy"],
            "body_type": "Inverted Triangle",
            "fit_preferences": ["Fitted", "Tailored"]
        },
        "occasion": {
            "type": "Formal Dinner",
            "location": "Restaurant/Venue",
            "formality": "Black Tie",
            "time_of_day": "Evening",
            "dress_code": "Formal Evening Wear"
        },
        "constraints": {
            "breathable": False,
            "wrinkle_resistant": True,
            "professionalism": True,
            "luxury": True
        }
    })
    return ctx


def select_context(scenario: Literal["beach_wedding", "office_meeting", "casual_date", "formal_dinner"] = "beach_wedding") -> Dict[str, Any]:
    """
    Select a context scenario.
    
    Args:
        scenario: One of 'beach_wedding', 'office_meeting', 'casual_date', 'formal_dinner'
    
    Returns:
        Context dictionary ready for outfit recommendation
    """
    scenarios = {
        "beach_wedding": get_beach_wedding_context,
        "office_meeting": get_office_meeting_context,
        "casual_date": get_casual_date_context,
        "formal_dinner": get_formal_dinner_context,
    }
    
    getter = scenarios.get(scenario, get_beach_wedding_context)
    return getter()


def validate_context(context: Dict[str, Any]) -> bool:
    """
    Validate that context has required fields for outfit recommendation.
    
    Args:
        context: Context dictionary
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = {"user_query", "weather", "user_profile", "occasion"}
    return all(key in context for key in required_keys)


if __name__ == "__main__":
    # Test all scenarios
    scenarios = ["beach_wedding", "office_meeting", "casual_date", "formal_dinner"]
    for scenario_name in scenarios:
        ctx = select_context(scenario_name)
        is_valid = validate_context(ctx)
        print(f"\n{scenario_name}:")
        print(f"  Query: {ctx['user_query']}")
        print(f"  Weather: {ctx['weather']['temperature_c']}°C, {ctx['weather']['condition']}")
        print(f"  Personal Color: {ctx['user_profile']['personal_color']}")
        print(f"  Occasion: {ctx['occasion']['type']}")
        print(f"  Valid: {is_valid}")
