"""
Mock data generator for Step 1.5 (Context Collector)

This module simulates the input from Person 2 (Context Collector).
When the real Person 2 output is ready, replace this with actual data loading.
"""

import json
from datetime import datetime
from typing import Dict, Any


def get_demo_context() -> Dict[str, Any]:
    """
    Get a demo context for outfit recommendation.
    
    Simulates a user requesting an outfit for a specific occasion.
    
    Returns:
        Context dict with user_query, weather, user_profile, and occasion
    """
    return {
        "user_id": "user_demo_001",
        "timestamp": datetime.now().isoformat(),
        "user_query": "I need an outfit for an outdoor summer wedding on the beach",
        "weather": {
            "temperature_c": 30,
            "condition": "Sunny",
            "humidity_percent": 70,
            "description": "Sunny with high humidity, hot"
        },
        "user_profile": {
            "gender": "Female",
            "age": 28,
            "personal_color": "Summer Mute",
            "color_preferences": ["light blue", "soft pink", "white", "beige"],
            "dislike_colors": ["black", "dark red"],
            "style_preferences": ["Elegant", "Minimalist", "Romantic"],
            "dislike_styles": ["Sporty", "Heavy"],
            "body_type": "Pear",
            "fit_preferences": ["A-line", "Flowing"]
        },
        "occasion": {
            "type": "Wedding Guest",
            "location": "Beach",
            "formality": "Semi-formal",
            "time_of_day": "Afternoon",
            "dress_code": "Elegant Casual"
        },
        "constraints": {
            "max_temperature": 32,
            "breathable": True,
            "avoid_heavy_materials": True
        }
    }


def get_beach_wedding_context() -> Dict[str, Any]:
    """
    Alternative demo context: Beach wedding in summer.
    """
    return {
        "user_id": "user_beach_001",
        "timestamp": datetime.now().isoformat(),
        "user_query": "週末要去海邊參加婚禮，需要優雅但輕盈的裝扮",
        "weather": {
            "temperature_c": 28,
            "condition": "Sunny",
            "humidity_percent": 75,
            "description": "晴天，海風明顯，紫外線強"
        },
        "user_profile": {
            "gender": "Female",
            "age": 32,
            "personal_color": "Summer Soft",
            "color_preferences": ["淡藍", "薄荷綠", "米色", "珍珠白"],
            "dislike_colors": ["深色", "冷色"],
            "style_preferences": ["優雅", "簡約", "浪漫"],
            "dislike_styles": ["運動風", "厚重"],
            "body_type": "Hourglass",
            "fit_preferences": ["修身", "傘形"]
        },
        "occasion": {
            "type": "海邊婚禮賓客",
            "location": "海灘",
            "formality": "半正式",
            "time_of_day": "下午",
            "dress_code": "優雅休閒"
        },
        "constraints": {
            "max_temperature": 35,
            "breathable": True,
            "avoid_heavy_materials": True,
            "sun_protection": True
        }
    }


def get_office_meeting_context() -> Dict[str, Any]:
    """
    Alternative demo context: Office business meeting in fall.
    """
    return {
        "user_id": "user_office_001",
        "timestamp": datetime.now().isoformat(),
        "user_query": "Important client meeting today, need professional and polished look",
        "weather": {
            "temperature_c": 18,
            "condition": "Cloudy",
            "humidity_percent": 60,
            "description": "Autumn, cool but not cold"
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
            "min_temperature": 15,
            "professionalism": True,
            "wrinkle_resistant": True
        }
    }


def select_context(scenario: str = "beach_wedding") -> Dict[str, Any]:
    """
    Select a context scenario by name.
    
    Args:
        scenario: One of "beach_wedding", "office_meeting", or "default"
    
    Returns:
        Context dict for the selected scenario
    """
    scenarios = {
        "beach_wedding": get_beach_wedding_context,
        "office_meeting": get_office_meeting_context,
        "default": get_demo_context,
    }
    
    context_fn = scenarios.get(scenario, get_demo_context)
    return context_fn()


if __name__ == "__main__":
    # Print example contexts
    print("=== Beach Wedding Context ===")
    print(json.dumps(get_beach_wedding_context(), indent=2, ensure_ascii=False))
    print("\n=== Office Meeting Context ===")
    print(json.dumps(get_office_meeting_context(), indent=2, ensure_ascii=False))
