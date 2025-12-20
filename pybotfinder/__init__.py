"""
pybotfinder - 微博社交机器人检测工具包

基于随机森林的微博社交机器人检测系统，实现从数据采集到模型预测的完整流程。
"""

__version__ = "0.1.3"
__author__ = "Xiao MENG"
__email__ = "xiaomeng7-c@my.cityu.edu.hk"

from .collector import WeiboCollector, get_profile, get_recent_weibos, crawl_account
from .feature_extractor import FeatureExtractor
from .model_trainer import ModelTrainer
from .predictor import BotPredictor

__all__ = [
    "WeiboCollector",
    "get_profile",
    "get_recent_weibos",
    "crawl_account",
    "FeatureExtractor",
    "ModelTrainer",
    "BotPredictor",
]

