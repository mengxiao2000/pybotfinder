"""
Weibo crawler: fetch profile info + latest 30 weibos for accounts
- No data processing
- Save raw JSON
- Python >= 3.8
"""

import requests
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default headers
DEFAULT_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "client-version": "v2.47.142",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://weibo.com",
}

DEFAULT_REQUEST_SLEEP = 0.3  # seconds


class WeiboCollector:
    """微博数据采集器"""
    
    def __init__(self, cookie: Optional[str] = None, 
                 output_dir: str = "dataset",
                 request_sleep: float = DEFAULT_REQUEST_SLEEP):
        """
        初始化采集器
        
        Args:
            cookie: 微博Cookie字符串（必需）
            output_dir: 输出目录
            request_sleep: 请求间隔（秒）
        """
        self.cookie = cookie
        self.output_dir = Path(output_dir)
        self.profiles_dir = self.output_dir / "profiles_dir"
        self.posts_dir = self.output_dir / "posts_dir"
        self.request_sleep = request_sleep
        
        # 创建输出目录
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置headers和cookies
        self.headers = DEFAULT_HEADERS.copy()
        self.cookies = {}
        
        if cookie:
            self.set_cookie(cookie)
    
    def set_cookie(self, cookie: str):
        """设置Cookie并更新headers"""
        self.cookie = cookie
        self.cookies = {'cookie': cookie}
        
        # 从cookie中提取XSRF-TOKEN
        if 'XSRF-TOKEN=' in cookie:
            try:
                xsrf_token = cookie.split('XSRF-TOKEN=')[1].split(';')[0].strip()
                self.headers['x-xsrf-token'] = xsrf_token
            except:
                pass
    
    def get_profile(self, uid: str, save_path: Optional[str] = None) -> Optional[str]:
        """
        获取用户Profile信息
        
        Args:
            uid: 用户ID
            save_path: 保存路径（如果为None，使用默认路径）
            
        Returns:
            保存的文件路径，失败返回None
        """
        if not self.cookie:
            raise ValueError("需要设置Cookie，请使用 set_cookie() 方法或初始化时传入cookie参数")
        
        url = "https://weibo.com/ajax/profile/info"
        params = {"uid": uid}

        try:
            r = requests.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                params=params,
                timeout=10,
            )
            r.raise_for_status()
            
            if save_path is None:
                save_path = str(self.profiles_dir / f"{uid}.json")

            with open(save_path, "w", encoding="utf-8") as f:
                f.write(r.text)

            logger.info(f"✓ Profile saved: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"✗ Failed to get profile for {uid}: {e}")
            return None

    def get_recent_weibos(
        self,
        uid: str,
        limit: int = 30,
        save_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        获取用户最近的微博
        
        Args:
            uid: 用户ID
            limit: 最多获取的微博数量
            save_path: 保存路径（如果为None，使用默认路径）
            
        Returns:
            保存的文件路径，失败返回None
        """
        if not self.cookie:
            raise ValueError("需要设置Cookie，请使用 set_cookie() 方法或初始化时传入cookie参数")
        
        url = "https://weibo.com/ajax/statuses/mymblog"

        all_weibos = []
        page = 1
        since_id = None

        try:
            while len(all_weibos) < limit:
                params = {
                    "uid": uid,
                    "page": page,
                    "feature": 0,
                }
                if since_id:
                    params["since_id"] = since_id

                r = requests.get(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    params=params,
                    timeout=10,
                )
                r.raise_for_status()

                data = r.json()
                block = data.get("data", {})
                weibos = block.get("list", [])

                if not weibos:
                    break

                all_weibos.extend(weibos)
                since_id = block.get("since_id")
                page += 1

                time.sleep(self.request_sleep)

            all_weibos = all_weibos[:limit]

            if save_path is None:
                save_path = str(self.posts_dir / f"{uid}.json")

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(all_weibos, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Posts saved: {save_path} ({len(all_weibos)} posts)")
            return save_path
        except Exception as e:
            logger.error(f"✗ Failed to get posts for {uid}: {e}")
            return None

    def crawl_account(self, uid: str, weibo_limit: int = 30) -> Dict[str, Optional[str]]:
        """
        采集单个账号的数据
        
        Args:
            uid: 用户ID
            weibo_limit: 最多采集的微博数量
            
        Returns:
            包含profile_path和posts_path的字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"采集用户: {uid}")
        logger.info(f"{'='*60}")
        
        profile_file = self.get_profile(uid)
        weibo_file = self.get_recent_weibos(uid, weibo_limit)
        
        if profile_file and weibo_file:
            logger.info(f"✓ 用户 {uid} 采集完成")
            logger.info(f"  Profile: {profile_file}")
            logger.info(f"  Posts  : {weibo_file}")
        else:
            logger.warning(f"✗ 用户 {uid} 采集失败")
        
        return {
            'profile_path': profile_file,
            'posts_path': weibo_file
        }

    def crawl_userlist(
        self,
        userlist_file: str,
        weibo_limit: int = 30,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        从userlist文件批量采集用户数据
        
        Args:
            userlist_file: 用户列表文件路径（每行一个用户ID）
            weibo_limit: 每个用户最多采集的微博数量
            skip_existing: 是否跳过已存在的用户数据
            
        Returns:
            统计信息字典
        """
        user_ids = self._read_userlist(userlist_file)
        return self.crawl_users(user_ids, weibo_limit, skip_existing)

    def crawl_users(
        self,
        user_ids: List[str],
        weibo_limit: int = 30,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        批量采集用户数据
        
        Args:
            user_ids: 用户ID列表
            weibo_limit: 每个用户最多采集的微博数量
            skip_existing: 是否跳过已存在的用户数据
            
        Returns:
            统计信息字典
        """
        logger.info(f"\n总计: {len(user_ids)} 个用户")
        logger.info(f"输出目录: {self.output_dir}/")
        logger.info(f"  - profiles_dir/")
        logger.info(f"  - posts_dir/")
        logger.info("="*60)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for idx, uid in enumerate(user_ids, 1):
            # 检查是否已存在
            if skip_existing:
                profile_exists = (self.profiles_dir / f"{uid}.json").exists()
                posts_exists = (self.posts_dir / f"{uid}.json").exists()
                if profile_exists and posts_exists:
                    logger.info(f"[{idx}/{len(user_ids)}] ⏭ 跳过用户 {uid}（数据已存在）")
                    skipped_count += 1
                    continue
            
            logger.info(f"\n[{idx}/{len(user_ids)}] 开始采集用户 {uid}")
            
            try:
                result = self.crawl_account(uid, weibo_limit)
                
                if result['profile_path'] and result['posts_path']:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 在用户之间添加延迟
                time.sleep(self.request_sleep)
                
            except KeyboardInterrupt:
                logger.warning("\n用户中断采集")
                break
            except Exception as e:
                logger.error(f"✗ 采集用户 {uid} 时发生异常: {e}")
                failed_count += 1
                continue
        
        # 输出统计信息
        logger.info(f"\n{'='*60}")
        logger.info(f"=== 采集完成 ===")
        logger.info(f"{'='*60}")
        logger.info(f"成功: {success_count} 个用户")
        logger.info(f"失败: {failed_count} 个用户")
        logger.info(f"跳过: {skipped_count} 个用户")
        logger.info(f"总计: {len(user_ids)} 个用户")
        logger.info(f"{'='*60}\n")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total': len(user_ids)
        }

    def _read_userlist(self, file_path: str) -> List[str]:
        """读取userlist文件"""
        user_ids = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        user_ids.append(line)
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
        
        return user_ids


# 为了向后兼容，保留函数接口
def get_profile(uid: str, cookie: str, save_path: Optional[str] = None) -> Optional[str]:
    """获取用户Profile信息（函数接口）"""
    collector = WeiboCollector(cookie=cookie)
    return collector.get_profile(uid, save_path)


def get_recent_weibos(
    uid: str,
    cookie: str,
    limit: int = 30,
    save_path: Optional[str] = None,
) -> Optional[str]:
    """获取用户最近的微博（函数接口）"""
    collector = WeiboCollector(cookie=cookie)
    return collector.get_recent_weibos(uid, limit, save_path)


def crawl_account(uid: str, cookie: str, weibo_limit: int = 30) -> Dict[str, Optional[str]]:
    """采集单个账号的数据（函数接口）"""
    collector = WeiboCollector(cookie=cookie)
    return collector.crawl_account(uid, weibo_limit)

