"""
模型训练与评估模块
使用随机森林模型进行机器人检测，包含交叉验证和网格搜索
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
import joblib

logger = logging.getLogger(__name__)


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, features_file: str = "features.json", 
                 test_size: float = 0.2,
                 random_state: int = 42):
        """
        初始化模型训练器
        
        Args:
            features_file: 特征文件路径
            test_size: 测试集比例（默认0.2，即20%）
            random_state: 随机种子
        """
        self.features_file = Path(features_file)
        self.test_size = test_size
        self.random_state = random_state
        self.model = None
        self.feature_names = None
        self.best_params_ = None
        self.cv_scores_ = None
        
    def load_features(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        加载特征数据
        
        Returns:
            X: 特征矩阵
            y: 标签向量
            feature_names: 特征名称列表
        """
        logger.info(f"加载特征文件: {self.features_file}")
        
        with open(self.features_file, 'r', encoding='utf-8') as f:
            features_list = json.load(f)
        
        logger.info(f"共加载 {len(features_list)} 条记录")
        
        # 提取特征和标签
        X_list = []
        y_list = []
        feature_names = None
        
        for record in features_list:
            # 提取标签
            label = record.get('label')
            if label is None:
                logger.warning(f"跳过无标签记录: {record.get('user_id', 'unknown')}")
                continue
            
            # 提取特征（排除user_id和label）
            feature_dict = {k: v for k, v in record.items() 
                          if k not in ['user_id', 'label']}
            
            if feature_names is None:
                feature_names = sorted(feature_dict.keys())
            
            # 构建特征向量
            feature_vector = [feature_dict.get(name, 0) for name in feature_names]
            X_list.append(feature_vector)
            y_list.append(label)
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        logger.info(f"特征矩阵形状: {X.shape}")
        logger.info(f"标签分布: {np.bincount(y)}")
        
        return X, y, feature_names
    
    def split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        划分训练集和测试集
        
        Args:
            X: 特征矩阵
            y: 标签向量
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        logger.info(f"划分数据集: 训练集 {1-self.test_size:.0%}, 测试集 {self.test_size:.0%}")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y  # 保持类别分布
        )
        
        logger.info(f"训练集大小: {len(X_train)}")
        logger.info(f"测试集大小: {len(X_test)}")
        logger.info(f"训练集标签分布: {np.bincount(y_train)}")
        logger.info(f"测试集标签分布: {np.bincount(y_test)}")
        
        return X_train, X_test, y_train, y_test
    
    def train_with_cv(self, X_train: np.ndarray, y_train: np.ndarray,
                      cv_folds: int = 5) -> Dict[str, Any]:
        """
        使用交叉验证训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练标签
            cv_folds: 交叉验证折数（默认5折）
            
        Returns:
            交叉验证结果字典
        """
        logger.info(f"开始 {cv_folds} 折交叉验证...")
        
        # 定义参数网格
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2']
        }
        
        # 创建基础模型
        base_model = RandomForestClassifier(
            random_state=self.random_state,
            n_jobs=-1,
            class_weight='balanced'  # 处理类别不平衡
        )
        
        # 网格搜索
        logger.info("进行网格搜索...")
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state)
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        # 保存最佳模型和参数
        self.model = grid_search.best_estimator_
        self.best_params_ = grid_search.best_params_
        self.cv_scores_ = grid_search.cv_results_
        
        logger.info(f"最佳参数: {self.best_params_}")
        logger.info(f"最佳交叉验证F1分数: {grid_search.best_score_:.4f}")
        
        # 计算各折的详细分数
        cv_scores = cross_val_score(
            self.model,
            X_train,
            y_train,
            cv=cv,
            scoring='f1'
        )
        
        logger.info(f"交叉验证F1分数: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        return {
            'best_params': self.best_params_,
            'best_cv_score': grid_search.best_score_,
            'cv_scores_mean': cv_scores.mean(),
            'cv_scores_std': cv_scores.std(),
            'cv_scores': cv_scores.tolist()
        }
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        在测试集上评估模型
        
        Args:
            X_test: 测试特征
            y_test: 测试标签
            
        Returns:
            评估结果字典
        """
        if self.model is None:
            raise ValueError("模型尚未训练，请先调用 train_with_cv")
        
        logger.info("在测试集上评估模型...")
        
        # 预测
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # 计算指标
        accuracy = accuracy_score(y_test, y_pred)
        
        # 正负类别的精确率、召回率、F1-score
        precision = precision_score(y_test, y_pred, average=None, zero_division=0)
        recall = recall_score(y_test, y_pred, average=None, zero_division=0)
        f1 = f1_score(y_test, y_pred, average=None, zero_division=0)
        
        # 宏平均和加权平均
        precision_macro = precision_score(y_test, y_pred, average='macro', zero_division=0)
        recall_macro = recall_score(y_test, y_pred, average='macro', zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        precision_weighted = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall_weighted = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        # 混淆矩阵
        cm = confusion_matrix(y_test, y_pred)
        
        # 打印详细报告
        logger.info("\n" + "="*60)
        logger.info("测试集评估结果")
        logger.info("="*60)
        logger.info(f"准确率 (Accuracy): {accuracy:.4f}")
        logger.info(f"\n各类别指标:")
        logger.info(f"  类别 0 (人类):")
        logger.info(f"    精确率 (Precision): {precision[0]:.4f}")
        logger.info(f"    召回率 (Recall): {recall[0]:.4f}")
        logger.info(f"    F1-score: {f1[0]:.4f}")
        logger.info(f"  类别 1 (机器人):")
        logger.info(f"    精确率 (Precision): {precision[1]:.4f}")
        logger.info(f"    召回率 (Recall): {recall[1]:.4f}")
        logger.info(f"    F1-score: {f1[1]:.4f}")
        logger.info(f"\n宏平均 (Macro Average):")
        logger.info(f"  精确率: {precision_macro:.4f}")
        logger.info(f"  召回率: {recall_macro:.4f}")
        logger.info(f"  F1-score: {f1_macro:.4f}")
        logger.info(f"\n加权平均 (Weighted Average):")
        logger.info(f"  精确率: {precision_weighted:.4f}")
        logger.info(f"  召回率: {recall_weighted:.4f}")
        logger.info(f"  F1-score: {f1_weighted:.4f}")
        logger.info(f"\n混淆矩阵:")
        logger.info(f"  {cm}")
        
        # 分类报告
        report = classification_report(y_test, y_pred, target_names=['人类', '机器人'], output_dict=True)
        logger.info(f"\n分类报告:")
        logger.info(classification_report(y_test, y_pred, target_names=['人类', '机器人']))
        
        return {
            'accuracy': accuracy,
            'precision': {
                'class_0': float(precision[0]),
                'class_1': float(precision[1]),
                'macro': float(precision_macro),
                'weighted': float(precision_weighted)
            },
            'recall': {
                'class_0': float(recall[0]),
                'class_1': float(recall[1]),
                'macro': float(recall_macro),
                'weighted': float(recall_weighted)
            },
            'f1_score': {
                'class_0': float(f1[0]),
                'class_1': float(f1[1]),
                'macro': float(f1_macro),
                'weighted': float(f1_weighted)
            },
            'confusion_matrix': cm.tolist(),
            'classification_report': report
        }
    
    def get_feature_importance(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        获取特征重要性
        
        Args:
            top_n: 返回前N个重要特征
            
        Returns:
            特征重要性列表（特征名，重要性分数）
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        if self.feature_names is None:
            raise ValueError("特征名称未设置")
        
        importances = self.model.feature_importances_
        feature_importance = list(zip(self.feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"\n前 {top_n} 个重要特征:")
        for i, (name, importance) in enumerate(feature_importance[:top_n], 1):
            logger.info(f"  {i}. {name}: {importance:.4f}")
        
        return feature_importance[:top_n]
    
    def save_model(self, model_path: str = "bot_detection_model.pkl"):
        """
        保存训练好的模型
        
        Args:
            model_path: 模型保存路径
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'best_params': self.best_params_
        }, model_path)
        
        logger.info(f"模型已保存到: {model_path}")
    
    def load_model(self, model_path: str = "bot_detection_model.pkl"):
        """
        加载已训练的模型
        
        Args:
            model_path: 模型文件路径
        """
        data = joblib.load(model_path)
        self.model = data['model']
        self.feature_names = data['feature_names']
        self.best_params_ = data.get('best_params')
        
        logger.info(f"模型已从 {model_path} 加载")
    
    def train_and_evaluate(self, save_model: bool = True, 
                          model_path: str = "bot_detection_model.pkl",
                          cv_folds: int = 5) -> Dict[str, Any]:
        """
        完整的训练和评估流程
        
        Args:
            save_model: 是否保存模型
            model_path: 模型保存路径
            cv_folds: 交叉验证折数
            
        Returns:
            完整的评估结果字典
        """
        # 1. 加载数据
        X, y, feature_names = self.load_features()
        self.feature_names = feature_names
        
        # 2. 划分数据集
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # 3. 交叉验证训练
        cv_results = self.train_with_cv(X_train, y_train, cv_folds=cv_folds)
        
        # 4. 测试集评估
        test_results = self.evaluate(X_test, y_test)
        
        # 5. 特征重要性
        feature_importance = self.get_feature_importance()
        
        # 6. 保存模型
        if save_model:
            self.save_model(model_path)
        
        # 7. 汇总结果
        results = {
            'cv_results': cv_results,
            'test_results': test_results,
            'feature_importance': [(name, float(imp)) for name, imp in feature_importance],
            'model_path': model_path if save_model else None
        }
        
        return results

