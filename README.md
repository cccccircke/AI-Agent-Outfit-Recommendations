# AI-Agent-Outfit-Recommendations

Prototype for Outfit Planner (Step 3) using FAISS + LightGBM + OpenAI LLM with LangChain-style prompts.

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

- Replace synthetic data with real clothing catalog (images + metadata)
- Integrate CLIP embeddings for visual similarity
- Collect user feedback (implicit via clicks/purchases, explicit via ratings) to improve ranking model
- Add A/B testing framework for model iteration
- Deploy as REST API (FastAPI/Flask) for frontend integration
- Implement caching layer (Redis) for frequently-requested contexts

## Notes

- LLM calls require internet connection and active OpenAI account
- Without LLM, system falls back to heuristic explanations
- Model training uses synthetic data; production should use real labeled examples
- FAISS CPU version included; for GPU support, install `faiss-gpu` instead


# AI-Agent-Outfit-Recommendations
The Outfit Planner represents the pivotal reasoning engine of the AI fashion assistant, designed to autonomously bridge the gap between a user's abstract intent and the concrete inventory established in the Catalog Builder. 
