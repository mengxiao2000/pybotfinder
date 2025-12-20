"""
命令行工具入口点
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .collector import WeiboCollector
from .feature_extractor import FeatureExtractor
from .model_trainer import ModelTrainer
from .predictor import BotPredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect(args):
    """数据采集命令"""
    if not args.cookie:
        logger.error("需要提供Cookie，使用 --cookie 参数")
        sys.exit(1)
    
    collector = WeiboCollector(
        cookie=args.cookie,
        output_dir=args.output_dir,
        request_sleep=args.sleep
    )
    
    if args.user_id:
        # 采集单个用户
        result = collector.crawl_account(args.user_id, args.limit)
        if result['profile_path'] and result['posts_path']:
            logger.info("采集成功")
        else:
            logger.error("采集失败")
            sys.exit(1)
    elif args.userlist:
        # 批量采集
        stats = collector.crawl_userlist(
            args.userlist,
            weibo_limit=args.limit,
            skip_existing=not args.force
        )
        logger.info(f"采集完成: {stats}")
    else:
        logger.error("需要提供 --user-id 或 --userlist 参数")
        sys.exit(1)


def extract(args):
    """特征提取命令"""
    extractor = FeatureExtractor(
        profiles_dir=args.profiles_dir,
        posts_dir=args.posts_dir
    )
    
    if args.user_id:
        # 提取单个用户特征
        features = extractor.extract_features(args.user_id)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump([features], f, ensure_ascii=False, indent=2)
            logger.info(f"特征已保存到 {args.output}")
        else:
            print(json.dumps(features, ensure_ascii=False, indent=2))
    elif args.userlist:
        # 批量提取
        user_ids = extractor._read_userlist(args.userlist)
        features_list = extractor.extract_features_batch(user_ids)
        
        output_file = args.output or "features.json"
        extractor.save_features(features_list, output_file)
        logger.info(f"已提取 {len(features_list)} 个用户的特征")
    else:
        logger.error("需要提供 --user-id 或 --userlist 参数")
        sys.exit(1)


def train(args):
    """模型训练命令"""
    trainer = ModelTrainer(
        features_file=args.features,
        test_size=args.test_size,
        random_state=args.random_state
    )
    
    results = trainer.train_and_evaluate(
        save_model=True,
        model_path=args.output,
        cv_folds=args.cv_folds
    )
    
    # 保存训练结果
    if args.save_results:
        results_file = args.save_results
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"训练结果已保存到 {results_file}")
    
    logger.info("训练完成")


def predict(args):
    """预测命令"""
    if not Path(args.model).exists():
        logger.error(f"模型文件不存在: {args.model}")
        sys.exit(1)
    
    predictor = BotPredictor(model_path=args.model)
    
    if args.cookie:
        predictor.set_cookie(args.cookie)
    
    if args.user_id:
        # 预测单个用户
        if args.from_file:
            result = predictor.predict_from_features_file(
                args.user_id,
                profiles_dir=args.profiles_dir,
                posts_dir=args.posts_dir
            )
        else:
            if not args.cookie:
                logger.error("从网络采集需要Cookie，使用 --cookie 参数")
                sys.exit(1)
            result = predictor.predict_from_user_id(args.user_id, max_posts=args.limit)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.userlist:
        # 批量预测
        if not args.from_file and not args.cookie:
            logger.error("批量预测需要Cookie或使用 --from-file 参数")
            sys.exit(1)
        
        user_ids = []
        with open(args.userlist, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    user_ids.append(line)
        
        if args.from_file:
            results = []
            for user_id in user_ids:
                result = predictor.predict_from_features_file(
                    user_id,
                    profiles_dir=args.profiles_dir,
                    posts_dir=args.posts_dir
                )
                results.append(result)
        else:
            results = predictor.batch_predict(user_ids, max_posts=args.limit)
        
        output_file = args.output or "predictions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"预测结果已保存到 {output_file}")
    else:
        logger.error("需要提供 --user-id 或 --userlist 参数")
        sys.exit(1)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="pybotfinder - 微博社交机器人检测工具包"
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # collect 命令
    collect_parser = subparsers.add_parser('collect', help='采集微博用户数据')
    collect_parser.add_argument('--user-id', help='用户ID')
    collect_parser.add_argument('--userlist', help='用户列表文件')
    collect_parser.add_argument('--cookie', required=True, help='微博Cookie')
    collect_parser.add_argument('--output-dir', default='dataset', help='输出目录')
    collect_parser.add_argument('--limit', type=int, default=30, help='最多采集的微博数量')
    collect_parser.add_argument('--sleep', type=float, default=0.3, help='请求间隔（秒）')
    collect_parser.add_argument('--force', action='store_true', help='强制重新采集已存在的用户')
    collect_parser.set_defaults(func=collect)
    
    # extract 命令
    extract_parser = subparsers.add_parser('extract', help='提取特征')
    extract_parser.add_argument('--user-id', help='用户ID')
    extract_parser.add_argument('--userlist', help='用户列表文件')
    extract_parser.add_argument('--profiles-dir', default='dataset/profiles_dir', help='Profile数据目录')
    extract_parser.add_argument('--posts-dir', default='dataset/posts_dir', help='Posts数据目录')
    extract_parser.add_argument('--output', help='输出文件')
    extract_parser.set_defaults(func=extract)
    
    # train 命令
    train_parser = subparsers.add_parser('train', help='训练模型')
    train_parser.add_argument('--features', required=True, help='特征文件路径')
    train_parser.add_argument('--output', default='bot_detection_model.pkl', help='模型输出路径')
    train_parser.add_argument('--test-size', type=float, default=0.2, help='测试集比例')
    train_parser.add_argument('--cv-folds', type=int, default=5, help='交叉验证折数')
    train_parser.add_argument('--random-state', type=int, default=42, help='随机种子')
    train_parser.add_argument('--save-results', help='保存训练结果到文件')
    train_parser.set_defaults(func=train)
    
    # predict 命令
    predict_parser = subparsers.add_parser('predict', help='预测')
    predict_parser.add_argument('--user-id', help='用户ID')
    predict_parser.add_argument('--userlist', help='用户列表文件')
    predict_parser.add_argument('--model', required=True, help='模型文件路径')
    predict_parser.add_argument('--cookie', help='微博Cookie（从网络采集时需要）')
    predict_parser.add_argument('--from-file', action='store_true', help='从已有数据文件预测')
    predict_parser.add_argument('--profiles-dir', default='dataset/profiles_dir', help='Profile数据目录')
    predict_parser.add_argument('--posts-dir', default='dataset/posts_dir', help='Posts数据目录')
    predict_parser.add_argument('--limit', type=int, default=30, help='最多采集的微博数量')
    predict_parser.add_argument('--output', help='输出文件（批量预测时）')
    predict_parser.set_defaults(func=predict)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

