# JSON Schema 與評估指標設定

## 1. JSON Schema 定義

所有 request/response 的格式都在 `src/schemas.py` 中，用 JSON Schema draft-07 定義。

### 核心 Schemas

#### 1.1 Item（衣物）
```json
{
  "item_id": "item_42",
  "title": "白色棉質短袖襯衫",
  "role": "top",  // top, bottom, outer, shoes, accessory
  "color": "white",
  "colors_secondary": ["beige"],
  "style": ["casual", "smart-casual"],
  "material": ["cotton"],
  "pattern": ["plain"],
  "season": ["spring", "summer"],
  "fit": "regular",  // slim, regular, relaxed, oversized
  "length": "short",  // short, knee, midi, long
  "gender": "female",  // male, female, unisex
  "age_range": [18, 50],
  "brand": "H&M",
  "price_usd": 29.99,
  "popularity": 0.85,  // 0-1
  "available": true,
  "image_url": "https://...",
  "embedding": [0.1, 0.2, ...],  // 384-dim vector from sentence-transformers
  "tags": ["professional", "breathable", "casual"]
}
```

#### 1.2 Weather Context（天氣）
```json
{
  "temp_c": 22,
  "humidity": 60,
  "condition": "sunny",  // sunny, cloudy, rainy, snowy, windy
  "uv_index": 6,
  "wind_speed_kmh": 15
}
```

#### 1.3 User Context（使用者情境）
```json
{
  "user_id": "user_demo",
  "date_time": "2025-12-10T09:00:00Z",
  "location": "台北",
  "weather": { ... },
  "preferences": {
    "styles": ["casual", "smart-casual"],
    "colors": ["white", "navy"],
    "avoid": ["neon"],
    "fit_pref": "regular"
  },
  "occasion": ["casual_walk", "coffee_meet"],
  "itinerary": [
    {
      "time": "09:00",
      "activity": "coffee_date",
      "location": "cafe"
    }
  ],
  "palette_analysis": {  // from step 1.5
    "dominant_colors": ["white", "navy"],
    "seasonal_palette": "spring"
  },
  "demographics": {
    "age": 28,
    "gender": "female"
  },
  "last_worn_history": ["item_5", "item_12"]
}
```

#### 1.4 Recommendation Request（推薦請求）
```json
{
  "user_id": "user_demo",
  "weather": { "temp_c": 22, "condition": "sunny", ... },
  "occasion": ["casual_walk"],
  "preferences": { "styles": ["casual"], "colors": [...] },
  "palette_analysis": { ... },
  "demographics": { "age": 28, "gender": "female" },
  "last_worn_history": ["item_5"],
  "top_n": 3,  // 要回傳幾套
  "use_llm": true  // 是否用 LLM 生成說明
}
```

#### 1.5 Single Outfit Recommendation（單套推薦）
```json
{
  "rank": 1,
  "outfit_id": "outfit_demo_1",
  "overall_score": 0.92,  // 0-1
  "confidence": 0.88,     // 模型信心分數
  "items": [
    {
      "role": "top",
      "item_id": "item_42",
      "title": "白色棉質襯衫",
      "color": "white",
      "style": "casual",
      "material": "cotton",
      "match_score": 0.95,  // 與 context 匹配度
      "image_url": "https://..."
    },
    { "role": "bottom", ... },
    { "role": "shoes", ... }
  ],
  "suitability": {
    "temp_ok": true,
    "weather_ok": true,
    "occasion_ok": true,
    "weather_explanation": "棉質透氣，適合 22°C"
  },
  "reasons": [
    "• 簡潔白色襯衫搭配中性卡其褲，展現都市休閒風格",
    "• 全身色彩偏淡，清爽適合陽光咖啡約會",
    "• 布料輕薄透氣，完美應對春夏季節"
  ],
  "accessory_suggestions": [
    "棕色皮質腰帶",
    "金色簡約手錶",
    "淺色帆布包包"
  ],
  "color_harmony": {
    "harmony_score": 0.92,
    "notes": "白色主調搭配卡其和米色形成溫暖中性的配色"
  },
  "visual_preview_url": "https://...",
  "explainability_trace": {  // 特徵權重透明化
    "color_harmony_score": 0.92,
    "style_match_score": 0.95,
    "weather_suitability_score": 0.90,
    "user_pref_alignment": 0.88,
    "novelty_score": 0.75
  }
}
```

