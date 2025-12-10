# 修改總結：Outfit Planner Input/Output 重構

**日期**: 2025-12-10  
**目標**: 定義並實現 Step 3 與前後步驟的資料串接規範

---

## 📋 執行清單

### ✅ 已完成的工作

#### 1. **資料格式規範文檔** (`INPUT_OUTPUT_SPEC.md`)
- 詳細定義 Person 1 輸入格式 (`outfit_descriptions.json` + `outfit_embeddings.npy`)
- 詳細定義 Person 2 輸入格式 (User Context JSON)
- 詳細定義 Person 4 輸出格式 (Recommendation JSON with VTON Prompt)
- 包含完整的資料流程圖和使用範例

#### 2. **Mock Context 模組** (`src/mock_context.py`)
**目的**: 模擬 Person 2 的輸入（因為 Person 2 還未交件）

**實現的功能**:
- `get_demo_context()` - 基礎示例
- `get_beach_wedding_context()` - 海邊婚禮場景（中英文混合）
- `get_office_meeting_context()` - 辦公室會議場景
- `select_context(scenario)` - 場景選擇函式

**輸入結構** 包含:
```python
{
  "user_query": "自然語言查詢",
  "weather": {"temperature_c", "condition", "humidity_percent"},
  "user_profile": {
    "personal_color": "色彩季型",
    "color_preferences": ["偏好顏色列表"],
    "style_preferences": ["偏好風格列表"],
    "body_type": "身材類型"
  },
  "occasion": {"type", "location", "formality"},
  "constraints": {"額外限制"}
}
```

#### 3. **CatalogLoader 類別** (`src/data_loader.py` 擴展)
**目的**: 統一加載和搜尋服裝目錄

**新增功能**:
- `CatalogLoader(catalog_path, embeddings_path)` - 主類別
- `search_by_text(query)` - 語義相似度搜尋（使用嵌入向量）
- `_search_by_keyword()` - 關鍵字搜尋（備用方案）
- `search_by_attributes()` - 屬性過濾
- `get_stats()` - 目錄統計

**支援的搜尋模式**:
1. **Embedding-based** (優先): 使用 Sentence Transformer
2. **Keyword-based** (備用): 簡單的關鍵字匹配

#### 4. **核心推薦介面** (`src/recommend_interface.py` 新建)
**目的**: 完整的 Retrieve → Reason → Decide 流程

**主要類別**:
- `RecommendationOutput` - 標準化輸出格式 (dataclass)
- `OutfitRecommender` - 推薦引擎

**核心方法**:
- `recommend(context)` - 完整推薦流程
- `_retrieve_candidates(context)` - 語義搜尋
- `_select_best_outfit(context, candidates)` - 評估與選擇
- `_generate_reasoning(context, selected_item)` - 生成推薦理由
- `_generate_vton_prompt(context, selected_item)` - 生成虛擬試衣 prompt

**輸出格式** (給 Person 4):
```json
{
  "selected_outfit_filename": "12.jpg",
  "selected_outfit_id": "outfit_12",
  "reasoning": "推薦理由（Traditional Chinese）",
  "vton_prompt": "Stable Diffusion prompt...",
  "negative_prompt": "應避免特徵...",
  "confidence_score": 0.87,
  "fashion_notes": "額外洞察...",
  "generated_at": "ISO 8601 時間戳"
}
```

#### 5. **增強的 Prompts** (`src/prompts.py` 擴展)
**新增 Prompts**:
- `VTON_PROMPT_GENERATION` - 虛擬試衣 prompt 生成
- `COMPLETE_RECOMMENDATION_PROMPT` - 完整推薦輸出格式

**VTON Prompt 結構** (5 部分):
```
[衣服描述] + [身體姿勢] + [背景設定] + [光線條件] + [影像品質]
```

#### 6. **集成示例** (`src/integration_example.py` 新建)
**目的**: 展示完整的 input/output 流程

**包含的步驟**:
1. 展示 Person 2 的輸入格式（mock context）
2. 展示 Person 1 目錄加載
3. 運行推薦流程
4. 展示 Person 4 的輸出格式

**生成的檔案**:
- `context_example_beach.json` - 海邊婚禮輸入示例
- `context_example_office.json` - 辦公室會議輸入示例
- `recommendation_output.json` - 推薦輸出示例
- `complete_example_input_output.json` - 完整 input/output 對照

