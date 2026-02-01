# Azure Functions 最佳實踐指南

根據 Microsoft 官方文檔及實務經驗整理的 Azure Functions 開發與部署最佳實踐。

---

## 目錄

1. [架構設計原則](#架構設計原則)
2. [效能與可靠性](#效能與可靠性)
3. [安全性](#安全性)
4. [部署與 CI/CD](#部署與-cicd)
5. [監控與日誌](#監控與日誌)
6. [成本優化](#成本優化)
7. [開發規範](#開發規範)

---

## 架構設計原則

### 1. 選擇正確的 Hosting Plan

#### 選擇指南

| 場景 | 推薦方案 | 原因 |
|------|---------|------|
| 開發/測試 | Consumption Plan | 免費額度充足 |
| 生產環境（一般） | **Flex Consumption** 或 Premium | 兼顧效能與成本 |
| 關鍵業務系統 | Premium Plan | 無冷啟動、VNet 整合 |
| 長時間運作 | Dedicated Plan | 固定成本、可與其他服務共用資源 |
| 自訂容器環境 | Container Apps | 完全控制執行環境 |

#### 重要考量

- **冷啟動問題**：
  - Premium Plan：設定 Always Ready Instances 避免冷啟動
  - Flex Consumption：使用 Always Ready Instances 保持暖機狀態
  - Consumption Plan：接受冷啟動或遷移至其他方案

- **區域限制**：
  - ⚠️ Linux Consumption Plan 將於 **2028/09/30 淘汰**
  - 建議提早遷移至 Flex Consumption Plan

### 2. Function App 組織架構

#### 單一 Function App 的限制

**建議拆分的情況**：

1. **記憶體占用高**
   - 單一 Function 占用大量記憶體時，應獨立部署
   - 避免影響同 App 中的其他 Function

2. **負載模式差異大**
   ```
   ✅ 好的做法：
   - App A: 高頻率、低記憶體的 Functions
   - App B: 低頻率、高記憶體的 Functions
   
   ❌ 壞的做法：
   - 混合不同負載模式在同一 App 中
   ```

3. **權限隔離需求**
   - 不同 Function 需要不同的資料庫連線字串時
   - 應拆分成不同 App 以最小化權限範圍

4. **設定差異**
   - `host.json` 設定適用於整個 App
   - 需要不同 host.json 設定時應拆分

#### 部署策略

```
專案結構建議：
├── FunctionApp.Core/           # 高頻率、核心業務
├── FunctionApp.Background/     # 背景作業、長時間運作
└── FunctionApp.Admin/          # 管理功能、高權限
```

---

## 效能與可靠性

### 1. 避免長時間運作的 Function

#### 問題

- HTTP 觸發器最長回應時間：**230 秒**（Azure Load Balancer 限制）
- 超過逾時時間會導致不可預期的錯誤

#### 解決方案

**方案 A：使用 Durable Functions**

```csharp
// 適用於：需要長時間處理的工作流程
[FunctionName("HttpStart")]
public static async Task<HttpResponseData> HttpStart(
    [HttpTrigger(AuthorizationLevel.Anonymous, "post")] HttpRequestData req,
    [DurableClient] DurableTaskClient client)
{
    string instanceId = await client.ScheduleNewOrchestrationInstanceAsync(
        nameof(ProcessLongRunningTask));

    return client.CreateCheckStatusResponse(req, instanceId);
}
```

**方案 B：使用 Queue 模式**

```csharp
// HTTP Function: 接收請求並放入 Queue
[Function("SubmitTask")]
public async Task<HttpResponseData> SubmitTask(
    [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequestData req,
    [QueueOutput("tasks")] ICollector<string> taskQueue)
{
    var payload = await req.ReadAsStringAsync();
    taskQueue.Add(payload);
    
    var response = req.CreateResponse(HttpStatusCode.Accepted);
    await response.WriteStringAsync("Task queued");
    return response;
}

// Queue Function: 實際處理任務
[Function("ProcessTask")]
public void ProcessTask(
    [QueueTrigger("tasks")] string task)
{
    // 長時間處理邏輯
}
```

### 2. 函式設計原則

#### 無狀態設計（Stateless）

```csharp
// ❌ 錯誤：使用靜態變數儲存狀態
public class BadFunction
{
    private static int _counter = 0;  // 多實例會有問題
    
    [Function("BadCounter")]
    public HttpResponseData Run([HttpTrigger] HttpRequestData req)
    {
        _counter++;  // 不可靠
        return req.CreateResponse(HttpStatusCode.OK);
    }
}

// ✅ 正確：狀態儲存在外部
public class GoodFunction
{
    private readonly ITableClient _tableClient;
    
    [Function("GoodCounter")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger] HttpRequestData req)
    {
        // 從外部儲存讀取/更新狀態
        await _tableClient.IncrementCounterAsync();
        return req.CreateResponse(HttpStatusCode.OK);
    }
}
```

#### 冪等性設計（Idempotent）

```csharp
// Timer Trigger 必須設計成冪等
[Function("DailyReport")]
public async Task GenerateDailyReport(
    [TimerTrigger("0 0 9 * * *")] TimerInfo timer)
{
    var today = DateTime.UtcNow.Date;
    
    // 檢查是否已處理
    if (await _reportService.IsReportGeneratedAsync(today))
    {
        _logger.LogInformation("Report already generated for {Date}", today);
        return;  // 冪等：重複執行不會產生副作用
    }
    
    await _reportService.GenerateAsync(today);
}
```

#### 防禦性程式設計

```csharp
[Function("ProcessOrder")]
public async Task ProcessOrder(
    [QueueTrigger("orders")] OrderMessage order)
{
    try
    {
        // 1. 驗證輸入
        if (order == null || string.IsNullOrEmpty(order.OrderId))
        {
            _logger.LogWarning("Invalid order message");
            return; // 不要 throw，避免無限重試
        }
        
        // 2. 檢查是否已處理（防止重複處理）
        if (await _orderService.IsProcessedAsync(order.OrderId))
        {
            _logger.LogInformation("Order {OrderId} already processed", order.OrderId);
            return;
        }
        
        // 3. 處理訂單
        await _orderService.ProcessAsync(order);
        
        // 4. 標記為已處理
        await _orderService.MarkAsProcessedAsync(order.OrderId);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Failed to process order {OrderId}", order.OrderId);
        throw; // 重試機制會處理
    }
}
```

### 3. 非同步程式設計

```csharp
// ❌ 錯誤：阻塞式呼叫
public HttpResponseData BadAsync([HttpTrigger] HttpRequestData req)
{
    var result = _httpClient.GetAsync("https://api.example.com").Result;  // 會阻塞執行緒
    return req.CreateResponse(HttpStatusCode.OK);
}

// ✅ 正確：完全非同步
public async Task<HttpResponseData> GoodAsync([HttpTrigger] HttpRequestData req)
{
    var result = await _httpClient.GetAsync("https://api.example.com");
    return req.CreateResponse(HttpStatusCode.OK);
}
```

### 4. 連線管理

#### 使用靜態 HttpClient

```csharp
// ❌ 錯誤：每次建立新的 HttpClient
public class BadHttpFunction
{
    [Function("CallApi")]
    public async Task Run([TimerTrigger("0 */5 * * * *")] TimerInfo timer)
    {
        using var client = new HttpClient();  // 會耗盡 Socket
        await client.GetAsync("https://api.example.com");
    }
}

// ✅ 正確：使用 DI 注入或靜態實例
public class GoodHttpFunction
{
    private readonly IHttpClientFactory _httpClientFactory;
    
    public GoodHttpFunction(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }
    
    [Function("CallApi")]
    public async Task Run([TimerTrigger("0 */5 * * * *")] TimerInfo timer)
    {
        var client = _httpClientFactory.CreateClient();
        await client.GetAsync("https://api.example.com");
    }
}
```

#### Program.cs 設定

```csharp
var host = new HostBuilder()
    .ConfigureFunctionsWebApplication()
    .ConfigureServices(services =>
    {
        // 註冊 HttpClient
        services.AddHttpClient();
        
        // 或設定具名 HttpClient
        services.AddHttpClient("MyApi", client =>
        {
            client.BaseAddress = new Uri("https://api.example.com");
            client.Timeout = TimeSpan.FromSeconds(30);
        });
    })
    .Build();

host.Run();
```

### 5. 批次處理

```csharp
// ✅ Event Hub 批次處理
[Function("ProcessEventBatch")]
public void ProcessBatch(
    [EventHubTrigger("events", Connection = "EventHubConnection")] EventData[] events)
{
    _logger.LogInformation("Processing {Count} events", events.Length);
    
    foreach (var evt in events)
    {
        // 處理單一事件
    }
}
```

**host.json 設定**

```json
{
  "version": "2.0",
  "extensions": {
    "eventHubs": {
      "batchCheckpointFrequency": 5,
      "eventProcessorOptions": {
        "maxBatchSize": 256,
        "prefetchCount": 512
      }
    }
  }
}
```

---

## 安全性

### 1. 使用 Managed Identity

```csharp
// ✅ 使用 Managed Identity 存取 Azure 資源
public class SecureFunction
{
    private readonly BlobServiceClient _blobClient;
    
    public SecureFunction()
    {
        // 使用 DefaultAzureCredential (支援 Managed Identity)
        _blobClient = new BlobServiceClient(
            new Uri("https://mystorageaccount.blob.core.windows.net"),
            new DefaultAzureCredential());
    }
}
```

**啟用 Managed Identity**

```bash
# 啟用系統指派的 Managed Identity
az functionapp identity assign \
  --name <function-app-name> \
  --resource-group <resource-group>

# 授予權限（以 Blob Storage 為例）
az role assignment create \
  --assignee <principal-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Storage/storageAccounts/<storage-account>
```

### 2. 敏感資料管理

#### 使用 Azure Key Vault

```bash
# 在 Function App 設定中引用 Key Vault Secret
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "ConnectionString=@Microsoft.KeyVault(SecretUri=https://<vault-name>.vault.azure.net/secrets/<secret-name>)"
```

#### 程式碼中讀取

```csharp
public class MyFunction
{
    [Function("SecureFunction")]
    public HttpResponseData Run([HttpTrigger] HttpRequestData req)
    {
        // 從環境變數讀取（已由 Azure 自動解析 Key Vault）
        var connectionString = Environment.GetEnvironmentVariable("ConnectionString");
        return req.CreateResponse(HttpStatusCode.OK);
    }
}
```

### 3. 授權層級設定

```csharp
// 公開 API（如健康檢查、版本資訊）
[Function("Health")]
public HttpResponseData Health(
    [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
{
    return req.CreateResponse(HttpStatusCode.OK);
}

// 內部 API（需要 Function Key）
[Function("InternalApi")]
public HttpResponseData Internal(
    [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequestData req)
{
    return req.CreateResponse(HttpStatusCode.OK);
}

// 管理 API（需要 Admin Key）
[Function("AdminApi")]
public HttpResponseData Admin(
    [HttpTrigger(AuthorizationLevel.Admin, "delete")] HttpRequestData req)
{
    return req.CreateResponse(HttpStatusCode.OK);
}
```

### 4. 網路安全

#### 使用 Virtual Network 整合（Premium Plan）

```bash
# 整合到 VNet
az functionapp vnet-integration add \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --vnet <vnet-name> \
  --subnet <subnet-name>
```

#### 限制輸入 IP

```bash
# 設定 IP 限制
az functionapp config access-restriction add \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --rule-name "AllowOfficeIP" \
  --action Allow \
  --ip-address "203.0.113.0/24" \
  --priority 100
```

---

## 部署與 CI/CD

### 1. Run from Package（推薦）

**好處**：
- ✅ 避免檔案鎖定問題
- ✅ 改善冷啟動效能
- ✅ 原子性部署（全部成功或全部失敗）

#### 設定方式

```bash
# 方式 1: 使用 ZIP 部署
func azure functionapp publish <function-app-name> --build remote

# 方式 2: 設定 WEBSITE_RUN_FROM_PACKAGE
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "WEBSITE_RUN_FROM_PACKAGE=1"
```

### 2. 使用 Deployment Slots（零停機部署）

```bash
# 建立 Staging Slot
az functionapp deployment slot create \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --slot staging

# 部署到 Staging
func azure functionapp publish <function-app-name> --slot staging

# 驗證 Staging
curl https://<function-app-name>-staging.azurewebsites.net/api/health

# Swap 到 Production
az functionapp deployment slot swap \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --slot staging
```

### 3. GitHub Actions CI/CD 範例

```yaml
name: Deploy Azure Function

on:
  push:
    branches: [ main ]

env:
  AZURE_FUNCTIONAPP_NAME: my-function-app
  DOTNET_VERSION: '8.0.x'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup .NET
      uses: actions/setup-dotnet@v3
      with:
        dotnet-version: ${{ env.DOTNET_VERSION }}
    
    - name: Build and Test
      run: |
        dotnet build --configuration Release
        dotnet test
    
    - name: Publish
      run: |
        dotnet publish --configuration Release --output ./output
    
    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: ${{ env.AZURE_FUNCTIONAPP_NAME }}
        package: './output'
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

### 4. 環境變數管理

#### local.settings.json（本地開發）

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "Environment": "Development",
    "ApiKey": "local-dev-key"
  }
}
```

#### Azure 環境（透過 CLI）

```bash
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings \
    "Environment=Production" \
    "ApiKey=@Microsoft.KeyVault(SecretUri=https://vault.azure.net/secrets/api-key)"
```

---

## 監控與日誌

### 1. Application Insights 整合

#### 啟用 Application Insights

```bash
# 建立 Application Insights
az monitor app-insights component create \
  --app <app-insights-name> \
  --location eastus \
  --resource-group <resource-group>

# 連結到 Function App
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings "APPINSIGHTS_INSTRUMENTATIONKEY=<instrumentation-key>"
```

#### 程式碼中使用日誌

```csharp
public class MyFunction
{
    private readonly ILogger<MyFunction> _logger;
    
    public MyFunction(ILogger<MyFunction> logger)
    {
        _logger = logger;
    }
    
    [Function("ProcessOrder")]
    public async Task Run([QueueTrigger("orders")] OrderMessage order)
    {
        // 結構化日誌
        _logger.LogInformation("Processing order {OrderId} for customer {CustomerId}", 
            order.Id, order.CustomerId);
        
        try
        {
            await ProcessOrderAsync(order);
            
            // 自訂度量
            _logger.LogMetric("OrderProcessed", 1, new Dictionary<string, object>
            {
                ["CustomerId"] = order.CustomerId,
                ["Amount"] = order.Amount
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process order {OrderId}", order.Id);
            throw;
        }
    }
}
```

### 2. host.json 監控設定

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20,
        "excludedTypes": "Request"  // 不對 HTTP Request 採樣
      },
      "enableLiveMetricsFilters": true
    },
    "logLevel": {
      "default": "Information",
      "Function": "Information",
      "Host": "Warning"
    }
  }
}
```

### 3. 健康檢查端點

```csharp
[Function("HealthCheck")]
public async Task<HttpResponseData> HealthCheck(
    [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "health")] HttpRequestData req)
{
    var health = new
    {
        Status = "Healthy",
        Version = Assembly.GetExecutingAssembly()
            .GetCustomAttribute<AssemblyInformationalVersionAttribute>()?
            .InformationalVersion,
        Timestamp = DateTime.UtcNow
    };
    
    // 可加入依賴服務檢查
    try
    {
        await _dbContext.Database.CanConnectAsync();
        health = health with { DatabaseStatus = "Connected" };
    }
    catch
    {
        health = health with { DatabaseStatus = "Disconnected", Status = "Degraded" };
    }
    
    var response = req.CreateResponse(HttpStatusCode.OK);
    await response.WriteAsJsonAsync(health);
    return response;
}
```

### 4. 告警設定

```bash
# CPU 使用率告警
az monitor metrics alert create \
  --name "HighCPU" \
  --resource-group <resource-group> \
  --scopes /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name> \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m
```

---

## 成本優化

### 1. 選擇合適的 Hosting Plan

| 場景 | 建議 | 估算成本 |
|------|------|---------|
| 低流量 API | Consumption Plan | < $5/月（含免費額度）|
| 中流量應用 | Flex Consumption | $50-200/月 |
| 高可用系統 | Premium Plan (EP1) | ~$160/月起 |

### 2. 避免共用 Storage Account

```bash
# ❌ 錯誤：多個 Function App 共用同一個 Storage
# AzureWebJobsStorage=<same-storage-account>

# ✅ 正確：每個 Function App 使用獨立的 Storage Account
az functionapp config appsettings set \
  --name function-app-1 \
  --settings "AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=storage1;..."

az functionapp config appsettings set \
  --name function-app-2 \
  --settings "AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=storage2;..."
```

### 3. 設定 Daily Usage Quota（僅開發環境）

```bash
# 開發環境設定每日用量限制（避免費用失控）
# ⚠️ 生產環境不要設定此限制
az functionapp config appsettings set \
  --name <dev-function-app> \
  --settings "AzureWebJobsMaxExecutions=100000"
```

### 4. 使用多個 Worker Process

```bash
# 提高單一實例的處理能力，減少擴展需求
az functionapp config appsettings set \
  --name <function-app-name> \
  --settings "FUNCTIONS_WORKER_PROCESS_COUNT=2"
```

---

## 開發規範

### 1. 專案結構

```
AzureWebApp.Functions/
├── Functions/                  # Function 端點
│   ├── HttpTriggers/
│   │   ├── VersionFunction.cs
│   │   └── HealthCheckFunction.cs
│   ├── TimerTriggers/
│   │   └── DailyReportFunction.cs
│   └── QueueTriggers/
│       └── ProcessOrderFunction.cs
├── Models/                     # 資料模型
│   ├── Requests/
│   ├── Responses/
│   └── Entities/
├── Services/                   # 業務邏輯
│   ├── IOrderService.cs
│   └── OrderService.cs
├── Extensions/                 # 擴充方法
├── Program.cs                  # DI 註冊
├── host.json
└── local.settings.json
```

### 2. 依賴注入（DI）

```csharp
// Program.cs
var host = new HostBuilder()
    .ConfigureFunctionsWebApplication()
    .ConfigureServices(services =>
    {
        // 註冊服務
        services.AddScoped<IOrderService, OrderService>();
        services.AddSingleton<IConfiguration>(sp => 
            new ConfigurationBuilder()
                .AddEnvironmentVariables()
                .Build());
        
        // 註冊 DbContext
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(
                Environment.GetEnvironmentVariable("SqlConnectionString")));
        
        // 註冊 HttpClient
        services.AddHttpClient();
    })
    .Build();

host.Run();
```

### 3. 錯誤處理

```csharp
public class ResilientFunction
{
    [Function("ProcessWithRetry")]
    public async Task Run(
        [QueueTrigger("tasks")] TaskMessage task,
        FunctionContext context)
    {
        var logger = context.GetLogger<ResilientFunction>();
        
        try
        {
            // 業務邏輯
            await ProcessTaskAsync(task);
        }
        catch (TransientException ex)
        {
            // 暫時性錯誤：重試
            logger.LogWarning(ex, "Transient error, will retry");
            throw;  // 讓 Azure Functions 重試機制處理
        }
        catch (PermanentException ex)
        {
            // 永久性錯誤：記錄並移到 Dead Letter Queue
            logger.LogError(ex, "Permanent error, moving to DLQ");
            // 不要 throw，避免無限重試
        }
        catch (Exception ex)
        {
            // 未預期的錯誤
            logger.LogCritical(ex, "Unexpected error");
            throw;
        }
    }
}
```

### 4. 單元測試

```csharp
public class VersionFunctionTests
{
    [Fact]
    public async Task Run_ReturnsVersionInfo()
    {
        // Arrange
        var logger = new Mock<ILogger<VersionFunction>>();
        var function = new VersionFunction(logger.Object);
        var context = new Mock<FunctionContext>();
        var request = new Mock<HttpRequestData>(context.Object);
        
        var response = new Mock<HttpResponseData>(context.Object);
        response.SetupProperty(r => r.StatusCode);
        request.Setup(r => r.CreateResponse()).Returns(response.Object);
        
        // Act
        var result = await function.Run(request.Object);
        
        // Assert
        Assert.Equal(HttpStatusCode.OK, result.StatusCode);
    }
}
```

---

## 快速檢查清單

### 部署前檢查

- [ ] 選擇正確的 Hosting Plan
- [ ] 設定獨立的 Storage Account
- [ ] 啟用 Application Insights
- [ ] 設定 Managed Identity（生產環境）
- [ ] 移除 `AzureWebJobsDashboard` 設定
- [ ] 設定健康檢查端點
- [ ] 配置告警規則
- [ ] 測試 Deployment Slot（如適用）

### 程式碼審查

- [ ] 所有 I/O 操作使用 `async/await`
- [ ] 避免使用 `.Result` 或 `.Wait()`
- [ ] HttpClient 使用 DI 注入
- [ ] Function 設計為無狀態
- [ ] 實作冪等性（Timer/Queue Triggers）
- [ ] 正確的錯誤處理
- [ ] 結構化日誌
- [ ] 敏感資料不寫入日誌

### 效能優化

- [ ] 啟用批次處理（EventHub/Queue）
- [ ] 設定適當的 host.json 並行參數
- [ ] 使用 `FUNCTIONS_WORKER_PROCESS_COUNT`（Python/Node.js）
- [ ] 避免長時間運作（改用 Durable Functions）
- [ ] 連線重用（HttpClient、DbContext）

---

## 參考資料

### 官方文檔

- [Azure Functions 最佳實踐](https://learn.microsoft.com/azure/azure-functions/functions-best-practices)
- [效能與可靠性](https://learn.microsoft.com/azure/azure-functions/performance-reliability)
- [安全性概念](https://learn.microsoft.com/azure/azure-functions/security-concepts)
- [Durable Functions 概觀](https://learn.microsoft.com/azure/azure-functions/durable/durable-functions-overview)
- [Application Insights 監控](https://learn.microsoft.com/azure/azure-functions/functions-monitoring)

### 架構參考

- [Azure Architecture Center - Serverless](https://learn.microsoft.com/azure/architecture/reference-architectures/serverless/web-app)
- [Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)

---

**最後更新**：2026年2月（基於 Microsoft 官方文檔）
