# AI-Agent-Outfit-Recommendations

**Step 3: Outfit Planner** for a 4-step AI outfit recommendation system.

Combines FAISS retrieval, LightGBM ranking, and OpenAI LLM explanations to generate personalized outfit recommendations based on weather, occasion, and color preferences.

### Complete 4-Step System

```
Step 1: Catalog Builder
  ↓ (outfit_descriptions.json)
Step 1.5: Personal Style + Context Collector
  ↓ (palette_analysis + weather + occasion)
Step 3: Outfit Planner (THIS PROJECT) ⭐
  ↓ (top-3 outfit recommendations)
Step 4: Virtual Try-On Presenter
```

## Quick Start

### 1. Setup environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate sample data and build FAISS index:

```bash
python -m src.data
python -m src.index
```

### Embeddings and model compatibility

- If you have `outfit_embeddings.npy`, ensure you initialize the catalog loader with a matching `model_name` or allow auto-detection.
- Example: the repository example `src/outfit_embeddings.npy` uses `distiluse-base-multilingual-cased-v2` (512-dim). To enable embedding-based search:

```python
from src.data_loader import CatalogLoader
# Option 1: pass the correct model_name explicitly
loader = CatalogLoader(catalog_path='items.json', embeddings_path='src/outfit_embeddings.npy', model_name='distiluse-base-multilingual-cased-v2')

# Option 2: allow auto-detection (CatalogLoader will try common models)
loader = CatalogLoader(catalog_path='items.json', embeddings_path='src/outfit_embeddings.npy')
```

If dimensions do not match, `CatalogLoader` will automatically fallback to keyword-based search and print a warning. See `INPUT_OUTPUT_SPEC.md` for details on regenerating embeddings with a compatible model.


### 3. Train ranking model (creates `model.joblib`):

```bash
python -m src.train
```

### 4. Run recommendation (without LLM):

```bash
python -m src.recommend
```

### 5. Run with LLM-powered explanations (requires OpenAI API key):

```bash
export OPENAI_API_KEY="sk-..."
python -m src.recommend --with-llm
```

## Architecture

### Data Flow

1. **Retrieval (FAISS)**: Embed user context + preferences → retrieve top-50 matching items via sentence-transformers
2. **Assembly**: Combine candidates into valid outfits (top + bottom + shoes)
3. **Ranking**: Score each outfit using:
   - LightGBM model (trained on heuristic labels)
   - Features: color match, style preference, season fit, popularity
4. **Explanation**: Either heuristic or LLM-powered (if `--with-llm` flag + API key)
5. **Output**: JSON with top-N recommendations, reasons, and accessory suggestions

### LLM Integration

When `--with-llm` flag is used, the system calls OpenAI API for:
- **explain_outfit**: Generate natural language reasoning for each outfit (Chinese)
- **suggest_accessories**: Recommend 2-3 complementary accessories
- **validate_style**: Check style match with user preferences
- **check_weather**: Verify weather suitability
- **color_harmony**: Evaluate color balance

All prompts are defined in `src/prompts.py` using LangChain's PromptTemplate format.

## Environment Variables

- `OPENAI_API_KEY`: Required for `--with-llm` mode. Get from https://platform.openai.com/api-keys
- Optional: `OPENAI_MODEL` (default: "gpt-3.5-turbo")
- Optional: `OPENAI_TEMPERATURE` (default: 0.7)

## File Structure

```
src/
├── data.py              # Generate synthetic items and contexts
├── index.py             # Build FAISS index from item embeddings
├── train.py             # Train LightGBM ranking model
├── recommend.py         # Main recommendation pipeline
├── prompts.py           # LangChain prompt templates
├── llm_chain.py         # OpenAI LLM wrapper and chains
data/
├── items.index          # FAISS index (auto-generated)
├── items_emb.npy        # Embeddings (auto-generated)
model.joblib            # Trained LightGBM model (auto-generated)
```

## Output Format

```json
{
  "user_id": "user_demo",
  "timestamp": "2025-12-10T09:00:00Z",
  "recommendations": [
    {
      "rank": 1,
      "overall_score": 0.92,
      "items": [
        {
          "role": "top",
          "item_id": "item_5",
          "title": "white cotton top",
          "color": "white",
          "image_url": ""
        }
      ],
      "reasons": ["• 清新設計...", "• 透氣布料..."],
      "accessory_suggestions": ["棕色皮帶", "簡約金表"]
    }
  ]
}
```

## Next Steps

### Immediate (For Integration)

