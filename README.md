# Azure Function App

這是一個使用 C# (.NET 8.0) 和 Azure Functions v4 建立的專案。

## 專案結構

```
AzureWebApp.Functions/
├── Functions/
│   ├── HttpTriggerFunction.cs   # HTTP Trigger API 端點
│   └── VersionFunction.cs        # 版本資訊 API 端點
├── Models/
│   └── VersionInfo.cs            # 版本資訊資料模型
├── Program.cs                     # 應用程式進入點
├── host.json                      # Functions 執行階段設定
├── local.settings.json            # 本地開發設定
└── AzureWebApp.Functions.csproj   # 專案檔（含建置時 Git 整合）
```

## 已建立的 API 端點

### HttpTriggerFunction
- **端點**: `http://localhost:7071/api/HttpTriggerFunction`
- **方法**: GET, POST
- **授權層級**: Function
- **功能**: 基本的 HTTP Trigger 範例

### VersionFunction (版本資訊)
- **端點**: `http://localhost:7071/api/version`
- **方法**: GET
- **授權層級**: Anonymous（公開存取）
- **功能**: 回傳應用程式版本資訊
- **回傳格式**: JSON
  ```json
  {
    "Version": "70b6a61",           // Git commit hash (短格式)
    "BuildTime": "2026-02-01T14:30:00Z",  // 建置時間 (UTC)
    "Environment": "Development"     // 執行環境
  }
  ```

#### 技術實作細節

1. **Git Commit 整合（關鍵實作）**
   
   在 `AzureWebApp.Functions.csproj` 中加入以下設定，在每次建置時自動取得 Git commit hash：

   ```xml
   <PropertyGroup>
     <TargetFramework>net8.0</TargetFramework>
     <!-- 設定 SourceRevisionId 為 Git commit hash -->
     <SourceRevisionId>$(GitCommitHash)</SourceRevisionId>
     <!-- 將版本資訊嵌入 AssemblyInformationalVersion -->
     <InformationalVersion>$(GitCommitHash)-$(BuildTime)</InformationalVersion>
   </PropertyGroup>
   
   <!-- 建置前自動執行，取得 Git commit hash -->
   <Target Name="SetBuildInfo" BeforeTargets="GetAssemblyVersion">
     <Exec Command="git rev-parse --short HEAD" ConsoleToMSBuild="true" IgnoreExitCode="true">
       <Output TaskParameter="ConsoleOutput" PropertyName="GitCommitHash" />
     </Exec>
     <PropertyGroup>
       <!-- 如果無法取得 Git hash，設定為 unknown -->
       <GitCommitHash Condition="'$(GitCommitHash)' == ''">unknown</GitCommitHash>
       <!-- 記錄建置時間 (UTC) -->
       <BuildTime>$([System.DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"))</BuildTime>
     </PropertyGroup>
   </Target>
   ```

   **運作原理：**
   - `SetBuildInfo` Target 在 `GetAssemblyVersion` 之前執行
   - 使用 `git rev-parse --short HEAD` 取得短版本的 commit hash (7位)
   - 將 commit hash 和建置時間儲存到 MSBuild 屬性
   - 透過 `InformationalVersion` 嵌入到編譯後的組件 Metadata
   - 程式執行時透過 Reflection 讀取 `AssemblyInformationalVersionAttribute`

2. **建置時間**
   - 從編譯後的組件檔案最後修改時間取得
   - 格式：ISO 8601 (UTC)

3. **環境偵測**
   - 從環境變數讀取：`AZURE_FUNCTIONS_ENVIRONMENT` 或 `ASPNETCORE_ENVIRONMENT`
   - 本地開發預設：`Development`
   - Azure 部署後：`Production`

#### 使用範例

```bash
# 本地測試
curl http://localhost:7071/api/version

# Azure 部署後
curl https://<function-app-name>.azurewebsites.net/api/version
```

## 本地執行

### 前置需求

1. 安裝 .NET 8 SDK 到系統（使用專案中的安裝腳本）:
   ```bash
   # 使用專案中的 dotnet-install.sh
   chmod +x ./dotnet-install.sh
   sudo ./dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet
   ```
   
   > **說明**：專案已包含 Microsoft 官方的 `dotnet-install.sh` 安裝腳本，無需額外下載。

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