---

## 📁 檔案結構總覽

### 新建檔案
```
src/
├── mock_context.py              ⭐ 模擬 Person 2 輸入
├── recommend_interface.py       ⭐ 核心推薦引擎（Retrieve→Reason→Decide）
└── integration_example.py       ⭐ 完整流程示範

.github/
└── copilot-instructions.md      (先前創建的 AI 指南)

INPUT_OUTPUT_SPEC.md             ⭐ 詳細的資料規範文檔
```

### 修改的檔案
```
src/
├── data_loader.py               (新增 CatalogLoader 類別)
└── prompts.py                   (新增 VTON & Complete Recommendation prompts)
```

---

## 🔄 資料流程

```
┌─────────────────────────────────────┐
│ Person 1: Catalog Builder           │
│ outfit_descriptions.json (200 items)│
│ outfit_embeddings.npy (200×384)    │
└────────────┬────────────────────────┘
             │
             ├─→ CatalogLoader.search_by_text()
             │   (Embedding-based semantic search)
             │
┌────────────┴────────────────────────┐
│ Person 2: Context Collector         │
│ (或 mock_context.py 模擬)            │
│ {user_query, weather, preferences} │
└────────────┬────────────────────────┘
             │
             │ OutfitRecommender.recommend()
             │   ├─ Retrieve: search_by_text()
             │   ├─ Reason: heuristic scoring
             │   ├─ Decide: select best
             │   └─ Generate: VTON prompt
             │
┌────────────▼────────────────────────┐
│ Person 4: Virtual Try-On Presenter  │
│ {selected_outfit_filename,          │
│  reasoning,                         │
│  vton_prompt,                       │
│  confidence_score, ...}             │
└─────────────────────────────────────┘
```

---

## 💻 使用方式

### 方式 1: 運行集成示例
```bash
cd /workspaces/AI-Agent-Outfit-Recommendations
python src/integration_example.py
```

**輸出**:
- 展示 Person 2 的 mock input
- 展示推薦流程
- 展示 Person 4 的 output 格式
- 生成範例 JSON 檔案

### 方式 2: 使用推薦介面
```python
from src.recommend_interface import OutfitRecommender
from src.mock_context import select_context

# 選擇場景
context = select_context("beach_wedding")

# 生成推薦
recommender = OutfitRecommender(catalog_path="items.json")
output = recommender.recommend(context=context)

# 輸出 JSON（給 Person 4）
print(output.to_json())
```

### 方式 3: 直接調用
```bash
python src/recommend_interface.py beach_wedding
# 或帶 LLM 增強
python src/recommend_interface.py beach_wedding --with-llm
```

---

## 📊 輸出示例

### Input (Person 2 提供)
```json
{
  "user_id": "user_beach_001",
  "user_query": "週末要去海邊參加婚禮",
  "weather": {"temperature_c": 28, "condition": "Sunny"},
  "user_profile": {
    "personal_color": "Summer Soft",
    "color_preferences": ["淡藍", "米色", "珍珠白"],
    "style_preferences": ["優雅", "簡約", "浪漫"],
    "body_type": "Hourglass"
  },
  "occasion": {"type": "海邊婚禮賓客", "formality": "半正式"}
}
```

### Output (Person 4 接收)
```json
{
  "selected_outfit_filename": "12.jpg",
  "selected_outfit_id": "outfit_12",
  "reasoning": "這件淡藍色雪紡洋裝非常適合海邊婚禮。顏色符合Summer Soft色調，材質透氣適合30度高溫。傘形剪裁修飾沙漏身材。",
  "vton_prompt": "A photorealistic image of an elegant woman wearing a light blue chiffon dress (flowing silhouette, romantic style), standing gracefully on a beach, sunny lighting...",
  "negative_prompt": "ugly, distorted, blurry, low quality...",
  "confidence_score": 0.87,
  "fashion_notes": "完美詮釋Summer Soft色彩季型。傘形剪裁修飾沙漏身材。得體展現半正式場合的優雅氣質。",
  "generated_at": "2025-12-10T12:39:28.664697"
}
```

---

## 🔧 技術細節

