"""
配置文件 (config.py)
====================

集中管理所有常量和配置项，避免硬编码散落在各处。

使用方法：
    from config import Config

    max_files = Config.MAX_UPLOAD_FILES
    api_key = Config.get_api_key()

    # 验证 API 密钥
    is_valid, error_msg = Config.validate_api_key()

配置分类：
    - 文件上传配置：上传数量、大小、类型限制
    - 图片处理配置：缩略图、压缩质量
    - API 配置：端点、模型、超时
    - PDF 配置：编译超时
    - 编辑器配置：UI 参数
    - 运行模式：调试/生产

作者: Math OCR App
最后更新: 2026-01-14
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 模块公共接口
__all__ = ["Config"]


class Config:
    """
    应用配置类

    所有配置项都是类属性，通过 Config.XXX 访问。
    带有 @classmethod 的是工具方法。
    """

    # ==================== 运行模式 ====================
    DEBUG_MODE: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ==================== 文件上传配置 ====================
    MAX_UPLOAD_FILES: int = 5  # 最多上传图片数量
    MAX_FILE_SIZE_MB: int = 10  # 单个文件最大大小（MB）
    MAX_IMAGE_DIMENSION: int = 4096  # 图片最大尺寸（像素）
    ALLOWED_EXTENSIONS: list[str] = ["png", "jpg", "jpeg"]

    # ==================== 图片处理配置 ====================
    THUMBNAIL_MAX_HEIGHT: int = 150  # 缩略图最大高度（像素）
    JPEG_QUALITY: int = 85  # JPEG 压缩质量

    # ==================== API 配置 ====================
    API_HOST: str = "api.302.ai"
    API_ENDPOINT: str = "/v1/chat/completions"
    API_MODEL: str = "gemini-2.5-flash"
    API_TIMEOUT: int = 120  # API 调用超时（秒）
    DAILY_API_LIMIT: int = 50  # 每日 API 调用次数上限

    # ==================== PDF 配置 ====================
    PDF_COMPILE_TIMEOUT: int = 60  # PDF 编译超时（秒）

    # ==================== 编辑器配置 ====================
    EDITOR_HEIGHT: int = 450  # 编辑器高度（像素）
    EDITOR_FONT_SIZE: int = 14  # 编辑器字体大小

    # ==================== API 密钥管理 ====================
    @classmethod
    def get_api_key(cls) -> str | None:
        """获取 API 密钥"""
        return os.getenv("API_KEY")

    @classmethod
    def validate_api_key(cls) -> tuple[bool, str]:
        """
        验证 API 密钥是否存在且格式正确

        返回: (是否有效, 错误信息)
        """
        api_key = cls.get_api_key()

        if not api_key:
            return False, "未找到 API 密钥。请在 .env 文件中设置 API_KEY=your_key"

        if len(api_key) < 10:
            return False, "API 密钥格式不正确（长度过短）"

        # 可以添加更多验证逻辑
        return True, ""

    @classmethod
    def get_max_file_size_bytes(cls) -> int:
        """获取最大文件大小（字节）"""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024
