"""
特征提取模块
从采集的原始JSON数据中提取用于机器人检测的特征
"""

import json
import re
import math
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics
import logging

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy未安装，峰度和偏度特征将被跳过。请运行: pip install scipy")

logger = logging.getLogger(__name__)

# 尝试导入SnowNLP
try:
    from snownlp import SnowNLP
    SNOWNLP_AVAILABLE = True
except ImportError:
    SNOWNLP_AVAILABLE = False
    logger.warning("SnowNLP未安装，情感特征将被跳过。请运行: pip install snownlp")

# 敏感词列表（示例，可以根据需要扩展）
SENSITIVE_WORDS = [
    '广告', '推广', '营销', '代理', '代购', '刷', '刷单', '刷粉',
    '兼职', '赚钱', '投资', '理财', '贷款', '借款', '信用卡'
]


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self, profiles_dir: str = "dataset/profiles_dir", 
                 posts_dir: str = "dataset/posts_dir"):
        """
        初始化特征提取器
        
        Args:
            profiles_dir: profile数据目录
            posts_dir: posts数据目录
        """
        self.profiles_dir = Path(profiles_dir)
        self.posts_dir = Path(posts_dir)
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        加载用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            包含profile和posts的字典
        """
        result = {"profile": None, "posts": None}
        
        # 加载profile
        profile_file = self.profiles_dir / f"{user_id}.json"
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    result["profile"] = json.load(f)
            except Exception as e:
                logger.warning(f"加载profile失败 {user_id}: {e}")
        
        # 加载posts
        posts_file = self.posts_dir / f"{user_id}.json"
        if posts_file.exists():
            try:
                with open(posts_file, 'r', encoding='utf-8') as f:
                    result["posts"] = json.load(f)
            except Exception as e:
                logger.warning(f"加载posts失败 {user_id}: {e}")
        
        return result
    
    def extract_profile_features(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取profile-level特征
        
        Args:
            profile_data: profile原始JSON数据
            
        Returns:
            特征字典
        """
        features = {}
        
        try:
            # 获取用户信息
            user = None
            if profile_data and 'data' in profile_data:
                user = profile_data['data'].get('user', {})
            
            if not user:
                # 如果结构不同，尝试其他路径
                if 'data' in profile_data and 'userInfo' in profile_data['data']:
                    user = profile_data['data']['userInfo']
            
            if not user:
                logger.warning("无法找到用户信息")
                return self._get_default_profile_features()
            
            # 昵称相关特征（只保留最重要的）
            screen_name = str(user.get('screen_name', '') or user.get('name', '') or '')
            features['screen_name_length'] = len(screen_name)
            features['screen_name_digit_count'] = len(re.findall(r'\d', screen_name))
            
            # 描述相关特征
            description = str(user.get('description', '') or user.get('desc', '') or '')
            features['description_length'] = len(description)
            features['description_has_sensitive_word'] = 1 if description and any(word in description for word in SENSITIVE_WORDS) else 0

            # 性别特征（只保留未知性别，因为机器人可能更倾向于不设置性别）
            gender = str(user.get('gender', 'n') or 'n')
            features['gender_n'] = 1 if gender == 'n' else 0
            
            # 粉丝和关注数
            followers_count = self._safe_int(user.get('followers_count', 0))
            friends_count = self._safe_int(user.get('friends_count', 0) or user.get('follow_count', 0))
            features['followers_count'] = followers_count
            features['friends_count'] = friends_count
            features['followers_friends_ratio'] = followers_count / friends_count if friends_count > 0 else 0
            
            # 微博数
            statuses_count = self._safe_int(user.get('statuses_count', 0))
            features['statuses_count'] = statuses_count
            
            # 头像是否默认（移除封面图特征）
            profile_image_url = str(user.get('profile_image_url', '') or user.get('avatar_hd', '') or '')
            features['is_default_avatar'] = 1 if 'default' in profile_image_url.lower() or not profile_image_url else 0
            
        except Exception as e:
            logger.error(f"提取profile特征时出错: {e}")
            return self._get_default_profile_features()
        
        return features
    
    def extract_posts_features(self, posts_data: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        提取posts-level特征
        
        Args:
            posts_data: posts原始JSON列表
            
        Returns:
            特征字典
        """
        features = {}
        
        if posts_data is None or not isinstance(posts_data, list) or len(posts_data) == 0:
            return self._get_default_posts_features()
        
        try:
            # 基本统计
            features['posts_count'] = len(posts_data)
            
            # 区分原创和转发
            original_posts = []
            repost_posts = []
            
            for post in posts_data:
                if post is None or not isinstance(post, dict):
                    continue
                # 判断是否为转发（通过retweeted_status字段）
                retweeted_status = post.get('retweeted_status')
                if retweeted_status is not None and retweeted_status:
                    # 有retweeted_status且不为空，说明是转发
                    repost_posts.append(post)
                else:
                    # 没有retweeted_status或为空，说明是原创
                    original_posts.append(post)
            
            features['original_ratio'] = len(original_posts) / len(posts_data) if posts_data else 0
            
            # 原创帖子的内容特征
            if original_posts:
                original_features = self._extract_original_posts_features(original_posts)
                features.update(original_features)
            else:
                # 如果没有原创帖子，使用默认值
                original_features = self._get_default_original_posts_features()
                features.update(original_features)
            
            # 时间相关特征
            time_features = self._extract_time_features(posts_data)
            features.update(time_features)
            
            # 地理位置特征
            location_features = self._extract_location_features(posts_data)
            features.update(location_features)
            
            # 转发用户信息熵
            repost_entropy = self._calculate_repost_user_entropy(repost_posts)
            features['repost_user_entropy'] = repost_entropy
            
            # 情感特征（基于SnowNLP）- 原创和转发分开计算
            sentiment_features = self._extract_sentiment_features(original_posts, repost_posts)
            features.update(sentiment_features)
            
            # 词汇多样性特征
            diversity_features = self._extract_vocabulary_diversity_features(original_posts, repost_posts)
            features.update(diversity_features)
            
        except Exception as e:
            import traceback
            logger.error(f"提取posts特征时出错: {e}")
            logger.error(traceback.format_exc())
            return self._get_default_posts_features()
        
        return features
    
    def _extract_original_posts_features(self, original_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取原创帖子的特征"""
        features = {}
        
        # 内容长度
        text_lengths = []
        punctuation_counts = []
        pic_counts = []
        video_counts = []
        # 互动数据
        likes_counts = []
        reposts_counts = []
        comments_counts = []
        
        for post in original_posts:
            # 获取文本内容
            text = str(post.get('text_raw', '') or post.get('text', '') or '')
            # 清理HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            text_lengths.append(len(text))
            punctuation_counts.append(len(re.findall(r'[，。！？、；：""''（）【】]', text)))
            
            # 图片数量
            pic_num = self._safe_int(post.get('pic_num', 0))
            if pic_num == 0 and post.get('pic_ids'):
                pic_num = len(post['pic_ids']) if isinstance(post['pic_ids'], list) else 1
            pic_counts.append(pic_num)
            
            # 视频数量（检查是否有视频相关字段）
            has_video = 1 if post.get('page_info') or post.get('video') or post.get('media_info') else 0
            video_counts.append(has_video)
            
            # 点赞、转发、评论数
            likes_count = self._safe_int(post.get('attitudes_count', 0) or post.get('like_count', 0))
            reposts_count = self._safe_int(post.get('reposts_count', 0) or post.get('repost_count', 0))
            comments_count = self._safe_int(post.get('comments_count', 0) or post.get('comment_count', 0))
            
            likes_counts.append(likes_count)
            reposts_counts.append(reposts_count)
            comments_counts.append(comments_count)
        
        # 计算均值和标准差（只保留重要的特征）
        features['avg_text_length_original'] = statistics.mean(text_lengths) if text_lengths else 0
        
        features['avg_punctuation_count_original'] = statistics.mean(punctuation_counts) if punctuation_counts else 0
        features['std_punctuation_count_original'] = statistics.stdev(punctuation_counts) if len(punctuation_counts) > 1 else 0
        
        features['avg_pic_count_original'] = statistics.mean(pic_counts) if pic_counts else 0
        
        features['avg_video_count_original'] = statistics.mean(video_counts) if video_counts else 0
        features['std_video_count_original'] = statistics.stdev(video_counts) if len(video_counts) > 1 else 0
        
        # 互动数据的均值和标准差
        features['avg_likes_original'] = statistics.mean(likes_counts) if likes_counts else 0
        features['std_likes_original'] = statistics.stdev(likes_counts) if len(likes_counts) > 1 else 0
        
        features['avg_reposts_original'] = statistics.mean(reposts_counts) if reposts_counts else 0
        features['std_reposts_original'] = statistics.stdev(reposts_counts) if len(reposts_counts) > 1 else 0
        
        features['avg_comments_original'] = statistics.mean(comments_counts) if comments_counts else 0
        features['std_comments_original'] = statistics.stdev(comments_counts) if len(comments_counts) > 1 else 0
        
        # 词汇多样性：计算原创内容的词汇多样性
        original_texts = []
        for post in original_posts:
            text = str(post.get('text_raw', '') or post.get('text', '') or '')
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'http[s]?://\S+', '', text)
            text = re.sub(r'@\w+', '', text)
            text = re.sub(r'#.*?#', '', text)
            text = text.strip()
            if text:
                original_texts.append(text)
        
        if original_texts:
            # 将所有原创文本拼接
            combined_text = ' '.join(original_texts)
            features['vocabulary_diversity_original'] = self._calculate_vocabulary_diversity(combined_text)
        else:
            features['vocabulary_diversity_original'] = 0.0
        
        return features
    
    def _calculate_vocabulary_diversity(self, text: str) -> float:
        """计算词汇多样性：unique词语数 / 总词语数"""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # 使用正则表达式提取中文词语和英文单词
        # 中文：连续的中文字符作为一个词
        # 英文：连续的字母作为一个词
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        
        if not words:
            return 0.0
        
        total_words = len(words)
        unique_words = len(set(words))
        
        # 词汇多样性 = unique词语数 / 总词语数
        diversity = unique_words / total_words if total_words > 0 else 0.0
        
        return diversity
    
    def _extract_vocabulary_diversity_features(self, original_posts: List[Dict[str, Any]], 
                                               repost_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取词汇多样性特征（原创和转发评价分开）"""
        features = {}
        
        # 原创内容的词汇多样性（已经在_extract_original_posts_features中计算）
        # 这里只需要计算转发评价的词汇多样性
        
        # 提取所有转发评价文本
        repost_comment_texts = []
        for post in repost_posts:
            comment_text = self._extract_repost_comment_text(post)
            if comment_text:
                repost_comment_texts.append(comment_text)
        
        if repost_comment_texts:
            # 将所有转发评价文本拼接
            combined_repost_text = ' '.join(repost_comment_texts)
            features['vocabulary_diversity_repost'] = self._calculate_vocabulary_diversity(combined_repost_text)
        else:
            features['vocabulary_diversity_repost'] = 0.0
        
        return features
    
    def _extract_hour_distribution_features(self, timestamps: List[float]) -> Dict[str, Any]:
        """提取24小时分布的统计特征（均值、标准差、峰度、偏度）"""
        features = {}
        
        if not timestamps:
            return {
                'hour_distribution_mean': 0.0,
                'hour_distribution_std': 0.0,
                'hour_distribution_kurtosis': 0.0,
                'hour_distribution_skewness': 0.0,
            }
        
        # 提取每个帖子的发布小时（0-23）
        hours = []
        for ts in timestamps:
            dt = datetime.fromtimestamp(ts)
            hours.append(dt.hour)
        
        if not hours:
            return {
                'hour_distribution_mean': 0.0,
                'hour_distribution_std': 0.0,
                'hour_distribution_kurtosis': 0.0,
                'hour_distribution_skewness': 0.0,
            }
        
        # 计算24小时分布（每个小时的发帖数）
        hour_counts = [0] * 24
        for hour in hours:
            hour_counts[hour] += 1
        
        # 计算均值、标准差
        features['hour_distribution_mean'] = statistics.mean(hours) if hours else 0.0
        features['hour_distribution_std'] = statistics.stdev(hours) if len(hours) > 1 else 0.0
        
        # 计算峰度和偏度（需要scipy）
        if SCIPY_AVAILABLE and len(hours) > 3:
            # 使用小时分布数据计算峰度和偏度
            features['hour_distribution_kurtosis'] = float(stats.kurtosis(hour_counts))
            features['hour_distribution_skewness'] = float(stats.skew(hour_counts))
        else:
            features['hour_distribution_kurtosis'] = 0.0
            features['hour_distribution_skewness'] = 0.0
        
        return features
    
    def _extract_time_features(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取时间相关特征"""
        features = {}
        
        # 解析发布时间
        timestamps = []
        for post in posts_data:
            if post is None or not isinstance(post, dict):
                continue
            created_at = post.get('created_at', '')
            if created_at:
                try:
                    # 解析时间字符串，格式可能是 "Mon Dec 15 13:21:39 +0800 2025"
                    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                    timestamps.append(dt.timestamp())
                except:
                    try:
                        # 尝试其他格式
                        dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        timestamps.append(dt.timestamp())
                    except:
                        pass
        
        if len(timestamps) < 2:
            features['avg_post_interval'] = 0
            features['std_post_interval'] = 0
            features['peak_hourly_posts'] = len(timestamps)
            features['peak_daily_posts'] = len(timestamps)
            features['avg_daily_posts'] = len(timestamps)  # 如果只有1个或0个帖子，平均每天发帖数就是帖子数
            features['std_daily_posts'] = 0
        else:
            # 计算时间间隔
            intervals = []
            sorted_timestamps = sorted(timestamps)
            for i in range(1, len(sorted_timestamps)):
                interval = sorted_timestamps[i] - sorted_timestamps[i-1]
                intervals.append(interval)
            
            features['avg_post_interval'] = statistics.mean(intervals) if intervals else 0
            features['std_post_interval'] = statistics.stdev(intervals) if len(intervals) > 1 else 0
            
            # 计算峰值（按小时和天）
            hourly_counts = {}
            daily_counts = {}
            
            for ts in timestamps:
                dt = datetime.fromtimestamp(ts)
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                day_key = dt.strftime("%Y-%m-%d")
                
                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            features['peak_hourly_posts'] = max(hourly_counts.values()) if hourly_counts else 0
            features['peak_daily_posts'] = max(daily_counts.values()) if daily_counts else 0
            
            # 计算平均每天发帖数量和标准差
            if daily_counts:
                daily_post_counts = list(daily_counts.values())
                unique_days = len(daily_post_counts)
                total_posts = sum(daily_post_counts)
                features['avg_daily_posts'] = total_posts / unique_days if unique_days > 0 else 0
                features['std_daily_posts'] = statistics.stdev(daily_post_counts) if len(daily_post_counts) > 1 else 0
            else:
                features['avg_daily_posts'] = 0
                features['std_daily_posts'] = 0
            
            # 周期性变量：24小时分布的统计特征
            hour_distribution_features = self._extract_hour_distribution_features(timestamps)
            features.update(hour_distribution_features)
        
        # 即使时间戳少，也可以计算小时分布（在if-else之外统一处理）
        if 'hour_distribution_mean' not in features:
            hour_distribution_features = self._extract_hour_distribution_features(timestamps)
            features.update(hour_distribution_features)
        
        return features
    
    def _extract_location_features(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取地理位置特征"""
        features = {}
        
        location_count = 0
        for post in posts_data:
            if post is None or not isinstance(post, dict):
                continue
            region_name = post.get('region_name', '') or post.get('location', '')
            if region_name and region_name.strip():
                location_count += 1
        
        features['location_ratio'] = location_count / len(posts_data) if posts_data else 0
        
        return features
    
    def _calculate_repost_user_entropy(self, repost_posts: List[Dict[str, Any]]) -> float:
        """计算被转发用户的信息熵"""
        if not repost_posts:
            return 0.0
        
        user_counts = {}
        for post in repost_posts:
            if post is None or not isinstance(post, dict):
                continue
            retweeted = post.get('retweeted_status')
            if retweeted and isinstance(retweeted, dict):
                user = retweeted.get('user')
                if user and isinstance(user, dict):
                    user_id = user.get('id') or user.get('idstr', '')
                    if user_id:
                        user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        if not user_counts:
            return 0.0
        
        # 计算信息熵
        total = sum(user_counts.values())
        entropy = 0.0
        for count in user_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _extract_sentiment_features(self, original_posts: List[Dict[str, Any]], 
                                   repost_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取基于SnowNLP的情感特征（原创和转发分开计算）"""
        features = {}
        
        if not SNOWNLP_AVAILABLE:
            # 如果SnowNLP不可用，返回默认值
            return {
                'avg_sentiment_positive_original': 0.0,
                'std_sentiment_positive_original': 0.0,
                'avg_sentiment_negative_original': 0.0,
                'std_sentiment_negative_original': 0.0,
                'avg_sentiment_positive_repost': 0.0,
                'std_sentiment_positive_repost': 0.0,
                'avg_sentiment_negative_repost': 0.0,
                'std_sentiment_negative_repost': 0.0,
            }
        
        # 处理原创帖子
        original_positive_scores = []
        original_negative_scores = []
        
        for post in original_posts:
            if post is None or not isinstance(post, dict):
                continue
            
            text = self._clean_text_for_sentiment(post)
            if not text:
                continue
            
            try:
                s = SnowNLP(text)
                sentiment = s.sentiments
                
                if sentiment > 0.5:
                    original_positive_scores.append(sentiment)
                else:
                    original_negative_scores.append(1 - sentiment)
            except Exception as e:
                logger.debug(f"原创帖子情感分析失败: {e}")
                continue
        
        # 处理转发帖子的用户评价部分
        repost_positive_scores = []
        repost_negative_scores = []
        
        for post in repost_posts:
            if post is None or not isinstance(post, dict):
                continue
            
            # 获取转发时的用户评价（转发帖子的text_raw中，去掉被转发内容的部分）
            text = self._extract_repost_comment_text(post)
            if not text:
                continue
            
            try:
                s = SnowNLP(text)
                sentiment = s.sentiments
                
                if sentiment > 0.5:
                    repost_positive_scores.append(sentiment)
                else:
                    repost_negative_scores.append(1 - sentiment)
            except Exception as e:
                logger.debug(f"转发评价情感分析失败: {e}")
                continue
        
        # 计算原创帖子的情感特征（均值和标准差）
        if original_positive_scores:
            features['avg_sentiment_positive_original'] = statistics.mean(original_positive_scores)
            features['std_sentiment_positive_original'] = statistics.stdev(original_positive_scores) if len(original_positive_scores) > 1 else 0.0
        else:
            features['avg_sentiment_positive_original'] = 0.0
            features['std_sentiment_positive_original'] = 0.0
        
        if original_negative_scores:
            features['avg_sentiment_negative_original'] = statistics.mean(original_negative_scores)
            features['std_sentiment_negative_original'] = statistics.stdev(original_negative_scores) if len(original_negative_scores) > 1 else 0.0
        else:
            features['avg_sentiment_negative_original'] = 0.0
            features['std_sentiment_negative_original'] = 0.0
        
        # 计算转发评价的情感特征（均值和标准差）
        if repost_positive_scores:
            features['avg_sentiment_positive_repost'] = statistics.mean(repost_positive_scores)
            features['std_sentiment_positive_repost'] = statistics.stdev(repost_positive_scores) if len(repost_positive_scores) > 1 else 0.0
        else:
            features['avg_sentiment_positive_repost'] = 0.0
            features['std_sentiment_positive_repost'] = 0.0
        
        if repost_negative_scores:
            features['avg_sentiment_negative_repost'] = statistics.mean(repost_negative_scores)
            features['std_sentiment_negative_repost'] = statistics.stdev(repost_negative_scores) if len(repost_negative_scores) > 1 else 0.0
        else:
            features['avg_sentiment_negative_repost'] = 0.0
            features['std_sentiment_negative_repost'] = 0.0
        
        return features
    
    def _clean_text_for_sentiment(self, post: Dict[str, Any]) -> str:
        """清理文本用于情感分析"""
        text = str(post.get('text_raw', '') or post.get('text', '') or '')
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除URL、@、#等
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#.*?#', '', text)
        text = text.strip()
        return text if len(text) >= 2 else ''
    
    def _extract_repost_comment_text(self, post: Dict[str, Any]) -> str:
        """提取转发时的用户评价文本（去掉被转发内容）"""
        text = self._clean_text_for_sentiment(post)
        if not text:
            return ''
        
        # 转发帖子的文本通常包含"//@用户名: 被转发内容"的格式
        # 我们需要提取"//"之前的部分，即用户的评价
        # 如果包含"//"，则提取"//"之前的部分；否则整个文本都是评价
        if '//' in text:
            comment_part = text.split('//')[0].strip()
            return comment_part
        else:
            # 如果没有"//"，可能整个文本都是评价，或者格式不同
            # 尝试查找"@"符号，如果存在，可能是"@用户名: 评价"的格式
            # 这里简化处理，返回整个文本
            return text
    
    def _safe_int(self, value: Any) -> int:
        """安全转换为整数"""
        if value is None:
            return 0
        try:
            if isinstance(value, str):
                # 移除逗号（处理如 "29,099,585" 的格式）
                value = value.replace(',', '')
                # 处理带单位的数字，如 "332.6万"
                if '万' in value:
                    num = float(value.replace('万', '')) * 10000
                    return int(num)
                elif 'k' in value.lower():
                    num = float(value.lower().replace('k', '')) * 1000
                    return int(num)
                else:
                    return int(float(value))
            return int(value)
        except:
            return 0
    
    def _get_default_profile_features(self) -> Dict[str, Any]:
        """返回默认的profile特征值"""
        return {
            'screen_name_length': 0,
            'screen_name_digit_count': 0,
            'description_length': 0,
            'description_has_sensitive_word': 0,
            'gender_n': 1,
            'followers_count': 0,
            'friends_count': 0,
            'followers_friends_ratio': 0,
            'statuses_count': 0,
            'is_default_avatar': 1,
        }
    
    def _get_default_posts_features(self) -> Dict[str, Any]:
        """返回默认的posts特征值"""
        default_original = self._get_default_original_posts_features()
        return {
            'posts_count': 0,
            'original_ratio': 0,
            'avg_post_interval': 0,
            'std_post_interval': 0,
            'peak_hourly_posts': 0,
            'peak_daily_posts': 0,
            'avg_daily_posts': 0,
            'std_daily_posts': 0,
            'location_ratio': 0,
            'repost_user_entropy': 0,
            'vocabulary_diversity_repost': 0.0,
            'hour_distribution_mean': 0.0,
            'hour_distribution_std': 0.0,
            'hour_distribution_kurtosis': 0.0,
            'hour_distribution_skewness': 0.0,
            # 注意：不再包含total_comments/likes/reposts，这些应从profile的status_total_counter获取
            **default_original
        }
    
    def _get_default_original_posts_features(self) -> Dict[str, Any]:
        """返回默认的原创帖子特征值"""
        return {
            'avg_text_length_original': 0,
            'avg_punctuation_count_original': 0,
            'std_punctuation_count_original': 0,
            'avg_pic_count_original': 0,
            'avg_video_count_original': 0,
            'std_video_count_original': 0,
            'avg_likes_original': 0,
            'std_likes_original': 0,
            'avg_reposts_original': 0,
            'std_reposts_original': 0,
            'avg_comments_original': 0,
            'std_comments_original': 0,
            'vocabulary_diversity_original': 0.0,
            'avg_sentiment_positive_original': 0.0,
            'std_sentiment_positive_original': 0.0,
            'avg_sentiment_negative_original': 0.0,
            'std_sentiment_negative_original': 0.0,
            'avg_sentiment_positive_repost': 0.0,
            'std_sentiment_positive_repost': 0.0,
            'avg_sentiment_negative_repost': 0.0,
            'std_sentiment_negative_repost': 0.0,
        }
    
    def extract_features(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        提取单个用户的完整特征
        
        Args:
            user_id: 用户ID
            
        Returns:
            完整的特征字典，如果profile数据缺失或无效则返回None
        """
        user_data = self.load_user_data(user_id)
        
        # 如果profile数据缺失，返回None（不包含在训练数据中）
        if user_data['profile'] is None:
            logger.warning(f"用户 {user_id} 的profile文件不存在，跳过")
            return None
        
        profile_features = self.extract_profile_features(user_data['profile'])
        posts_features = self.extract_posts_features(user_data['posts'])
        
        # 检查是否成功提取到有效的profile特征
        # 如果所有关键profile特征都是默认值（全0），说明profile数据无效，应该跳过
        key_profile_features = ['followers_count', 'friends_count', 'statuses_count', 'screen_name_length']
        all_zero = all(profile_features.get(k, 0) == 0 for k in key_profile_features)
        if all_zero:
            logger.warning(f"用户 {user_id} 的profile数据无效（无法提取用户信息），跳过")
            return None
        
        # 合并特征
        all_features = {**profile_features, **posts_features}
        all_features['user_id'] = user_id
        
        return all_features
    
    def extract_features_batch(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量提取特征
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            特征列表
        """
        features_list = []
        
        for idx, user_id in enumerate(user_ids, 1):
            try:
                features = self.extract_features(user_id)
                # 如果返回None（profile数据缺失），跳过该账号
                if features is not None:
                    features_list.append(features)
                if idx % 100 == 0:
                    logger.info(f"已处理 {idx}/{len(user_ids)} 个用户")
            except Exception as e:
                logger.error(f"提取用户 {user_id} 特征失败: {e}")
                continue
        
        return features_list
    
    def extract_features_from_userlists(self, userlist_files: List[str], 
                                       label_mapping: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        """
        从userlist文件提取特征并添加标签
        
        Args:
            userlist_files: userlist文件路径列表
            label_mapping: 文件到标签的映射，例如 {"bot.txt": 1, "human.txt": 0}
            
        Returns:
            带标签的特征列表
        """
        all_features = []
        
        for file_path in userlist_files:
            user_ids = self._read_userlist(file_path)
            file_name = Path(file_path).name
            
            # 获取标签
            label = None
            if label_mapping:
                label = label_mapping.get(file_name)
            
            logger.info(f"处理文件: {file_name} ({len(user_ids)} 个用户, 标签: {label})")
            
            for user_id in user_ids:
                try:
                    features = self.extract_features(user_id)
                    # 如果返回None（profile数据缺失），跳过该账号
                    if features is None:
                        continue
                    if label is not None:
                        features['label'] = label
                    all_features.append(features)
                except Exception as e:
                    logger.error(f"提取用户 {user_id} 特征失败: {e}")
                    continue
        
        return all_features
    
    def _read_userlist(self, file_path: str) -> List[str]:
        """读取userlist文件"""
        user_ids = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        user_ids.append(line)
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
        return user_ids
    
    def save_features(self, features_list: List[Dict[str, Any]], output_file: str):
        """
        保存特征到JSON文件
        
        Args:
            features_list: 特征列表
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(features_list, f, ensure_ascii=False, indent=2)
        logger.info(f"特征已保存到 {output_file} ({len(features_list)} 条记录)")

