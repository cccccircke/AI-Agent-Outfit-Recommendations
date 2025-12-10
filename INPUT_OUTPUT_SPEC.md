# Input / Output 規範 (Interface Specification)

## 概述

此文件定義了 Step 3 (Outfit Planner) 與相鄰步驟的資料串接規範。

```
Step 1 (Catalog Builder)
    ↓ outfit_descriptions.json + outfit_embeddings.npy
Step 1.5 (Context Collector) / Mock Context
    ↓ user context JSON
Step 3 (Outfit Planner) ⭐ 本專案
    ↓ recommendation output JSON
Step 4 (Virtual Try-On Presenter)
```

---

## INPUT SPECIFICATION (來自 Person 1 和 Person 2)

### 來源 1: Person 1 (Catalog Builder) 的靜態資料

#### 檔案 1: `outfit_descriptions.json`
位置: 專案根目錄或 `src/` 資料夾
用途: 存儲所有可用服裝的詳細描述與屬性

**格式範例:**
```json
[
  {
    "item_id": "outfit_12",
    "category": "Dress",
    "subcategory": "Chiffon Dress",
    "complete_description": "Light blue chiffon dress, flowing silhouette, perfect for summer occasions",
    "color_primary": "light blue",
    "color_secondary": "white",
    "pattern": "plain",
    "material": "chiffon",
    "style_aesthetic": "Romantic",
    "fit_silhouette": "A-line",
    "sleeve_length": "sleeveless",
    "length": "knee-length",
    "image_url": "path/to/image/12.jpg",
    "price": 1500,
    "available": true
  },
  {
    "item_id": "outfit_45",
    "category": "Upper",
    "subcategory": "Cotton Shirt",
    "complete_description": "White cotton shirt, breathable, suitable for hot weather",
    ...
  }
]
```

**必需欄位:**
- `item_id`: 唯一識別符 (格式: "outfit_{num}")
- `category`: 服裝類別 (Dress, Upper, Lower, Set, Accessory)
- `color_primary`: 主要顏色
- `material`: 材質
- `style_aesthetic`: 風格分類
- `complete_description`: 完整描述文本

**可選欄位:**
- `color_secondary`: 次要顏色
- `pattern`: 圖案 (plain, stripe, floral, check)
- `fit_silhouette`: 剪裁 (fitted, A-line, flowing, straight)
- `sleeve_length`: 袖長
- `length`: 長度
- `image_url`: 圖片路徑
- `price`: 價格
- `available`: 是否可用

#### 檔案 2: `outfit_embeddings.npy`
位置: 專案根目錄或 `data/` 資料夾
用途: 服裝描述的語義向量 (用於語義相似度搜尋)

**格式:**
- NumPy 陣列格式 (`.npy`)
- 維度: `(num_items, embedding_dim)`，本 repository 範例為 `(58, 512)`（請以實際檔案為準）
- 模型: 生成 embeddings 的模型會決定 `embedding_dim`，本範例的向量係使用 `distiluse-base-multilingual-cased-v2`（512 維）生成。
- 值: 浮點向量（建議 `dtype=float32`），可選擇是否做 L2 正規化（但在本系統中會在查詢時標準化以計算 cosine 相似度）。

**注意與對應關係:**
- `outfit_embeddings.npy` 的第 i 列（行）必須對應 `items.json` 或 `outfit_descriptions.json` 中第 i 個 item（以檔案中列出的順序為基準）。保持索引一致對相似度搜尋非常重要。

**生成方式 (在 Person 1 的工作中):**
以下為使用與本 repo 範例相同模型生成 512 維向量的範例：
```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 使用與 embeddings 相同的模型（範例: distiluse-base-multilingual-cased-v2）
model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

# descriptions 必須與 items.json 中的 item 順序完全一致
descriptions = [item['complete_description'] for item in catalog]

# 產生向量 (dtype=float32 建議)
embeddings = model.encode(descriptions, convert_to_numpy=True)
embeddings = embeddings.astype('float32')

# 選擇是否正規化 (系統會在查詢時計算 cosine，相容性取決於上游/下游)
# from sklearn.preprocessing import normalize
# embeddings = normalize(embeddings, axis=1)

np.save('outfit_embeddings.npy', embeddings)
```

**若出現維度不匹配**
- `CatalogLoader` 會在載入 `outfit_embeddings.npy` 與指定的 `model_name` 時檢查向量維度是否相容（若不相容，會停用 embedding-based 搜尋並回退至 keyword fallback，並在日誌中顯示警告）。
- 因此，若你收到「embedding dimension mismatch」之類的警告，請確認 `outfit_embeddings.npy` 的維度，並以相同模型重新產生 embeddings，或在初始化 `CatalogLoader` 時傳入正確的 `model_name`。

**快速檢查指令**
```bash
# 檢查 embeddings shape
python - <<'PY'
import numpy as np
arr = np.load('src/outfit_embeddings.npy')
print('shape:', arr.shape)
print('dtype:', arr.dtype)
PY
```

---

### 來源 2: Person 2 (Context Collector) 的動態情境

