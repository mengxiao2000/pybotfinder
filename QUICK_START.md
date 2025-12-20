# 快速发布指南

所有个人信息已配置完成！现在你可以直接发布到 PyPI 和 GitHub。

## ✅ 已完成的配置

- ✅ 个人信息已更新（Xiao MENG, xiaomeng7-c@my.cityu.edu.hk）
- ✅ GitHub URL 已更新（https://github.com/mengxiao2000/pybotfinder）
- ✅ PyPI Token 已配置（.pypirc 文件）

## 🚀 发布步骤

### 1. 安装构建工具

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder
pip install --upgrade build twine
```

### 2. 构建分发包

```bash
python -m build
```

这会在 `dist/` 目录下生成：
- `pybotfinder-0.1.0.tar.gz` (源码包)
- `pybotfinder-0.1.0-py3-none-any.whl` (wheel包)

### 3. 检查分发包

```bash
twine check dist/*
```

### 4. 测试上传到 TestPyPI（推荐先测试）

```bash
twine upload --repository testpypi dist/*
```

然后测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ pybotfinder
```

### 5. 上传到正式 PyPI

确认测试无误后，上传到正式 PyPI：

```bash
twine upload dist/*
```

### 6. 初始化 Git 并推送到 GitHub

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: pybotfinder v0.1.0"

# 添加远程仓库
git remote add origin https://github.com/mengxiao2000/pybotfinder.git

# 推送到 GitHub
git branch -M main
git push -u origin main

# 创建标签
git tag v0.1.0
git push origin v0.1.0
```

### 7. 创建 GitHub Release

1. 访问 https://github.com/mengxiao2000/pybotfinder
2. 点击 "Releases" → "Create a new release"
3. 填写：
   - Tag: `v0.1.0`
   - Title: `v0.1.0 - Initial Release`
   - Description: 
     ```
     ## 初始版本发布
     
     - 数据采集模块
     - 特征提取模块（49个特征）
     - 模型训练模块（随机森林）
     - 预测模块
     - 命令行工具
     ```
4. 点击 "Publish release"

## 📝 验证安装

发布后，验证安装：

```bash
pip install pybotfinder
python -c "from pybotfinder import BotPredictor; print('安装成功！')"
```

## ⚠️ 注意事项

1. **.pypirc 文件安全**: `.pypirc` 文件包含你的 PyPI token，请确保：
   - 不要提交到 Git（已在 .gitignore 中）
   - 不要分享给他人
   - 如果泄露，立即在 PyPI 上撤销并重新生成 token

2. **版本号**: 每次发布新版本时，需要更新：
   - `setup.py` 中的 `version`
   - `pyproject.toml` 中的 `version`
   - `pybotfinder/__init__.py` 中的 `__version__`

3. **测试优先**: 建议先在 TestPyPI 测试，确认无误后再发布到正式 PyPI

## 🎉 完成！

发布完成后，你的包就可以通过以下方式安装：

```bash
pip install pybotfinder
```

祝发布顺利！

