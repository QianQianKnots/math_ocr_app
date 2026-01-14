"""
日志模块 (logger.py)
===================

提供统一的日志记录功能，支持同时输出到控制台和文件。

功能特性：
    - 控制台输出：INFO 及以上级别，方便开发调试
    - 文件输出：DEBUG 及以上级别，完整记录便于排查
    - 自动按日期分割日志文件
    - 最多保留 7 天日志

日志级别：
    DEBUG   → 详细调试信息（变量值、函数参数）
    INFO    → 正常运行记录（用户操作、请求成功）
    WARNING → 警告但不影响运行（接近限额、配置缺失）
    ERROR   → 错误但程序继续（单次 API 失败）
    CRITICAL→ 严重错误，程序可能崩溃

使用方法：
    from logger import logger
    
    logger.info("用户上传了 3 张图片")
    logger.debug(f"图片尺寸: {image.size}")
    logger.error("API 调用失败", exc_info=True)

作者: Math OCR App
最后更新: 2026-01-14
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

__all__ = ["logger", "setup_logger"]

# 日志目录
LOG_DIR = Path(__file__).parent / "logs"

# 日志格式
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _cleanup_old_logs(log_dir: Path, days: int = 7):
    """
    清理旧日志文件
    
    Args:
        log_dir: 日志目录
        days: 保留天数
    """
    if not log_dir.exists():
        return
    
    cutoff = datetime.now() - timedelta(days=days)
    
    for log_file in log_dir.glob("*.log*"):
        try:
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink()
        except Exception:
            pass  # 静默忽略删除失败


def setup_logger(
    name: str = "math_ocr",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    配置并返回 logger 实例
    
    Args:
        name: logger 名称
        console_level: 控制台输出级别
        file_level: 文件输出级别
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)  # 设置最低级别，具体由 handler 控制
    
    # 创建格式器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # ==================== 控制台 Handler ====================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ==================== 文件 Handler ====================
    try:
        # 创建日志目录
        LOG_DIR.mkdir(exist_ok=True)
        
        # 清理旧日志
        _cleanup_old_logs(LOG_DIR)
        
        # 日志文件路径
        log_file = LOG_DIR / "app.log"
        
        # 使用 TimedRotatingFileHandler，每天轮转，保留 7 天
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",      # 每天午夜轮转
            interval=1,           # 间隔 1 天
            backupCount=7,        # 保留 7 个备份
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"  # 备份文件后缀格式
        logger.addHandler(file_handler)
        
    except Exception as e:
        # 文件 handler 创建失败，只用控制台
        logger.warning(f"无法创建日志文件: {e}")
    
    return logger


# 创建全局 logger 实例
logger = setup_logger()


# ==================== 便捷函数 ====================

def log_api_call(endpoint: str, success: bool, duration: float = None, error: str = None):
    """
    记录 API 调用
    
    Args:
        endpoint: API 端点
        success: 是否成功
        duration: 耗时（秒）
        error: 错误信息（如果失败）
    """
    if success:
        msg = f"API 调用成功: {endpoint}"
        if duration:
            msg += f" ({duration:.2f}s)"
        logger.info(msg)
    else:
        msg = f"API 调用失败: {endpoint}"
        if error:
            msg += f" - {error}"
        logger.error(msg)


def log_user_action(action: str, details: dict = None):
    """
    记录用户操作
    
    Args:
        action: 操作类型
        details: 详细信息
    """
    msg = f"用户操作: {action}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" ({detail_str})"
    logger.info(msg)


def log_error(error: Exception, context: str = None):
    """
    记录错误（带堆栈）
    
    Args:
        error: 异常对象
        context: 上下文描述
    """
    msg = f"错误发生"
    if context:
        msg += f" [{context}]"
    msg += f": {type(error).__name__}: {str(error)}"
    logger.error(msg, exc_info=True)