1. **Step 1 Integration**
   - Download outfit catalog from [BDA_Final_Project_114-1](https://github.com/beyondderrscene/BDA_Final_Project_114-1)
   - Test `src/data_loader.py` with real `outfit_descriptions.json`
   - Replace synthetic data with actual clothing catalog

2. **Step 1.5 Integration**
   - Use `src/context_generator.py` to create user context from color analysis + weather + occasion
   - Integrate with actual weather API
   - Collect real color analysis results (skin tone, undertone, palette)

3. **Step 4 Interface**
   - Review `examples/STEP4_INTERFACE.md` for complete API specification
   - Implement virtual try-on using Step 3 output format
   - Set up image loading from Google Drive (item_id → image_url mapping)

### Running Integration Test

```bash
# Run end-to-end test (Step 1 → Step 3 → Step 4)
python -m src.integration_test

# With real Step 1 data
python -m src.integration_test --step1-path /path/to/outfit_descriptions.json

# With LLM explanations
python -m src.integration_test --with-llm
```

### Model Training & Deployment

- See `examples/DEPLOYMENT_PLAN.md` for complete launch checklist
- `examples/EVALUATION_GUIDE.md` has offline metrics (NDCG, Precision, MAP)
- Target metrics: NDCG > 0.70, CTR > 10%, Acceptance Rate > 15%

## Testing & Validation

```bash
# Validate JSON schemas
python -m examples.schema_validation_example

# Run evaluation with sample data
python -m src.evaluate_example

# Test with specific context
python src/context_generator.py
```
- Deploy as REST API (FastAPI/Flask) for frontend integration
- Implement caching layer (Redis) for frequently-requested contexts

## 🎯 Input/Output Specification (NEW)

### For Integration with Other Steps

This project now includes comprehensive **Input/Output specifications** for seamless integration:

**📖 Documentation**:
- **`INPUT_OUTPUT_SPEC.md`** ⭐⭐⭐ - Complete data format specifications
- **`QUICK_START.md`** - 30-second overview for developers
- **`IMPLEMENTATION_SUMMARY.md`** - Technical implementation details

**📥 INPUT (from Person 2 - Context Collector)**:
```json
{
  "user_query": "週末要去海邊參加婚禮",
  "weather": {"temperature_c": 28, "condition": "Sunny"},
  "user_profile": {
    "personal_color": "Summer Soft",
    "color_preferences": ["淡藍", "米色"],
    "style_preferences": ["優雅", "浪漫"],
    "body_type": "Hourglass"
  },
  "occasion": {"type": "海邊婚禮", "formality": "半正式"}
}
```

**📤 OUTPUT (for Person 4 - Virtual Try-On Presenter)**:
```json
{
  "selected_outfit_filename": "12.jpg",
  "selected_outfit_id": "outfit_12",
  "reasoning": "這件淡藍色雪紡洋裝非常適合海邊婚禮...",
  "vton_prompt": "A photorealistic image of an elegant woman wearing a light blue chiffon dress...",
  "negative_prompt": "ugly, distorted, blurry...",
  "confidence_score": 0.87,
  "fashion_notes": "完美詮釋Summer Soft色彩季型...",
  "generated_at": "2025-12-10T12:39:28"
}
```

### New Modules

- **`src/mock_context.py`** - Mock data for Person 2 (Context Collector)
- **`src/data_loader.py`** (Enhanced) - CatalogLoader with semantic search
- **`src/recommend_interface.py`** (New) - Complete Retrieve→Reason→Decide pipeline
- **`src/integration_example.py`** - Full end-to-end demonstration

### Quick Demo

```bash
# Show complete input/output formats
python src/integration_example.py

# Run recommendation with mock data
python src/recommend_interface.py beach_wedding

# Use as library
python -c "
from src.recommend_interface import main_recommend
result = main_recommend('beach_wedding')
print(result)
"
```

### 📁 Example Input/Output Files

For reference and testing, generated example files are available in `examples/input_output/`:

- **`examples/input_output/complete_example_input_output.json`** - Full input/output pair (beach wedding scenario)
- **`examples/input_output/context_example_beach.json`** - Person 2 input example (beach wedding)
- **`examples/input_output/context_example_office.json`** - Person 2 input example (office meeting)
- **`examples/input_output/integration_test_output.json`** - Full integration test output with multiple recommendations
- **`examples/input_output/catalog_for_step3.json`** - Sample Person 1 catalog (200 synthetic items)

**Quickest way to inspect examples:**
```bash
# View complete input/output example
cat examples/input_output/complete_example_input_output.json | python -m json.tool

# View Person 2 input format (beach scenario)
cat examples/input_output/context_example_beach.json | python -m json.tool

# View Person 4 output format (integration test)
cat examples/input_output/integration_test_output.json | python -m json.tool
```

## Notes

- LLM calls require internet connection and active OpenAI account
- Without LLM, system falls back to heuristic explanations
- Model training uses synthetic data; production should use real labeled examples
- FAISS CPU version included; for GPU support, install `faiss-gpu` instead

---

**Latest Updates (2025-12-10)**:
- ✅ Complete Input/Output specification defined
- ✅ Mock Context module for Person 2 simulation
- ✅ Enhanced CatalogLoader with embedding-based search
- ✅ Core recommendation interface (Retrieve→Reason→Decide)
- ✅ VTON prompt generation for virtual try-on
- ✅ Full integration examples and documentation 
