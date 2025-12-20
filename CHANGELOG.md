# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-12-20

### Added
- 训练好的模型文件 (`bot_detection_model.pkl`) 包含在包中
- 模型基于 8424 个用户训练（3845个机器人，4579个人类）
- 模型性能：准确率 98.99%，F1分数 0.9899
- `BotPredictor` 现在默认使用包内模型，无需手动指定模型路径

### Changed
- 更新 `BotPredictor.__init__()` 的 `model_path` 参数为可选，默认为 `None`（使用包内模型）
- 更新 `MANIFEST.in` 以包含 `.pkl` 模型文件

### Fixed
- 修复模型文件未包含在分发包中的问题

## [0.1.0] - 2025-12-20

### Added
- 初始版本发布
- 数据采集模块 (`WeiboCollector`)
- 特征提取模块 (`FeatureExtractor`)
- 模型训练模块 (`ModelTrainer`)
- 端到端预测模块 (`BotPredictor`)
- 命令行接口 (`cli.py`)
- 完整的文档和示例

[0.1.1]: https://github.com/mengxiao2000/pybotfinder/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/mengxiao2000/pybotfinder/releases/tag/v0.1.0