### 方法 1：使用本地部署腳本（推薦用於開發測試）

專案提供本地部署腳本 [local-deploy-azure.sh](local-deploy-azure.sh)，自動化完整的部署流程：

```bash
# 賦予執行權限
chmod +x ./local-deploy-azure.sh

# 執行部署
./local-deploy-azure.sh
```

**腳本功能：**
1. ✅ 檢查 Azure CLI 登入狀態
2. ✅ 顯示當前使用的 Azure 訂閱
3. ✅ 清理並建置專案（Release 模式）
4. ✅ 部署到 Azure Function App
5. ✅ 自動取得 Function Key
6. ✅ 顯示測試 URL 和呼叫範例

**前置需求：**
- 已安裝 Azure CLI (`az`)
- 已安裝 Azure Functions Core Tools (`func`)
- 已登入 Azure (`az login`)
- 已建立 Function App

**輸出範例：**
```bash
✓ 部署完成！
✓ Function Key: abc123...
測試 URL：
https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction?code=abc123...

測試 Function：
curl "https://func-yao-lab-938612.azurewebsites.net/api/httptriggerfunction?code=abc123..."
```

> **注意**：此腳本包含專案特定配置（Function App 名稱、Resource Group），已加入 `.gitignore`，不會提交到版本控制。

### 方法 2：手動部署步驟

1. 使用 Azure CLI 登入:
   ```bash
   az login
   ```

2. 建立 Function App（首次部署）:
   ```bash
   az functionapp create --resource-group <resource-group> \
     --consumption-plan-location eastus \
     --runtime dotnet-isolated \
     --functions-version 4 \
     --name <function-app-name> \
     --storage-account <storage-account>
   ```

3. 建置並部署:
   ```bash
   # 建置專案
   cd AzureWebApp.Functions
   dotnet build -c Release
   
   # 部署到 Azure
   func azure functionapp publish <function-app-name>
   ```

## 使用 GitHub Actions 自動部署

專案已設定 GitHub Actions workflow，可在推送程式碼到 main 分支時自動部署到 Azure Function App。

### Workflow 配置

Workflow 檔案位置：[.github/workflows/deploy-azure-function.yml](.github/workflows/deploy-azure-function.yml)

**主要功能：**
- ✅ 自動建置 .NET 8.0 專案
- ✅ 執行測試和發布
- ✅ 部署到 Azure Function App
- ✅ 部署後健康檢查（呼叫 `/api/version` 端點）
- ✅ 支援手動觸發（workflow_dispatch）

**觸發條件：**
- Push 到 `main` 分支時自動執行
- 可從 GitHub Actions 頁面手動觸發

### 設定步驟

#### 步驟 1: 設定 GitHub Secret

需要在 GitHub Repository 中設定以下 Secret：

| Secret 名稱 | 說明 |
|------------|------|
| `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` | Azure Function App 的發布設定檔 |

**方法 1：使用自動化腳本（推薦）**

專案提供自動化腳本 [setup-github-secret.sh](setup-github-secret.sh)：

```bash
# 賦予執行權限
chmod +x ./setup-github-secret.sh

# 執行腳本
./setup-github-secret.sh
```

**前置需求：**
- 已安裝並登入 Azure CLI (`az login`)
- 已安裝並登入 GitHub CLI (`gh auth login`)

腳本會自動完成：
1. 檢查必要工具（Azure CLI + GitHub CLI）
2. 從 Azure 取得 Publish Profile
3. 使用 GitHub CLI 直接寫入 Secret
4. 驗證設定並自動清理敏感暫存檔

**方法 2：手動設定**

```bash
# 1. 取得 Publish Profile
az functionapp deployment list-publishing-profiles \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --xml

# 2. 複製輸出的 XML 內容

# 3. 前往 GitHub Repository → Settings → Secrets and variables → Actions
# 4. 點選 "New repository secret"
# 5. Name: AZURE_FUNCTIONAPP_PUBLISH_PROFILE
# 6. Value: 貼上步驟 1 的 XML 內容
# 7. 點選 "Add secret"
```

#### 步驟 2: 更新 Workflow 配置

編輯 [.github/workflows/deploy-azure-function.yml](.github/workflows/deploy-azure-function.yml)，確認以下環境變數：

