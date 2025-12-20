# 设置指南

在发布之前，请完成以下设置：

## 1. 更新个人信息

### 在以下文件中更新你的信息：

#### `setup.py`
```python
author="Your Name",
author_email="your.email@example.com",
url="https://github.com/yourusername/pybotfinder",
```

#### `pyproject.toml`
```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

#### `pybotfinder/__init__.py`
```python
__author__ = "Your Name"
__email__ = "your.email@example.com"
```

#### `README.md`
- 更新作者部分
- 更新 GitHub URL（如果有）

## 2. 准备 PyPI Token（用于发布）

### 步骤：

1. 访问 [PyPI](https://pypi.org/) 并注册账号（如果还没有）
2. 登录后，进入 Account settings
3. 滚动到 "API tokens" 部分
4. 点击 "Add API token"
5. 填写：
   - Token name: `pybotfinder`（或任何你喜欢的名字）
   - Scope: 选择 "Entire account" 或 "Project: pybotfinder"
6. 点击 "Add token"
7. **重要**：复制 token（格式类似 `pypi-xxxxxxxxxxxxx`），它只会显示一次！

### 配置认证（两种方式选一种）

#### 方式1：使用配置文件（推荐）

创建或编辑 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-你的token（以pypi-开头）
```

#### 方式2：使用环境变量

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-你的token
```

## 3. 准备 GitHub（用于代码托管）

### 步骤：

1. 在 GitHub 上创建新仓库（例如：`pybotfinder`）
2. 不要初始化 README、.gitignore 或 LICENSE（我们已经有了）

### 连接本地仓库到 GitHub：

```bash
cd pybotfinder
git init
git add .
git commit -m "Initial commit: pybotfinder package"
git branch -M main
git remote add origin https://github.com/yourusername/pybotfinder.git
git push -u origin main
```

## 4. 测试安装

在发布前，先测试本地安装：

```bash
cd pybotfinder
pip install -e .
```

然后测试导入：

```python
python -c "from pybotfinder import BotPredictor; print('Import successful!')"
```

## 5. 构建和测试上传

### 安装构建工具：

```bash
pip install --upgrade build twine
```

### 构建分发包：

```bash
python -m build
```

### 检查分发包：

```bash
twine check dist/*
```

### 测试上传到 TestPyPI：

1. 在 [TestPyPI](https://test.pypi.org/) 注册账号
2. 上传：
   ```bash
   twine upload --repository testpypi dist/*
   ```
3. 测试安装：
   ```bash
   pip install --index-url https://test.pypi.org/simple/ pybotfinder
   ```

## 6. 发布到 PyPI

确认一切正常后，上传到正式 PyPI：

```bash
twine upload dist/*
```

## 7. 创建 GitHub Release

1. 在 GitHub 仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写：
   - Tag: `v0.1.0`
   - Title: `v0.1.0 - Initial Release`
   - Description: 描述这个版本的功能
4. 点击 "Publish release"

## 需要的信息清单

在开始之前，请准备：

- [ ] PyPI 账号（如果没有，需要注册）
- [ ] PyPI API Token（需要从 PyPI 获取）
- [ ] GitHub 账号（如果没有，需要注册）
- [ ] GitHub 仓库 URL（创建仓库后获得）
- [ ] 你的姓名和邮箱（用于作者信息）

## 下一步

完成以上设置后，按照 [PUBLISHING.md](PUBLISHING.md) 中的详细步骤进行发布。

