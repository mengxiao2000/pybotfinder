#!/usr/bin/env python3
"""
重新训练模型脚本
从用户列表文件提取特征并训练模型
"""

import sys
import logging
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent))

from pybotfinder.feature_extractor import FeatureExtractor
from pybotfinder.model_trainer import ModelTrainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    # 配置路径
    base_dir = Path(__file__).parent.parent
    profiles_dir = base_dir / "pybotfinder_prepare" / "dataset" / "profiles_dir"
    posts_dir = base_dir / "pybotfinder_prepare" / "dataset" / "posts_dir"
    userlist_dir = Path(__file__).parent / "account_list"
    
    # 用户列表文件
    bot_file = userlist_dir / "bot.txt"
    human_file = userlist_dir / "human.txt"
    government_file = userlist_dir / "government.txt"
    influencer_file = userlist_dir / "influencer.txt"
    media_file = userlist_dir / "media.txt"
    
    # 输出文件
    features_output = Path(__file__).parent / "features.json"
    model_output = Path(__file__).parent / "pybotfinder" / "bot_detection_model.pkl"
    results_output = Path(__file__).parent / "training_results.json"
    
    logger.info("="*60)
    logger.info("开始重新训练模型")
    logger.info("="*60)
    
    # Step 1: 提取特征
    logger.info("\n步骤1: 提取特征...")
    extractor = FeatureExtractor(
        profiles_dir=str(profiles_dir),
        posts_dir=str(posts_dir)
    )
    
    # 构建用户列表文件和标签映射
    userlist_files = []
    label_mapping = {}
    
    if bot_file.exists():
        userlist_files.append(str(bot_file))
        label_mapping[bot_file.name] = 1  # 机器人=1
        logger.info(f"  - 机器人样本: {bot_file}")
    
    # 人类样本（标签=0）
    human_files = []
    if human_file.exists():
        human_files.append(human_file)
        label_mapping[human_file.name] = 0
    if government_file.exists():
        human_files.append(government_file)
        label_mapping[government_file.name] = 0
    if influencer_file.exists():
        human_files.append(influencer_file)
        label_mapping[influencer_file.name] = 0
    if media_file.exists():
        human_files.append(media_file)
        label_mapping[media_file.name] = 0
    
    for f in human_files:
        userlist_files.append(str(f))
        logger.info(f"  - 人类样本: {f.name}")
    
    if not userlist_files:
        logger.error("未找到用户列表文件！")
        return
    
    # 提取特征
    features_list = extractor.extract_features_from_userlists(
        userlist_files,
        label_mapping=label_mapping
    )
    
    logger.info(f"\n成功提取 {len(features_list)} 个用户的特征")
    
    # 保存特征
    extractor.save_features(features_list, str(features_output))
    logger.info(f"特征已保存到: {features_output}")
    
    # Step 2: 训练模型
    logger.info("\n步骤2: 训练模型...")
    trainer = ModelTrainer(features_file=str(features_output))
    
    results = trainer.train_and_evaluate(model_path=str(model_output))
    
    # 保存训练结果
    import json
    with open(results_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"训练结果已保存到: {results_output}")
    
    # 打印摘要
    logger.info("\n" + "="*60)
    logger.info("训练完成！")
    logger.info("="*60)
    logger.info(f"模型文件: {model_output}")
    logger.info(f"\n模型性能:")
    logger.info(f"  准确率: {results.get('accuracy', 0):.4f}")
    logger.info(f"  交叉验证F1分数: {results.get('cv_f1_mean', 0):.4f} (±{results.get('cv_f1_std', 0):.4f})")
    logger.info(f"  测试集F1分数 (宏平均): {results.get('test_f1_macro', 0):.4f}")
    logger.info(f"  测试集F1分数 (加权平均): {results.get('test_f1_weighted', 0):.4f}")
    logger.info(f"\n最佳参数:")
    for key, value in results.get('best_params', {}).items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()

