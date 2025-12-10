# Outfit Recommendation System Architecture (Enhanced V2)

## System Overview

This document describes the **As-Is → To-Be** transformation of the Outfit Recommendation System (Part 3) to support true end-to-end integration with Part 1 (Catalog Builder) and Part 4 (Virtual Try-On Presenter).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTFIT RECOMMENDATION SYSTEM                      │
│                          (Step 3 - Part 3)                          │
└─────────────────────────────────────────────────────────────────────┘

INPUT SOURCES:
┌─────────────────────────┐              ┌──────────────────────────┐
│   Part 1: Catalog       │              │ Part 2: Context (Mock)   │
│   Builder               │              │ (or real API)            │
├─────────────────────────┤              ├──────────────────────────┤
│ outfit_descriptions.json│              │ user_query               │
│ outfit_embeddings.npy   │              │ weather (temp, condition)│
│ (58 items, 512-dim)     │              │ user_profile             │
│                         │              │ occasion                 │
└────────────┬────────────┘              │ constraints              │
             │                           └────────────┬─────────────┘
             │                                        │
             └────────────────────┬───────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  YOUR OUTFIT PLANNER      │
                    │  (Step 3 - Part 3)        │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │1. RETRIEVE          │  │
                    │  │ CatalogLoaderV2:    │  │
                    │  │ - Hybrid search     │  │
                    │  │ - Embedding-based   │  │
                    │  │ - Keyword fallback  │  │
                    │  │ → Top 5 candidates  │  │
                    │  └────────────┬────────┘  │
                    │               │           │
                    │  ┌────────────▼────────┐  │
                    │  │2. THINK             │  │
                    │  │ Score candidates by:│  │
                    │  │ - Color match       │  │
                    │  │ - Style match       │  │
                    │  │ - Material fit      │  │
                    │  │ - Weather fitness   │  │
                    │  │ → Select best outfit│  │
                    │  └────────────┬────────┘  │
                    │               │           │
                    │  ┌────────────▼────────┐  │
                    │  │3. GENERATE          │  │
                    │  │ Create:             │  │
                    │  │ - Reasoning (ZH)    │  │
                    │  │ - VTON prompt (EN)  │  │
                    │  │ → Output JSON       │  │
                    │  └────────────┬────────┘  │
                    └───────────────┼──────────┘
                                    │
                                    │ RecommendationOutput
                                    │ {
                                    │   task_id,
                                    │   selected_outfit,
                                    │   reasoning_log,
                                    │   vton_generation_prompt,
                                    │   confidence_score
                                    │ }
                                    │
                    ┌───────────────▼──────────────┐
                    │ Part 4: Virtual Try-On       │
                    │ Presenter (VTON)             │
                    │                              │
                    │ - Receives JSON              │
                    │ - Uses vton_prompt           │
                    │ - Generates image            │
                    │ - Shows user                 │
                    └──────────────────────────────┘
```

---

## Data Flow & Integration Points

### Input 1: Part 1 (Catalog Builder)
**What you receive:**
```
src/outfit_descriptions.json - Dict of {item_id: {metadata}}
  - category, subcategory
  - color_primary, color_secondary
  - material, pattern
  - style_aesthetic, fit_silhouette
  - complete_description

src/outfit_embeddings.npy - NumPy array (n_items, embedding_dim)
  - 512-dimensional vectors (from distiluse model)
  - Pre-computed semantic embeddings
  - Index corresponds to JSON order
