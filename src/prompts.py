"""LangChain prompt templates for outfit recommendation explanations."""

from langchain.prompts import PromptTemplate

# 主要推薦解釋 prompt
EXPLAIN_OUTFIT_PROMPT = PromptTemplate(
    input_variables=["items", "occasion", "weather", "user_style", "reason"],
    template="""You are a professional fashion stylist. Given an outfit recommendation, provide a brief, engaging explanation in Traditional Chinese.

Outfit items:
{items}

User context:
- Occasion: {occasion}
- Weather: {weather}
- Preferred styles: {user_style}
- Primary reason: {reason}

Provide 2-3 short bullet points (each under 20 words) explaining why this outfit is perfect for the user. Format as:
• [reason 1]
• [reason 2]
• [optional accessory suggestion]

Output in Traditional Chinese."""
)

# 配件建議 prompt
ACCESSORY_SUGGESTION_PROMPT = PromptTemplate(
    input_variables=["top_color", "bottom_color", "occasion", "style"],
    template="""As a fashion expert, suggest 2-3 accessory items (bag, shoes, jewelry, scarf, belt) to complete this outfit.

Base outfit colors: Top={top_color}, Bottom={bottom_color}
Occasion: {occasion}
Style preference: {style}

Return ONLY a JSON array like:
["item1", "item2", "item3"]

Be specific (e.g., "棕色皮帶" instead of just "belt")."""
)

# 風格匹配驗證 prompt
STYLE_VALIDATION_PROMPT = PromptTemplate(
    input_variables=["styles", "items"],
    template="""Check if the given outfit items match the requested styles.

Requested styles: {styles}
Outfit items:
{items}

Respond with a JSON object:
{{"matches": true/false, "confidence": 0.0-1.0, "explanation": "..."}}

Respond ONLY with valid JSON, no markdown."""
)

# 天氣適配性檢查 prompt
WEATHER_CHECK_PROMPT = PromptTemplate(
    input_variables=["temp_c", "humidity", "condition", "items"],
    template="""Assess if this outfit is suitable for the given weather conditions.

Weather: {temp_c}°C, humidity {humidity}%, {condition}
Outfit items:
{items}

Return JSON:
{{"suitable": true/false, "score": 0.0-1.0, "adjustment": "..."}}

Respond ONLY with valid JSON."""
)

# 色彩和諧檢查 prompt
COLOR_HARMONY_PROMPT = PromptTemplate(
    input_variables=["colors"],
    template="""Evaluate the color harmony of this outfit.

Colors: {colors}

Rate the color harmony and provide brief styling notes.
Return JSON:
{{"harmony_score": 0.0-1.0, "notes": "..."}}

Respond ONLY with valid JSON."""
)


def get_explain_outfit_prompt():
    """Get the main outfit explanation prompt."""
    return EXPLAIN_OUTFIT_PROMPT


def get_accessory_suggestion_prompt():
    """Get the accessory suggestion prompt."""
    return ACCESSORY_SUGGESTION_PROMPT


def get_style_validation_prompt():
    """Get the style validation prompt."""
    return STYLE_VALIDATION_PROMPT


def get_weather_check_prompt():
    """Get the weather check prompt."""
    return WEATHER_CHECK_PROMPT


def get_color_harmony_prompt():
    """Get the color harmony prompt."""
    return COLOR_HARMONY_PROMPT
