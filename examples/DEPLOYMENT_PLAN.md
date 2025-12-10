# 上線前驗證計畫與持續監控

## 1. 上線前檢查清單 (Launch Checklist)

### Phase 1: 準備階段 (Week 1-2)

#### 1.1 資料準備
- [ ] 完整的物品目錄 (≥ 500 件衣物)
  - [ ] 每件衣物有完整 metadata (color, style, material, season, etc.)
  - [ ] 每件衣物有圖片 URL
  - [ ] 物品分類平衡（頂部:下半身:鞋:配飾 ≈ 4:4:2:1）
- [ ] 分割訓練數據 (70% train, 10% val, 20% test)
- [ ] ≥100 個手動標註的 outfit pairs (用於 ground truth)

#### 1.2 模型準備
- [ ] FAISS index 已構建並可快速檢索 (< 50ms)
- [ ] LightGBM ranking model 已訓練
- [ ] 超參數調優完成（使用驗證集）
- [ ] 模型序列化為 joblib/pickle 格式

#### 1.3 系統配置
- [ ] 環境變數已設定（OPENAI_API_KEY 若使用 LLM）
- [ ] 所有依賴已安裝並版本固定（requirements.txt）
- [ ] 日誌系統已配置（DEBUG/INFO/ERROR 級別）
- [ ] 監控告警設置（CPU、內存、API 調用）

### Phase 2: 離線驗證 (Week 2-3)

#### 2.1 性能驗證
```bash
指標目標值（MVP 階段）：
□ NDCG@3 ≥ 0.70
□ Precision@3 ≥ 0.75
□ MAP@5 ≥ 0.70
□ MRR ≥ 0.65
□ P99 延遲 < 200ms (檢索 + 排序)
□ Coverage ≥ 0.30 (推薦物品多樣性)
```

運行命令：
```bash
python -m src.evaluate_example  # 查看示例評估
```

#### 2.2 多樣性與覆蓋檢查
```
□ Top-3 outfits 不重複率 > 90%
  (同一用戶連續請求應得到不同推薦)
□ 7 天內，物品覆蓋率 > 40%
  (避免總是推薦同樣物品)
□ 用戶間個性化分數 > 0.60
  (不同用戶應得到不同推薦)
```

#### 2.3 LLM 質量檢查（若使用）
```
□ 生成的解釋句子長度 15-50 字
□ 手動檢查 20 個生成的解釋，≥80% 令人滿意
□ 配件建議合理度 ≥ 90%
□ 平均 LLM 延遲 < 1 秒/請求
```

#### 2.4 API 容錯測試
```bash
□ 當 FAISS 檢索失敗，系統 fallback 至預設推薦
□ 當 LLM API 超時，使用啟發式解釋替代
□ 模型檔案缺失時，使用線上版本或舊版本
□ 數據驗證失敗時，返回 400 Bad Request（不是 500）
```

### Phase 3: 影子上線 (Week 3-4)

#### 3.1 設置
- [ ] 開啟新的服務實例（影子環境）
- [ ] 複製 10% 的生產流量到影子服務
- [ ] 實時記錄所有互動日誌到 JSON Lines 格式

#### 3.2 監控指標
```
每小時檢查：
□ 請求成功率 > 99%
□ P99 延遲 < 500ms
□ 無異常錯誤（error rate < 0.1%）

每天檢查：
□ 離線 NDCG@3 穩定 (±5%)
□ CTR 的預期值（用於後續 A/B 對標）
□ 用戶反饋比例（dislike rate）
```

#### 3.3 日誌格式（for offline evaluation）
```jsonl
# logs/shadow_interactions_20251210.jsonl
{"timestamp": "2025-12-10T10:30:45Z", "user_id": "user_123", "outfit_id": "outfit_456", "event": "show", "position": 1, "score": 0.92}
{"timestamp": "2025-12-10T10:31:12Z", "user_id": "user_123", "outfit_id": "outfit_456", "event": "click"}
{"timestamp": "2025-12-10T10:31:30Z", "user_id": "user_123", "outfit_id": "outfit_456", "event": "apply"}
{"timestamp": "2025-12-10T10:35:20Z", "user_id": "user_123", "outfit_id": "outfit_456", "event": "purchase"}
```

---

## 2. A/B 測試計劃

### 設計
```
對照組 (Control): 舊的推薦模型或啟發式規則
測試組 (Treatment): 新的 LightGBM ranking model
流量分配: 50% / 50%
運行時間: 1-2 週（直到達到統計功率 80%、α=0.05）
樣本量目標: ≥ 10,000 用戶 / 組
```

### 主要指標
| 指標 | 公式 | 假設/目標 |
|------|------|---------|
| **CTR** | clicks / shown | 新 > 舊 (p < 0.05) |
| **Acceptance Rate** | applied / shown | 新 > 舊 |
| **Conversion Rate** | purchased / applied | 新 ≥ 舊 (同等即可) |
| **Dislike Rate** | dislikes / shown | 新 < 舊 |

