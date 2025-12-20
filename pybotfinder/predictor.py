"""
端到端预测模块
整合数据采集、特征提取和模型预测，实现完整的机器人检测流程
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import tempfile
import shutil

from .collector import WeiboCollector
from .feature_extractor import FeatureExtractor
import joblib
import numpy as np

logger = logging.getLogger(__name__)


class BotPredictor:
    """机器人检测预测器"""
    
    def __init__(self, model_path: str = "bot_detection_model.pkl",
                 cookie: Optional[str] = None):
        """
        初始化预测器
        
        Args:
            model_path: 训练好的模型文件路径
            cookie: 微博Cookie（用于数据采集）
        """
        self.model_path = Path(model_path)
        self.cookie = cookie
        self.model = None
        self.feature_names = None
        self.best_params = None
        
        # 创建collector（如果需要）
        self.collector = None
        if cookie:
            self.collector = WeiboCollector(cookie=cookie)
        
        # 加载模型
        self._load_model()
    
    def _load_model(self):
        """加载训练好的模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        logger.info(f"加载模型: {self.model_path}")
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.feature_names = data['feature_names']
        self.best_params = data.get('best_params')
        
        logger.info(f"模型加载成功，特征数量: {len(self.feature_names)}")
    
    def set_cookie(self, cookie: str):
        """
        设置Cookie
        
        Args:
            cookie: 微博Cookie字符串
        """
        self.cookie = cookie
        self.collector = WeiboCollector(cookie=cookie)
        logger.info("Cookie已设置")
    
    def collect_user_data(self, user_id: str, max_posts: int = 30,
                          temp_dir: Optional[str] = None) -> Tuple[Optional[Dict], Optional[list]]:
        """
        采集用户数据
        
        Args:
            user_id: 用户ID
            max_posts: 最多采集的帖子数量
            temp_dir: 临时目录（如果为None，使用系统临时目录）
            
        Returns:
            (profile_data, posts_data) 元组
        """
        if not self.collector:
            raise ValueError("需要提供Cookie才能采集数据，请使用 set_cookie() 方法设置")
        
        logger.info(f"开始采集用户 {user_id} 的数据...")
        
        # 创建临时目录
        if temp_dir is None:
            temp_dir_obj = tempfile.mkdtemp(prefix="pybotfinder_")
            cleanup_temp = True
        else:
            temp_dir_obj = Path(temp_dir)
            temp_dir_obj.mkdir(parents=True, exist_ok=True)
            cleanup_temp = False
        
        try:
            profiles_dir = Path(temp_dir_obj) / "profiles_dir"
            posts_dir = Path(temp_dir_obj) / "posts_dir"
            profiles_dir.mkdir(parents=True, exist_ok=True)
            posts_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用collector采集数据
            profile_path = str(profiles_dir / f"{user_id}.json")
            posts_path = str(posts_dir / f"{user_id}.json")
            
            # 采集profile
            profile_file = self.collector.get_profile(user_id, save_path=profile_path)
            if profile_file and Path(profile_file).exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            else:
                profile_data = None
            
            # 采集posts
            posts_file = self.collector.get_recent_weibos(user_id, limit=max_posts, save_path=posts_path)
            if posts_file and Path(posts_file).exists():
                with open(posts_file, 'r', encoding='utf-8') as f:
                    posts_data = json.load(f)
            else:
                posts_data = None
            
            if profile_data is None:
                logger.warning(f"用户 {user_id} 的profile数据采集失败")
            else:
                logger.info(f"Profile数据采集成功")
            
            if posts_data is None or len(posts_data) == 0:
                logger.warning(f"用户 {user_id} 的posts数据采集失败或为空")
            else:
                logger.info(f"Posts数据采集成功，共 {len(posts_data)} 条")
            
            return profile_data, posts_data
            
        except Exception as e:
            logger.error(f"采集用户数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
        finally:
            # 清理临时目录
            if cleanup_temp and Path(temp_dir_obj).exists():
                shutil.rmtree(temp_dir_obj)
                logger.debug(f"已清理临时目录: {temp_dir_obj}")
    
    def extract_features(self, profile_data: Optional[Dict], 
                        posts_data: Optional[list]) -> Dict[str, Any]:
        """
        提取用户特征
        
        Args:
            profile_data: Profile数据
            posts_data: Posts数据
            
        Returns:
            特征字典
        """
        logger.info("提取用户特征...")
        
        # 创建临时特征提取器
        extractor = FeatureExtractor()
        
        # 提取profile特征
        profile_features = extractor.extract_profile_features(profile_data)
        
        # 提取posts特征
        posts_features = extractor.extract_posts_features(posts_data)
        
        # 合并特征
        all_features = {**profile_features, **posts_features}
        
        logger.info(f"特征提取完成，共 {len(all_features)} 个特征")
        
        return all_features
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用模型进行预测
        
        Args:
            features: 特征字典
            
        Returns:
            预测结果字典，包含：
            - label: 预测标签 (0=人类, 1=机器人)
            - probability: 预测概率
            - probability_human: 人类概率
            - probability_bot: 机器人概率
        """
        if self.model is None:
            raise ValueError("模型未加载")
        
        if self.feature_names is None:
            raise ValueError("特征名称未设置")
        
        logger.info("进行模型预测...")
        
        # 构建特征向量（按照训练时的特征顺序）
        feature_vector = []
        for name in self.feature_names:
            value = features.get(name, 0)
            # 确保是数值类型
            try:
                feature_vector.append(float(value))
            except (ValueError, TypeError):
                feature_vector.append(0.0)
        
        X = np.array([feature_vector])
        
        # 预测
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        result = {
            'label': int(prediction),
            'label_name': '机器人' if prediction == 1 else '人类',
            'probability': float(probabilities[prediction]),
            'probability_human': float(probabilities[0]),
            'probability_bot': float(probabilities[1]),
            'confidence': '高' if max(probabilities) > 0.8 else '中' if max(probabilities) > 0.6 else '低'
        }
        
        logger.info(f"预测结果: {result['label_name']} (概率: {result['probability']:.4f})")
        
        return result
    
    def predict_from_user_id(self, user_id: str, max_posts: int = 30) -> Dict[str, Any]:
        """
        从用户ID进行端到端预测
        
        Args:
            user_id: 用户ID
            max_posts: 最多采集的帖子数量
            
        Returns:
            完整的预测结果，包含：
            - user_id: 用户ID
            - prediction: 预测结果
            - features: 提取的特征（可选）
        """
        logger.info("="*60)
        logger.info(f"开始端到端预测: 用户 {user_id}")
        logger.info("="*60)
        
        # 1. 采集数据
        profile_data, posts_data = self.collect_user_data(user_id, max_posts=max_posts)
        
        if profile_data is None and (posts_data is None or len(posts_data) == 0):
            return {
                'user_id': user_id,
                'success': False,
                'error': '数据采集失败，无法进行预测'
            }
        
        # 2. 提取特征
        features = self.extract_features(profile_data, posts_data)
        
        # 3. 预测
        prediction = self.predict(features)
        
        # 4. 返回结果
        result = {
            'user_id': user_id,
            'success': True,
            'prediction': prediction,
            'features_count': len(features),
            'posts_collected': len(posts_data) if posts_data else 0
        }
        
        logger.info("="*60)
        logger.info("预测完成")
        logger.info("="*60)
        
        return result
    
    def predict_from_features_file(self, user_id: str, 
                                   profiles_dir: str = "dataset/profiles_dir",
                                   posts_dir: str = "dataset/posts_dir") -> Dict[str, Any]:
        """
        从已采集的数据文件进行预测（不需要Cookie）
        
        Args:
            user_id: 用户ID
            profiles_dir: Profile数据目录
            posts_dir: Posts数据目录
            
        Returns:
            预测结果
        """
        logger.info(f"从已有数据预测用户 {user_id}...")
        
        # 创建特征提取器
        extractor = FeatureExtractor(
            profiles_dir=profiles_dir,
            posts_dir=posts_dir
        )
        
        # 提取特征
        features = extractor.extract_features(user_id)
        
        # 预测
        prediction = self.predict(features)
        
        return {
            'user_id': user_id,
            'success': True,
            'prediction': prediction,
            'features_count': len(features)
        }
    
    def batch_predict(self, user_ids: list, max_posts: int = 30) -> list:
        """
        批量预测多个用户
        
        Args:
            user_ids: 用户ID列表
            max_posts: 最多采集的帖子数量
            
        Returns:
            预测结果列表
        """
        results = []
        
        for idx, user_id in enumerate(user_ids, 1):
            logger.info(f"\n处理用户 {idx}/{len(user_ids)}: {user_id}")
            try:
                result = self.predict_from_user_id(user_id, max_posts=max_posts)
                results.append(result)
            except Exception as e:
                logger.error(f"预测用户 {user_id} 时出错: {e}")
                results.append({
                    'user_id': user_id,
                    'success': False,
                    'error': str(e)
                })
        
        return results

