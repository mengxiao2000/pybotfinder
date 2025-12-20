#!/bin/bash

# GitHub 推送脚本
# 使用前请确保已创建 GitHub 仓库：https://github.com/new

echo "🚀 开始推送到 GitHub..."

# 检查远程仓库配置
echo "📋 检查远程仓库配置..."
git remote -v

# 使用 token 配置远程 URL（临时）
echo "🔐 配置认证..."
echo "⚠️  请先设置环境变量 GITHUB_TOKEN，或编辑此脚本替换 YOUR_TOKEN"
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 错误：未设置 GITHUB_TOKEN 环境变量"
    echo "   请运行：export GITHUB_TOKEN=your_token_here"
    echo "   或编辑此脚本，将 YOUR_TOKEN 替换为你的实际 token"
    exit 1
fi
git remote set-url origin https://mengxiao2000:${GITHUB_TOKEN}@github.com/mengxiao2000/pybotfinder.git

# 推送主分支
echo "📤 推送主分支..."
if git push -u origin main; then
    echo "✅ 主分支推送成功！"
else
    echo "❌ 主分支推送失败，请检查："
    echo "   1. GitHub 仓库是否已创建：https://github.com/new"
    echo "   2. Token 权限是否正确（需要 repo 权限）"
    exit 1
fi

# 推送标签
echo "🏷️  推送版本标签..."
if git push origin v0.1.0; then
    echo "✅ 标签推送成功！"
else
    echo "⚠️  标签推送失败（可能已存在）"
fi

# 恢复正常的 URL（安全考虑）
echo "🔒 恢复远程 URL（移除 token）..."
git remote set-url origin https://github.com/mengxiao2000/pybotfinder.git

echo ""
echo "🎉 完成！"
echo ""
echo "📋 下一步："
echo "   1. 访问 https://github.com/mengxiao2000/pybotfinder 查看仓库"
echo "   2. 创建 GitHub Release："
echo "      - 访问：https://github.com/mengxiao2000/pybotfinder/releases/new"
echo "      - 选择标签：v0.1.0"
echo "      - 填写 Release 信息"
echo ""

