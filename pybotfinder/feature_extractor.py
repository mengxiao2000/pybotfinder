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

logger = logging.getLogger(__name__)

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
            
            # 昵称相关特征
            screen_name = str(user.get('screen_name', '') or user.get('name', '') or '')
            features['screen_name_length'] = len(screen_name)
            features['screen_name_digit_count'] = len(re.findall(r'\d', screen_name))
            features['screen_name_letter_count'] = len(re.findall(r'[a-zA-Z]', screen_name))
            features['screen_name_has_special_char'] = 1 if re.search(r'[^\w\s\u4e00-\u9fa5]', screen_name) else 0
            
            # 描述相关特征
            description = str(user.get('description', '') or user.get('desc', '') or '')
            features['description_length'] = len(description)
            features['description_has_sensitive_word'] = 1 if description and any(word in description for word in SENSITIVE_WORDS) else 0
            features['description_has_url'] = 1 if re.search(r'http[s]?://', description) else 0
            features['description_has_at'] = 1 if '@' in description else 0
            features['description_has_hash'] = 1 if '#' in description else 0
            features['description_has_digit'] = 1 if re.search(r'\d', description) else 0
            features['description_has_letter'] = 1 if re.search(r'[a-zA-Z]', description) else 0
            features['description_has_special_char'] = 1 if re.search(r'[^\w\s\u4e00-\u9fa5]', description) else 0
            
            # 性别特征（m=男, f=女, n=未知）
            gender = str(user.get('gender', 'n') or 'n')
            features['gender_m'] = 1 if gender == 'm' else 0
            features['gender_f'] = 1 if gender == 'f' else 0
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
            
            # 评论、点赞、转发数（从统计信息中获取，如果存在）
            # 注意：这些可能不在profile中，需要从posts聚合
            features['comments_count'] = 0  # 将在posts特征中计算
            features['likes_count'] = 0  # 将在posts特征中计算
            features['reposts_count'] = 0  # 将在posts特征中计算
            
            # 头像和封面图是否默认
            profile_image_url = str(user.get('profile_image_url', '') or user.get('avatar_hd', '') or '')
            cover_image = str(user.get('cover_image_phone', '') or user.get('cover_image', '') or '')
            features['is_default_avatar'] = 1 if 'default' in profile_image_url.lower() or not profile_image_url else 0
            features['is_default_cover'] = 1 if 'default' in cover_image.lower() or not cover_image else 0
            
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
            
            # 聚合评论、点赞、转发数
            total_comments = sum(self._safe_int(p.get('comments_count', 0)) for p in posts_data if p is not None and isinstance(p, dict))
            total_likes = sum(self._safe_int(p.get('attitudes_count', 0)) for p in posts_data if p is not None and isinstance(p, dict))
            total_reposts = sum(self._safe_int(p.get('reposts_count', 0)) for p in posts_data if p is not None and isinstance(p, dict))
            features['total_comments'] = total_comments
            features['total_likes'] = total_likes
            features['total_reposts'] = total_reposts
            
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
        link_counts = []
        at_counts = []
        hash_counts = []
        
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
            
            # 链接数量
            link_count = len(re.findall(r'http[s]?://', text))
            link_counts.append(link_count)
            
            # @数量
            at_count = len(re.findall(r'@\w+', text))
            at_counts.append(at_count)
            
            # #数量
            hash_count = len(re.findall(r'#.*?#', text))
            hash_counts.append(hash_count)
        
        # 计算均值和标准差
        features['avg_text_length_original'] = statistics.mean(text_lengths) if text_lengths else 0
        features['std_text_length_original'] = statistics.stdev(text_lengths) if len(text_lengths) > 1 else 0
        
        features['avg_punctuation_count_original'] = statistics.mean(punctuation_counts) if punctuation_counts else 0
        features['std_punctuation_count_original'] = statistics.stdev(punctuation_counts) if len(punctuation_counts) > 1 else 0
        
        features['avg_pic_count_original'] = statistics.mean(pic_counts) if pic_counts else 0
        features['std_pic_count_original'] = statistics.stdev(pic_counts) if len(pic_counts) > 1 else 0
        
        features['avg_video_count_original'] = statistics.mean(video_counts) if video_counts else 0
        features['std_video_count_original'] = statistics.stdev(video_counts) if len(video_counts) > 1 else 0
        
        features['avg_link_count_original'] = statistics.mean(link_counts) if link_counts else 0
        features['std_link_count_original'] = statistics.stdev(link_counts) if len(link_counts) > 1 else 0
        
        features['avg_at_count_original'] = statistics.mean(at_counts) if at_counts else 0
        features['std_at_count_original'] = statistics.stdev(at_counts) if len(at_counts) > 1 else 0
        
        features['avg_hash_count_original'] = statistics.mean(hash_counts) if hash_counts else 0
        features['std_hash_count_original'] = statistics.stdev(hash_counts) if len(hash_counts) > 1 else 0
        
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
    
    def _safe_int(self, value: Any) -> int:
        """安全转换为整数"""
        if value is None:
            return 0
        try:
            if isinstance(value, str):
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
            'screen_name_letter_count': 0,
            'screen_name_has_special_char': 0,
            'description_length': 0,
            'description_has_sensitive_word': 0,
            'description_has_url': 0,
            'description_has_at': 0,
            'description_has_hash': 0,
            'description_has_digit': 0,
            'description_has_letter': 0,
            'description_has_special_char': 0,
            'gender_m': 0,
            'gender_f': 0,
            'gender_n': 1,
            'followers_count': 0,
            'friends_count': 0,
            'followers_friends_ratio': 0,
            'statuses_count': 0,
            'comments_count': 0,
            'likes_count': 0,
            'reposts_count': 0,
            'is_default_avatar': 1,
            'is_default_cover': 1,
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
            'location_ratio': 0,
            'repost_user_entropy': 0,
            'total_comments': 0,
            'total_likes': 0,
            'total_reposts': 0,
            **default_original
        }
    
    def _get_default_original_posts_features(self) -> Dict[str, Any]:
        """返回默认的原创帖子特征值"""
        return {
            'avg_text_length_original': 0,
            'std_text_length_original': 0,
            'avg_punctuation_count_original': 0,
            'std_punctuation_count_original': 0,
            'avg_pic_count_original': 0,
            'std_pic_count_original': 0,
            'avg_video_count_original': 0,
            'std_video_count_original': 0,
            'avg_link_count_original': 0,
            'std_link_count_original': 0,
            'avg_at_count_original': 0,
            'std_at_count_original': 0,
            'avg_hash_count_original': 0,
            'std_hash_count_original': 0,
        }
    
    def extract_features(self, user_id: str) -> Dict[str, Any]:
        """
        提取单个用户的完整特征
        
        Args:
            user_id: 用户ID
            
        Returns:
            完整的特征字典
        """
        user_data = self.load_user_data(user_id)
        
        profile_features = self.extract_profile_features(user_data['profile'])
        posts_features = self.extract_posts_features(user_data['posts'])
        
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

