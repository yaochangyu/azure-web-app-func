# GitHub Actions Workflows

## 部署到 Azure Function App

此專案使用 GitHub Actions 自動部署到 Azure Function App。

### 🚀 觸發條件

- **自動觸發**：推送程式碼到 `main` 分支時自動部署
- **手動觸發**：可在 GitHub Actions 頁面手動執行

### ⚙️ 必要設定

#### 1. 取得 Azure Function App Publish Profile

在本機執行以下命令：

```bash
az functionapp deployment list-publishing-profiles \
  --name func-yao-lab-938612 \
  --resource-group rg-yao-lab \
  --xml
```

複製完整的 XML 輸出內容。

#### 2. 設定 GitHub Secret

1. 前往 GitHub 專案頁面
2. 點選 `Settings` → `Secrets and variables` → `Actions`
3. 點選 `New repository secret`
4. 新增以下 Secret：

   - **Name**: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
   - **Value**: 貼上步驟 1 取得的完整 XML 內容

#### 3. 完成設定

儲存 Secret 後，下次推送到 `main` 分支時就會自動觸發部署。

### 📋 Workflow 執行流程

1. **Checkout 程式碼**
2. **設定 .NET 8.0 環境**
3. **還原相依套件** (`dotnet restore`)
4. **建置專案** (`dotnet build --configuration Release`)
5. **發佈專案** (`dotnet publish`)
6. **部署到 Azure Functions**
7. **健康檢查** (驗證部署是否成功)

### 🔍 檢視部署狀態

- 前往 GitHub 專案的 `Actions` 頁籤
- 可查看每次部署的詳細記錄
- 綠色勾勾表示部署成功

### 🛠️ 自訂設定

如需修改設定，編輯 [deploy-azure-function.yml](./deploy-azure-function.yml) 檔案：

- `AZURE_FUNCTIONAPP_NAME`: Function App 名稱
- `AZURE_FUNCTIONAPP_PACKAGE_PATH`: 專案目錄路徑
- `DOTNET_VERSION`: .NET 版本

### 📝 注意事項

- Publish Profile 包含敏感資訊，**絕不可**提交到 Git 儲存庫
- 使用 GitHub Secrets 安全地儲存認證資訊
- 每次重新產生 Publish Profile 時，需要更新 GitHub Secret

### 🔗 相關連結

- [Azure Functions GitHub Actions 文件](https://docs.microsoft.com/azure/azure-functions/functions-how-to-github-actions)
- [GitHub Actions 文件](https://docs.github.com/en/actions)
