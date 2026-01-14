"""
数据分析模块 (analytics.py)
==========================

收集匿名使用数据，用于优化和调试项目。

收集的数据：
    - 使用时间
    - 操作类型（OCR识别、PDF下载等）
    - 图片数量
    - 处理结果（成功/失败）
    - 错误信息（如有）

不收集的数据：
    - 用户身份信息
    - 图片内容
    - LaTeX 代码内容
    - API 密钥

数据存储：
    本地 JSON 文件 (analytics_data.json)

作者: Math OCR App
最后更新: 2026-01-14
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib
import uuid

# 模块公共接口
__all__ = [
    "log_event",
    "get_analytics_summary",
    "get_session_id",
    "ANALYTICS_ENABLED",
]

# 数据文件路径
ANALYTICS_FILE = Path(__file__).parent / "analytics_data.json"

# 是否启用数据收集（可通过环境变量禁用）
ANALYTICS_ENABLED = os.getenv("DISABLE_ANALYTICS", "false").lower() != "true"

# 会话 ID（每次启动应用生成一个唯一 ID）
_session_id: Optional[str] = None


def get_session_id() -> str:
    """
    获取当前会话 ID
    
    每次应用启动生成一个唯一的匿名 ID，用于关联同一会话的操作。
    """
    global _session_id
    if _session_id is None:
        # 使用 UUID 生成匿名会话 ID
        raw_id = str(uuid.uuid4())
        # 哈希处理，进一步匿名化
        _session_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
    return _session_id


def _load_analytics_data() -> list:
    """加载分析数据"""
    if not ANALYTICS_FILE.exists():
        return []
    
    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_analytics_data(data: list) -> None:
    """保存分析数据"""
    if not ANALYTICS_ENABLED:
        return
    
    try:
        # 只保留最近 1000 条记录，防止文件过大
        if len(data) > 1000:
            data = data[-1000:]
        
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # 静默失败


def log_event(
    event_type: str,
    success: bool = True,
    details: Optional[dict] = None,
) -> None:
    """
    记录一个使用事件
    
    Args:
        event_type: 事件类型，如 "ocr_recognition", "pdf_download"
        success: 是否成功
        details: 额外详情（不包含敏感信息）
    
    事件类型：
        - app_start: 应用启动
        - ocr_recognition: OCR 识别
        - pdf_download: PDF 下载
        - latex_edit: LaTeX 编辑
        - image_upload: 图片上传
        - error: 错误发生
    """
    if not ANALYTICS_ENABLED:
        return
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session_id": get_session_id(),
        "event_type": event_type,
        "success": success,
    }
    
    # 添加安全的详情（过滤敏感信息）
    if details:
        safe_details = {}
        # 只保留安全的字段
        safe_keys = [
            "image_count",      # 图片数量
            "processing_time",  # 处理时间
            "error_type",       # 错误类型（不含详情）
            "file_size_kb",     # 文件大小
            "latex_length",     # LaTeX 长度（字符数）
        ]
        for key in safe_keys:
            if key in details:
                safe_details[key] = details[key]
        
        if safe_details:
            event["details"] = safe_details
    
    # 保存事件
    data = _load_analytics_data()
    data.append(event)
    _save_analytics_data(data)


def get_analytics_summary() -> dict:
    """
    获取分析数据摘要
    
    Returns:
        包含统计信息的字典
    """
    data = _load_analytics_data()
    
    if not data:
        return {
            "total_events": 0,
            "unique_sessions": 0,
            "events_by_type": {},
            "success_rate": 0,
            "date_range": None,
        }
    
    # 统计
    events_by_type = {}
    sessions = set()
    success_count = 0
    dates = []
    
    for event in data:
        event_type = event.get("event_type", "unknown")
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        if event.get("session_id"):
            sessions.add(event["session_id"])
        
        if event.get("success"):
            success_count += 1
        
        if event.get("date"):
            dates.append(event["date"])
    
    return {
        "total_events": len(data),
        "unique_sessions": len(sessions),
        "events_by_type": events_by_type,
        "success_rate": round(success_count / len(data) * 100, 1) if data else 0,
        "date_range": {
            "start": min(dates) if dates else None,
            "end": max(dates) if dates else None,
        },
    }


def get_daily_stats() -> dict:
    """
    获取每日统计
    
    Returns:
        按日期分组的统计数据
    """
    data = _load_analytics_data()
    
    daily = {}
    for event in data:
        date = event.get("date", "unknown")
        if date not in daily:
            daily[date] = {"total": 0, "success": 0, "ocr": 0, "pdf": 0}
        
        daily[date]["total"] += 1
        if event.get("success"):
            daily[date]["success"] += 1
        if event.get("event_type") == "ocr_recognition":
            daily[date]["ocr"] += 1
        if event.get("event_type") == "pdf_download":
            daily[date]["pdf"] += 1
    
    return daily
