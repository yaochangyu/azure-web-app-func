# Azure 資源命名決策引導

互動式引導幫助您選擇最適合的 Azure 資源命名方案。

---

## 🎯 快速決策流程圖

```
開始
  │
  ├─ 這是什麼類型的環境？
  │   ├─ 個人學習/實驗 ────────────→ [方案 A: 實驗環境]
  │   ├─ 團隊開發專案 ────────────→ [方案 B: 應用環境]
  │   ├─ 企業多應用部署 ──────────→ [方案 C: 企業環境]
  │   └─ 多租戶 SaaS 服務 ────────→ [方案 D: 多租戶]
  │
  └─ 需要多少個應用/服務？
      ├─ 1-3 個小型應用 ──────────→ [單一資源群組]
      ├─ 4-10 個中型應用 ─────────→ [按應用分組]
      └─ 10+ 個大型微服務 ────────→ [按層級分組]
```

---

## 📋 決策問卷

### 第 1 步：確定組織/專案資訊

**問題 1.1：您的組織/團隊名稱是什麼？**
```
範例：
- 個人：你的名字縮寫 (yao, john, alice)
- 公司：公司縮寫 (acme, contoso, fabrikam)
- 部門：部門縮寫 (finance, hr, marketing)

建議：2-6 個字元，小寫字母
```

**問題 1.2：這個專案/工作負載的名稱是什麼？**
```
範例：
- 實驗環境：lab, sandbox, playground
- 應用程式：webapi, mobile, admin, portal
- 功能模組：users, orders, inventory, payments

建議：2-8 個字元，描述性名稱
```

**問題 1.3：這是什麼環境？**
```
選項：
- dev      (開發環境)
- test     (測試環境)
- stg      (預備環境)
- prod     (生產環境)
- sandbox  (沙箱環境)
- demo     (展示環境)
```

---

### 第 2 步：確定資源群組策略

**問題 2.1：您會部署多少個應用/服務？**
```
A. 1-3 個應用
   → 建議：單一資源群組
   → 範例：rg-{org}-{workload}-{env}

B. 4-10 個應用
   → 建議：按應用分組
   → 範例：rg-{org}-{app-name}-{env}

C. 10+ 個微服務
   → 建議：按層級或功能分組
   → 範例：rg-{org}-{layer}-{env}
```

**問題 2.2：資源是否需要共享？**
```
YES → 考慮共享資源群組
  範例：
  - rg-{org}-{workload}-{env}     [應用專屬]
  - rg-{org}-shared-{env}         [共享服務]

NO → 每個應用獨立資源群組
  範例：rg-{org}-{app-name}-{env}
```

---

### 第 3 步：生成命名方案

基於您的回答，系統會生成：

#### 範例輸出 1：實驗環境（個人）
```
輸入：
- 組織：yao
- 工作負載：lab
- 環境：dev
- 應用數：1-3

輸出命名方案：
┌────────────────────────────────────────┐
│ 資源群組                                │
│ rg-yao-lab-dev                         │
├────────────────────────────────────────┤
│ 應用服務                                │
│ asp-yao-webapi-dev                     │
│ app-yao-webapi-dev                     │
│ func-yao-processor-dev                 │
├────────────────────────────────────────┤
│ 共享服務                                │
│ kv-yao-dev                             │
│ appi-yao-dev                           │
│ sqldb-yao-lab-dev                      │
└────────────────────────────────────────┘
```

#### 範例輸出 2：企業應用（團隊）
```
輸入：
- 組織：contoso
- 工作負載：ecommerce
- 環境：prod
- 應用數：5-8

輸出命名方案：
┌────────────────────────────────────────┐
│ 資源群組架構                            │
├────────────────────────────────────────┤
│ rg-contoso-ecommerce-web-prod          │
│   ├─ asp-contoso-web-prod              │
│   └─ app-contoso-web-prod              │
├────────────────────────────────────────┤
│ rg-contoso-ecommerce-api-prod          │
│   ├─ asp-contoso-api-prod              │
│   └─ app-contoso-api-prod              │
├────────────────────────────────────────┤
│ rg-contoso-ecommerce-data-prod         │
│   ├─ sqldb-contoso-orders-prod         │
│   ├─ sqldb-contoso-users-prod          │
│   └─ cosmos-contoso-catalog-prod       │
├────────────────────────────────────────┤
│ rg-contoso-shared-prod                 │
│   ├─ kv-contoso-prod                   │
│   ├─ appi-contoso-prod                 │
│   └─ nsg-contoso-prod                  │
└────────────────────────────────────────┘
```