#### 1.6 Recommendation Response（完整推薦回應）
```json
{
  "request_id": "req_20251210_001",
  "user_id": "user_demo",
  "timestamp": "2025-12-10T09:00:00Z",
  "context_summary": {
    "temp_c": 22,
    "condition": "sunny",
    "occasion": ["casual_walk"],
    "preferences": { ... }
  },
  "recommendations": [
    { /* outfit 1 */ },
    { /* outfit 2 */ },
    { /* outfit 3 */ }
  ],
  "metadata": {
    "retrieval_time_ms": 45,        // FAISS 檢索
    "ranking_time_ms": 120,         // LightGBM 排序
    "llm_time_ms": 890,             // LLM 生成解釋
    "total_time_ms": 1055,
    "candidates_retrieved": 50,
    "candidates_assembled": 125,
    "llm_model": "gpt-3.5-turbo",
    "ranking_model": "lightgbm_v1",
    "embedding_model": "all-MiniLM-L6-v2"
  },
  "exposure_control": {
    "max_recs": 3,
    "diversity_penalty": 0.15,
    "freshness_weight": 0.1
  }
}
```

## 2. 評估指標

### Offline Metrics（模型開發階段）

#### 2.1 排序品質指標

| 指標 | 公式 | 說明 | 目標值 |
|------|------|------|--------|
| **NDCG@k** | $\frac{\sum_{i=1}^{k} \frac{\text{rel}_i}{\log_2(i+1)}}{\text{IDCG@k}}$ | 折扣累積收益 (k=3,5,10) | > 0.75 |
| **Precision@k** | $\frac{\text{相關項目數}}{k}$ | 前 k 個推薦中相關比例 | > 0.80 |
| **MAP@k** | $\frac{\sum_{i=1}^{k} P(i) \cdot \text{rel}(i)}{|\text{相關項目}|}$ | 平均精準度 | > 0.75 |
| **MRR** | $\frac{1}{\text{首個相關項目排名}}$ | 倒數排名 (0-1) | > 0.70 |

**使用範例：**
```python
from src.metrics import RecommendationMetrics

metrics = RecommendationMetrics()
predictions = [0.95, 0.85, 0.72]  # 模型的預測分數
labels = [1, 1, 0]                # 標籤：1=相關，0=不相關

ndcg = metrics.ndcg_at_k(predictions, k=3)  # 0.9634
precision = metrics.precision_at_k(labels, k=3)  # 0.6667
mrr = metrics.mean_reciprocal_rank(labels)  # 1.0
```

#### 2.2 多樣性指標

| 指標 | 說明 | 計算方式 | 目標值 |
|------|------|---------|--------|
| **Diversity@k** | 推薦集合內多樣性 | 向量對間平均距離 | > 0.50 |
| **Coverage** | 物品覆蓋率 | $\frac{\text{推薦的不重複物品}}{\text{目錄大小}}$ | > 0.40 |
| **Personalization** | 用戶間差異度 | 推薦集合重疊率的倒數 | > 0.70 |

**使用範例：**
```python
# 多樣性：計算推薦服裝向量間的距離
outfit_vectors = [
    [0.1, 0.2, 0.3],  # 套裝 1 的 embedding
    [0.4, 0.5, 0.6],  # 套裝 2 的 embedding
    [0.7, 0.8, 0.9]   # 套裝 3 的 embedding
]
diversity = metrics.diversity_score(outfit_vectors)  # ~0.87

# 覆蓋率：看有多少比例的服裝被推薦
recommended = ["item_1", "item_2", "item_1", "item_5"]  # 只有 3 件不重複
coverage = metrics.coverage(recommended, catalog_size=1000)  # 0.003
```

#### 2.3 模型校準度

| 指標 | 說明 | 計算方式 |
|------|------|---------|
| **Calibration Error** | 預測分數與實際接受率的偏差 | 分箱計算預期 vs 實際 |

```python
# 模型信心分數 vs 實際標籤
predicted = [0.9, 0.85, 0.7, 0.6]
actual = [1, 1, 0, 0]
cal_error = metrics.calibration_score(predicted, actual)
# 如果 calibration_error = 0.02，模型預測很準確
```

### Online Metrics（上線後監控）

#### 3.1 用戶參與度指標

| 指標 | 說明 | 計算 | 目標值 |
|------|------|------|--------|
| **CTR** | 點擊率 | clicked / shown | > 15% |
| **Acceptance Rate** | 接受率 | applied / shown | > 20% |
| **Conversion Rate** | 轉化率 | purchased / applied | > 10% |
| **Dislike Rate** | 不喜歡率 | dislikes / shown | < 5% |

