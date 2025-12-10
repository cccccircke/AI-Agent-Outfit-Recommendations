# 快速開始: Step 1-4 整合

本指南展示如何將所有4步整合在一起。

## 架構概覽

```
┌──────────────────────────┐
│ Step 1: 衣著目錄         │
│ (outfit_descriptions.json) │
└────────────────┬─────────┘
                 │
                 ▼
┌──────────────────────────┐
│ Step 1.5: 色彩分析 + 天氣 │
│ (context.json)            │
└────────────────┬─────────┘
                 │
                 ▼
┌──────────────────────────┐
│ Step 3: 衣著推薦器 ⭐    │
│ (This Project)            │
│ - FAISS 檢索              │
│ - LightGBM 排序           │
│ - LLM 解釋                │
└────────────────┬─────────┘
                 │
                 ▼
┌──────────────────────────┐
│ Step 4: 虛擬試衣間        │
│ (recommendations.json)     │
└──────────────────────────┘
```

## 完整數據流範例

### 1️⃣ Step 1: 衣著目錄

**輸出**: `outfit_descriptions.json`

```json
[
  {
    "id": "item_001",
    "category": "Upper",
    "complete_description": "白色棉質上衣",
    "color_primary": "white",
    "color_secondary": "cream",
    "pattern": "solid",
    "material": "cotton",
    "style_aesthetic": "minimalist",
    "fit_silhouette": "regular"
  },
  ...
]
```

**相關儲存庫**: https://github.com/beyondderrscene/BDA_Final_Project_114-1

### 2️⃣ Step 1.5: 色彩分析 + 上下文

**輸出**: `context.json`

```json
{
  "user_id": "user_001",
  "date_time": "2025-01-15T09:00:00",
  "palette_analysis": {
    "dominant_colors": ["white", "navy", "beige"],
    "seasonal_palette": "summer",
    "skin_tone": "neutral",
    "undertone": "cool"
  },
  "weather": {
    "temp_c": 22,
    "humidity": 60,
    "condition": "cloudy",
    "uv_index": 5,
    "wind_speed_kmh": 10
  },
  "preferences": {
    "styles": ["minimalist", "professional"],
    "colors": ["white", "navy", "beige"],
    "avoid": ["neon", "bright_patterns"],
    "fit_pref": "regular"
  },
  "occasion": ["work", "meeting"],
  "itinerary": [
    {"time": "09:00", "activity": "office_work", "location": "office"}
  ]
}
```

**產生方式**:
```bash
python -c "from src.context_generator import generate_step15_context; import json; ctx = generate_step15_context(); print(json.dumps(ctx, indent=2, ensure_ascii=False))"
```

### 3️⃣ Step 3: 衣著推薦器

**輸入**: `catalog.json` + `context.json`

**處理**:
```python
from src.recommend import recommend

recommendations = recommend(
    context_path="context.json",
    items_path="catalog.json",
    index_path="faiss.index",
    model_path="model.joblib",
    top_n=3,
    use_llm=True  # 啟用 LLM 解釋
)
```

**內部流程**:

```
1. 嵌入用戶上下文 (sentence-transformers)
   ↓
2. FAISS 檢索 (top-50 候選)
   ↓
3. 衣著組合 (top + bottom + shoes)
   ↓
4. 特徵工程 (色彩匹配度、風格、季節、人氣)
   ↓
5. LightGBM 排序 (top-3)
   ↓
6. LLM 解釋 (OpenAI GPT-3.5-turbo) 或 啟發式解釋
```

**性能指標**:
- 檢索: ~600ms
- 組合: ~100ms
- 排序: ~50ms
- LLM 解釋: ~2000ms (可選)
- **總耗時**: 2.7 秒 (含 LLM)

### 4️⃣ Step 4: 虛擬試衣間

**輸出**: `recommendations.json`

```json
{
  "status": "success",
  "timestamp": "2025-01-15T09:02:00Z",
  "recommended_outfits": [
    {
      "rank": 1,
      "score": 0.92,
      "confidence": 0.92,
      "items": {
        "top": "item_001",
        "bottom": "item_045",
        "shoes": "item_128"
      },
      "colors": {
        "primary": "white",
        "secondary": "navy"
      },
      "explanation": "這套造型完美詮釋優雅與舒適的結合。白色棉質上衣...",
      "accessories": [
        {
          "type": "bag",
          "color": "navy",
          "suggestion": "簡約手提包"
        },
        {
          "type": "watch",
          "color": "gold",
          "suggestion": "精緻手錶"
        }
      ],
      "metadata": {
        "style": "professional_casual",
        "occasion_fit": "office_meeting",
        "weather_fit": "mild_weather"
      }
    }
  ]
}
```