### 檢查點
```
Day 3: 樣本量 > 1000，初步查看趨勢
Day 7: 樣本量 > 5000，進行統計顯著性測試
Day 14: 樣本量 > 10000，最終決策
```

### 停止規則 (Early Stopping)
```
停止並回滾：
□ Dislike rate 新 > 舊 + 2%（質量下降）
□ P99 延遲 > 1 秒（性能問題）
□ Error rate > 1%（系統穩定性）
```

### 統計測試
```python
from src.metrics import ABTestFramework

framework = ABTestFramework()
framework.add_variant("control", metrics_control)
framework.add_variant("treatment", metrics_treatment)

results = framework.statistical_test("control", "treatment", metric="ctr")
if results["is_significant"] and results["winner"] == "treatment":
    print("✓ New model wins! Proceed to 100%")
else:
    print("✗ Inconclusive or control wins. Keep investigating.")
```

---

## 3. 持續監控計畫

### 3.1 實時監控面板（Daily）

#### 系統性能
```
Metric                 | Target    | Alert Threshold
API 延遲 (P50)         | < 100ms   | > 150ms
API 延遲 (P99)         | < 300ms   | > 500ms
成功率                 | > 99.5%   | < 99%
LLM API 調用成功率     | > 99%     | < 95%
```

#### 推薦質量
```
Metric                 | Target    | Alert Threshold
CTR                    | > 12%     | < 10%
Acceptance Rate        | > 18%     | < 15%
Dislike Rate           | < 3%      | > 5%
平均推薦分數           | > 0.80    | < 0.75
```

#### 成本監控
```
Metric                 | 計算方式              | Budget
LLM 成本/用戶          | 平均 token 數 * 費率   | < $0.001/user
檢索延遲               | FAISS 耗時            | < 50ms
總成本/日              | 所有 API 調用費用      | < $100/day (若 10K DAU)
```

### 3.2 每週回顧

```python
# 檢查離線 NDCG 是否下降（quality regression）
import subprocess
result = subprocess.run([
    "python", "-m", "src.evaluate_offline",
    "--test_file", "data/test_latest.jsonl",
    "--model_path", "model.joblib"
], capture_output=True)

if ndcg < 0.70:
    print("⚠️  NDCG 下降，需要重新訓練模型")
```

### 3.3 每月迭代

```
□ 收集 top-5 disliked outfits，分析失敗原因
□ 從用戶點擊/購買日誌中挖掘新的正標籤，進行 active learning
□ 重新訓練 ranking model（若新數據 > 10% variance）
□ 對比離線 NDCG，若改進 > 2%，部署新版本
□ A/B 測試新版本 3 天，確認無質量下降
```

---

## 4. 降級策略 (Graceful Degradation)

### 場景 1: FAISS 檢索失敗
```
重試 3 次，若全部失敗：
→ 使用預先計算的「熱門物品」組合
→ 根據簡單規則（性別、季節、溫度）篩選
→ 返回 fallback recommendations
```

### 場景 2: LLM API 超時或費用上限
```
→ 不調用 LLM，使用啟發式解釋代替
→ 記錄 warning 日誌，通知運維團隊
→ 完整推薦仍可用，只是解釋文本不夠自然
```

### 場景 3: 模型文件缺失或損壞
```
→ 使用上一個穩定版本（version control）
→ 或使用線上 model checkpoint（S3/GCS）
→ 記錄異常，觸發告警
```

### 場景 4: 高峰流量壓力
```
→ 啟用結果緩存（Redis，TTL=5 分鐘）
→ 降低 FAISS 檢索的 top-k（從 50 降至 30）
→ 減少 LLM 調用（只對 top-1 生成解釋）
```

---

## 5. 告警與事件響應

### 告警規則

| 告警 | 條件 | 嚴重性 | 響應 |
|-----|------|--------|------|
| **高延遲** | P99 > 500ms | 中 | 檢查 FAISS/LLM 服務狀態 |
| **質量下降** | CTR < 10% (vs 過去 7 日平均) | 中 | 對比新舊模型，檢查數據漂移 |
| **高誤率** | Error rate > 1% | 高 | 立即回滾或切換 fallback |
| **成本異常** | LLM 成本 > 預算 2 倍 | 中 | 禁用 LLM，調查 token 用量 |
| **Dislike 激增** | Dislike rate > 5% | 中 | 檢查推薦邏輯，可能發生數據漂移 |

### 事件響應流程
```
1. 監控告警觸發
   ↓
2. 自動打 PagerDuty / Slack 通知
   ↓
3. 值班工程師查看儀表板、日誌
   ↓
4. 判斷：是否需要立即回滾？
   - 若 error rate > 5%：YES，回滾
   - 若只是性能下降：NO，進一步診斷
   ↓
5. 如回滾，恢復舊版本，記錄事件
6. 事後檢查，修復問題後重新部署
```

