"""
模型训练脚本
从userlist文件提取特征并训练模型
"""

import argparse
import json
import logging
from pathlib import Path
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from pybotfinder import FeatureExtractor, ModelTrainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="训练机器人检测模型")
    parser.add_argument("--profiles-dir", type=str, default="../pybotfinder_prepare/dataset/profiles_dir",
                       help="Profile数据目录")
    parser.add_argument("--posts-dir", type=str, default="../pybotfinder_prepare/dataset/posts_dir",
                       help="Posts数据目录")
    parser.add_argument("--userlist-dir", type=str, default="..",
                       help="Userlist文件所在目录")
    parser.add_argument("--features-file", type=str, default="features.json",
                       help="特征文件保存路径")
    parser.add_argument("--model-path", type=str, default="pybotfinder/bot_detection_model.pkl",
                       help="模型保存路径")
    parser.add_argument("--test-size", type=float, default=0.2,
                       help="测试集比例（默认0.2）")
    parser.add_argument("--cv-folds", type=int, default=5,
                       help="交叉验证折数（默认5）")
    parser.add_argument("--random-state", type=int, default=42,
                       help="随机种子（默认42）")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("开始模型训练流程")
    logger.info("="*60)
    
    # 1. 提取特征
    logger.info("\n步骤1: 提取特征...")
    
    # 创建特征提取器
    extractor = FeatureExtractor(
        profiles_dir=args.profiles_dir,
        posts_dir=args.posts_dir
    )
    
    # 构建文件路径和标签映射
    userlist_dir = Path(args.userlist_dir)
    label_mapping = {}
    userlist_files = []
    
    # 添加机器人文件（标签=1）
    bot_file = userlist_dir / "bot.txt"
    if bot_file.exists():
        userlist_files.append(str(bot_file))
        label_mapping["bot.txt"] = 1
        logger.info(f"✓ 机器人文件: {bot_file} (标签=1)")
    else:
        logger.warning(f"✗ 文件不存在: {bot_file}")
    
    # 添加人类文件（标签=0）
    human_files = ["human.txt", "government.txt", "influencer.txt", "media.txt"]
    for human_file in human_files:
        file_path = userlist_dir / human_file
        if file_path.exists():
            userlist_files.append(str(file_path))
            label_mapping[human_file] = 0
            logger.info(f"✓ 人类文件: {file_path} (标签=0)")
        else:
            logger.warning(f"✗ 文件不存在: {file_path}")
    
    if not userlist_files:
        logger.error("没有找到任何userlist文件！")
        return
    
    logger.info(f"\n共 {len(userlist_files)} 个文件")
    logger.info("="*60)
    
    # 提取特征
    features_list = extractor.extract_features_from_userlists(
        userlist_files,
        label_mapping=label_mapping
    )
    
    logger.info(f"\n特征提取完成！共提取 {len(features_list)} 个用户的特征")
    
    # 统计标签分布
    label_counts = {}
    for features in features_list:
        label = features.get('label')
        if label is not None:
            label_counts[label] = label_counts.get(label, 0) + 1
    
    logger.info(f"\n标签分布:")
    for label, count in sorted(label_counts.items()):
        label_name = "机器人" if label == 1 else "人类"
        logger.info(f"  {label_name} (标签={label}): {count} 个用户")
    
    # 保存特征
    features_path = Path(args.features_file)
    extractor.save_features(features_list, str(features_path))
    logger.info(f"\n✅ 特征已保存到: {features_path}")
    
    # 2. 训练模型
    logger.info("\n" + "="*60)
    logger.info("步骤2: 训练模型...")
    logger.info("="*60)
    
    # 创建训练器
    trainer = ModelTrainer(
        features_file=str(features_path),
        test_size=args.test_size,
        random_state=args.random_state
    )
    
    # 训练和评估
    results = trainer.train_and_evaluate(
        save_model=True,
        model_path=args.model_path,
        cv_folds=args.cv_folds
    )
    
    logger.info(f"\n✅ 模型已保存到: {args.model_path}")
    
    # 打印摘要
    logger.info("\n" + "="*60)
    logger.info("训练摘要")
    logger.info("="*60)
    logger.info(f"最佳参数: {results['cv_results']['best_params']}")
    logger.info(f"交叉验证F1分数: {results['cv_results']['best_cv_score']:.4f}")
    logger.info(f"测试集准确率: {results['test_results']['accuracy']:.4f}")
    logger.info(f"测试集F1分数 (宏平均): {results['test_results']['f1_score']['macro']:.4f}")
    logger.info(f"测试集F1分数 (加权平均): {results['test_results']['f1_score']['weighted']:.4f}")
    logger.info("="*60)
    
    logger.info("\n🎉 模型训练完成！")


if __name__ == "__main__":
    main()
