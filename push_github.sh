#!/bin/bash

# GitHub推送脚本
# 使用方法：
# 1. 确保你有GitHub Personal Access Token
# 2. 运行此脚本：bash push_github.sh

set -e

REPO_URL="https://github.com/mengxiao2000/pybotfinder.git"
GITHUB_USERNAME="mengxiao2000"

echo "=========================================="
echo "GitHub 推送脚本"
echo "=========================================="
echo ""

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  检测到未提交的更改，请先提交："
    git status
    exit 1
fi

# 显示当前状态
echo "当前分支: $(git branch --show-current)"
echo "待推送的提交:"
git log origin/main..HEAD --oneline 2>/dev/null || git log --oneline -5

echo ""
echo "=========================================="
echo "推送选项："
echo "1. 使用GitHub CLI (gh) - 推荐"
echo "2. 使用SSH (如果已配置SSH key)"
echo "3. 手动输入token"
echo "=========================================="
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        if command -v gh &> /dev/null; then
            echo "使用GitHub CLI推送..."
            gh auth status || gh auth login
            git push origin main
            git push origin v0.1.1 2>/dev/null || echo "标签可能已存在"
        else
            echo "❌ GitHub CLI未安装，请先安装: brew install gh"
            exit 1
        fi
        ;;
    2)
        echo "使用SSH推送..."
        git remote set-url origin git@github.com:mengxiao2000/pybotfinder.git
        git push origin main
        git push origin v0.1.1 2>/dev/null || echo "标签可能已存在"
        ;;
    3)
        echo ""
        echo "请在浏览器中生成新的Personal Access Token:"
        echo "https://github.com/settings/tokens"
        echo "需要权限: repo (全部权限)"
        echo ""
        read -p "请输入你的GitHub Personal Access Token: " token
        
        if [ -z "$token" ]; then
            echo "❌ Token不能为空"
            exit 1
        fi
        
        # 使用token推送
        git remote set-url origin https://${GITHUB_USERNAME}:${token}@github.com/mengxiao2000/pybotfinder.git
        git push origin main
        git push origin v0.1.1 2>/dev/null || echo "标签可能已存在"
        
        # 清理URL中的token（安全考虑）
        git remote set-url origin https://github.com/mengxiao2000/pybotfinder.git
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 推送完成！"
echo "查看仓库: https://github.com/mengxiao2000/pybotfinder"

