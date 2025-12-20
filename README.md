# pybotfinder

微博社交机器人检测工具包 - Weibo Social Bot Detection Toolkit

基于随机森林的微博社交机器人检测系统，实现从数据采集到模型预测的完整流程。

## 功能特性

- 🔍 **数据采集**: 自动采集微博用户Profile和Posts数据
- 🎯 **特征提取**: 提取49个Profile-level和Posts-level特征
- 🤖 **模型训练**: 使用随机森林模型，支持5折交叉验证和网格搜索
- 📊 **端到端预测**: 从用户ID到预测结果的完整流程
- 🚀 **易于使用**: 提供Python API和命令行工具

## 安装

### 从PyPI安装（发布后）

```bash
pip install pybotfinder
```

### 从源码安装

```bash
git clone https://github.com/yourusername/pybotfinder.git
cd pybotfinder
pip install -e .
```

## 快速开始

### Python API使用

```python
from pybotfinder import BotPredictor, WeiboCollector, FeatureExtractor, ModelTrainer

# 1. 数据采集
collector = WeiboCollector(cookie="YOUR_WEIBO_COOKIE")
collector.crawl_account("1042567781", weibo_limit=30)

# 2. 特征提取
extractor = FeatureExtractor()
features = extractor.extract_features("1042567781")

# 3. 模型训练
trainer = ModelTrainer(features_file="features.json")
results = trainer.train_and_evaluate()

# 4. 预测
predictor = BotPredictor(model_path="bot_detection_model.pkl", cookie="YOUR_COOKIE")
result = predictor.predict_from_user_id("1042567781")
print(f"预测结果: {result['prediction']['label_name']}")
```

### 命令行使用

```bash
# 数据采集
pybotfinder-collect --user-id 1042567781 --cookie "YOUR_COOKIE"

# 特征提取
pybotfinder-extract --user-id 1042567781 --output features.json

# 模型训练
pybotfinder-train --features features.json --output model.pkl

# 预测
pybotfinder-predict --user-id 1042567781 --model model.pkl --cookie "YOUR_COOKIE"
```

## 核心模块

### 1. WeiboCollector - 数据采集模块

采集用户Profile信息和最近的微博。

```python
from pybotfinder import WeiboCollector

collector = WeiboCollector(cookie="YOUR_COOKIE")
collector.crawl_account("1042567781", weibo_limit=30)
```

### 2. FeatureExtractor - 特征提取模块

提取49个特征，包括：
- **Profile-level特征** (23个): 昵称、描述、性别、粉丝/关注、统计信息等
- **Posts-level特征** (26个): 帖子统计、原创内容特征、时间特征、地理位置等

```python
from pybotfinder import FeatureExtractor

extractor = FeatureExtractor()
features = extractor.extract_features("1042567781")
```

### 3. ModelTrainer - 模型训练模块

使用随机森林模型进行训练，支持：
- 5折交叉验证
- 网格搜索最优超参数
- 完整的评估指标

```python
from pybotfinder import ModelTrainer

trainer = ModelTrainer(features_file="features.json")
results = trainer.train_and_evaluate()
```

### 4. BotPredictor - 预测模块

端到端预测，支持：
- 从已有数据文件预测（不需要Cookie）
- 从网络实时采集预测（需要Cookie）
- 批量预测

```python
from pybotfinder import BotPredictor

predictor = BotPredictor(model_path="bot_detection_model.pkl", cookie="YOUR_COOKIE")
result = predictor.predict_from_user_id("1042567781")
```

## 模型性能

根据实际训练结果：

- **准确率**: 99.67%
- **交叉验证F1**: 0.9970
- **测试集F1 (宏平均)**: 0.9966
- **测试集F1 (加权平均)**: 0.9967

### 各类别性能

- **人类 (类别0)**:
  - 精确率: 1.0000
  - 召回率: 0.9920
  - F1-score: 0.9960

- **机器人 (类别1)**:
  - 精确率: 0.9945
  - 召回率: 1.0000
  - F1-score: 0.9972

## 特征说明

### Profile-level特征 (23个)

- 昵称特征: 长度、数字/字母数量、特殊字符
- 描述特征: 长度、敏感词、URL、@、#、数字、字母、特殊字符
- 基本统计: 性别、粉丝数、关注数、粉丝关注比、微博数
- 互动统计: 评论数、点赞数、转发数
- 视觉特征: 头像/封面是否默认

### Posts-level特征 (26个)

- 基本统计: 帖子数量、原创比例
- 原创内容特征: 文本长度、标点、图片、视频、链接、@、# 的均值和标准差
- 时间特征: 发布间隔、峰值发布数量
- 其他: 地理位置比例、转发用户信息熵

## 依赖包

- `requests>=2.31.0` - HTTP请求
- `scikit-learn>=1.3.0` - 机器学习
- `numpy>=1.24.0` - 数值计算
- `pandas>=2.0.0` - 数据处理
- `joblib>=1.3.0` - 模型序列化

## 注意事项

1. **Cookie设置**: 从网络采集数据需要有效的微博Cookie
2. **数据格式**: 确保数据格式与训练时一致
3. **模型文件**: 预测前确保模型文件存在
4. **特征顺序**: 预测时特征顺序必须与训练时一致

## 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/pybotfinder.git
cd pybotfinder

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black pybotfinder/
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Xiao MENG - xiaomeng7-c@my.cityu.edu.hk

## 致谢

感谢所有为本项目做出贡献的开发者！
