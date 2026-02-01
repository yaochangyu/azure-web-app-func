#!/bin/bash

# ==========================================
# 設定 GitHub Actions 使用 Service Principal 部署
# ==========================================
# 此腳本會：
# 1. 建立 Azure Service Principal
# 2. 設定適當的權限
# 3. 將憑證儲存到 GitHub Secrets
# ==========================================

set -e  # 遇到錯誤立即停止

# 配置變數
RESOURCE_GROUP="rg-yao-lab"
SP_NAME="github-actions-func-yao-lab"
GITHUB_REPO="yaochangyu/azure-web-app-func"

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}設定 Service Principal 部署${NC}"
echo -e "${GREEN}========================================${NC}"

# 步驟 1: 檢查必要工具
echo -e "\n${YELLOW}[步驟 1]${NC} 檢查必要工具..."

if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ Azure CLI (az) 未安裝${NC}"
    echo "請先安裝: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI (gh) 未安裝${NC}"
    echo "請先安裝: https://cli.github.com/"
    exit 1
fi

echo -e "${GREEN}✓ 必要工具已安裝${NC}"

# 步驟 2: 檢查 Azure 登入狀態
echo -e "\n${YELLOW}[步驟 2]${NC} 檢查 Azure 登入狀態..."
if ! az account show &> /dev/null; then
    echo -e "${RED}未登入 Azure，請先執行: az login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Azure 帳戶已登入${NC}"

# 步驟 3: 檢查 GitHub 登入狀態
echo -e "\n${YELLOW}[步驟 3]${NC} 檢查 GitHub CLI 登入狀態..."
if ! gh auth status &> /dev/null; then
    echo -e "${RED}未登入 GitHub，請先執行: gh auth login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ GitHub CLI 已登入${NC}"

# 步驟 4: 取得 Azure 訂閱資訊
echo -e "\n${YELLOW}[步驟 4]${NC} 取得 Azure 訂閱資訊..."
SUBSCRIPTION_INFO=$(az account show --query "{SubscriptionId:id, SubscriptionName:name, TenantId:tenantId}" -o json)
SUBSCRIPTION_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.SubscriptionId')
TENANT_ID=$(echo $SUBSCRIPTION_INFO | jq -r '.TenantId')
SUBSCRIPTION_NAME=$(echo $SUBSCRIPTION_INFO | jq -r '.SubscriptionName')

echo -e "${BLUE}訂閱名稱: ${NC}$SUBSCRIPTION_NAME"
echo -e "${BLUE}訂閱 ID: ${NC}$SUBSCRIPTION_ID"
echo -e "${BLUE}租戶 ID: ${NC}$TENANT_ID"

# 步驟 5: 檢查 Service Principal 是否已存在
echo -e "\n${YELLOW}[步驟 5]${NC} 檢查 Service Principal 是否存在..."
EXISTING_SP=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")

if [ -n "$EXISTING_SP" ]; then
    echo -e "${YELLOW}⚠ Service Principal '$SP_NAME' 已存在 (App ID: $EXISTING_SP)${NC}"
    read -p "是否刪除並重新建立？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "刪除現有的 Service Principal..."
        az ad sp delete --id "$EXISTING_SP"
        echo -e "${GREEN}✓ 已刪除${NC}"
    else
        echo "使用現有的 Service Principal"
        # 重設密碼以取得新的 client secret
        echo "重設憑證..."
        SP_CREDENTIALS=$(az ad sp credential reset --id "$EXISTING_SP" --query "{clientId:appId, clientSecret:password, subscriptionId:'$SUBSCRIPTION_ID', tenantId:tenant}" -o json)
    fi
fi

# 步驟 6: 建立 Service Principal（如果不存在）
if [ -z "$SP_CREDENTIALS" ]; then
    echo -e "\n${YELLOW}[步驟 6]${NC} 建立 Service Principal..."
    
    # 建立 Service Principal 並賦予 Resource Group 的 Contributor 權限
    SP_CREDENTIALS=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
        --sdk-auth \
        --output json 2>&1)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 建立 Service Principal 失敗${NC}"
        echo "$SP_CREDENTIALS"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Service Principal 建立成功${NC}"
fi

# 步驟 7: 儲存憑證到暫存檔
echo -e "\n${YELLOW}[步驟 7]${NC} 準備 Azure 憑證..."
TEMP_CREDS_FILE=$(mktemp)
echo "$SP_CREDENTIALS" > "$TEMP_CREDS_FILE"

CLIENT_ID=$(echo "$SP_CREDENTIALS" | jq -r '.clientId')
echo -e "${BLUE}Client ID: ${NC}$CLIENT_ID"

# 步驟 8: 將憑證儲存到 GitHub Secrets
echo -e "\n${YELLOW}[步驟 8]${NC} 將憑證儲存到 GitHub Secrets..."
gh secret set AZURE_CREDENTIALS < "$TEMP_CREDS_FILE" --repo "$GITHUB_REPO"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 儲存 GitHub Secret 失敗${NC}"
    rm "$TEMP_CREDS_FILE"
    exit 1
fi

# 清理暫存檔
rm "$TEMP_CREDS_FILE"
echo -e "${GREEN}✓ AZURE_CREDENTIALS 已儲存到 GitHub Secrets${NC}"

# 步驟 9: 顯示摘要資訊
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 設定完成！${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${BLUE}設定摘要：${NC}"
echo -e "  Service Principal: ${GREEN}$SP_NAME${NC}"
echo -e "  Client ID: ${GREEN}$CLIENT_ID${NC}"
echo -e "  Resource Group: ${GREEN}$RESOURCE_GROUP${NC}"
echo -e "  GitHub Repository: ${GREEN}$GITHUB_REPO${NC}"

echo -e "\n${BLUE}GitHub Secret：${NC}"
echo -e "  ✓ AZURE_CREDENTIALS"

echo -e "\n${YELLOW}下一步：${NC}"
echo -e "  1. 確認 .github/workflows/deploy-azure-function.yml 已更新"
echo -e "  2. 推送程式碼到 GitHub 觸發部署"
echo -e "  3. 到 GitHub Actions 查看部署狀態"
echo -e "     ${BLUE}https://github.com/$GITHUB_REPO/actions${NC}"

echo -e "\n${GREEN}腳本執行完成${NC}"
