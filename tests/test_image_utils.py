"""
图片工具模块测试 (test_image_utils.py)
=====================================

测试 image_utils.py 中的所有函数。

运行方式：
    pytest tests/test_image_utils.py -v
"""
import pytest
import base64
from PIL import Image

from image_utils import (
    convert_to_rgb,
    create_thumbnail,
    image_to_base64,
    validate_image,
    validate_file_size,
    concatenate_images,
)


class TestConvertToRGB:
    """测试 convert_to_rgb 函数"""

    def test_rgb_image_unchanged(self):
        """RGB 图片应该保持不变"""
        img = Image.new("RGB", (100, 100), color="red")
        result = convert_to_rgb(img)
        assert result.mode == "RGB"
        assert result.size == (100, 100)

    def test_rgba_to_rgb(self):
        """RGBA 图片应该正确转换为 RGB"""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        result = convert_to_rgb(img)
        assert result.mode == "RGB"
        assert result.size == (100, 100)

    def test_palette_to_rgb(self):
        """调色板模式 (P) 应该正确转换为 RGB"""
        img = Image.new("P", (100, 100))
        result = convert_to_rgb(img)
        assert result.mode == "RGB"

    def test_grayscale_to_rgb(self):
        """灰度图 (L) 应该正确转换为 RGB"""
        img = Image.new("L", (100, 100), color=128)
        result = convert_to_rgb(img)
        assert result.mode == "RGB"

    def test_la_to_rgb(self):
        """带 alpha 的灰度图 (LA) 应该正确转换"""
        img = Image.new("LA", (100, 100))
        result = convert_to_rgb(img)
        assert result.mode == "RGB"


class TestCreateThumbnail:
    """测试 create_thumbnail 函数"""

    def test_large_image_scaled_down(self):
        """大图应该被缩小到指定高度"""
        img = Image.new("RGB", (1000, 500))
        thumbnail = create_thumbnail(img, max_height=100)
        assert thumbnail.size[1] <= 100

    def test_small_image_unchanged(self):
        """小于最大高度的图应该保持不变"""
        img = Image.new("RGB", (50, 50))
        thumbnail = create_thumbnail(img, max_height=100)
        assert thumbnail.size == (50, 50)

    def test_aspect_ratio_preserved(self):
        """缩放应该保持宽高比"""
        img = Image.new("RGB", (200, 100))  # 2:1 比例
        thumbnail = create_thumbnail(img, max_height=50)
        # 高度变为 50，宽度应该变为 100
        assert thumbnail.size == (100, 50)

    def test_returns_rgb(self):
        """返回的缩略图应该是 RGB 模式"""
        img = Image.new("RGBA", (200, 200))
        thumbnail = create_thumbnail(img, max_height=100)
        assert thumbnail.mode == "RGB"


class TestValidateImage:
    """测试 validate_image 函数"""

    def test_valid_image(self):
        """正常尺寸图片应该通过验证"""
        img = Image.new("RGB", (1000, 1000))
        is_valid, error = validate_image(img)
        assert is_valid is True
        assert error == ""

    def test_too_large_image(self):
        """超过最大尺寸的图片应该被拒绝"""
        img = Image.new("RGB", (10000, 10000))
        is_valid, error = validate_image(img)
        assert is_valid is False
        assert "过大" in error

    def test_too_small_image(self):
        """过小的图片应该被拒绝"""
        img = Image.new("RGB", (5, 5))
        is_valid, error = validate_image(img)
        assert is_valid is False
        assert "过小" in error

    def test_edge_case_minimum(self):
        """刚好 10x10 的图片应该通过"""
        img = Image.new("RGB", (10, 10))
        is_valid, error = validate_image(img)
        assert is_valid is True


class TestValidateFileSize:
    """测试 validate_file_size 函数"""

    def test_valid_size(self):
        """正常大小文件应该通过"""
        is_valid, error = validate_file_size(1024 * 1024)  # 1MB
        assert is_valid is True
        assert error == ""

    def test_too_large(self):
        """超过限制的文件应该被拒绝"""
        is_valid, error = validate_file_size(100 * 1024 * 1024)  # 100MB
        assert is_valid is False
        assert "过大" in error

    def test_zero_size(self):
        """零大小文件应该通过（技术上有效）"""
        is_valid, error = validate_file_size(0)
        assert is_valid is True


class TestConcatenateImages:
    """测试 concatenate_images 函数"""

    def test_empty_list_returns_none(self):
        """空列表应该返回 None"""
        result = concatenate_images([])
        assert result is None

    def test_single_image_returns_copy(self):
        """单张图片应该返回其副本（转为 RGB）"""
        img = Image.new("RGB", (100, 100), color="red")
        result = concatenate_images([img])
        assert result is not None
        assert result.size == (100, 100)
        assert result.mode == "RGB"

    def test_two_images_vertical_concat(self):
        """两张图片应该垂直拼接"""
        img1 = Image.new("RGB", (100, 50), color="red")
        img2 = Image.new("RGB", (100, 50), color="blue")
        result = concatenate_images([img1, img2])
        
        assert result is not None
        assert result.size[0] == 100  # 宽度不变
        assert result.size[1] == 100  # 高度相加

    def test_different_widths_unified(self):
        """不同宽度的图片应该统一为最大宽度"""
        img1 = Image.new("RGB", (100, 50), color="red")
        img2 = Image.new("RGB", (200, 50), color="blue")
        result = concatenate_images([img1, img2])
        
        assert result is not None
        assert result.size[0] == 200  # 应该是最大宽度

    def test_rgba_images_converted(self):
        """RGBA 图片应该在拼接时转为 RGB"""
        img1 = Image.new("RGBA", (100, 50))
        img2 = Image.new("RGBA", (100, 50))
        result = concatenate_images([img1, img2])
        
        assert result is not None
        assert result.mode == "RGB"

    def test_three_images(self):
        """三张图片应该正确拼接"""
        imgs = [
            Image.new("RGB", (100, 30), color="red"),
            Image.new("RGB", (100, 40), color="green"),
            Image.new("RGB", (100, 50), color="blue"),
        ]
        result = concatenate_images(imgs)
        
        assert result is not None
        assert result.size[0] == 100
        assert result.size[1] == 120  # 30 + 40 + 50


class TestImageToBase64:
    """测试 image_to_base64 函数"""

    def test_returns_string(self):
        """应该返回字符串"""
        img = Image.new("RGB", (10, 10), color="red")
        result = image_to_base64(img)
        assert isinstance(result, str)

    def test_valid_base64(self):
        """返回的应该是有效的 base64 编码"""
        img = Image.new("RGB", (10, 10), color="red")
        result = image_to_base64(img)
        
        # 应该能成功解码
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_rgba_converted(self):
        """RGBA 图片应该被转换后编码"""
        img = Image.new("RGBA", (10, 10))
        result = image_to_base64(img)
        
        # 应该成功（不抛出异常）
        assert isinstance(result, str)
        assert len(result) > 0

    def test_jpeg_format(self):
        """默认应该是 JPEG 格式"""
        img = Image.new("RGB", (10, 10), color="red")
        result = image_to_base64(img)
        
        # 解码后检查 JPEG 魔数
        decoded = base64.b64decode(result)
        assert decoded[:2] == b'\xff\xd8'  # JPEG 文件头
