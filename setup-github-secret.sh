#!/bin/bash

# ==========================================
# GitHub Secret 設定腳本
# ==========================================
# 此腳本協助設定 GitHub Actions 所需的 Azure Publish Profile
# 注意：暫存檔會在設定完成後自動刪除
# ==========================================

set -e  # 遇到錯誤立即停止

# 配置變數
FUNCTION_APP_NAME="func-yao-lab-938612"
RESOURCE_GROUP="rg-yao-lab"
GITHUB_REPO="yaochangyu/azure-web-app-func"
TEMP_FILE="/tmp/azure-publish-profile-$(date +%s).xml"

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GitHub Secret 設定輔助工具${NC}"
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

# 步驟 1: 檢查 Azure 登入狀態
echo -e "\n${YELLOW}[步驟 1/5]${NC} 檢查 Azure 登入狀態..."
if ! az account show &> /dev/null; then
    echo -e "${RED}✗ 未登入 Azure，請先執行: az login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Azure 帳戶已登入${NC}"

# 步驟 2: 從 Azure 取得 Publish Profile
echo -e "\n${YELLOW}[步驟 2/5]${NC} 從 Azure 取得 Publish Profile..."
az functionapp deployment list-publishing-profiles \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --xml > "$TEMP_FILE"

if [ ! -s "$TEMP_FILE" ]; then
    echo -e "${RED}✗ 取得 Publish Profile 失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Publish Profile 已儲存到暫存檔${NC}"
echo -e "${YELLOW}   暫存檔位置: $TEMP_FILE${NC}"

# 步驟 3: 複製到剪貼簿（如果可用）
echo -e "\n${YELLOW}[步驟 3/5]${NC} 準備複製到剪貼簿..."

if command -v xclip &> /dev/null; then
    cat "$TEMP_FILE" | xclip -selection clipboard
    echo -e "${GREEN}✓ 已複製到剪貼簿 (xclip)${NC}"
elif command -v pbcopy &> /dev/null; then
    cat "$TEMP_FILE" | pbcopy
    echo -e "${GREEN}✓ 已複製到剪貼簿 (pbcopy)${NC}"
elif command -v clip.exe &> /dev/null; then
    cat "$TEMP_FILE" | clip.exe
    echo -e "${GREEN}✓ 已複製到剪貼簿 (Windows clip)${NC}"
else
    echo -e "${YELLOW}⚠ 未找到剪貼簿工具，請手動複製${NC}"
    echo -e "${YELLOW}   執行以下命令查看內容: cat $TEMP_FILE${NC}"
fi

# 步驟 4: 顯示設定指引
echo -e "\n${YELLOW}[步驟 4/5]${NC} 設定 GitHub Secret"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}請按照以下步驟設定：${NC}"
echo ""
echo -e "1️⃣  開啟瀏覽器，前往："
echo -e "   ${BLUE}https://github.com/${GITHUB_REPO}/settings/secrets/actions${NC}"
echo ""
echo -e "2️⃣  點選 ${GREEN}'New repository secret'${NC} 按鈕"
echo ""
echo -e "3️⃣  填寫以下資訊："
echo -e "   Name:  ${GREEN}AZURE_FUNCTIONAPP_PUBLISH_PROFILE${NC}"
echo -e "   Value: ${YELLOW}貼上剪貼簿內容（已自動複製）${NC}"
echo ""
echo -e "4️⃣  點選 ${GREEN}'Add secret'${NC} 按鈕完成"
echo -e "${BLUE}========================================${NC}"

# 如果剪貼簿不可用，顯示檔案內容
if ! command -v xclip &> /dev/null && ! command -v pbcopy &> /dev/null && ! command -v clip.exe &> /dev/null; then
    echo -e "\n${YELLOW}Publish Profile 內容：${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    cat "$TEMP_FILE"
    echo -e "${BLUE}----------------------------------------${NC}"
fi

# 步驟 5: 等待使用者確認
echo -e "\n${YELLOW}[步驟 5/5]${NC} 等待確認..."
read -p "$(echo -e ${GREEN}是否已完成 GitHub Secret 設定？ [y/N]: ${NC})" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}✓ 設定完成！${NC}"
    
    # 顯示後續步驟
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 GitHub Actions 已準備就緒！${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}測試部署方式：${NC}"
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
    echo -e "${BLUE}========================================${NC}"
else
    echo -e "\n${YELLOW}⚠ 設定未完成${NC}"
    echo -e "${YELLOW}暫存檔將保留在: $TEMP_FILE${NC}"
    echo -e "${RED}請注意：此檔案包含敏感資訊，完成設定後請手動刪除${NC}"
    echo -e "${YELLOW}刪除命令: rm $TEMP_FILE${NC}"
    
    # 取消自動清理
    trap - EXIT INT TERM
    exit 0
fi

# 正常結束，自動清理會由 trap 執行
echo -e "\n${GREEN}腳本執行完成${NC}"
