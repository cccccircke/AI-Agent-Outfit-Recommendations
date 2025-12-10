# 快速開始指南 (Quick Start)

## 🎯 目標

本指南幫助你快速理解 Step 3 (Outfit Planner) 的 Input/Output 規範，以及如何串接其他步驟。

---

## ⚡ 30 秒快速概覽

```
Person 1 的靜態資料 (服裝目錄)
       ↓
    [搜尋]
       ↓
Person 2 的動態情境 (使用者查詢)
       ↓
    [推薦引擎]
       ↓
Person 4 的輸出格式 (JSON with VTON prompt)
```

---

## 📥 INPUT: Person 2 (Context Collector)

你的 Step 3 需要接收這樣的資料:

```json
{
  "user_query": "週末要去海邊參加婚禮",
  "weather": {
    "temperature_c": 28,
    "condition": "Sunny",
    "humidity_percent": 75
  },
  "user_profile": {
    "personal_color": "Summer Soft",
    "color_preferences": ["淡藍", "米色"],
    "style_preferences": ["優雅", "浪漫"],
    "body_type": "Hourglass"
  },
  "occasion": {
    "type": "海邊婚禮",
    "formality": "半正式"
  }
}
```

**目前狀態**: 使用 `mock_context.py` 模擬  
**期望**: Person 2 提供真實資料  

---

## 📤 OUTPUT: Person 4 (Virtual Try-On Presenter)

你的 Step 3 需要輸出這樣的格式:

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

**重點欄位**:
- `selected_outfit_filename` - 哪張圖 (Person 1 的目錄裡)
- `reasoning` - 為什麼選這件 (Traditional Chinese)
- `vton_prompt` - 虛擬試衣指令 (English)

---

## 🔍 資料來源: Person 1 (Catalog Builder)

你的 Step 3 需要加載 Person 1 的資料:

```python
from src.data_loader import CatalogLoader

# 加載目錄
loader = CatalogLoader(
    catalog_path="outfit_descriptions.json",
    embeddings_path="outfit_embeddings.npy"  # 可選
)

# 搜尋
candidates = loader.search_by_text(
    query="light blue breathable summer dress",
    top_k=5
)
```

## 預期檔案與 Embedding 注意事項

- `outfit_descriptions.json` - 服裝元資料 (num_items 項目)
- `outfit_embeddings.npy` - 嵌入向量 (num_items x embedding_dim)

注意：embedding 的維度 `embedding_dim` 由 Person 1 在產生 embeddings 時所使用的模型決定。本專案範例檔案為 `(58, 512)`（使用 `distiluse-base-multilingual-cased-v2`）。

若 `outfit_embeddings.npy` 的維度與本地預設 `model_name` 不相容，`CatalogLoader` 會：

- 嘗試自動偵測可相容的模型（一小組常見模型），找到第一個維度相符者並使用它；
- 若未找到相容模型，則退回為 keyword-based fallback（不使用 embeddings），並在日誌顯示警告。

因此，為了啟用 embedding-based 搜尋，有兩種方式：

1. 在 `CatalogLoader` 初始化時指定相容的 `model_name`（例如 `distiluse-base-multilingual-cased-v2`）：

```python
from src.data_loader import CatalogLoader
loader = CatalogLoader(
    catalog_path='items.json',
    embeddings_path='src/outfit_embeddings.npy',
    model_name='distiluse-base-multilingual-cased-v2'  # 與 embeddings 產生模型一致
)
```

2. 或讓 `CatalogLoader` 自動偵測（預設行為）：

```python
loader = CatalogLoader(catalog_path='items.json', embeddings_path='src/outfit_embeddings.npy')
```

**目前狀態**: 使用合成資料 (`items.json`)  
**期望**: Person 1 提供真實資料  

---

## 💡 核心邏輯 (Outfit Planner)

```python
from src.recommend_interface import OutfitRecommender
from src.mock_context import select_context

# 1. 準備使用者情境
context = select_context("beach_wedding")

# 2. 初始化推薦引擎
recommender = OutfitRecommender(
    catalog_path="items.json"  # 從 Person 1
)

# 3. 生成推薦
output = recommender.recommend(context=context)

# 4. 輸出給 Person 4
print(output.to_json())
```

**3 個關鍵步驟**:
1. **Retrieve**: 根據使用者查詢搜尋目錄
2. **Reason**: 評估候選項目與使用者偏好的匹配度
3. **Decide**: 選擇最佳項目並生成 VTON prompt

---

## 🚀 運行示例

### 方法 1: 集成示例 (最簡單)

```bash
python src/integration_example.py
```

輸出:
- ✅ Person 2 的 mock input
- ✅ Person 1 的目錄加載
- ✅ Person 4 的 output 格式
- ✅ 生成 4 個範例 JSON 檔案

### 方法 2: 推薦介面 (直接使用)

```bash
python src/recommend_interface.py beach_wedding
```

### 方法 3: Python Code (編程使用)

