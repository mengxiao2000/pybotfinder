#!/bin/bash
# 快速推送脚本 - 直接运行此脚本

cd /Users/mengxiao/Documents/微博/pybotfinder

echo "=========================================="
echo "GitHub 代码推送"
echo "=========================================="
echo ""
echo "当前待推送的提交:"
git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline -5
echo ""
echo "=========================================="
echo "请获取你的GitHub Personal Access Token:"
echo "https://github.com/settings/tokens"
echo "需要权限: repo (全部权限)"
echo "=========================================="
echo ""
read -sp "请输入你的GitHub Personal Access Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

echo ""
echo "正在推送..."

# 设置远程URL（包含token）
git remote set-url origin https://mengxiao2000:${TOKEN}@github.com/mengxiao2000/pybotfinder.git

# 推送代码
if git push origin main; then
    echo "✅ 代码推送成功"
else
    echo "❌ 代码推送失败"
    git remote set-url origin https://github.com/mengxiao2000/pybotfinder.git
    exit 1
fi

# 推送标签
if git push origin v0.1.1 2>/dev/null; then
    echo "✅ 标签推送成功"
else
    echo "⚠️  标签可能已存在或推送失败"
fi

# 清理URL（安全考虑）
git remote set-url origin https://github.com/mengxiao2000/pybotfinder.git

echo ""
echo "=========================================="
echo "✅ 推送完成！"
echo "=========================================="
echo "查看仓库: https://github.com/mengxiao2000/pybotfinder"
echo "查看标签: https://github.com/mengxiao2000/pybotfinder/releases/tag/v0.1.1"

