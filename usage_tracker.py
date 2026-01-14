"""
使用量追踪模块 (usage_tracker.py)
================================

追踪每日 API 调用次数，并提供使用限制检查。

主要功能：
    - get_today_usage(): 获取今日使用次数
    - increment_usage(): 增加使用次数
    - can_use_api(): 检查是否还能调用 API
    - get_usage_info(): 获取使用量信息

数据存储：
    使用 JSON 文件存储每日使用记录。
    文件路径: usage_data.json

作者: Math OCR App
最后更新: 2026-01-14
"""

import json
import os
from datetime import datetime
from pathlib import Path

from config import Config

# 模块公共接口
__all__ = [
    "get_today_usage",
    "increment_usage",
    "can_use_api",
    "get_usage_info",
    "reset_today_usage",
]

# 使用数据文件路径
USAGE_FILE = Path(__file__).parent / "usage_data.json"


def _get_today_date() -> str:
    """获取今天的日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def _load_usage_data() -> dict:
    """加载使用数据"""
    if not USAGE_FILE.exists():
        return {}
    
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_usage_data(data: dict) -> None:
    """保存使用数据"""
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # 静默失败，不影响主功能


def get_today_usage() -> int:
    """
    获取今日使用次数
    
    Returns:
        今日已使用的次数
    """
    data = _load_usage_data()
    today = _get_today_date()
    return data.get(today, 0)


def increment_usage() -> int:
    """
    增加今日使用次数
    
    Returns:
        增加后的使用次数
    """
    data = _load_usage_data()
    today = _get_today_date()
    
    # 清理旧数据（只保留最近 7 天）
    keys_to_remove = []
    for date_key in data.keys():
        try:
            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
            if (datetime.now() - date_obj).days > 7:
                keys_to_remove.append(date_key)
        except ValueError:
            keys_to_remove.append(date_key)
    
    for key in keys_to_remove:
        del data[key]
    
    # 增加今日计数
    current_count = data.get(today, 0)
    data[today] = current_count + 1
    
    _save_usage_data(data)
    return data[today]


def can_use_api() -> tuple[bool, str]:
    """
    检查是否还能调用 API
    
    Returns:
        (是否可用, 提示信息)
    """
    today_usage = get_today_usage()
    max_usage = Config.DAILY_API_LIMIT
    
    if today_usage >= max_usage:
        return False, f"今日 API 调用次数已达上限（{max_usage} 次），请明天再试"
    
    remaining = max_usage - today_usage
    return True, f"今日剩余调用次数：{remaining}/{max_usage}"


def get_usage_info() -> dict:
    """
    获取使用量信息
    
    Returns:
        包含使用量信息的字典
    """
    today_usage = get_today_usage()
    max_usage = Config.DAILY_API_LIMIT
    
    return {
        "today": today_usage,
        "limit": max_usage,
        "remaining": max(0, max_usage - today_usage),
        "date": _get_today_date(),
        "can_use": today_usage < max_usage,
    }


def reset_today_usage() -> None:
    """
    重置今日使用次数（用于测试）
    """
    data = _load_usage_data()
    today = _get_today_date()
    data[today] = 0
    _save_usage_data(data)
