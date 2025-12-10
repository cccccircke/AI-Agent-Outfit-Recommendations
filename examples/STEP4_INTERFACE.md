# Step 4: 虛擬試衣間呈現器 (Virtual Try-On Presenter)

## 概述

Step 3 輸出被格式化為 Step 4 的輸入。本文件定義了 Step 3 → Step 4 的介面規範。

## Step 3 輸出格式（Step 4 輸入）

### 響應結構

```json
{
  "status": "success",
  "timestamp": "2025-01-15T10:30:00",
  "recommended_outfits": [
    {
      "rank": 1,
      "score": 0.92,
      "confidence": 0.92,
      "items": {
        "top": "item_0034",
        "bottom": "item_0087",
        "shoes": "item_0156"
      },
      "colors": {
        "primary": "beige",
        "secondary": "green"
      },
      "explanation": "這套造型完美詮釋優雅與舒適的結合...",
      "accessories": [
        {"type": "bag", "color": "beige", "suggestion": "托特包"},
        {"type": "scarf", "color": "green", "suggestion": "絲巾"}
      ],
      "metadata": {
        "style": "casual_professional",
        "occasion_fit": "office_meeting",
        "weather_fit": "cool_weather"
      }
    }
  ],
  "next_steps": [
    "1. 使用者從前3推薦中選擇",
    "2. Step 4 從 Google Drive 載入衣物圖像",
    "3. 執行虛擬試衣間可視化",
    "4. 回饋至 Step 3（接受/拒絕）"
  ]
}
```

## 介面規範

### 輸入（從 Step 3）

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| `rank` | int | 推薦排序（1-3） | 1 |
| `score` | float | 推薦分數（0-1） | 0.92 |
| `items.top` | string | 上衣物品 ID | "item_0034" |
| `items.bottom` | string | 下衣物品 ID | "item_0087" |
| `items.shoes` | string | 鞋類物品 ID | "item_0156" |
| `colors.primary` | string | 主色 | "beige" |
| `colors.secondary` | string | 副色 | "green" |
| `explanation` | string | 自然語言解釋 | "完美詮釋優雅與舒適..." |
| `accessories` | array | 配件建議 | [{"type":"bag", "color":"beige"}] |
| `metadata.style` | string | 風格標籤 | "casual_professional" |
| `metadata.occasion_fit` | string | 場合適配 | "office_meeting" |
| `metadata.weather_fit` | string | 天氣適配 | "cool_weather" |

### 輸出（從 Step 4）

Step 4 應該生成虛擬試衣間可視化，包括：

1. **圖像載入**
   - 從 Google Drive 中基於物品 ID 獲取圖像
   - 預期結構：`/images/{item_id}.jpg`

2. **虛擬試衣**
   - AR 或 3D 模型中展示完整造型
   - 可視化衣物組合

3. **使用者互動**
   - 左右滑動查看排名 1-3 的推薦
   - 點擊接受/拒絕
   - 可選：調整顏色、風格參數並要求新推薦

4. **回饋迴圈**
   - 發送使用者選擇：`{"accepted_outfit_rank": 2, "user_feedback": "too_formal"}`
   - 觸發 Step 3 再次運行（可選）

## 資料流範例