---

## 6. 監控代碼示例

### 實時監控（每 5 分鐘查詢一次）

```python
# monitor.py
import time
from src.metrics import OnlineMetrics
import logging

logger = logging.getLogger(__name__)

def monitor_loop():
    online = OnlineMetrics()
    
    while True:
        # 讀取最近 5 分鐘的日誌
        logs = read_recent_logs(minutes=5)
        for log in logs:
            online.log_interaction(log['outfit_id'], log['event'])
        
        # 檢查指標
        summary = online.get_summary()
        
        if summary['ctr'] < 0.10:
            logger.warning(f"⚠️  CTR 下降：{summary['ctr']:.2%}")
        
        if summary['dislike_rate'] > 0.05:
            logger.error(f"❌ Dislike 率過高：{summary['dislike_rate']:.2%}")
        
        # 發送到監控系統（Prometheus/Grafana）
        send_to_monitoring({
            'ctr': summary['ctr'],
            'acceptance_rate': summary['acceptance_rate'],
            'dislike_rate': summary['dislike_rate'],
            'timestamp': time.time()
        })
        
        time.sleep(300)  # 每 5 分鐘檢查一次
```

### 日夜間評估報告

```python
# daily_report.py
import json
from datetime import datetime
from src.metrics import OnlineMetrics

def generate_daily_report():
    yesterday = datetime.now().replace(hour=0, minute=0, second=0)
    logs = read_logs_between(yesterday, yesterday + timedelta(days=1))
    
    online = OnlineMetrics()
    for log in logs:
        online.log_interaction(log['outfit_id'], log['event'])
    
    report = {
        'date': yesterday.date().isoformat(),
        'metrics': online.get_summary(),
        'status': 'HEALTHY' if online.get_ctr() > 0.12 else 'NEEDS_REVIEW'
    }
    
    # 寄送報告郵件或保存至檔案
    with open(f"reports/daily_{yesterday.date()}.json", "w") as f:
        json.dump(report, f, indent=2)
```

---

## 7. 回滾計畫 (Rollback)

### 快速回滾
```bash
# 若檢測到 error rate > 5%，立即執行
./scripts/rollback.sh v1.0  # 回滾到上一穩定版本

# 驗證
curl http://localhost:8000/health  # 檢查服務是否恢復
```

### 版本管理
```
src/recommend.py
  └─ model_v1.0.joblib (目前上線版)
  └─ model_v0.9.joblib (上一版本，回滾用)
  └─ model_v0.8.joblib (備份)
```

### 根本原因分析 (RCA)
```
1. 收集影響時間段的完整日誌
2. 比較推薦結果（新 vs 舊）
3. 檢查數據漂移（item distribution 是否改變？）
4. 檢查模型（訓練數據是否有問題？）
5. 更新監控告警，避免重複
```

---

## 8. 定量成功指標

### MVP 目標（第一個月）
| 指標 | 目標值 | 檢查點 |
|------|--------|--------|
| NDCG@3 | 0.70+ | 第 2 週 |
| CTR | 10%+ | 第 3 週 |
| Acceptance Rate | 15%+ | 第 3 週 |
| 服務可用性 | 99.5%+ | 每日 |
| 平均延遲 | < 200ms | 每日 |

### v1.1 目標（第二個月）
| 指標 | 目標值 |
|------|--------|
| NDCG@3 | 0.75+ |
| CTR | 12%+ |
| Acceptance Rate | 18%+ |
| Dislike Rate | < 3% |

### v1.2 目標（第三個月）
| 指標 | 目標值 |
|------|--------|
| NDCG@3 | 0.80+ |
| CTR | 15%+ |
| Conversion Rate | 10%+ |
| Coverage | 50%+ |

---

## 9. 快速開始驗證

```bash
# 1. 部署前完整評估
python -m src.evaluate_example

# 2. 模擬 7 天用戶互動
python scripts/simulate_week.py

# 3. 生成評估報告
python scripts/generate_report.py

# 4. A/B 測試模擬
python scripts/ab_test_simulation.py

# 5. 檢查所有指標是否達標
python scripts/check_launch_readiness.py
```

---

## 10. 檢查清單最終確認

上線前最後確認（由產品/工程主管簽核）：

```
上線前 48 小時確認清單：

系統
□ 所有相依套件已固定版本
□ 環境變數已配置（含 secret）
□ 監控告警已設定
□ 日誌系統可用
□ 備份和回滾腳本已測試

性能
□ NDCG@3 ≥ 0.70
□ P99 延遲 < 300ms
□ Error rate ≤ 0.1%

用戶體驗
□ LLM 生成文本滿意度 ≥ 80%
□ 多樣性檢查通過（top-3 無重複）
□ 容錯測試通過

文件
□ README 已更新
□ API 文件已更新
□ 運維手冊已編寫
□ 事故響應流程已文件化

簽核
工程主管: ______ 日期: ______
產品主管: ______ 日期: ______
```