**使用範例：**
```python
from src.metrics import OnlineMetrics

online = OnlineMetrics()

# 記錄用戶互動
online.log_interaction("outfit_123", "show")       # 顯示
online.log_interaction("outfit_123", "click")      # 點擊
online.log_interaction("outfit_123", "apply")      # 套用
online.log_interaction("outfit_123", "purchase")   # 購買

summary = online.get_summary()
# {
#   "ctr": 0.25,
#   "acceptance_rate": 0.20,
#   "conversion_rate": 0.50,
#   "dislike_rate": 0.02
# }
```

#### 3.2 A/B 測試框架

```python
from src.metrics import ABTestFramework

framework = ABTestFramework()
framework.add_variant("control", metrics_control)      # 對照組
framework.add_variant("treatment", metrics_treatment)  # 測試組

results = framework.statistical_test(
    "control", 
    "treatment", 
    metric="ctr"
)
# {
#   "p_value": 0.032,          # < 0.05 = 統計顯著
#   "is_significant": true,
#   "winner": "treatment",
#   "chi2_statistic": 4.65
# }
```

### 監控面板建議指標

#### 每日監控
- **系統性能**：P50/P95/P99 延遲、API 錯誤率
- **質量**：CTR、Acceptance Rate、Dislike Rate
- **多樣性**：Coverage、Diversity@top-3
- **成本**：LLM API 成本/用戶、檢索時間

#### 每週監控
- **NDCG@3、MAP@5**（離線評估）
- **用戶滿意度**（5-star rating）
- **A/B 測試結果**（統計顯著性）

#### 每月監控
- **轉化率**、**重複用戶率**
- **模型校準度**（Calibration Error）
- **新型號 vs 舊型號**性能對比

## 3. 評估工作流程

### Phase 1: 離線評估（模型開發）
1. 準備標註資料（用戶點擊/購買歷史）
2. 分割：70% 訓練、10% 驗證、20% 測試
3. 訓練模型（LightGBM ranker）
4. 評估：NDCG@3, Precision@3, MAP@5
5. 超參數調整、再評估

### Phase 2: 上線前驗證
1. 準備 100-200 個真實用戶的 candidate test set
2. 離線評估（用之前的指標）
3. 多樣性檢查（Coverage > 40%？）
4. 性能檢查（P99 延遲 < 500ms？）

### Phase 3: A/B 測試（上線）
1. 分流 50% 用戶到新模型（測試組）、50% 舊模型（對照組）
2. 運行 1-2 週，收集足夠樣本（n > 10k）
3. 檢查 CTR、Acceptance Rate 是否顯著改進（p < 0.05）
4. 如果勝出，逐步放量至 100%

### Phase 4: 持續監控（穩定運營）
- 監控 CTR/Acceptance/Dislike 是否下降（quality regression）
- 每月重新評估 NDCG@3
- 定期收集用戶反饋並微調 ranking model

## 4. 評估指令

```bash
# 離線評估
python -m src.eval_offline \
  --test_file data/test.jsonl \
  --model_path model.joblib \
  --output results.json

# 線上監控（讀取日誌）
python -m src.eval_online \
  --log_file logs/interactions_20251210.jsonl \
  --output metrics_daily.json

# A/B 測試統計
python -m src.ab_test \
  --control_log logs/control_20251201_20251210.jsonl \
  --treatment_log logs/treatment_20251201_20251210.jsonl \
  --metric ctr
```

## 5. 評估指標目標值（起點）

| 階段 | NDCG@3 | CTR | Acceptance | Conversion | Coverage |
|------|--------|-----|------------|-----------|----------|
| MVP（第一版） | > 0.70 | > 10% | > 15% | > 5% | > 30% |
| v1.1（優化） | > 0.75 | > 12% | > 18% | > 8% | > 40% |
| v1.2（個性化） | > 0.80 | > 15% | > 20% | > 10% | > 50% |

---

## 6. 快速開始驗證

```bash
# 1. 生成示例資料
python -m src.data

# 2. 建立 index + 訓練模型
python -m src.index
python -m src.train

# 3. 離線評估（模擬）
python -c "
from src.metrics import RecommendationMetrics
m = RecommendationMetrics()
print('NDCG@3:', m.ndcg_at_k([0.95, 0.85, 0.72], k=3))
print('Precision@3:', m.precision_at_k([1, 1, 0], k=3))
"

# 4. 推薦 + 記錄互動
python -m src.recommend

# 5. 模擬線上監控
python -c "
from src.metrics import OnlineMetrics
o = OnlineMetrics()
o.log_interaction('outfit_1', 'show')
o.log_interaction('outfit_1', 'click')
print(o.get_summary())
"
```
