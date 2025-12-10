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

# VTON (Virtual Try-On) Prompt 生成 - 這是關鍵的新 Prompt
VTON_PROMPT_GENERATION = PromptTemplate(
    input_variables=["outfit_description", "color", "material", "fit", "occasion", "style"],
    template="""Generate a detailed Stable Diffusion/AI image generation prompt for virtual try-on of this outfit.

Outfit Details:
- Description: {outfit_description}
- Color: {color}
- Material: {material}
- Fit: {fit}
- Occasion: {occasion}
- Style: {style}

Create a photorealistic prompt that includes:
1. Detailed outfit description
2. Body positioning and pose
3. Setting/background appropriate for the occasion
4. Lighting conditions
5. Photography style and quality

Output format (JSON):
{{
    "vton_prompt": "A photorealistic image of a model wearing [complete outfit description], [pose], [background], [lighting], [photo quality]",
    "negative_prompt": "ugly, distorted, blurry, low quality, amateur, unfinished",
    "style_note": "[brief note about how the outfit expresses the desired style]"
}}

Respond ONLY with valid JSON."""
)


# Enhanced VTON / Outfit recommendation prompt (emphasize environment and lighting)
OUTFIT_RECOMMENDATION_PROMPT_V2 = PromptTemplate(
    input_variables=["outfit_description", "color", "material", "fit", "occasion", "style", "weather", "time_of_day"],
    template="""You are a virtual stylist generating a Stable Diffusion-ready prompt.

Include:
1) Complete outfit description (color, material, fit)
2) Background/setting appropriate for the occasion (e.g., beach, office lobby, restaurant)
3) Lighting and shadows adapted to the weather and time of day (e.g., "golden hour lighting, long soft shadows" for sunny afternoon)
4) Pose and body positioning
5) Photography style and quality

Weather: {weather}
Time of day: {time_of_day}

Output a JSON object only with these keys: `vton_prompt`, `negative_prompt`, `style_note`.
Make sure the `vton_prompt` explicitly mentions the environment and lighting as described above.

Example vton_prompt start: "A photorealistic image of a model wearing {color} {material} {outfit_description}, standing in a {occasion} with {lighting}..."

Respond ONLY with valid JSON."""
)

# 完整推薦輸出 Prompt - 給 Person 4 (Virtual Try-On Presenter)
COMPLETE_RECOMMENDATION_PROMPT = PromptTemplate(
    input_variables=["selected_outfit", "occasion", "weather", "user_style", "personal_color"],
    template="""You are a fashion AI assistant. Create a complete outfit recommendation in JSON format for virtual try-on presentation.

Selected Outfit:
{selected_outfit}

User Context:
- Occasion: {occasion}
- Weather: {weather}
- Style preferences: {user_style}
- Personal color: {personal_color}

Generate:
1. A clear reasoning explanation (why this outfit is perfect)
2. A detailed VTON prompt for image generation
3. Key fashion insights

Output format (JSON):
{{
    "selected_outfit_id": "...",
    "selected_outfit_filename": "...",
    "reasoning": "...",
    "vton_prompt": "...",
    "negative_prompt": "...",
    "fashion_notes": "...",
    "confidence_score": 0.0-1.0
}}

Respond ONLY with valid JSON, ensure Traditional Chinese for reasoning if needed."""
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


def get_vton_prompt_generation():
    """Get the VTON prompt generation template."""
    return VTON_PROMPT_GENERATION


def get_outfit_recommendation_prompt_v2():
    """Get the enhanced VTON/outfit recommendation prompt (V2)."""
    return OUTFIT_RECOMMENDATION_PROMPT_V2


def get_complete_recommendation_prompt():
    """Get the complete recommendation output prompt for Person 4."""
    return COMPLETE_RECOMMENDATION_PROMPT
