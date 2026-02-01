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
