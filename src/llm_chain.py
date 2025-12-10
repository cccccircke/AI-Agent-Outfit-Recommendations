"""LLM-based tools for outfit recommendation using OpenAI API."""

import json
import os
from typing import List, Dict, Optional

import openai

from src.prompts import (
    get_explain_outfit_prompt,
    get_accessory_suggestion_prompt,
    get_style_validation_prompt,
    get_weather_check_prompt,
    get_color_harmony_prompt,
)


class OutfitExplainer:
    """Use LLM to generate natural language explanations for outfit recommendations."""

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize with OpenAI LLM.
        
        Args:
            model: Model name (e.g., "gpt-3.5-turbo", "gpt-4")
            temperature: Sampling temperature for creativity
        
        Requires OPENAI_API_KEY environment variable.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        openai.api_key = api_key
        self.model = model
        self.temperature = temperature

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with given prompt."""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=500,
        )
        return response["choices"][0]["message"]["content"]

    def explain_outfit(
        self,
        items: List[Dict],
        occasion: str,
        weather: Dict,
        user_style: List[str],
        primary_reason: str = "comfort and style",
    ) -> str:
        """
        Generate natural language explanation for outfit.
        
        Args:
            items: List of outfit items with title, color, style
            occasion: Event type (e.g., "office", "date", "casual")
            weather: Dict with temp_c, humidity, condition
            user_style: List of user's preferred styles
            primary_reason: Main reason for recommendation
        
        Returns:
            Multi-line explanation string with bullet points
        """
        items_str = "\n".join([
            f"- {it['role'].upper()}: {it['title']} ({it['color']}, {it['style']})"
            for it in items
        ])
        weather_str = f"{weather['temp_c']}°C, {weather.get('condition', 'unknown')}, humidity {weather.get('humidity', 'N/A')}%"
        style_str = ", ".join(user_style)
        
        template = get_explain_outfit_prompt()
        prompt = template.format(
            items=items_str,
            occasion=occasion,
            weather=weather_str,
            user_style=style_str,
            reason=primary_reason,
        )
        
        return self._call_openai(prompt).strip()

    def suggest_accessories(
        self,
        top_color: str,
        bottom_color: str,
        occasion: str,
        style: str,
    ) -> List[str]:
        """
        Suggest accessories for the outfit.
        
        Args:
            top_color: Color of top item
            bottom_color: Color of bottom item
            occasion: Event type
            style: Style preference
        
        Returns:
            List of suggested accessory names
        """
        template = get_accessory_suggestion_prompt()
        prompt = template.format(
            top_color=top_color,
            bottom_color=bottom_color,
            occasion=occasion,
            style=style,
        )
        
        result = self._call_openai(prompt)
        try:
            accessories = json.loads(result.strip())
            return accessories if isinstance(accessories, list) else [accessories]
        except json.JSONDecodeError:
            # fallback: split by comma
            return [a.strip() for a in result.split(",")]

    def validate_style(self, styles: List[str], items: List[Dict]) -> Dict:
        """
        Validate if outfit matches requested styles.
        
        Args:
            styles: Requested styles
            items: Outfit items
        
        Returns:
            Dict with matches, confidence, explanation
        """
        styles_str = ", ".join(styles)
        items_str = "\n".join([f"- {it['title']}" for it in items])
        
        template = get_style_validation_prompt()
        prompt = template.format(
            styles=styles_str,
            items=items_str,
        )
        
        result = self._call_openai(prompt)
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"matches": True, "confidence": 0.5, "explanation": result}

    def check_weather_suitability(
        self,
        temp_c: int,
        humidity: int,
        condition: str,
        items: List[Dict],
    ) -> Dict:
        """
        Check if outfit is suitable for weather.
        
        Args:
            temp_c: Temperature in Celsius
            humidity: Humidity percentage
            condition: Weather condition (sunny, rainy, etc.)
            items: Outfit items
        
        Returns:
            Dict with suitable, score, adjustment
        """
        items_str = "\n".join([f"- {it['title']} ({it['material']})" for it in items])
        
        template = get_weather_check_prompt()
        prompt = template.format(
            temp_c=temp_c,
            humidity=humidity,
            condition=condition,
            items=items_str,
        )
        
        result = self._call_openai(prompt)
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"suitable": True, "score": 0.7, "adjustment": ""}

    def evaluate_color_harmony(self, colors: List[str]) -> Dict:
        """
        Evaluate color harmony of outfit.
        
        Args:
            colors: List of colors in the outfit
        
        Returns:
            Dict with harmony_score and notes
        """
        colors_str = ", ".join(colors)
        
        template = get_color_harmony_prompt()
        prompt = template.format(colors=colors_str)
        
        result = self._call_openai(prompt)
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"harmony_score": 0.75, "notes": "Colors are well-coordinated"}


def create_explanation_tools():
    """
    Factory function to create LLM-based explanation tools.
    
    Returns:
        Dict of tools keyed by name
    """
    try:
        explainer = OutfitExplainer()
    except ValueError as e:
        print(f"Warning: {e}. Explanation tools will be unavailable.")
        return {}
    
    return {
        "explainer": explainer,
        "explain_outfit": explainer.explain_outfit,
        "suggest_accessories": explainer.suggest_accessories,
        "validate_style": explainer.validate_style,
        "check_weather": explainer.check_weather_suitability,
        "color_harmony": explainer.evaluate_color_harmony,
    }
