# pybotfinder

微博社交机器人检测工具包 - Weibo Social Bot Detection Toolkit

基于随机森林的微博社交机器人检测系统，提供开箱即用的预测功能。

## 安装

```bash
pip install pybotfinder
```

## 快速开始 - 预测

### Python API

```python
from pybotfinder import BotPredictor

# 初始化预测器（使用包内默认模型）
predictor = BotPredictor(cookie="YOUR_WEIBO_COOKIE")

# 预测单个用户
result = predictor.predict_from_user_id("1042567781")
print(f"预测结果: {result['prediction']['label_name']}")
print(f"机器人得分: {result['prediction']['bot_score']:.4f}")
```

### 命令行

```bash
pybotfinder-predict --user-id 1042567781 --cookie "YOUR_WEIBO_COOKIE"
```

### 预测结果格式

```python
{
    'user_id': '1042567781',
    'prediction': {
        'label': 1,  # 0=人类, 1=机器人
        'label_name': '机器人',  # '人类' 或 '机器人'
        'bot_score': 0.95  # 机器人得分（范围0-1，值越大表示越可能是机器人）
    }
}
```

**返回值说明：**
- `label`: 预测标签，0表示人类，1表示机器人
- `label_name`: 标签名称，'人类' 或 '机器人'
- `bot_score`: 机器人得分，是模型预测该账号为机器人的概率值（范围0-1）
  - `bot_score` 接近1表示模型认为该账号很可能是机器人
  - `bot_score` 接近0表示模型认为该账号很可能是人类
  - **注意**：`bot_score` 是模型输出的概率值，不是统计意义上的置信区间，应结合具体应用场景理解

## 训练数据来源

模型基于以下数据训练：

- **机器人样本** (3845个): 来自 `bot.txt`，包含已标注的机器人账号
- **人类样本** (4579个): 来自以下文件：
  - `human.txt` (2270个): 普通用户账号，通过实时推文中以常用虚词为搜索词采集
  - `government.txt` (597个): 政府机构账号，通过微博政务榜单采集
  - `influencer.txt` (931个): 影响者账号，通过微博V影响力榜单采集
  - `media.txt` (781个): 媒体账号，以“新闻”为关键词搜索相关的认证账号采集

**总样本数**: 8424个用户

## 训练特征

模型使用46个特征进行训练，包括：

### Profile-level特征 (24个)

1. **昵称特征** (4个):
   - `screen_name_length`: 昵称长度
   - `screen_name_digit_count`: 昵称中数字数量
   - `screen_name_letter_count`: 昵称中字母数量
   - `screen_name_has_special_char`: 昵称中是否包含特殊字符（1=是，0=否）

2. **描述特征** (9个):
   - `description_length`: 描述长度
   - `description_has_sensitive_word`: 描述中是否包含敏感词（1=是，0=否）
   - `description_has_url`: 描述中是否包含URL（1=是，0=否）
   - `description_has_at`: 描述中是否包含@（1=是，0=否）
   - `description_has_hash`: 描述中是否包含#（1=是，0=否）
   - `description_has_digit`: 描述中是否包含数字（1=是，0=否）
   - `description_has_letter`: 描述中是否包含字母（1=是，0=否）
   - `description_has_special_char`: 描述中是否包含特殊字符（1=是，0=否）

3. **基本统计** (6个):
   - `gender_m`: 性别（男性=1，其他=0）
   - `gender_f`: 性别（女性=1，其他=0）
   - `gender_n`: 性别（未知=1，其他=0）
   - `followers_count`: 粉丝数
   - `friends_count`: 关注数
   - `followers_friends_ratio`: 粉丝/关注比例
   - `statuses_count`: 微博总数

4. **互动统计** (3个):
   - `comments_count`: 总评论数（从profile的status_total_counter字段获取）
   - `likes_count`: 总点赞数（从profile的status_total_counter字段获取）
   - `reposts_count`: 总转发数（从profile的status_total_counter字段获取）

5. **视觉特征** (2个):
   - `is_default_avatar`: 是否使用默认头像（1=是，0=否）
   - `is_default_cover`: 是否使用默认封面（1=是，0=否）

### Posts-level特征 (25个)

1. **基本统计** (2个):
   - `posts_count`: 收集到的帖子数量
   - `original_ratio`: 原创微博比例

2. **原创内容特征** (14个，均值和标准差):
   - `avg_text_length_original`: 平均文本长度
   - `std_text_length_original`: 文本长度标准差
   - `avg_punctuation_count_original`: 平均标点符号数
   - `std_punctuation_count_original`: 标点符号数标准差
   - `avg_pic_count_original`: 平均图片数
   - `std_pic_count_original`: 图片数标准差
   - `avg_video_count_original`: 平均视频数
   - `std_video_count_original`: 视频数标准差
   - `avg_link_count_original`: 平均链接数
   - `std_link_count_original`: 链接数标准差
   - `avg_at_count_original`: 平均@数量
   - `std_at_count_original`: @数量标准差
   - `avg_hash_count_original`: 平均#数量
   - `std_hash_count_original`: #数量标准差

3. **时间特征** (4个):
   - `avg_post_interval`: 平均发帖间隔（秒）
   - `std_post_interval`: 发帖间隔标准差（秒）
   - `peak_hourly_posts`: 峰值小时发帖数
   - `peak_daily_posts`: 峰值日发帖数

4. **其他特征** (2个):
   - `location_ratio`: 包含地理位置的微博比例
   - `repost_user_entropy`: 转发用户信息熵

## 模型评估

### 整体性能

- **准确率 (Accuracy)**: 99.17%
- **交叉验证F1分数**: 0.9872 (±0.0036)
- **测试集F1分数 (宏平均)**: 0.9916
- **测试集F1分数 (加权平均)**: 0.9917

### 各类别性能

**人类 (类别0)**:
- 精确率 (Precision): 0.9870
- 召回率 (Recall): 0.9978
- F1-score: 0.9924

**机器人 (类别1)**:
- 精确率 (Precision): 0.9974
- 召回率 (Recall): 0.9844
- F1-score: 0.9908

## 注意事项

1. **Cookie获取**: 
   - Cookie需要从微博网页版获取
   - 访问 https://weibo.com 并登录
   - 打开浏览器开发者工具（F12）
   - 在Network标签中找到任意请求，复制请求头中的Cookie值
   - Cookie格式示例: `SUB=xxx; SUBP=xxx; ...`
   - Cookie用于访问微博API采集用户数据，请妥善保管

2. **模型文件**: 
   - 包内已包含训练好的模型文件 (`bot_detection_model.pkl`)
   - 无需额外下载或训练，安装后即可使用

3. **数据采集**: 
   - 预测时需要采集用户数据，请确保网络连接正常
   - 采集过程可能需要几秒钟时间

4. **返回值说明**: 
   - `label`: 预测标签，0表示人类，1表示机器人
   - `label_name`: 标签名称，'人类' 或 '机器人'
   - `bot_score`: 机器人得分，是模型预测该账号为机器人的概率值（范围0-1）
     - `bot_score` 接近1表示模型认为该账号很可能是机器人
     - `bot_score` 接近0表示模型认为该账号很可能是人类
     - **重要提示**：`bot_score` 是模型输出的概率值，不是统计意义上的置信区间或假设检验的p值，应结合具体应用场景理解和使用，避免过度解读

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 作者

Xiao MENG - xiaomeng7-c@my.cityu.edu.hk