```python
from src.recommend_interface import main_recommend

result = main_recommend(
    scenario="beach_wedding",
    use_llm=False
)

import json
print(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## 📊 資料格式參考

### 完整 Input 格式 (Person 2)

```python
{
    "user_id": str,
    "timestamp": str (ISO 8601),
    "user_query": str,
    "weather": {
        "temperature_c": int,
        "condition": str,
        "humidity_percent": int
    },
    "user_profile": {
        "gender": str,
        "age": int,
        "personal_color": str,
        "color_preferences": List[str],
        "style_preferences": List[str],
        "body_type": str
    },
    "occasion": {
        "type": str,
        "location": str,
        "formality": str
    }
}
```

### 完整 Output 格式 (Person 4)

```python
{
    "selected_outfit_filename": str,      # 必需
    "selected_outfit_id": str,             # 必需
    "reasoning": str,                      # 必需 (Traditional Chinese)
    "vton_prompt": str,                    # 必需 (English)
    "negative_prompt": str,                # 可選
    "confidence_score": float (0-1),       # 可選
    "fashion_notes": str,                  # 可選
    "generated_at": str (ISO 8601)         # 可選
}
```

---

## 🔧 系統架構

```
src/
├── mock_context.py              ← Person 2 模擬
├── data_loader.py               ← Person 1 資料載入
├── recommend_interface.py       ← 核心邏輯 (Retrieve→Reason→Decide)
├── integration_example.py       ← 完整示例
├── prompts.py                   ← VTON prompt 模板
└── llm_chain.py                 ← LLM 調用 (可選)
```

---

## 🎓 3 個場景示例

### 場景 1: 海邊婚禮 (Beach Wedding)

```python
context = {
    "user_query": "週末要去海邊參加婚禮",
    "weather": {"temperature_c": 28, "condition": "Sunny"},
    "user_profile": {
        "personal_color": "Summer Soft",
        "color_preferences": ["淡藍", "米色"],
        "style_preferences": ["優雅", "浪漫"]
    }
}
# 推薦: 輕盈、透氣、淡色系連衣裙
```

### 場景 2: 辦公室會議 (Office Meeting)

```python
context = {
    "user_query": "重要客戶會議",
    "weather": {"temperature_c": 18, "condition": "Cloudy"},
    "user_profile": {
        "personal_color": "Autumn Deep",
        "color_preferences": ["navy", "burgundy"],
        "style_preferences": ["Professional", "Minimalist"]
    }
}
# 推薦: 得體、剪裁得宜的專業穿搭
```

### 場景 3: 休閒約會 (Casual Date)

```python
context = {
    "user_query": "週末約會",
    "weather": {"temperature_c": 22, "condition": "Pleasant"},
    "user_profile": {
        "personal_color": "Spring Light",
        "color_preferences": ["white", "soft pink"],
        "style_preferences": ["Elegant", "Casual"]
    }
}
# 推薦: 輕鬆但精緻的日常穿搭
```

---

## 📚 詳細文檔

- **`INPUT_OUTPUT_SPEC.md`** - 完整的資料格式規範 ⭐⭐⭐
- **`IMPLEMENTATION_SUMMARY.md`** - 實現總結與技術細節
- **`.github/copilot-instructions.md`** - AI 代理開發指南

---

## ❓ 常見問題

### Q: Person 1 的資料什麼時候才會到?
A: 等待中。目前使用合成資料測試系統。

### Q: Person 2 的資料什麼時候才會到?
A: 等待中。目前使用 `mock_context.py` 模擬。

### Q: VTON Prompt 應該怎麼寫?
A: 參考 `INPUT_OUTPUT_SPEC.md` 中的 VTON Prompt 編寫指南。

### Q: 支援中英文混合嗎?
A: 是的。`reasoning` 用 Traditional Chinese，`vton_prompt` 用 English。

### Q: 如果 embedding 不可用怎麼辦?
A: 自動 fallback 到關鍵字搜尋。

### Q: 可以使用 LLM 增強推理嗎?
A: 可以。設定 `use_llm=True`，並提供 `OPENAI_API_KEY`。

---

## ✅ 驗證清單

在與 Person 4 集成前，確保:

- [ ] `items.json` 存在並有有效的服裝資料
- [ ] `recommend_interface.py` 能成功運行
- [ ] 輸出 JSON 包含所有必需欄位
- [ ] `vton_prompt` 結構合理 (衣服+身體+背景+光線+品質)
- [ ] `reasoning` 是 Traditional Chinese
- [ ] `confidence_score` 在 0-1 之間
- [ ] 時間戳是 ISO 8601 格式

---

## 🚀 後續步驟

1. **等待 Person 1** - 提供真實的 outfit_descriptions.json + embeddings.npy
2. **等待 Person 2** - 提供真實的使用者情境 API
3. **集成 Person 4** - 接收推薦輸出進行虛擬試衣
4. **迭代改進** - 基於真實資料優化推薦品質

---

**最後更新**: 2025-12-10  
**狀態**: ✅ 可用且經過測試  
**聯絡**: 見 README.md