```

**How you use it:**
- `CatalogLoaderV2` loads both files
- Supports auto-detection of embedding model (512-dim → distiluse)
- Provides `search_by_text()` with hybrid search
  - Primary: Embedding-based cosine similarity
  - Fallback: Keyword matching (if embeddings incompatible)

---

### Input 2: Part 2 (Context Collector) - or Mock

**What you receive:**
```json
{
  "user_id": "user_beach_wedding_001",
  "timestamp": "2025-12-10T13:19:09",
  "user_query": "週末要去海邊參加婚禮，需要優雅但輕盈的裝扮",
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
    "color_preferences": ["light blue", "mint green", "beige"],
    "dislike_colors": ["deep colors"],
    "style_preferences": ["Elegant", "Romantic"],
    "dislike_styles": ["Sporty", "Heavy"],
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
    "breathable": true,
    "avoid_heavy_materials": true,
    "sun_protection": true,
    "max_temperature": 35
  }
}
```

**How you use it:**
- `mock_context_v2.py` simulates this with 4 complete scenarios:
  - `get_beach_wedding_context()`
  - `get_office_meeting_context()`
  - `get_casual_date_context()`
  - `get_formal_dinner_context()`
- `select_context(scenario)` returns full context
- `validate_context(context)` checks required fields

---

## Retrieve-Think-Generate Pipeline

### Phase 1: RETRIEVE
```python
# Input: User query + weather + preferences
# Process: Hybrid search on catalog

query = "light blue breathable summer elegant dress beach wedding"
candidates = catalog_loader.search_by_text(query, top_k=5)
# → Returns: [(item, score), ...] sorted by similarity
```

**Retrieval Logic:**
- Combines multiple signals:
  1. User's natural language query
  2. Weather keywords (hot → "breathable", cold → "warm")
  3. Style preferences from user_profile
  4. Color preferences
  5. Personal color season
  6. Occasion type
- Creates composite search query
- Searches embeddings with cosine similarity
- Falls back to keyword matching if incompatible

---

### Phase 2: THINK
```python
# Input: Retrieved candidates + context
# Process: Score and rank based on multiple factors

best_score = -1
for item, retrieval_score in candidates:
    score = retrieval_score
    
    # Color match: +0.25
    if item.color in user.color_preferences:
        score += 0.25
    
    # Style match: +0.25
    if item.style in user.style_preferences:
        score += 0.25
    
    # Material fitness: +0.2
    if temp > 28 and item.material in ["cotton", "linen", "silk"]:
        score += 0.2
    
    # Final: min(score, 1.0)
    best_score = max(best_score, min(score, 1.0))

# → Returns: (selected_item, final_score)
```

**Scoring Factors:**
1. **Retrieval Score** (base, 0-1): From embedding similarity
2. **Color Match** (+0.25): Personal color theory alignment
3. **Style Match** (+0.25): User's aesthetic preferences
4. **Material Fitness** (+0.2): Weather appropriateness
5. **Final Score**: Capped at 1.0

---

### Phase 3: GENERATE
```python
# Input: Selected item + context
# Process: Create explanation and VTON prompt

# 1. Generate Chinese reasoning
reasoning = f"色調'{item.color}'完美詮釋您的{user.personal_color}色彩季型。"
reasoning += f"{item.material}材質透氣輕盈，適合{temp}°C高溫環境。"
reasoning += f"風格'{item.style}'展現您喜愛的特質。"

# 2. Generate VTON prompt for Stable Diffusion
vton_prompt = (
    f"A photorealistic image of a woman wearing a {item.color} {item.material} {item.category}. "
    f"She is on a {location}, {style_keyword} style, {lighting_keyword}, "
    f"professional photography, cinematic composition, ultra high quality, 8k resolution"
)

