# Changelog

所有重要的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-01-XX

### 新增
- 初始版本发布
- 数据采集模块 (`WeiboCollector`)
- 特征提取模块 (`FeatureExtractor`)
- 模型训练模块 (`ModelTrainer`)
- 预测模块 (`BotPredictor`)
- 命令行工具 (CLI)
- 完整的文档和示例

### 功能
- 支持采集微博用户Profile和Posts数据
- 提取49个Profile-level和Posts-level特征
- 使用随机森林模型进行机器人检测
- 支持5折交叉验证和网格搜索
- 端到端预测流程
- 批量处理支持

### 性能
- 准确率: 99.67%
- 交叉验证F1: 0.9970
- 测试集F1 (宏平均): 0.9966

