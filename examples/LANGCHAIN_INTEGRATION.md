# LangChain Integration Guide

This guide explains how LangChain-style prompts and OpenAI LLM integration work in the outfit recommendation system.

## Overview

The system uses **LangChain's PromptTemplate** design pattern combined with **OpenAI GPT** API to:
1. Generate natural language explanations for outfit recommendations (in Traditional Chinese)
2. Validate style matches
3. Check weather suitability
4. Suggest complementary accessories
5. Evaluate color harmony

## Architecture

```
User Context (JSON)
        ↓
[Retrieval (FAISS)] → Candidate Items
        ↓
[Assembly] → Outfit Combinations
        ↓
[Ranking (LightGBM)] → Top-N Outfits
        ↓
[LLM Chain] → Natural Language Explanations + Accessories
        ↓
Output (JSON with reasons)
```

## Key Components

### 1. Prompt Templates (`src/prompts.py`)

Each prompt template is a structured instruction that can be reused:

```python
EXPLAIN_OUTFIT_PROMPT = PromptTemplate(
    input_variables=["items", "occasion", "weather", "user_style", "reason"],
    template="""You are a professional fashion stylist..."""
)
```

**Input variables** are placeholders that get filled at runtime with actual data.

### 2. LLM Chain (`src/llm_chain.py`)

The `OutfitExplainer` class wraps OpenAI API calls:

```python
explainer = OutfitExplainer(model="gpt-3.5-turbo", temperature=0.7)

# Generate explanation
reasons = explainer.explain_outfit(
    items=[...],
    occasion="office",
    weather={"temp_c": 20, "humidity": 60, "condition": "sunny"},
    user_style=["casual", "smart-casual"]
)
```

### 3. Integration in Recommendation (`src/recommend.py`)

```python
# Enable LLM mode
python -m src.recommend --with-llm
```

When this flag is set:
- System initializes `OutfitExplainer` with OpenAI API key from env
- For each recommended outfit, it calls LLM to generate:
  - 2-3 bullet-point explanations
  - 2-3 accessory suggestions
- If LLM unavailable, falls back to heuristic explanations

## Prompt Template Examples

### 1. Explain Outfit (Main Flow)

**Input:**
```
Items: white shirt, navy pants, brown shoes
Occasion: office_casual
Weather: 20°C, sunny
User styles: casual, smart-casual
```

**Prompt:**
```
You are a professional fashion stylist. Given an outfit recommendation, 
provide a brief explanation in Traditional Chinese.

[Items, weather, styles...]

Provide 2-3 short bullet points explaining why this outfit is perfect.
```

**Output:**
```
• 白色襯衫搭配深藍褲子形成經典配色，既正式又舒適
• 材質組合透氣耐穿，適合辦公室環境
• 搭配棕色皮鞋完成整體造型
```

### 2. Accessory Suggestion

**Input:** top_color="white", bottom_color="navy", occasion="office", style="smart-casual"

**Output:**
```json
["棕色皮帶", "金色手錶", "黑色公事包"]
```

### 3. Style Validation

**Input:** Requested styles = ["casual", "boho"], Items = [...]

**Output:**
```json
{
  "matches": true,
  "confidence": 0.92,
  "explanation": "The outfit perfectly captures boho-casual aesthetic"
}
```

### 4. Weather Check

**Input:** temp_c=18, humidity=65, condition="rainy", items=[...]

**Output:**
```json
{
  "suitable": true,
  "score": 0.95,
  "adjustment": "Consider adding a rain jacket"
}
```

### 5. Color Harmony

**Input:** colors=["white", "navy", "brown"]

**Output:**
```json
{
  "harmony_score": 0.92,
  "notes": "Classic and timeless combination. Navy and brown complement white perfectly."
}
```

## Environment Setup

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Set environment variable:

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 2. Optional Configuration

```bash
export OPENAI_MODEL="gpt-3.5-turbo"  # or "gpt-4"
export OPENAI_TEMPERATURE="0.7"      # 0.0 (deterministic) to 1.0 (creative)
```

### 3. Run with LLM

```bash
python -m src.recommend --with-llm
```

## How Prompts Work

### PromptTemplate Mechanics

```python
# Define template
template = PromptTemplate(
    input_variables=["item1", "item2"],
    template="Please compare {item1} and {item2}"
)

# Fill in values
prompt_str = template.format(
    item1="red shirt",
    item2="blue shirt"
)
# Result: "Please compare red shirt and blue shirt"

# Send to LLM
response = openai.ChatCompletion.create(
    messages=[{"role": "user", "content": prompt_str}],
    ...
)
```

