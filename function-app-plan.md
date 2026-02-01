# Azure Function App 託管方案比較

Azure Function App 除了 Flex Consumption Plan 之外，還有以下幾種託管方案（Hosting Plans）。

## 1. **Consumption Plan（消費方案）**

### 計費方式
按執行次數和執行時間計費

### 優點
- 自動擴展
- 用多少付多少
- 預設有免費額度（每月 100 萬次執行 + 400,000 GB-s）

### 限制
- 逾時時間：最長 5 分鐘（可設定為 10 分鐘）
- 記憶體：最大 1.5 GB
- 冷啟動問題（閒置後首次執行較慢）

### 適用場景
間歇性工作負載、成本敏感應用

### ⚠️ 重要通知
**Linux Consumption Plan 即將淘汰**：2028年9月30日後，Linux 上的 Consumption Plan 將被淘汰。建議遷移到 Flex Consumption Plan。Windows Consumption Plan 不受影響。

---

## 2. **Flex Consumption Plan（彈性消費方案）**

### 計費方式
按執行時間和執行個體數量計費

### 優點
- 更快的擴展速度
- 可設定並行執行數量
- 虛擬網路整合
- 彈性的執行個體大小（512 MB、2,048 MB 或 4,096 MB）

### 限制
- 逾時時間：無限制（但建議小於 30 分鐘）
- **目前僅支援 Linux**
- 有區域訂閱記憶體配額限制

### 適用場景
需要快速擴展且對效能有要求的應用

---

## 3. **Premium Plan（進階方案，又稱 Elastic Premium）**

### 計費方式
按預先配置的執行個體數量計費

### 優點
- **無冷啟動**（可保持預先暖機的執行個體）
- 虛擬網路連線能力
- 逾時時間：無限制
- 更強大的執行個體（最大 4 vCPU / 14 GB RAM）
- 更快的擴展速度

### 適用場景
需要持續運作、避免冷啟動的生產環境

---

## 4. **Dedicated (App Service) Plan（專用方案）**

### 計費方式
按 App Service Plan 的虛擬機器計費（固定月費）

### 優點
- 可與其他 App Service（Web App、API）共用資源
- 可使用 Azure App Service 的所有功能
- 完全掌控擴展設定
- 可在隔離環境中執行

### 適用場景
- 已有閒置的 App Service Plan
- 需要長時間執行的 Function
- 需要特定的運算資源規格

---

## 5. **Container Apps（容器應用程式環境）**

### 計費方式
按容器執行時間計費

### 優點
- 自訂容器映像
- 與 Azure Container Apps 整合
- Kubernetes 風格的擴展

### 適用場景
需要完全自訂執行環境的應用

---

## 快速比較表

| 方案 | 冷啟動 | 最長執行時間 | 擴展速度 | VNet 整合 | 最大實例數 | 適合場景 |
|------|--------|--------------|----------|-----------|------------|----------|
| Consumption | ✅ 有 | 10 分鐘 | 慢 | ❌ | 200 (Win) / 100 (Linux) | 低頻率、成本優先 |
| Flex Consumption | 🟡 較少 | 無限制* | 快 | ✅ | 1000 | 高頻率、快速擴展 |
| Premium | ❌ 無 | 無限制* | 最快 | ✅ | 100 (Win) / 20-100 (Linux) | 生產環境、無冷啟動 |
| Dedicated | ❌ 無 | 無限制* | 手動 | ✅ | 10-30 (100 ASE) | 已有 App Service |
| Container Apps | 🟡 視情況 | 無限制* | 快 | ✅ | 300-1000 | 自訂容器 |

**註**：所有方案的 HTTP 觸發器都有 **230 秒**的回應限制（Azure Load Balancer 限制）。若需更長時間處理，建議使用 [Durable Functions async pattern](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview#async-http)。

---

## 選擇建議

### 開發/測試環境
- **推薦**：Consumption Plan
- **原因**：免費額度足夠開發測試使用

### 生產環境（一般）
- **推薦**：Flex Consumption 或 Premium
- **原因**：兼顧效能與成本

### 生產環境（關鍵業務）
- **推薦**：Premium Plan
- **原因**：無冷啟動，保證效能

### 長時間背景工作
- **推薦**：Dedicated Plan
- **原因**：固定成本，適合長時間運作

### 自訂環境需求
- **推薦**：Container Apps
- **原因**：完全控制執行環境

---

## 部署範例

### Consumption Plan（預設）
```bash
az functionapp create \
  --resource-group <resource-group> \
  --consumption-plan-location eastus \
  --runtime dotnet-isolated \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account>
```

### Premium Plan
```bash
# 先建立 Premium Plan
az functionapp plan create \
  --resource-group <resource-group> \
  --name <plan-name> \
  --location eastus \
  --sku EP1

# 再建立 Function App
az functionapp create \
  --resource-group <resource-group> \
  --plan <plan-name> \
  --runtime dotnet-isolated \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account>
```

### Dedicated (App Service) Plan
```bash
# 先建立 App Service Plan
az appservice plan create \
  --resource-group <resource-group> \
  --name <plan-name> \
  --location eastus \
  --sku B1

# 再建立 Function App
az functionapp create \
  --resource-group <resource-group> \
  --plan <plan-name> \
  --runtime dotnet-isolated \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account>
```

### Flex Consumption Plan
```bash
az functionapp create \
  --resource-group <resource-group> \
  --name <function-app-name> \
  --storage-account <storage-account> \
  --runtime dotnet-isolated \
  --functions-version 4 \
  --flexconsumption-location eastus
```

**注意**：Flex Consumption Plan 目前僅支援 Linux。

---

## 成本估算參考

> ⚠️ **免責聲明**：以下價格僅供參考，實際費用可能因地區、使用量和促銷活動而異。請參考 [Azure Functions 官方定價頁面](https://azure.microsoft.com/pricing/details/functions/) 取得最新資訊。

### Consumption Plan
- **免費額度**：每月 100 萬次執行 + 400,000 GB-s
- **超過免費額度**（參考價）：
  - 執行次數：每 100 萬次約 $0.20 USD
  - 執行時間：每 GB-s 約 $0.000016 USD

### Premium Plan (EP1)
- **基本費用**（參考價）：約 $160 USD/月
- **優點**：無冷啟動、VNet 整合、更快擴展

### Dedicated Plan (B1)
- **基本費用**（參考價）：約 $55 USD/月
- **優點**：可與其他 App Service 共用資源

---

## 參考資料

- [Azure Functions 主機選項](https://learn.microsoft.com/azure/azure-functions/functions-scale)
- [Azure Functions 定價](https://azure.microsoft.com/pricing/details/functions/)
- [選擇正確的託管方案](https://learn.microsoft.com/azure/azure-functions/functions-scale#overview-of-plans)
- [Linux Consumption Plan 淘汰通知](https://go.microsoft.com/fwlink/?linkid=2335809)
- [Durable Functions Async HTTP Pattern](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview#async-http)

---

**最後更新**：2026年2月（基於 Microsoft 官方文檔）
