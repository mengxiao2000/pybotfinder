# 安全修复说明

## 问题

GitHub Secret Scanning 检测到提交中包含 Personal Access Token。

## 已修复

✅ 已从以下文件中移除硬编码的 token：
- `README_GITHUB.md`
- `push_to_github.sh`

## 安全的推送方法

### 方法1：使用环境变量（推荐）

```bash
# 设置环境变量（仅在当前终端会话有效）
export GITHUB_TOKEN=your_token_here

# 运行脚本
./push_to_github.sh
```

### 方法2：使用 GitHub Desktop

1. 打开 GitHub Desktop
2. 添加本地仓库
3. 点击 "Publish repository"
4. GitHub Desktop 会自动处理认证

### 方法3：交互式输入

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder
git push -u origin main
# 当提示输入用户名时：mengxiao2000
# 当提示输入密码时：粘贴你的 token
```

### 方法4：使用 Git Credential Helper

```bash
# 配置 credential helper
git config --global credential.helper osxkeychain

# 推送（会提示输入，之后会保存到 keychain）
git push -u origin main
```

## 重要提示

⚠️ **永远不要**：
- 在代码中硬编码 token
- 将包含 token 的文件提交到 Git
- 在公开仓库中分享 token

✅ **应该**：
- 使用环境变量
- 使用 Git credential helper
- 使用 GitHub Desktop
- 定期轮换 token

## 如果 token 已泄露

如果 token 已经提交到 Git 历史：

1. **立即撤销旧 token**：
   - 访问：https://github.com/settings/tokens
   - 找到并删除泄露的 token

2. **创建新 token**：
   - 创建新的 Personal Access Token
   - 使用新 token 进行后续操作

3. **清理 Git 历史**（如果需要）：
   ```bash
   # 使用 git filter-branch 或 BFG Repo-Cleaner
   # 注意：这会重写 Git 历史
   ```

## 当前状态

- ✅ 硬编码的 token 已从文件中移除
- ✅ .gitignore 已更新，忽略敏感文件
- ✅ 已提交安全修复

现在可以安全地推送到 GitHub 了！

