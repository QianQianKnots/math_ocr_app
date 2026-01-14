"""
配置模块测试 (test_config.py)
============================

测试 config.py 中的配置类。

运行方式：
    pytest tests/test_config.py -v
"""
import pytest
import os

from config import Config


class TestConfigConstants:
    """测试配置常量"""

    def test_max_upload_files_positive(self):
        """最大上传数量应该是正整数"""
        assert Config.MAX_UPLOAD_FILES > 0
        assert isinstance(Config.MAX_UPLOAD_FILES, int)

    def test_max_file_size_positive(self):
        """最大文件大小应该是正整数"""
        assert Config.MAX_FILE_SIZE_MB > 0
        assert isinstance(Config.MAX_FILE_SIZE_MB, int)

    def test_max_image_dimension_positive(self):
        """最大图片尺寸应该是正整数"""
        assert Config.MAX_IMAGE_DIMENSION > 0
        assert isinstance(Config.MAX_IMAGE_DIMENSION, int)

    def test_allowed_extensions_not_empty(self):
        """允许的扩展名列表不应为空"""
        assert len(Config.ALLOWED_EXTENSIONS) > 0

    def test_allowed_extensions_lowercase(self):
        """扩展名应该是小写"""
        for ext in Config.ALLOWED_EXTENSIONS:
            assert ext == ext.lower()

    def test_api_timeout_positive(self):
        """API 超时应该是正整数"""
        assert Config.API_TIMEOUT > 0
        assert isinstance(Config.API_TIMEOUT, int)

    def test_daily_api_limit_positive(self):
        """每日 API 限额应该是正整数"""
        assert Config.DAILY_API_LIMIT > 0
        assert isinstance(Config.DAILY_API_LIMIT, int)


class TestConfigMethods:
    """测试配置方法"""

    def test_get_max_file_size_bytes(self):
        """get_max_file_size_bytes 应该返回正确的字节数"""
        expected = Config.MAX_FILE_SIZE_MB * 1024 * 1024
        assert Config.get_max_file_size_bytes() == expected

    def test_validate_api_key_format(self):
        """validate_api_key 应该返回元组"""
        result = Config.validate_api_key()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


class TestApiConfig:
    """测试 API 配置"""

    def test_api_host_not_empty(self):
        """API host 不应为空"""
        assert Config.API_HOST
        assert isinstance(Config.API_HOST, str)

    def test_api_endpoint_starts_with_slash(self):
        """API endpoint 应该以 / 开头"""
        assert Config.API_ENDPOINT.startswith("/")

    def test_api_model_not_empty(self):
        """API model 不应为空"""
        assert Config.API_MODEL
        assert isinstance(Config.API_MODEL, str)


class TestEditorConfig:
    """测试编辑器配置"""

    def test_editor_height_positive(self):
        """编辑器高度应该是正整数"""
        assert Config.EDITOR_HEIGHT > 0

    def test_editor_font_size_reasonable(self):
        """编辑器字体大小应该合理（10-30）"""
        assert 10 <= Config.EDITOR_FONT_SIZE <= 30