### 搜尋機制
1. **語義搜尋** (優先):
   - 使用 Sentence Transformer (`all-MiniLM-L6-v2`)
   - Query embedding + 餘弦相似度
   - 閾值: 0.3

2. **關鍵字搜尋** (備用):
   - 當嵌入向量不可用時
   - 簡單的詞頻匹配

### 評分機制
- **色彩匹配**: +0.2 (如果顏色在偏好列表)
- **風格匹配**: +0.2 (如果風格在偏好列表)
- **檢索分數**: 0.0-1.0 (語義相似度)
- **最終分數**: 使用最高分

### VTON Prompt 構成
| 部分 | 內容範例 |
|------|---------|
| 衣服 | "light blue chiffon dress" |
| 身體/姿勢 | "elegant woman, standing gracefully" |
| 背景 | "on a sunny beach" |
| 光線 | "golden hour lighting" |
| 品質 | "photorealistic, 8k, ultra detailed" |

---

## 🚀 後續步驟

### 即將進行
1. **接收 Person 1 的真實資料**:
   - 實際的 `outfit_descriptions.json`
   - 實際的 `outfit_embeddings.npy`

2. **接收 Person 2 的 API**:
   - 取代 `mock_context.py`
   - 連接真實的使用者情境資料庫

3. **LLM 增強** (可選):
   - 使用 `OutfitExplainer` 進行 LLM-based 推理
   - 提高推薦理由的自然度

4. **集成 Person 4**:
   - 接收 `recommendation_output.json`
   - 使用 vton_prompt 生成虛擬試衣圖像

### 當前的 Mock 資料
- `items.json`: 合成資料 (200 件衣服)
- `context.json`: 示例輸入
- `mock_context.py`: 3 個場景模板

---

## 📝 關鍵檔案參考

### 必讀文檔
1. **`INPUT_OUTPUT_SPEC.md`** - 完整的資料規範 ⭐⭐⭐
2. **`.github/copilot-instructions.md`** - AI 代理指南
3. **`src/recommend_interface.py`** - 核心邏輯

### 範例檔案
- `context_example_beach.json` - Person 2 輸入示例
- `context_example_office.json` - 另一個輸入示例
- `complete_example_input_output.json` - 完整 input/output 對照

---

## ✨ 亮點

### 架構優勢
✅ **清晰的責任邊界**: Retrieve → Reason → Decide  
✅ **模組化設計**: 易於測試和維護  
✅ **備用方案**: Embedding 不可用時使用關鍵字搜尋  
✅ **可擴展性**: 支援 LLM 增強（設定 `use_llm=True`）  

### 資料相容性
✅ **同時支援中英文**: reasoning 用中文，VTON prompt 用英文  
✅ **完全定義的格式**: JSON schema + 範例  
✅ **向後相容**: 現有代碼不需修改  

### 生產就緒
✅ **錯誤處理**: Fallback 機制  
✅ **可觀測性**: 詳細的日誌和信心分數  
✅ **文檔完善**: 規範 + 使用範例 + 代碼註解  

---

## 🎯 驗證清單

- [x] `mock_context.py` 能正確生成 3 個場景
- [x] `CatalogLoader` 能加載 `items.json`
- [x] `OutfitRecommender` 能完整運行推薦流程
- [x] 輸出格式符合 Person 4 需求
- [x] VTON prompt 結構完整
- [x] `integration_example.py` 能成功運行
- [x] 生成的 JSON 檔案有效且可解析
- [x] 中文和英文都正確編碼

---

## 📞 問題排查

### 如果 CatalogLoader 找不到檔案
```bash
# 檢查 items.json 是否存在
ls -l items.json

# 指定正確的路徑
loader = CatalogLoader(catalog_path="/path/to/items.json")
```

### 如果 vton_prompt 質量不好
1. 檢查 context 中的天氣、場合資訊是否完整
2. 提供更多細節描述在 user_query
3. 考慮使用 LLM 增強 (設定 `use_llm=True`)

### 如果嵌入向量搜尋失敗
- 自動 fallback 到關鍵字搜尋
- 檢查 `outfit_embeddings.npy` 是否存在且格式正確

---

**最後更新**: 2025-12-10  
**狀態**: ✅ 完成可用  
**下一步**: 等待 Person 1 和 Person 2 的真實資料
