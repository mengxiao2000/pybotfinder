# GitHub 推送指南

## 当前状态
- ✅ 代码已提交到本地仓库
- ✅ 版本标签 v0.1.1 已创建
- ⏳ 等待推送到 GitHub

## 方法1: 使用推送脚本（推荐）

运行推送脚本，按提示操作：

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder
bash push_github.sh
```

脚本会提供3种推送方式供选择。

## 方法2: 手动使用Token推送

### 步骤1: 获取新的Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置：
   - Note: `pybotfinder-push`
   - Expiration: 根据需要选择
   - 权限：勾选 `repo` (全部权限)
4. 点击 "Generate token"
5. **复制token**（只显示一次）

### 步骤2: 使用Token推送

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder

# 替换 YOUR_TOKEN 为你的新token
git remote set-url origin https://mengxiao2000:YOUR_TOKEN@github.com/mengxiao2000/pybotfinder.git

# 推送代码
git push origin main

# 推送标签
git push origin v0.1.1

# 清理URL（安全考虑）
git remote set-url origin https://github.com/mengxiao2000/pybotfinder.git
```

## 方法3: 使用GitHub Desktop

1. 下载安装 GitHub Desktop: https://desktop.github.com/
2. 打开 GitHub Desktop
3. File → Add Local Repository
4. 选择：`/Users/mengxiao/Documents/微博/pybotfinder`
5. 点击 "Publish repository" 或 "Push origin"

## 方法4: 使用GitHub CLI

如果已安装GitHub CLI：

```bash
# 安装（如果未安装）
brew install gh

# 登录
gh auth login

# 推送
cd /Users/mengxiao/Documents/微博/pybotfinder
git push origin main
git push origin v0.1.1
```

## 方法5: 配置SSH Key（长期方案）

### 生成SSH Key
```bash
ssh-keygen -t ed25519 -C "xiaomeng7-c@my.cityu.edu.hk"
```

### 添加SSH Key到GitHub
1. 复制公钥：`cat ~/.ssh/id_ed25519.pub`
2. 访问：https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥并保存

### 使用SSH推送
```bash
cd /Users/mengxiao/Documents/微博/pybotfinder
git remote set-url origin git@github.com:mengxiao2000/pybotfinder.git
git push origin main
git push origin v0.1.1
```

## 验证推送

推送成功后，访问：
- 仓库：https://github.com/mengxiao2000/pybotfinder
- 标签：https://github.com/mengxiao2000/pybotfinder/releases/tag/v0.1.1

## 当前待推送的提交

```
72f1749 chore: 清理文档文件，解决合并冲突
254c052 docs: 添加更新日志和v0.1.1说明文档
ab9a307 v0.1.1: 添加训练好的模型文件，支持开箱即用
```

## 注意事项

1. **Token安全**: 不要在代码中硬编码token
2. **Token权限**: 确保token有 `repo` 权限
3. **Token过期**: 如果token过期，需要生成新的