---

## 🔍 命名方案模板庫

### 模板 1: 實驗/學習環境 (Lab)

**適用場景：**
- ✅ 個人學習 Azure
- ✅ 技術實驗和 POC
- ✅ 多個小型測試項目
- ✅ 臨時部署和測試

**命名結構：**
```
rg-{your-name}-lab-dev

資源命名：
- asp-{your-name}-{service}-dev
- app-{your-name}-{service}-dev
- kv-{your-name}-dev          [共享]
- appi-{your-name}-dev        [共享]
```

**完整範例：**
```
rg-yao-lab-dev
├── asp-yao-webapi-dev
├── app-yao-webapi-dev
├── func-yao-processor-dev
├── kv-yao-dev
├── appi-yao-dev
└── sqldb-yao-lab-dev
```

---

### 模板 2: 單一應用部署 (Simple)

**適用場景：**
- ✅ 單一 Web 應用
- ✅ 簡單的前後端架構
- ✅ 小型團隊項目

**命名結構：**
```
rg-{org}-{app-name}-{env}

資源命名：
- asp-{org}-{app-name}-{env}
- app-{org}-{app-name}-{env}
- sqldb-{org}-{app-name}-{env}
- kv-{org}-{env}
- appi-{org}-{app-name}-{env}
```

**完整範例：**
```
rg-contoso-portal-prod
├── asp-contoso-portal-prod
├── app-contoso-portal-prod
├── sqldb-contoso-portal-prod
├── kv-contoso-prod
└── appi-contoso-portal-prod
```

---

### 模板 3: 微服務架構 (Microservices)

**適用場景：**
- ✅ 微服務架構
- ✅ 多個獨立服務
- ✅ 容器化部署

**命名結構：**
```
rg-{org}-{service}-{env}    [每個服務一個群組]

或

rg-{org}-{layer}-{env}      [按層級分組]
- compute / api / data / platform
```

**完整範例（按服務）：**
```
rg-fabrikam-users-prod
├── func-fabrikam-users-prod
└── cosmos-fabrikam-users-prod

rg-fabrikam-orders-prod
├── func-fabrikam-orders-prod
└── sqldb-fabrikam-orders-prod

rg-fabrikam-shared-prod
├── kv-fabrikam-prod
├── appi-fabrikam-prod
└── nsg-fabrikam-prod
```

**完整範例（按層級）：**
```
rg-fabrikam-compute-prod
├── asp-fabrikam-api-prod
├── app-fabrikam-api-prod
└── func-fabrikam-worker-prod

rg-fabrikam-data-prod
├── sqldb-fabrikam-orders-prod
├── sqldb-fabrikam-users-prod
└── cosmos-fabrikam-catalog-prod

rg-fabrikam-platform-prod
├── kv-fabrikam-prod
├── appi-fabrikam-prod
└── vnet-fabrikam-prod
```

---

### 模板 4: 多租戶 SaaS (Multi-tenant)

**適用場景：**
- ✅ SaaS 平台
- ✅ 多客戶服務
- ✅ 資源隔離需求

**命名結構（方案 A - 每租戶一個訂閱）：**
```
rg-{org}-{tenant-id}-{env}
```

**命名結構（方案 B - 共享基礎設施）：**
```
rg-{org}-platform-{env}      [共享平台]
rg-{org}-tenant-{id}-{env}   [租戶專屬]
```