### 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 使用者輸入：天氣、場合、色彩偏好                          │
│    (體溫: 22°C, 場合: 辦公室會議, 色系: 藍白系)             │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1.5: 上下文收集器                                      │
│ 輸出: context.json                                          │
│ {                                                           │
│   "weather": {"temp_c": 22, "condition": "cloudy"},        │
│   "occasion": ["work", "meeting"],                         │
│   "palette_analysis": {"colors": ["white", "navy"]}        │
│ }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: 衣著推薦器                                          │
│ 輸入: catalog.json + context.json                           │
│ 處理:                                                       │
│  1. FAISS 檢索 (600ms)                                     │
│  2. 衣著組合 (100ms)                                       │
│  3. LightGBM 排序 (50ms)                                  │
│  4. LLM 解釋 (2000ms 可選)                                │
│ 輸出: recommendations.json (3 個造型)                       │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: 虛擬試衣間呈現器                                    │
│ 輸入: recommendations.json                                  │
│ 處理:                                                       │
│  1. 從 Google Drive 載入 3 個造型的圖像                     │
│  2. 渲染 AR/3D 虛擬試衣間                                 │
│  3. 展示造型說明、配件建議                                 │
│ 輸出: 使用者選擇 + 視覺回饋                                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 回饋迴圈 (可選)                                             │
│ 使用者反饋: "太正式" / "顏色不喜歡" / "接受"                │
│ → 觸發 Step 3 微調或 Step 1.5 更新偏好                     │
└─────────────────────────────────────────────────────────────┘
```

## 物品 ID 映射

Step 4 需要將物品 ID 對應到 Google Drive 上的圖像。

### 預期結構

```
Google Drive (folder: 2u4u ek7bp6)
├── images/
│   ├── item_0001.jpg  (top: white_shirt)
│   ├── item_0002.jpg  (bottom: navy_pants)
│   ├── item_0003.jpg  (shoes: black_heels)
│   └── ...
└── metadata.json  (物品信息，可選)
```

### 映射邏輯

1. 接收 `items: {"top": "item_0034", "bottom": "item_0087", "shoes": "item_0156"}`
2. 構建 URL: `https://drive.google.com/uc?export=download&id={FILE_ID}`
3. 為各項物品載入圖像
4. 在虛擬試衣間中組合展示

## 色彩與配件標準化

### 色彩名稱標準

| 英文 | 中文 | 色代 |
|------|------|------|
| beige | 米色 | #F5F5DC |
| navy | 海軍藍 | #000080 |
| white | 白色 | #FFFFFF |
| black | 黑色 | #000000 |
| gray | 灰色 | #808080 |
| green | 綠色 | #008000 |
| blue | 藍色 | #0000FF |
| pink | 粉紅色 | #FFC0CB |
| brown | 棕色 | #A52A2A |
| red | 紅色 | #FF0000 |

### 配件類型

```json
{
  "type": "bag|scarf|belt|jewelry|hat|watch",
  "color": "color_name",
  "suggestion": "具體中文建議"
}
```

## 場合代碼

| 代碼 | 說明 | 適合溫度 |
|------|------|---------|
| office_meeting | 辦公室會議 | 15-25°C |
| casual_walk | 休閒散步 | 15-28°C |
| date | 約會 | 15-28°C |
| gym | 健身 | 20-35°C |
| formal_event | 正式活動 | 15-25°C |
| beach | 海灘 | 25-35°C |
| shopping | 購物 | 15-28°C |

## 天氣適配代碼

| 代碼 | 溫度範圍 | 濕度 | 風力 |
|------|---------|------|------|
| cool_weather | <15°C | any | <20km/h |
| mild_weather | 15-25°C | any | <20km/h |
| warm_weather | 25-35°C | <70% | <20km/h |
| hot_weather | >35°C | any | any |
| rainy | any | >80% | any |
| windy | any | any | >20km/h |

## 成功標準

Step 4 實現應滿足：

- ✓ 接收 Step 3 JSON 輸出
- ✓ 載入對應的衣物圖像（從 Google Drive）
- ✓ 渲染虛擬試衣間
- ✓ 顯示造型說明與配件建議
- ✓ 記錄使用者選擇（接受/拒絕）
- ✓ 可選：支持顏色/風格微調

## 回饋迴圈 (可選)

使用者反饋可用來改進 Step 3：

```json
{
  "user_id": "user_001",
  "recommended_outfit_rank": 1,
  "action": "accepted|rejected",
  "feedback": "too_formal|color_mismatch|style_mismatch|none",
  "timestamp": "2025-01-15T10:35:00",
  "suggested_adjustment": "更休閒的款式"
}
```

### 回饋處理

1. **接受**: 記錄為正樣本，更新用戶喜好
2. **拒絕**: 記錄為負樣本，更新 LightGBM 模型
3. **微調**: 修改場合/天氣參數並重新運行 Step 3

## 部署檢查清單

- [ ] 從 Google Drive 安全獲取圖像（OAuth 2.0）
- [ ] 快取圖像（避免重複下載）
- [ ] 處理缺失圖像的回退方案
- [ ] 測試 AR 渲染性能
- [ ] 日誌記錄使用者選擇
- [ ] 監控 Step 3→Step 4 延遲 (<3秒)
- [ ] A/B 測試虛擬試衣間 UI 變體
