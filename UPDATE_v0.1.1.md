# v0.1.1 更新说明

## ✅ 已完成的工作

### 1. 模型训练
- ✅ 从以下文件提取特征并训练模型：
  - `bot.txt` (3845个机器人账号，标签=1)
  - `human.txt` (2270个人类账号，标签=0)
  - `government.txt` (597个政府账号，标签=0)
  - `influencer.txt` (931个影响者账号，标签=0)
  - `media.txt` (781个媒体账号，标签=0)

### 2. 模型性能
- **总样本数**: 8424个用户
- **准确率**: 98.99%
- **F1分数**: 0.9899 (宏平均)
- **测试集表现**:
  - 人类类别: Precision=0.9839, Recall=0.9978, F1=0.9908
  - 机器人类别: Precision=0.9974, Recall=0.9805, F1=0.9889

### 3. 包更新
- ✅ 模型文件 (`bot_detection_model.pkl`, 916KB) 已包含在包中
- ✅ `BotPredictor` 现在默认使用包内模型，无需手动指定路径
- ✅ 版本号更新至 0.1.1
- ✅ 已发布到 PyPI: https://pypi.org/project/pybotfinder/0.1.1/

### 4. 使用方式

#### 安装最新版本
```bash
pip install --upgrade pybotfinder
```

#### 使用默认模型（推荐）
```python
from pybotfinder import BotPredictor

# 使用包内默认模型，无需指定模型路径
predictor = BotPredictor(cookie="your_weibo_cookie")

# 预测用户
result = predictor.predict_from_user_id("user_id")
print(f"预测结果: {result['label']}, 置信度: {result['score']}")
```

#### 使用自定义模型
```python
# 如果需要使用自己的模型
predictor = BotPredictor(
    model_path="path/to/your/model.pkl",
    cookie="your_weibo_cookie"
)
```

## 📦 文件变更

### 新增文件
- `pybotfinder/bot_detection_model.pkl` - 训练好的模型文件
- `train_model.py` - 模型训练脚本
- `CHANGELOG.md` - 更新日志

### 修改文件
- `pybotfinder/__init__.py` - 版本号更新至 0.1.1
- `pybotfinder/predictor.py` - 支持默认使用包内模型
- `MANIFEST.in` - 包含 `.pkl` 文件
- `setup.py` - 版本号更新
- `pyproject.toml` - 版本号更新

## 🚀 GitHub 推送

由于 Git 认证问题，需要手动推送：

```bash
cd /Users/mengxiao/Documents/微博/pybotfinder
git push origin main
git push origin v0.1.1
```

或者使用 GitHub Desktop 推送。

## ✨ 主要改进

1. **开箱即用**: 安装后即可使用，无需额外训练模型
2. **高性能**: 模型准确率达到 98.99%
3. **易用性**: 简化了 `BotPredictor` 的使用方式
4. **完整性**: 包包含所有必需文件，包括模型

## 📊 模型详情

### 最佳参数
- `max_depth`: 20
- `max_features`: 'sqrt'
- `min_samples_leaf`: 2
- `min_samples_split`: 2
- `n_estimators`: 50

### 重要特征（Top 5）
1. `original_ratio`: 0.2041 - 原创微博比例
2. `followers_friends_ratio`: 0.1067 - 粉丝/关注比例
3. `statuses_count`: 0.0927 - 微博总数
4. `std_post_interval`: 0.0907 - 发帖间隔标准差
5. `peak_hourly_posts`: 0.0685 - 峰值小时发帖数