```yaml
env:
  AZURE_FUNCTIONAPP_NAME: 'func-yao-lab-938612'  # 您的 Function App 名稱
  AZURE_FUNCTIONAPP_PACKAGE_PATH: 'AzureWebApp.Functions'
  DOTNET_VERSION: '8.0.x'
```

#### 步驟 3: 觸發部署

**方法 1：使用空 commit 腳本（快速觸發）**

專案提供快速建立空 commit 的腳本 [empty-commit.sh](empty-commit.sh)：

```bash
# 賦予執行權限
chmod +x ./empty-commit.sh

# 建立空 commit
./empty-commit.sh

# 推送到 GitHub 觸發部署
git push origin main
```

> **說明**：腳本會建立一個帶時間戳記的空 commit，不會變更任何程式碼。

**方法 2：手動推送程式碼**
```bash
git add .
git commit -m "Update function code"
git push origin main
```

**方法 3：透過 GitHub 網頁觸發**
1. 前往 GitHub Repository → Actions
2. 選擇 "Deploy to Azure Function App" workflow
3. 點選 "Run workflow" → "Run workflow"

**方法 4：使用 GitHub CLI 觸發**
```bash
gh workflow run "Deploy to Azure Function App" --repo yaochangyu/azure-web-app-func
```

### 監控部署

1. **查看執行狀態**
   - 前往：`https://github.com/yaochangyu/azure-web-app-func/actions`
   - 查看最新的 workflow 執行記錄

2. **部署成功驗證**
   
   Workflow 會自動執行健康檢查：
   ```bash
   curl https://func-yao-lab-938612.azurewebsites.net/api/version
   ```

   成功回應範例：
   ```json
   {
     "Version": "a1b2c3d",
     "BuildTime": "2026-02-01T10:30:00Z",
     "Environment": "Production"
   }
   ```

3. **查看部署日誌**
   - 在 GitHub Actions 執行頁面查看詳細日誌
   - 或透過 Azure Portal → Function App → Deployment Center 查看

### Workflow 執行步驟

```
1. Checkout code (actions/checkout@v4)
   ↓
2. Setup .NET 8.0 (actions/setup-dotnet@v4)
   ↓
3. Restore dependencies (dotnet restore)
   ↓
4. Build project (dotnet build --configuration Release)
   ↓
5. Publish project (dotnet publish --output ./output)
   ↓
6. Deploy to Azure (Azure/functions-action@v1)
   ↓
7. Health Check (curl /api/version)
   ↓
8. ✅ 部署完成
```

### 疑難排解

**問題 1：Publish Profile 無效**
```bash
# 重新取得 Publish Profile
az functionapp deployment list-publishing-profiles \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --xml

# 更新 GitHub Secret
```

**問題 2：建置失敗**
- 檢查 .NET 版本是否正確（需要 8.0.x）
- 確認專案檔路徑正確
- 查看 GitHub Actions 日誌中的錯誤訊息

**問題 3：健康檢查失敗**
- 確認 Function App 已成功啟動（可能需要等待 30-60 秒）
- 檢查 `/api/version` 端點是否正常運作
- 查看 Azure Portal 中的 Function App 日誌

### 安全性建議

- ✅ **Publish Profile 已自動加密** - GitHub Secrets 採用加密儲存
- ✅ **暫存檔自動清理** - `setup-github-secret.sh` 會自動刪除敏感檔案
- ⚠️ **定期輪換憑證** - 建議每 90 天重新產生 Publish Profile
- ⚠️ **限制分支權限** - 只允許受信任的分支觸發部署

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

- .NET 8.0
- Azure Functions v4
- Isolated Worker Process (2.x)
- Application Insights (監控)

## 套件版本

- Microsoft.Azure.Functions.Worker: 2.50.0
- Microsoft.Azure.Functions.Worker.Sdk: 2.0.5
- Microsoft.Azure.Functions.Worker.Extensions.Http: 3.2.0

## 注意事項

- 專案使用 .NET 8.0，需確保系統已安裝對應的 SDK
- 使用 IHostApplicationBuilder 模式（Worker 2.x 推薦）
- 建議使用系統的 dotnet (`/usr/bin/dotnet`) 以確保完整的 ICU 支援
