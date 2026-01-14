"""
使用量追踪模块测试 (test_usage_tracker.py)
=========================================

测试 usage_tracker.py 中的函数。

运行方式：
    pytest tests/test_usage_tracker.py -v
"""
import pytest
import json
import os
from pathlib import Path
from datetime import datetime

# 在导入前设置测试用的数据文件
TEST_USAGE_FILE = Path(__file__).parent / "test_usage_data.json"


class TestUsageTracker:
    """测试使用量追踪功能"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, monkeypatch):
        """每个测试前后的设置和清理"""
        # 导入模块并替换数据文件路径
        import usage_tracker
        monkeypatch.setattr(usage_tracker, "USAGE_FILE", TEST_USAGE_FILE)
        
        # 清理测试文件
        if TEST_USAGE_FILE.exists():
            TEST_USAGE_FILE.unlink()
        
        yield
        
        # 测试后清理
        if TEST_USAGE_FILE.exists():
            TEST_USAGE_FILE.unlink()

    def test_get_today_usage_empty(self):
        """没有数据时应该返回 0"""
        from usage_tracker import get_today_usage
        assert get_today_usage() == 0

    def test_increment_usage(self):
        """increment_usage 应该增加计数"""
        from usage_tracker import get_today_usage, increment_usage
        
        initial = get_today_usage()
        increment_usage()
        assert get_today_usage() == initial + 1

    def test_increment_usage_multiple(self):
        """多次调用 increment_usage 应该累加"""
        from usage_tracker import get_today_usage, increment_usage
        
        for _ in range(5):
            increment_usage()
        
        assert get_today_usage() == 5

    def test_can_use_api_under_limit(self):
        """未达限额时应该返回 True"""
        from usage_tracker import can_use_api
        
        can_use, message = can_use_api()
        assert can_use is True
        # message 可能包含剩余次数信息，只检查 can_use 状态

    def test_get_usage_info_structure(self):
        """get_usage_info 应该返回正确的结构"""
        from usage_tracker import get_usage_info
        
        info = get_usage_info()
        
        assert "today" in info
        assert "limit" in info
        assert "remaining" in info
        assert "can_use" in info
        
        assert isinstance(info["today"], int)
        assert isinstance(info["limit"], int)
        assert isinstance(info["remaining"], int)
        assert isinstance(info["can_use"], bool)

    def test_remaining_calculation(self):
        """剩余次数计算应该正确"""
        from usage_tracker import get_usage_info, increment_usage
        from config import Config
        
        info = get_usage_info()
        expected_remaining = Config.DAILY_API_LIMIT - info["today"]
        assert info["remaining"] == expected_remaining
        
        increment_usage()
        
        info = get_usage_info()
        assert info["remaining"] == expected_remaining - 1