### Error Handling

If LLM call fails or returns invalid JSON:
- System falls back to heuristic explanations
- Or uses default values
- Never crashes the recommendation

```python
try:
    response = self._call_openai(prompt)
    return json.loads(response)  # Try parsing JSON
except json.JSONDecodeError:
    return {"harmony_score": 0.75, "notes": "Default fallback"}
```

## Cost Considerations

### API Pricing (as of Dec 2025)

- **gpt-3.5-turbo**: ~$0.0005 per 1000 tokens
- **gpt-4**: ~$0.03 per 1000 tokens

### Cost Optimization

1. **Use gpt-3.5-turbo** for most explanations (faster, cheaper)
2. **Cache results** for common context types (Redis)
3. **Batch requests** if possible
4. **Monitor token usage**:
   - Average explanation: ~100 tokens
   - Per outfit recommendation: ~500 tokens
   - Cost per user: ~$0.0003 with caching

### Monitoring

```python
# Track in production
metadata = {
    "llm_model": "gpt-3.5-turbo",
    "tokens_used": response.usage.total_tokens,
    "cost_usd": response.usage.total_tokens * 0.0000005
}
```

## Advanced Customization

### 1. Modify Prompt Template

Edit `src/prompts.py`:

```python
EXPLAIN_OUTFIT_PROMPT = PromptTemplate(
    input_variables=["items", "occasion", ...],
    template="""Your custom prompt here with {variables}"""
)
```

### 2. Add New Prompt Chain

```python
def validate_fit(self, size, body_type):
    """Custom chain for fit validation"""
    prompt = "Given size {size} and body type {body_type}, is this outfit flattering?"
    result = self._call_openai(prompt.format(...))
    return result
```

### 3. Fine-tune Temperature

Lower = more focused/deterministic; Higher = more creative/diverse

```python
explainer = OutfitExplainer(temperature=0.3)  # More consistent
```

## Testing & Debugging

### 1. Test without API key (heuristic mode)

```bash
python -m src.recommend  # No --with-llm flag
```

### 2. Test with mock LLM

Create `src/mock_llm.py`:

```python
class MockExplainer:
    def explain_outfit(self, *args, **kwargs):
        return "• Mock explanation 1\n• Mock explanation 2"
```

### 3. Log API calls

Add logging to `src/llm_chain.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def _call_openai(self, prompt):
    logger.debug(f"Calling OpenAI with prompt:\n{prompt[:100]}...")
    response = openai.ChatCompletion.create(...)
    logger.debug(f"Response: {response['choices'][0]['message']['content'][:100]}...")
    return response[...]
```

## Integration with Frontend

### API Endpoint

The recommendation output JSON can be directly used by frontend:

```javascript
// Frontend code
fetch("/api/recommendations", {
  method: "POST",
  body: JSON.stringify({
    weather: { temp_c: 22, condition: "sunny" },
    occasion: "coffee_date",
    user_style: ["casual"]
  })
})
.then(r => r.json())
.then(data => {
  // data.recommendations[0].reasons (from LLM)
  // data.recommendations[0].accessory_suggestions (from LLM)
  // data.recommendations[0].visual_preview_url (to virtual try-on)
})
```

## Troubleshooting

### Issue: "OPENAI_API_KEY environment variable not set"

**Solution:**
```bash
export OPENAI_API_KEY="sk-..."
# Or pass via .env file (use python-dotenv)
```

### Issue: "Rate limit exceeded"

**Solution:** Add retry logic with exponential backoff
```python
import time
for attempt in range(3):
    try:
        return self._call_openai(prompt)
    except openai.error.RateLimitError:
        time.sleep(2 ** attempt)
```

### Issue: LLM returns invalid JSON

**Solution:** Already handled! System falls back to defaults. Check logs for details.

## Next Steps

1. **Collect feedback** on LLM-generated explanations to evaluate quality
2. **A/B test** different prompts to find most engaging explanations
3. **Fine-tune** on domain-specific examples (fashion terminology)
4. **Integrate CLIP embeddings** for visual similarity (instead of just text)
5. **Cache common outputs** to reduce API costs
6. **Add monitoring** (OpenAI usage, latency, quality metrics)

