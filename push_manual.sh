#!/bin/bash

# 手动推送脚本 - 使用交互式输入

echo "🚀 准备推送到 GitHub..."
echo ""
echo "⚠️  当提示输入用户名和密码时："
echo "   用户名：mengxiao2000"
echo "   密码：粘贴你的 GitHub Personal Access Token"
echo "   Token: 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"
echo ""
read -p "按 Enter 继续..."

git push -u origin main
git push origin v0.1.0

echo ""
echo "✅ 完成！"