#### 輸入格式: `user_context.json`

由於 Person 2 尚未交件，我們提供 **Mock Context** (`src/mock_context.py`) 作為替代。

**完整格式:**
```json
{
  "user_id": "user_beach_001",
  "timestamp": "2025-12-10T14:30:00",
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
    "breathable": true,
    "avoid_heavy_materials": true,
    "sun_protection": true
  }
}
```

**必需欄位:**
- `user_id`: 使用者識別符
- `timestamp`: 請求時間
- `user_query`: 使用者的自然語言查詢
- `weather`: 天氣資訊 (temperature_c, condition)
- `user_profile`: 使用者偏好
  - `style_preferences`: 風格列表
  - `color_preferences`: 顏色列表
- `occasion`: 場合資訊 (type, formality)

**可選欄位:**
- `dislike_colors`: 不喜歡的顏色
- `dislike_styles`: 不喜歡的風格
- `body_type`: 身材類型
- `constraints`: 額外限制條件

---

## OUTPUT SPECIFICATION (給 Person 4)

### 輸出格式: `recommendation_output.json`

Person 4 (Virtual Try-On Presenter) 需要接收以下格式的推薦結果：

```json
{
  "selected_outfit_filename": "12.jpg",
  "selected_outfit_id": "outfit_12",
  "reasoning": "這件淡藍色雪紡洋裝非常適合海邊婚禮。顏色符合Summer Soft色調，材質透氣適合30度高溫。傘形剪裁修飾沙漏身材。展現半正式場合的優雅氣質。",
  "vton_prompt": "A photorealistic image of an elegant woman wearing a light blue chiffon dress (flowing silhouette, romantic style), standing gracefully on a beach, sunny lighting, professional photography, cinematic, ultra high quality, detailed facial features, natural skin",
  "negative_prompt": "ugly, distorted, blurry, low quality, amateur, unfinished, oversaturated, poorly lit, wrong proportions",
  "confidence_score": 0.87,
  "fashion_notes": "完美詮釋Summer Soft色彩季型。傘形剪裁修飾沙漏身材。得體展現半正式場合的優雅氣質。",
  "generated_at": "2025-12-10T14:35:22.123456"
}
```

**必需欄位:**
| 欄位 | 類型 | 用途 | 範例 |
|------|------|------|------|
| `selected_outfit_filename` | string | 圖片檔名 (從 Person 1 的目錄) | `"12.jpg"` |
| `selected_outfit_id` | string | 服裝唯一識別符 | `"outfit_12"` |
| `reasoning` | string | 推薦理由 (Traditional Chinese) | `"這件淡藍色...適合海邊婚禮"` |
| `vton_prompt` | string | Stable Diffusion/DALL-E prompt | `"A photorealistic image of..."` |

**可選但推薦欄位:**
| 欄位 | 類型 | 用途 |
|------|------|------|
| `negative_prompt` | string | 應避免的特徵 (VTON 用) |
| `confidence_score` | float (0-1) | 推薦信心度 |
| `fashion_notes` | string | 額外時尚洞察 |
| `generated_at` | string (ISO 8601) | 生成時間戳 |

### VTON Prompt 編寫指南

Virtual Try-On 需要精確的 prompt 以生成高質量圖像。

**好的 Prompt 結構:**
```
[Introduction] + [Outfit Details] + [Body/Pose] + [Background] + [Lighting] + [Quality]
```

**例子 1 (Beach Wedding):**
```
A photorealistic image of an elegant woman wearing a light blue chiffon dress 
(A-line silhouette, sleeveless, knee-length), 
standing gracefully on a sunny beach with soft waves in the background, 
romantic style, gentle wind blowing her dress, 
golden hour lighting with warm tones, 
professional photography, cinematic composition, 
ultra high quality, 8k resolution, detailed facial features, natural skin texture
```

**例子 2 (Office Meeting):**
```
A professional woman in a tailored navy blazer and cream silk blouse, 
sitting at a modern conference table with morning light streaming through floor-to-ceiling windows, 
confident posture, minimalist style, 
sharp professional lighting, 
corporate office setting, 
high quality photography, 8k, ultra detailed, realistic proportions
```

**Negative Prompt (通用):**
```
ugly, distorted, blurry, low quality, amateur, unfinished, 
oversaturated, poorly lit, wrong proportions, deformed, 
bad anatomy, extra limbs, missing limbs, 
watermark, text, signature
```

---

## 資料流程圖

