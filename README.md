# Azure Function App

這是一個使用 C# (.NET 10.0) 和 Azure Functions v4 建立的專案。

## 專案結構

```
AzureWebApp.Functions/
├── Functions/
│   └── HttpTriggerFunction.cs   # HTTP Trigger API 端點
├── Program.cs                     # 應用程式進入點
├── host.json                      # Functions 執行階段設定
├── local.settings.json            # 本地開發設定
└── AzureWebApp.Functions.csproj   # 專案檔
```

## 已建立的 API 端點

### HttpTriggerFunction
- **端點**: `http://localhost:7071/api/HttpTriggerFunction`
- **方法**: GET, POST
- **授權層級**: Function
- **功能**: 基本的 HTTP Trigger 範例

## 本地執行

### 前置需求

1. 安裝 .NET 10 SDK 到系統:
   ```bash
   wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh
   chmod +x /tmp/dotnet-install.sh
   sudo /tmp/dotnet-install.sh --channel 10.0 --install-dir /usr/share/dotnet
   ```

2. 安裝 Azure Functions Core Tools:
   ```bash
   sudo apt-get update
   sudo apt-get install -y azure-functions-core-tools-4
   ```

### 建置與執行

1. 還原套件:
   ```bash
   cd AzureWebApp.Functions
   /usr/bin/dotnet restore
   ```

2. 建置專案:
   ```bash
   /usr/bin/dotnet build
   ```

3. 啟動服務:
   ```bash
   export DOTNET_ROOT=/usr/share/dotnet
   export PATH=$DOTNET_ROOT:$PATH
   func start
   ```

4. 測試 API:
   ```bash
   curl http://localhost:7071/api/HttpTriggerFunction
   ```

## 部署到 Azure

1. 使用 Azure CLI 登入:
   ```bash
   az login
   ```

2. 建立 Function App:
   ```bash
   az functionapp create --resource-group <resource-group> \
     --consumption-plan-location eastus \
     --runtime dotnet-isolated \
     --functions-version 4 \
     --name <function-app-name> \
     --storage-account <storage-account>
   ```

3. 部署:
   ```bash
   func azure functionapp publish <function-app-name>
   ```

## 敏感資料管理

### 取得 Function Key

Function Key 用於授權控制，保護 HTTP 觸發器 Function 免於未經授權的存取。

#### 方法 1: 即時取得 Function Key（推薦用於測試）

```bash
# 取得特定 Function 的 Key
az functionapp function keys list \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --function-name HttpTriggerFunction \
  --query "default" -o tsv

# 取得 Host Key（適用於所有 Functions）
az functionapp keys list \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --query "functionKeys.default" -o tsv
```

#### 方法 2: 使用 Azure Key Vault（生產環境最佳實踐）

```bash
# 從 Key Vault 引用 Secret
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "MySecret=@Microsoft.KeyVault(SecretUri=https://<vault-name>.vault.azure.net/secrets/<secret-name>)"

# 設定應用程式環境變數
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "API_KEY=your-secret-value"
```

#### 方法 3: 本地開發環境

在 `local.settings.json` 中設定（此檔案不會被推送到 Git）：

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "API_KEY": "your-local-secret-key",
    "ConnectionStrings__MyDb": "Server=..."
  }
}
```

程式碼中讀取環境變數：

```csharp
var apiKey = Environment.GetEnvironmentVariable("API_KEY");
```

#### 方法 4: GitHub Secrets（CI/CD 流程）

1. 到 GitHub Repo → Settings → Secrets and variables → Actions
2. 新增 Secret（例如：`AZURE_FUNCTION_KEY`）
3. 在 workflow 中使用：

```yaml
- name: Test Function
  run: |
    curl https://<function-app-name>.azurewebsites.net/api/httptriggerfunction?code=${{ secrets.AZURE_FUNCTION_KEY }}
```

#### 方法 5: 使用 Managed Identity（無需 Key，最安全）

啟用 Managed Identity 後，可透過 Azure AD 進行身分驗證，完全不需要管理 Keys。

```bash
# 啟用系統指派的 Managed Identity
az functionapp identity assign \
  --name <function-app-name> \
  --resource-group <resource-group>
```

### 授權層級說明

Function 支援三種授權層級：

```csharp
// Anonymous - 不需要任何 Key（公開存取）
[HttpTrigger(AuthorizationLevel.Anonymous, "get")]

// Function - 需要 Function Key（預設，適合內部 API）
[HttpTrigger(AuthorizationLevel.Function, "get")]

// Admin - 需要 Master/Admin Key（管理功能）
[HttpTrigger(AuthorizationLevel.Admin, "get")]
```

**安全性建議：**
- ❌ 不要將 Keys 提交到版本控制系統
- ✅ 使用 Azure Key Vault 儲存敏感資訊
- ✅ 生產環境優先使用 Managed Identity
- ✅ 定期輪換 Keys

## 技術棧

- .NET 10.0
- Azure Functions v4
- Isolated Worker Process (2.x)
- Application Insights (監控)

## 套件版本

- Microsoft.Azure.Functions.Worker: 2.50.0
- Microsoft.Azure.Functions.Worker.Sdk: 2.0.5
- Microsoft.Azure.Functions.Worker.Extensions.Http: 3.2.0

## 注意事項

- 專案使用 .NET 10.0，需確保系統已安裝對應的 SDK
- 使用 IHostApplicationBuilder 模式（Worker 2.x 推薦）
- 建議使用系統的 dotnet (`/usr/bin/dotnet`) 以確保完整的 ICU 支援