**完整範例：**
```
# 共享平台
rg-saasapp-platform-prod
├── asp-saasapp-shared-prod
├── app-saasapp-api-prod
└── kv-saasapp-prod

# 租戶 A
rg-saasapp-tenant-001-prod
├── cosmos-saasapp-tenant-001-prod
└── sqldb-saasapp-tenant-001-prod

# 租戶 B
rg-saasapp-tenant-002-prod
├── cosmos-saasapp-tenant-002-prod
└── sqldb-saasapp-tenant-002-prod
```

---

## ✅ 驗證檢查清單

使用以下檢查清單驗證您的命名方案：

### 格式驗證
- [ ] 資源類型縮寫符合 Microsoft CAF 標準
- [ ] 組織/專案名稱清晰（2-6 字元）
- [ ] 工作負載名稱描述性（2-8 字元）
- [ ] 環境標識正確（dev/test/stg/prod）
- [ ] 所有名稱使用小寫字母和連字號
- [ ] 無特殊字元（除了連字號）

### 約束驗證
- [ ] Storage Account 名稱無連字號，3-24 字元
- [ ] Web App 名稱全球唯一
- [ ] Key Vault 名稱 3-24 字元
- [ ] SQL Server 名稱全球唯一，小寫

### 一致性驗證
- [ ] 所有資源使用相同的命名模式
- [ ] 組織名稱一致
- [ ] 環境標識一致
- [ ] 命名層級合理（不過於詳細或過於簡單）

### 可擴展性驗證
- [ ] 支援未來添加新資源
- [ ] 支援多環境部署
- [ ] 易於理解和維護
- [ ] 支援自動化腳本

---

## 🛠️ 互動式命名生成器

使用 Python 腳本生成命名方案：

```bash
python scripts/generate_naming.py
```

**互動流程：**
```
=== Azure 資源命名生成器 ===

問題 1: 您的組織/名稱是什麼？(2-6 字元)
> yao

問題 2: 這是什麼類型的環境？
  1. 實驗/學習環境 (lab)
  2. 單一應用 (app-name)
  3. 微服務架構 (microservices)
  4. 多租戶 SaaS (multi-tenant)
> 1

問題 3: 環境名稱？(dev/test/stg/prod)
> dev

問題 4: 您需要哪些資源？(多選，用逗號分隔)
  1. Web App
  2. Function App
  3. SQL Database
  4. Cosmos DB
  5. Key Vault
  6. Application Insights
> 1,2,5,6

生成命名方案：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
資源群組:
  rg-yao-lab-dev

計算資源:
  asp-yao-webapi-dev
  app-yao-webapi-dev
  func-yao-processor-dev

安全資源:
  kv-yao-dev

監控資源:
  appi-yao-dev

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
複製以下命令開始部署：

az group create --name rg-yao-lab-dev --location centralus
az appservice plan create --name asp-yao-webapi-dev --resource-group rg-yao-lab-dev --sku B1
az webapp create --name app-yao-webapi-dev --resource-group rg-yao-lab-dev --plan asp-yao-webapi-dev
az keyvault create --name kv-yao-dev --resource-group rg-yao-lab-dev
```

---

## 📚 相關資源

- [naming-conventions.md](naming-conventions.md) - 完整命名規範
- [security-best-practices.md](security-best-practices.md) - 安全最佳實踐
- `scripts/validate_naming.py` - 命名驗證工具
- `scripts/generate_naming.py` - 命名生成器

---

## 💡 提示與建議

### 常見錯誤
❌ **太長**: `rg-my-organization-web-application-development`  
✅ **正確**: `rg-myorg-webapp-dev`

❌ **不一致**: `RG-MyApp-PROD`, `app_myapp_prod`  
✅ **正確**: `rg-myapp-prod`, `app-myapp-prod`

❌ **無環境**: `rg-myapp`, `app-myapp`  
✅ **正確**: `rg-myapp-dev`, `app-myapp-dev`

### 最佳實踐
- ✅ 從簡單開始，需要時再擴展
- ✅ 保持命名一致性
- ✅ 使用描述性但簡潔的名稱
- ✅ 考慮未來的擴展性
- ✅ 遵循組織的命名標準
- ✅ 記錄您的命名約定
