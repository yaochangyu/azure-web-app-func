# 部署到 Azure Function App

## 📋 部署資訊

- **部署日期**: 2026-02-01
- **Function App 名稱**: func-yao-lab-938612
- **資源群組**: rg-yao-lab
- **位置**: Central US
- **Runtime**: .NET 8.0 (Isolated Worker)
- **作業系統**: Linux

---

## ✅ 部署成功步驟

### 步驟 1: 檢查 Azure 帳戶狀態

```bash
az account show --output table
```

**輸出結果:**
- 訂閱: Windows Azure MSDN - Visual Studio Ultimate
- 租戶: yaochang.yu (eee5a651-e304-4a7d-bc04-1b3fb2718735)

### 步驟 2: 列出現有的 Function Apps

```bash
az functionapp list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location, Runtime:kind, State:state}" --output table
```

**發現現有資源:**
- Function App: func-yao-lab-938612
- 資源群組: rg-yao-lab
- 狀態: Running
- Runtime: functionapp,linux

### 步驟 3: 檢查 Function App 配置

```bash
az functionapp show --name func-yao-lab-938612 --resource-group rg-yao-lab \
  --query "{Name:name, Runtime:linuxFxVersion, WorkerRuntime:siteConfig.appSettings[?name=='FUNCTIONS_WORKER_RUNTIME'].value | [0], Location:location}" \
  --output table
```

**配置資訊:**
- Runtime Version: DOTNET-ISOLATED|10.0
- 需要調整為 DOTNET-ISOLATED|8.0 (與專案一致)

### 步驟 4: 發布專案

```bash
cd /mnt/d/lab/azure-web-app-func/AzureWebApp.Functions
dotnet publish --configuration Release --output ./publish
```

**建置結果:**
- ✅ WorkerExtensions 編譯成功
- ✅ AzureWebApp.Functions 編譯成功
- 建置時間: 6.9 秒
- 輸出目錄: `./publish`

**關鍵檔案:**
```
publish/
├── .azurefunctions/
├── AzureWebApp.Functions.dll
├── AzureWebApp.Functions.deps.json
├── AzureWebApp.Functions.runtimeconfig.json
├── host.json
├── functions.metadata
├── extensions.json
├── worker.config.json
└── (相關依賴套件)
```

### 步驟 5: 部署到 Azure Function App

```bash
cd /mnt/d/lab/azure-web-app-func/AzureWebApp.Functions
func azure functionapp publish func-yao-lab-938612
```

**部署過程:**
1. 讀取 `local.settings.json`
2. 解析 worker runtime: `dotnet-isolated`
3. 更新 linuxFxVersion 為 `DOTNET-ISOLATED|8.0`
4. 執行建置 (Release 模式)
5. 上傳套件 (4.12 MB)
6. 同步觸發器

**部署結果:**
```
✅ Deployment completed successfully
✅ Functions in func-yao-lab-938612:
    HttpTriggerFunction - [httpTrigger]
        Invoke url: https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction
```

### 步驟 6: 獲取 Function Key (用於授權)

```bash
az functionapp function keys list \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --function-name HttpTriggerFunction \
  --query "default" \
  --output tsv
```

**Function Key:**
```
<YOUR_FUNCTION_KEY>
```

### 步驟 7: 測試已部署的函式

```bash
curl "https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction?code=<YOUR_FUNCTION_KEY>"
```

**測試回應:**
```json
{
  "message": "Welcome to Azure Functions!",
  "timestamp": "2026-02-01T10:24:56.1525853Z",
  "method": "GET",
  "url": "https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction"
}
```

✅ **測試成功!**

---

## 📝 重要注意事項

### 1. Runtime 版本調整
- 專案原本設定為 .NET 10.0
- 已在建置時調整為 .NET 8.0 (修改 `.csproj` 的 `TargetFramework`)
- 部署工具自動將 Function App 的 `linuxFxVersion` 更新為 `DOTNET-ISOLATED|8.0`

### 2. 授權層級
- HttpTriggerFunction 使用 `AuthorizationLevel.Function`
- 需要在 URL 中提供 `code` 參數
- 可在 Azure Portal 或透過 CLI 獲取 Function Key

### 3. Application Insights
- 已整合 Application Insights
- 可在 Azure Portal 查看詳細遙測數據
- 監控函式執行、效能和錯誤

---

## 🔧 後續操作

### 查看函式日誌
```bash
# 即時串流日誌
func azure functionapp logstream func-yao-lab-938612

# 或在 Azure Portal
# Function App → Monitor → Logs
```

### 管理函式設定
```bash
# 列出所有應用程式設定
az functionapp config appsettings list \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --output table

# 新增或更新設定
az functionapp config appsettings set \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --settings "MY_SETTING=value"
```

### 查看函式詳細資訊
在 Azure Portal:
1. 導航至 Function App: `func-yao-lab-938612`
2. 左側選單 → Functions → HttpTriggerFunction
3. 可查看:
   - Code + Test (查看/測試程式碼)
   - Monitor (監控執行歷史)
   - Integration (查看綁定配置)
   - Function Keys (管理授權金鑰)

---

## 🚀 快速重新部署

當程式碼有更新時:

```bash
# 1. 回到專案目錄
cd /mnt/d/lab/azure-web-app-func/AzureWebApp.Functions

# 2. 直接部署 (會自動執行 build 和 publish)
func azure functionapp publish func-yao-lab-938612

# 3. 測試更新後的函式
curl "https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction?code=YOUR_FUNCTION_KEY"
```

---

## 📚 相關資源

- **Function App URL**: https://func-yao-lab-938612.azurewebsites.net
- **Azure Portal**: https://portal.azure.com
- **官方文檔**: https://learn.microsoft.com/azure/azure-functions/
- **GitHub Repository**: https://github.com/yaochangyu/azure-web-app-func

---

## ✨ 部署成功標記

- [x] 專案建置成功
- [x] 部署到 Azure 成功
- [x] 函式測試通過
- [x] Application Insights 已整合
- [x] 文檔記錄完成

**部署時間**: 約 15 秒  
**套件大小**: 4.12 MB  
**狀態**: ✅ 正常運行
