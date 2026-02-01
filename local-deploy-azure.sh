#!/bin/bash

# ==========================================
# Azure Function App 部署腳本
# ==========================================
# 此腳本用於部署 Azure Functions 到 Azure
# 注意：此檔案包含敏感資訊，已加入 .gitignore
# ==========================================

set -e  # 遇到錯誤立即停止

# 配置變數
FUNCTION_APP_NAME="func-yao-lab-938612"
RESOURCE_GROUP="rg-yao-lab"
PROJECT_DIR="AzureWebApp.Functions"

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}開始部署到 Azure Function App${NC}"
echo -e "${GREEN}========================================${NC}"

# 步驟 1: 檢查 Azure 登入狀態
echo -e "\n${YELLOW}[步驟 1]${NC} 檢查 Azure 登入狀態..."
if ! az account show &> /dev/null; then
    echo -e "${RED}未登入 Azure，請先執行: az login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Azure 帳戶已登入${NC}"

# 步驟 2: 顯示目前訂閱
echo -e "\n${YELLOW}[步驟 2]${NC} 目前使用的訂閱："
az account show --query "{Name:name, SubscriptionId:id}" -o table

# 步驟 3: 清理並建置專案 (Release 模式)
echo -e "\n${YELLOW}[步驟 3]${NC} 清理並建置專案..."
cd "$(dirname "$0")"
dotnet restore
dotnet clean
dotnet build -c Release

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 建置失敗${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 建置成功${NC}"

# 步驟 4: 部署到 Azure Function App
echo -e "\n${YELLOW}[步驟 4]${NC} 部署到 Azure Function App: ${FUNCTION_APP_NAME}..."
cd "$PROJECT_DIR"
func azure functionapp publish "$FUNCTION_APP_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 部署失敗${NC}"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"

# 步驟 5: 取得 Function URL 和 Key
echo -e "\n${YELLOW}[步驟 5]${NC} 取得 Function 資訊..."

# 取得 Function Key
FUNCTION_KEY=$(az functionapp function keys list \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --function-name HttpTriggerFunction \
  --query "default" -o tsv 2>/dev/null)

if [ -z "$FUNCTION_KEY" ]; then
    echo -e "${YELLOW}⚠ 無法自動取得 Function Key，請手動執行：${NC}"
    echo "az functionapp function keys list --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --function-name HttpTriggerFunction"
else
    echo -e "${GREEN}✓ Function Key: ${FUNCTION_KEY}${NC}"
    
    # 顯示完整的呼叫 URL
    INVOKE_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/api/httptriggerfunction?code=${FUNCTION_KEY}"
    echo -e "\n${GREEN}測試 URL：${NC}"
    echo "$INVOKE_URL"
    
    echo -e "\n${YELLOW}測試 Function：${NC}"
    echo "curl \"$INVOKE_URL\""
fi

echo -e "\n${GREEN}部署流程結束${NC}"
