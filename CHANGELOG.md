# Changelog

All notable changes to pybotfinder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2025-12-21

### Fixed
- **Important fix**: Exclude accounts with missing or invalid profile data from training (previously used default zero values)
- Only accounts with valid profile data are now included in the training dataset

### Changed
- Updated training dataset with latest bot and human account lists
- Retrained model with 9,839 valid samples (4,780 bots, 5,059 humans) after excluding 246 accounts with missing profile data
- Model performance:
  - Accuracy: 97.00%
  - F1-score (macro): 0.9699
  - Cross-validation F1-score: 0.9714 (±0.0055)
  - Precision (bots): 99.56%
  - Recall (bots): 94.25%

## [0.3.1] - 2025-12-21

### Changed
- Updated training dataset with latest bot and human account lists
- Fixed collector.py path configuration to use correct account list directory

## [0.3.0] - 2025-12-19

### Added
- Initial release of pybotfinder package
- Bot detection model based on Random Forest
- Data collection tools for Weibo profiles and posts
- Feature extraction pipeline (46 features)
- Model training and evaluation tools
- Command-line interface (CLI)
- Python API for predictions

### Features
- Collect user profiles and recent posts from Weibo
- Extract behavioral and profile features
- Train and evaluate bot detection models
- Predict bot probability for individual users