# → Returns: (reasoning, vton_prompt)
```

**Output Generation:**
1. **Reasoning** (Traditional Chinese):
   - Color theory alignment
   - Material + weather fitness
   - Style characteristic explanation
   - Occasion appropriateness
   
2. **VTON Prompt** (English, for Stable Diffusion):
   - Outfit color + material + category
   - Body pose suggestion
   - Environment (location + lighting)
   - Lighting based on weather
   - Quality keywords (8k, professional, cinematic)

---

## Output Format (for Part 4)

```json
{
  "task_id": "recommendation_20251210_131909",
  "selected_outfit": {
    "filename": "12.jpg",
    "category": "Dress",
    "color": "Light Blue",
    "material": "Chiffon",
    "description": "A light blue chiffon dress with floral patterns..."
  },
  "reasoning_log": "色調'淡藍'完美詮釋您的Summer Soft色彩季型。雪紡材質透氣輕盈，適合32°C高溫環境。風格'優雅浪漫'展現您喜愛的特質。整體造型適合海邊婚禮賓客的場合。",
  "vton_generation_prompt": "A photorealistic image of an elegant woman wearing a light blue chiffon dress with floral patterns. She is standing gracefully on a sunny beach, elegant romantic style, golden hour lighting, sunny day, warm natural light, professional photography, cinematic composition, ultra high quality, 8k resolution, detailed fabric texture, natural skin texture, intricate details, perfect lighting, masterpiece",
  "alternative_candidates": [
    {"filename": "25.jpg", "category": "Dress", "description": "..."},
    {"filename": "38.jpg", "category": "Dress", "description": "..."}
  ],
  "confidence_score": 0.87,
  "generated_at": "2025-12-10T13:19:09"
}
```

**Key Fields for Part 4:**
1. **selected_outfit** - Which item was chosen
2. **reasoning_log** - User-friendly explanation (ZH)
3. **vton_generation_prompt** - Image generation instruction (EN)
4. **confidence_score** - How confident (0-1)
5. **alternative_candidates** - Backup options

---

## Implementation Status

### ✅ Completed (V2)
- `CatalogLoaderV2` - Part 1 integration with hybrid search
- `mock_context_v2.py` - 4 complete context scenarios
- `OutfitRecommenderV2` - Full Retrieve-Think-Generate chain
- Auto-detection of compatible embedding models (512-dim → distiluse)
- Fallback to keyword search when embeddings incompatible

### ✅ Key Features
1. **Hybrid Search**: Embedding + keyword fallback
2. **Intelligent Scoring**: Multi-factor evaluation
3. **Weather-Aware**: Temperature-based outfit matching
4. **Personal Color Theory**: Color season alignment
5. **Style Preference**: User's aesthetic matching
6. **VTON-Optimized**: Specialized prompts for image generation

### 🔄 Next Steps (for your implementation)
1. Replace `mock_context_v2.py` with real Part 2 API
2. Verify Part 1 provides both JSON + embeddings files
3. Test end-to-end with real Part 4 VTON system
4. Fine-tune scoring weights based on user feedback
5. Add optional LLM enhancement (GPT for better reasoning)

---

## Testing & Validation

### Quick Test
```bash
# Test the complete Retrieve-Think-Generate chain
python3 -m src.recommend_v2

# Output shows:
# - Task ID
# - Selected outfit
# - Reasoning (Traditional Chinese)
# - VTON prompt (English, for image generation)
# - Confidence score
# - Alternative candidates
```

### Test Different Scenarios
```bash
# In your code:
from src.mock_context_v2 import select_context
from src.recommend_v2 import OutfitRecommenderV2

recommender = OutfitRecommenderV2()

for scenario in ["beach_wedding", "office_meeting", "casual_date", "formal_dinner"]:
    context = select_context(scenario)
    output = recommender.recommend(context=context)
    print(f"{scenario}: {output.selected_outfit['filename']}")
```

---

## Architecture Comparison: As-Is vs To-Be

### As-Is (Before)
```
❌ Closed system using internal mock JSON
❌ No real Part 1 data integration
❌ Simple filtering/random selection
❌ No structured output for Part 4
❌ Unclear reasoning chain
```

### To-Be (After)
```
✅ Open system with Part 1 integration
✅ Real outfit_descriptions.json + embeddings
✅ Intelligent Retrieve-Think-Generate chain
✅ Standardized JSON output for Part 4
✅ Transparent multi-factor reasoning
✅ Hybrid search with auto-detection
✅ VTON-optimized prompt generation
```

---

## Files Reference

### Core V2 Modules
- `src/data_loader_v2.py` - CatalogLoaderV2 (Part 1 integration)
- `src/mock_context_v2.py` - Enhanced context scenarios
- `src/recommend_v2.py` - OutfitRecommenderV2 (RTG chain)

### Input Data (from Part 1)
- `src/outfit_descriptions.json` - Outfit metadata
- `src/outfit_embeddings.npy` - Pre-computed embeddings

### Example Outputs
- `examples/input_output/complete_example_input_output.json` - Full example
- `examples/input_output/integration_test_output.json` - Test results

---

**Last Updated**: 2025-12-10  
**Version**: V2 (Enhanced with Part 1 & Part 4 Integration)  
**Status**: ✅ Complete and Tested