```
┌──────────────────────────────────────────────────────────────┐
│ PERSON 1: Catalog Builder                                    │
│ - outfit_descriptions.json (200 items)                       │
│ - outfit_embeddings.npy (200 × 384)                          │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ├─→ src/data_loader.py (CatalogLoader)
                   │    - Load JSON & NPY
                   │    - Semantic search via embeddings
                   │
┌──────────────────┴───────────────────────────────────────────┐
│ PERSON 2: Context Collector (OR MOCK)                        │
│ - User query (natural language)                              │
│ - Weather, occasion, preferences                             │
│ - Personal color, style preferences                          │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ├─→ src/mock_context.py (select_context)
                   │    - 模擬多個場景
                   │    - user_query, weather, user_profile
                   │
┌──────────────────┴───────────────────────────────────────────┐
│ STEP 3: Outfit Planner (THIS PROJECT)                        │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ 1. RETRIEVE                                             │  │
│ │    - Embed user query via Sentence Transformer          │  │
│ │    - Search embeddings for top-5 candidates             │  │
│ │                                                         │  │
│ │ 2. REASON                                               │  │
│ │    - Match color preferences                            │  │
│ │    - Match style preferences                            │  │
│ │    - Consider weather appropriateness                   │  │
│ │    - Consider occasion formality                        │  │
│ │                                                         │  │
│ │ 3. DECIDE                                               │  │
│ │    - Select best outfit                                 │  │
│ │    - Generate reasoning (heuristic or LLM)              │  │
│ │    - Generate VTON prompt                               │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                              │
│ src/recommend_interface.py (OutfitRecommender)               │
│ - retrieve_candidates()                                      │
│ - select_best_outfit()                                       │
│ - generate_reasoning()                                       │
│ - generate_vton_prompt()                                     │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   └─→ Output: recommendation_output.json
                       {
                         "selected_outfit_filename": "12.jpg",
                         "reasoning": "...",
                         "vton_prompt": "...",
                         ...
                       }
                       │
                       │
┌──────────────────┴───────────────────────────────────────────┐
│ PERSON 4: Virtual Try-On Presenter                           │
│ - Receives selected_outfit_filename                          │
│ - Receives vton_prompt                                       │
│ - Generates image using Stable Diffusion/DALL-E             │
│ - Displays outfit + explanation to user                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 使用範例

### 方式 1: 使用 Mock Context

```bash
# 運行集成例子
python src/integration_example.py
```

這會:
1. 加載 mock context (海邊婚禮場景)
2. 搜尋目錄中的衣服
3. 生成推薦
4. 輸出 JSON 給 Person 4

### 方式 2: 使用自訂 Context

```python
from src.recommend_interface import OutfitRecommender
from src.mock_context import get_office_meeting_context

# 選擇場景
context = get_office_meeting_context()

# 生成推薦
recommender = OutfitRecommender(catalog_path="items.json")
output = recommender.recommend(context=context)

# 輸出 JSON
print(output.to_json())
```

### 方式 3: 整合到 API

```python
from src.recommend_interface import main_recommend

# 簡單的 API 端點
result = main_recommend(scenario="beach_wedding", use_llm=False)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## 檔案清單

本專案的關鍵檔案:

### 資料相關
- `items.json`: 來自 Person 1 的服裝目錄 (需提供)
- `outfit_embeddings.npy`: 來自 Person 1 的嵌入向量 (可選)
- `context.json`: 來自 Person 2 的使用者情境 (或使用 mock)

### 程式碼相關
- `src/data_loader.py`: 加載 & 搜尋目錄
- `src/mock_context.py`: Person 2 的模擬資料
- `src/recommend_interface.py`: **核心推薦邏輯** (Retrieve → Reason → Decide)
- `src/prompts.py`: LLM prompt templates (含 VTON)
- `src/integration_example.py`: 完整的 input/output 示例

### 輸出
- `recommendation_output.json`: 最終推薦輸出 (給 Person 4)
- `context_example_beach.json`: 範例 input
- `context_example_office.json`: 另一個範例 input
- `complete_example_input_output.json`: 完整 input/output 對照

---

## 後續步驟

1. **等待 Person 1**: 獲得真實的 `outfit_descriptions.json` + `outfit_embeddings.npy`
2. **等待 Person 2**: 獲得真實的使用者情境 API/資料庫連接
3. **替換 Mock**: 將 `mock_context.py` 替換為真實的 API 呼叫
4. **集成 Person 4**: 將 `recommendation_output.json` 傳遞給 Person 4 的虛擬試衣系統

---

## 常見問題

### Q: 如果 Person 1 的資料還沒準備好怎麼辦?
A: 使用 `src/data.py` 生成合成資料進行測試。

### Q: VTON Prompt 應該多詳細?
A: 包含 5 個部分: 衣服 + 身體 + 背景 + 光線 + 品質。細節越多，圖片越好。

### Q: 支援中英文混合嗎?
A: 可以。reasoning 用 Traditional Chinese，vton_prompt 用 English。

### Q: 如何提高推薦準確度?
A: 
1. 改進 embedding quality (Person 1)
2. 提供更詳細的 user context (Person 2)
3. 使用 LLM 增強推理 (設定 `use_llm=True`)

---

## 附錄: 完整工作流測試指令

```bash
# 1. 生成 mock 資料
python -m src.data

# 2. 構建 FAISS 索引
python -m src.index

# 3. 訓練排序模型
python -m src.train

# 4. 運行集成示例 (展示 input/output)
python src/integration_example.py

# 5. 使用推薦介面生成輸出
python src/recommend_interface.py

# 6. 檢查輸出
cat recommendation_output.json
```

---

**最後更新**: 2025-12-10  
**維護者**: AI Agent (Outfit Planner - Step 3)
