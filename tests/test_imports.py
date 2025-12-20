"""
测试模块导入
"""

def test_imports():
    """测试所有主要模块是否可以正常导入"""
    from pybotfinder import (
        WeiboCollector,
        FeatureExtractor,
        ModelTrainer,
        BotPredictor,
        get_profile,
        get_recent_weibos,
        crawl_account,
    )
    
    assert WeiboCollector is not None
    assert FeatureExtractor is not None
    assert ModelTrainer is not None
    assert BotPredictor is not None
    assert get_profile is not None
    assert get_recent_weibos is not None
    assert crawl_account is not None

