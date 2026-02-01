#!/bin/bash

# ==========================================
# GitHub Secret 自動設定腳本
# ==========================================
# 此腳本自動設定 GitHub Actions 所需的 Azure Publish Profile
# 使用 GitHub CLI 直接寫入 Secret，無需手動操作
# 注意：暫存檔會在設定完成後自動刪除
# ==========================================

set -e  # 遇到錯誤立即停止

# 配置變數
FUNCTION_APP_NAME="func-yao-lab-938612"
RESOURCE_GROUP="rg-yao-lab"
GITHUB_REPO="yaochangyu/azure-web-app-func"
SECRET_NAME="AZURE_FUNCTIONAPP_PUBLISH_PROFILE"
TEMP_FILE="/tmp/azure-publish-profile-$(date +%s).xml"

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GitHub Secret 自動設定工具${NC}"
echo -e "${BLUE}========================================${NC}"

# 清理函數 - 確保暫存檔被刪除
cleanup() {
    if [ -f "$TEMP_FILE" ]; then
        echo -e "\n${YELLOW}正在清理暫存檔...${NC}"
        rm -f "$TEMP_FILE"
        echo -e "${GREEN}✓ 暫存檔已刪除${NC}"
    fi
}

# 設定 trap 確保腳本結束時執行清理
trap cleanup EXIT INT TERM

# 步驟 1: 檢查必要工具
echo -e "\n${YELLOW}[步驟 1/4]${NC} 檢查必要工具..."

# 檢查 Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}✗ 未安裝 Azure CLI${NC}"
    echo -e "${YELLOW}   安裝方式: https://aka.ms/azure-cli${NC}"
    exit 1
fi

# 檢查 Azure 登入狀態
if ! az account show &> /dev/null; then
    echo -e "${RED}✗ 未登入 Azure，請先執行: az login${NC}"
    exit 1
fi

# 檢查 GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ 未安裝 GitHub CLI${NC}"
    echo -e "${YELLOW}   安裝方式:${NC}"
    echo -e "${YELLOW}   - Linux: sudo apt install gh${NC}"
    echo -e "${YELLOW}   - macOS: brew install gh${NC}"
    echo -e "${YELLOW}   - Windows: winget install GitHub.cli${NC}"
    echo -e "${YELLOW}   - 或參考: https://cli.github.com/manual/installation${NC}"
    exit 1
fi

# 檢查 GitHub 登入狀態
if ! gh auth status &> /dev/null; then
    echo -e "${RED}✗ 未登入 GitHub CLI，請先執行: gh auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Azure CLI 已安裝且已登入${NC}"
echo -e "${GREEN}✓ GitHub CLI 已安裝且已登入${NC}"

# 步驟 2: 從 Azure 取得 Publish Profile
echo -e "\n${YELLOW}[步驟 2/4]${NC} 從 Azure 取得 Publish Profile..."
az functionapp deployment list-publishing-profiles \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --xml > "$TEMP_FILE"

if [ ! -s "$TEMP_FILE" ]; then
    echo -e "${RED}✗ 取得 Publish Profile 失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Publish Profile 已取得${NC}"

# 步驟 3: 使用 GitHub CLI 設定 Secret
echo -e "\n${YELLOW}[步驟 3/4]${NC} 寫入 GitHub Secret..."

# 使用 gh secret set 命令
if gh secret set "$SECRET_NAME" --repo "$GITHUB_REPO" < "$TEMP_FILE"; then
    echo -e "${GREEN}✓ Secret 已成功寫入 GitHub Repository${NC}"
    echo -e "${YELLOW}   Repository: ${GITHUB_REPO}${NC}"
    echo -e "${YELLOW}   Secret Name: ${SECRET_NAME}${NC}"
else
    echo -e "${RED}✗ 寫入 Secret 失敗${NC}"
    exit 1
fi

# 步驟 4: 驗證設定
echo -e "\n${YELLOW}[步驟 4/4]${NC} 驗證設定..."

# 列出所有 Secrets（不會顯示內容，只顯示名稱）
if gh secret list --repo "$GITHUB_REPO" | grep -q "$SECRET_NAME"; then
    echo -e "${GREEN}✓ Secret 已存在於 Repository 中${NC}"
else
    echo -e "${YELLOW}⚠ 無法驗證 Secret（可能是權限問題）${NC}"
fi

# 顯示完成訊息
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 GitHub Secret 設定完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}後續步驟：${NC}"
echo ""
echo -e "方式 1️⃣  手動觸發 workflow"
echo -e "   前往: ${BLUE}https://github.com/${GITHUB_REPO}/actions${NC}"
echo -e "   選擇 'Deploy to Azure Function App' → 'Run workflow'"
echo ""
echo -e "方式 2️⃣  推送程式碼自動觸發"
echo -e "   ${GREEN}git add .${NC}"
echo -e "   ${GREEN}git commit -m \"Setup GitHub Actions\"${NC}"
echo -e "   ${GREEN}git push origin main${NC}"
echo ""
echo -e "方式 3️⃣  使用 GitHub CLI 手動觸發"
echo -e "   ${GREEN}gh workflow run \"Deploy to Azure Function App\" --repo ${GITHUB_REPO}${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"

# 正常結束，自動清理會由 trap 執行
echo -e "\n${GREEN}腳本執行完成${NC}"