**Step 4 負責**:
1. 解析推薦 JSON
2. 從 Google Drive 載入衣物圖像
3. 渲染虛擬試衣間 (AR/3D)
4. 展示配件建議
5. 記錄使用者選擇 (接受/拒絕)

更多詳細資訊見: `examples/STEP4_INTERFACE.md`

## 執行完整整合測試

### 快速測試 (合成數據)

```bash
# 生成所有需要的文件並運行完整管道
python -m src.integration_test

# 輸出位置:
# - catalog_for_step3.json (Step 1 目錄)
# - context_for_step3.json (Step 1.5 上下文)
# - integration_test_output.json (Step 4 輸入)
```

### 使用真實 Step 1 數據

```bash
# 1. 克隆 Step 1 儲存庫
git clone https://github.com/beyondderrscene/BDA_Final_Project_114-1.git
cd BDA_Final_Project_114-1

# 2. 找到 outfit_descriptions.json 的位置
find . -name "outfit_descriptions.json"

# 3. 回到此專案並運行整合測試
cd /workspaces/AI-Agent-Outfit-Recommendations
python -m src.integration_test --step1-path ../BDA_Final_Project_114-1/path/to/outfit_descriptions.json
```

### 使用 LLM 解釋 (需要 OpenAI API 金鑰)

```bash
export OPENAI_API_KEY="sk-your-key-here"
python -m src.integration_test --with-llm
```

## 驗證輸出格式

```bash
# 檢驗 JSON Schema
python -c "
from src.schemas import validate_schema
import json

with open('integration_test_output.json') as f:
    data = json.load(f)

# 驗證 Step 4 輸出格式
is_valid, error = validate_schema(data, 'RECOMMENDATION_RESPONSE')
print(f'Schema valid: {is_valid}')
if not is_valid:
    print(f'Error: {error}')
"
```

## 評估指標

### 離線指標

```bash
python -m src.evaluate_example

# 輸出:
# NDCG@3: 1.00
# Precision@3: 1.00
# MAP@5: 0.93
# Diversity: 0.45 (0-1 scale, higher is better)
# Coverage: 15% (items in recommendations / total catalog)
```

### 線上指標 (上線後)

監控:
- CTR (點擊率): 目標 > 10%
- Acceptance Rate: 目標 > 15%
- Conversion Rate: 目標 > 5%
- 用戶反饋: NPS > 30

詳見: `examples/EVALUATION_GUIDE.md`

## 部署檢查清單

- [ ] 從 Step 1 下載真實衣著目錄
- [ ] 測試 FAISS 索引性能 (<1秒 for top-50)
- [ ] 訓練 LightGBM 模型
- [ ] 設定 OpenAI API 金鑰 (可選)
- [ ] 驗證 Step 4 输出 JSON 格式
- [ ] 測試 Step 4 圖像載入 (Google Drive)
- [ ] 設定使用者回饋記錄
- [ ] 監控整個管道延遲 (<3秒)
- [ ] A/B 測試不同推薦模型

## 常見問題

### Q: 如果沒有 LLM API 金鑰怎麼辦?
**A**: 系統會自動使用啟發式解釋 (colour match rules, style compatibility)。

### Q: FAISS 索引多久更新一次?
**A**: 需要手動重建 (`python -m src.index`)。可配置為每天自動重建。

### Q: Step 4 如何獲取衣物圖像?
**A**: 通過物品 ID 從 Google Drive 下載。需要 OAuth 2.0 認證。

### Q: 推薦多久更新一次?
**A**: 實時。每個用戶請求都會執行完整管道 (2-3秒)。

### Q: 支持多語言嗎?
**A**: 目前支持繁體中文 (Traditional Chinese)。可擴展到其他語言。

## 檔案位置速查

| 檔案 | 功能 | 位置 |
|------|------|------|
| Step 1 目錄 | 衣著目錄 | `catalog_for_step3.json` |
| Step 1.5 上下文 | 色彩 + 天氣 | `context_for_step3.json` |
| Step 3 輸出 | 推薦結果 | `integration_test_output.json` |
| 整合測試 | 端對端測試 | `src/integration_test.py` |
| Step 4 規範 | API 接口 | `examples/STEP4_INTERFACE.md` |
| 評估指標 | 性能測量 | `src/metrics.py` |
| LLM 提示詞 | 解釋生成 | `src/prompts.py` |

## 聯繫方式

如有問題，請檢查:
1. `examples/DEPLOYMENT_PLAN.md` - 完整部署指南
2. `examples/EVALUATION_GUIDE.md` - 評估方法論
3. `examples/LANGCHAIN_INTEGRATION.md` - LLM 整合詳解
4. `examples/STEP4_INTERFACE.md` - Step 4 API 規範
