# pybotfinder

<img src="logo.png" width="200" align="right"/>

pybotfinder 是一个面向计算社会科学研究的 Python 包，
用于对微博（Weibo）用户进行社交机器人检测。
该工具包基于随机森林分类模型，
依据用户资料和最近发布的30条内容，
提取身份与行为模式特征，
支持研究者在社交媒体分析、舆情研究和自动化用户识别任务中，
快速地完成机器人检测。

<br clear="right"/>

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

- **机器人样本** (4994个账号ID): 来自 `bot.txt`，主要为自动化营销账号和少部分LLM驱动的机器人账号
- **人类样本** (5091个账号ID): 来自以下文件：
  - `human.txt` (2782个): 主要为通过实时推文中以常用虚词为搜索词采集的账号和少部分手动采集的人类账号
  - `government.txt` (597个): 政府机构账号，通过微博政务榜单采集
  - `influencer.txt` (931个): 影响者账号，通过微博V影响力榜单采集
  - `media.txt` (781个): 媒体账号，以"新闻"为关键词搜索相关的认证账号采集

**标签分布说明**:
- 账号ID总数：10,085个（机器人：4,994个，人类：5,091个）
- 由于部分账号在数据采集时可能已被封禁、删除或设置为私密，无法提取到有效的profile数据，这些账号被排除在训练数据之外
- 实际成功提取特征并参与训练的样本：9,839个（机器人：4,780个，人类：5,059个）
- 数据集划分：训练集7,871个（80%），测试集1,968个（20%）

## 训练特征

模型使用46个特征进行训练，包括：

### Profile-level特征 (10个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `screen_name_length` | 昵称长度 | 数值 |
| `screen_name_digit_count` | 昵称中数字数量 | 数值 |
| `description_length` | 描述长度 | 数值 |
| `description_has_sensitive_word` | 描述中是否包含敏感词 | 二值 (0/1) |
| `gender_n` | 性别（未知=1，其他=0） | 二值 (0/1) |
| `followers_count` | 粉丝数 | 数值 |
| `friends_count` | 关注数 | 数值 |
| `followers_friends_ratio` | 粉丝/关注比例 | 数值 |
| `statuses_count` | 微博总数 | 数值 |
| `is_default_avatar` | 是否使用默认头像 | 二值 (0/1) |

### Posts-level特征 (36个)

#### 基本统计 (2个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `posts_count` | 收集到的帖子数量 | 数值 |
| `original_ratio` | 原创微博比例 | 数值 (0-1) |

#### 原创内容特征 (7个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `avg_text_length_original` | 平均文本长度 | 数值 |
| `avg_punctuation_count_original` | 平均标点符号数 | 数值 |
| `std_punctuation_count_original` | 标点符号数标准差 | 数值 |
| `avg_pic_count_original` | 平均图片数 | 数值 |
| `avg_video_count_original` | 平均视频数 | 数值 |
| `std_video_count_original` | 视频数标准差 | 数值 |
| `vocabulary_diversity_original` | 原创内容词汇多样性（unique词语/总词语） | 数值 (0-1) |

#### 原创互动特征 (6个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `avg_likes_original` | 原创微博平均点赞数 | 数值 |
| `std_likes_original` | 原创微博点赞数标准差 | 数值 |
| `avg_reposts_original` | 原创微博平均转发数 | 数值 |
| `std_reposts_original` | 原创微博转发数标准差 | 数值 |
| `avg_comments_original` | 原创微博平均评论数 | 数值 |
| `std_comments_original` | 原创微博评论数标准差 | 数值 |

#### 时间特征 (10个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `avg_post_interval` | 平均发帖间隔（秒） | 数值 |
| `std_post_interval` | 发帖间隔标准差（秒） | 数值 |
| `peak_hourly_posts` | 峰值小时发帖数 | 数值 |
| `peak_daily_posts` | 峰值日发帖数 | 数值 |
| `avg_daily_posts` | 平均每天发帖数量 | 数值 |
| `std_daily_posts` | 每天发帖数量标准差 | 数值 |
| `hour_distribution_mean` | 24小时分布均值 | 数值 (0-23) |
| `hour_distribution_std` | 24小时分布标准差 | 数值 |
| `hour_distribution_kurtosis` | 24小时分布峰度 | 数值 |
| `hour_distribution_skewness` | 24小时分布偏度 | 数值 |

#### 情感特征 (8个，基于SnowNLP，原创和转发分开计算)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `avg_sentiment_positive_original` | 原创帖子积极情感平均值 | 数值 (0-1) |
| `std_sentiment_positive_original` | 原创帖子积极情感标准差 | 数值 |
| `avg_sentiment_negative_original` | 原创帖子消极情感平均值 | 数值 (0-1) |
| `std_sentiment_negative_original` | 原创帖子消极情感标准差 | 数值 |
| `avg_sentiment_positive_repost` | 转发评价积极情感平均值 | 数值 (0-1) |
| `std_sentiment_positive_repost` | 转发评价积极情感标准差 | 数值 |
| `avg_sentiment_negative_repost` | 转发评价消极情感平均值 | 数值 (0-1) |
| `std_sentiment_negative_repost` | 转发评价消极情感标准差 | 数值 |

#### 其他特征 (3个)

| 特征名称 | 描述 | 类型 |
|---------|------|------|
| `location_ratio` | 包含地理位置的微博比例 | 数值 (0-1) |
| `repost_user_entropy` | 转发用户信息熵 | 数值 |
| `vocabulary_diversity_repost` | 转发评价词汇多样性（unique词语/总词语） | 数值 (0-1) |

## 模型评估

### 整体性能

| 指标 | 数值 |
|------|------|
| **准确率 (Accuracy)** | 97.00% |
| **交叉验证F1分数** | 0.9714 (±0.0055) |
| **测试集F1分数 (宏平均)** | 0.9699 |
| **测试集F1分数 (加权平均)** | 0.9700 |

### 各类别性能

| 类别 | 精确率 (Precision) | 召回率 (Recall) | F1-score |
|------|-------------------|----------------|----------|
| **人类 (类别0)** | 0.9483 | 0.9960 | 0.9716 |
| **机器人 (类别1)** | 0.9956 | 0.9425 | 0.9683 |

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
   - 如果用户的profile数据采集失败（账号不存在、被封禁或Cookie无效），预测将返回错误信息，不会进行预测

4. **返回值说明**: 
   - `label`: 预测标签，0表示人类，1表示机器人
   - `label_name`: 标签名称，'人类' 或 '机器人'
   - `bot_score`: 机器人得分，是模型预测该账号为机器人的概率值（范围0-1）
     - `bot_score` 接近1表示模型认为该账号很可能是机器人
     - `bot_score` 接近0表示模型认为该账号很可能是人类
     - **重要提示**：`bot_score` 是模型输出的概率值，不是统计意义上的置信区间或假设检验的p值，应结合具体应用场景理解和使用，避免过度解读

5. **模型评估说明**:
   **模型评估结果仅反映其在测试集上的性能，未必能够直接外推至真实应用情境。因此，在实际部署或研究应用之前，建议基于具体应用场景下的人工标注数据对模型进行进一步评估。**

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

