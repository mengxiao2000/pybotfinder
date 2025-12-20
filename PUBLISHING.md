# 发布指南

本指南将帮助你将 pybotfinder 发布到 GitHub 和 PyPI。

## 准备工作

### 1. 更新版本号

在发布新版本前，需要更新以下文件中的版本号：

- `setup.py`: `version="0.1.0"`
- `pyproject.toml`: `version = "0.1.0"`
- `pybotfinder/__init__.py`: `__version__ = "0.1.0"`

### 2. 更新作者信息

在以下文件中更新你的信息：

- `setup.py`: `author` 和 `author_email`
- `pyproject.toml`: `authors`
- `README.md`: 作者部分

### 3. 更新 GitHub URL

在 `setup.py` 中更新你的 GitHub 仓库 URL：

```python
url="https://github.com/yourusername/pybotfinder",
```

## 发布到 GitHub

### 1. 初始化 Git 仓库（如果还没有）

```bash
cd pybotfinder
git init
git add .
git commit -m "Initial commit"
```

### 2. 创建 GitHub 仓库

1. 在 GitHub 上创建一个新仓库（例如：`pybotfinder`）
2. 不要初始化 README、.gitignore 或 LICENSE（我们已经有了）

### 3. 连接到远程仓库

```bash
git remote add origin https://github.com/yourusername/pybotfinder.git
git branch -M main
git push -u origin main
```

### 4. 创建 Release

1. 在 GitHub 仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写版本号（例如：`v0.1.0`）
4. 填写 Release 标题和描述
5. 点击 "Publish release"

## 发布到 PyPI

### 1. 安装构建工具

```bash
pip install --upgrade build twine
```

### 2. 构建分发包

```bash
cd pybotfinder
python -m build
```

这会在 `dist/` 目录下生成：
- `pybotfinder-0.1.0.tar.gz` (源码包)
- `pybotfinder-0.1.0-py3-none-any.whl` (wheel包)

### 3. 检查分发包

```bash
twine check dist/*
```

### 4. 测试上传到 TestPyPI（推荐）

首先在 [TestPyPI](https://test.pypi.org/) 注册账号，然后：

```bash
twine upload --repository testpypi dist/*
```

测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ pybotfinder
```

### 5. 上传到 PyPI

#### 5.1 注册 PyPI 账号

1. 访问 [PyPI](https://pypi.org/)
2. 注册账号
3. 验证邮箱

#### 5.2 获取 API Token（推荐）

1. 登录 PyPI
2. 进入 Account settings
3. 滚动到 "API tokens"
4. 点击 "Add API token"
5. 填写描述（例如：`pybotfinder`）
6. 选择 Scope: "Entire account" 或 "Project: pybotfinder"
7. 点击 "Add token"
8. 复制 token（只显示一次，请保存好）

#### 5.3 配置认证

创建或编辑 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-你的token（以pypi-开头）
```

或者使用环境变量：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-你的token
```

#### 5.4 上传

```bash
twine upload dist/*
```

### 6. 验证安装

```bash
pip install pybotfinder
```

## 版本更新流程

1. 更新版本号（在 `setup.py`、`pyproject.toml` 和 `__init__.py` 中）
2. 更新 `CHANGELOG.md`（如果使用）
3. 提交更改：
   ```bash
   git add .
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```
4. 构建和上传：
   ```bash
   python -m build
   twine upload dist/*
   ```

## 常见问题

### Q: 上传时提示 "File already exists"

A: 该版本已经存在于 PyPI。你需要：
- 更新版本号
- 或者删除 PyPI 上的旧版本（不推荐）

### Q: 如何更新已发布的包？

A: 必须使用新的版本号。PyPI 不允许覆盖已发布的版本。

### Q: 忘记密码怎么办？

A: 使用 API Token 代替密码，更安全且方便。

## 安全提示

1. **不要提交敏感信息**：确保 `.pypirc` 和包含 token 的文件在 `.gitignore` 中
2. **使用 API Token**：比密码更安全
3. **测试先行**：先在 TestPyPI 测试，确认无误后再上传到 PyPI

## 参考资源

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI 文档](https://pypi.org/help/)
- [Twine 文档](https://twine.readthedocs.io/)

