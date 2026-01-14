"""
图片工具模块 (image_utils.py)
============================

提供图片处理的公共函数，被多个模块复用，避免代码重复。

主要功能：
    - convert_to_rgb(): 图片格式转换 (RGBA/P → RGB)
    - create_thumbnail(): 生成缩略图
    - image_to_base64(): 图片转 Base64 编码
    - validate_image(): 验证图片尺寸
    - validate_file_size(): 验证文件大小
    - concatenate_images(): 多图垂直拼接

依赖模块：
    - PIL (Pillow): 图片处理库
    - config.py: 配置常量

使用示例：
    from image_utils import convert_to_rgb, create_thumbnail

    image = Image.open("photo.png")
    rgb_image = convert_to_rgb(image)
    thumbnail = create_thumbnail(rgb_image)

作者: Math OCR App
最后更新: 2026-01-14
"""

import io
import base64
from PIL import Image
from config import Config

# 模块公共接口
__all__ = [
    "convert_to_rgb",
    "create_thumbnail",
    "image_to_base64",
    "validate_image",
    "validate_file_size",
    "concatenate_images",
]


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """
    将图片转换为 RGB 模式（处理 RGBA 等不支持 JPEG 的模式）

    Args:
        image: PIL Image 对象

    Returns:
        RGB 模式的 PIL Image 对象
    """
    try:
        if image.mode == "RGB":
            return image
        elif image.mode in ("RGBA", "LA"):
            # 创建白色背景
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            # 使用 alpha 通道作为 mask
            rgb_image.paste(image, mask=image.split()[-1])
            return rgb_image
        elif image.mode == "P":
            # 调色板模式，先转 RGBA
            try:
                rgba_image = image.convert("RGBA")
                rgb_image = Image.new("RGB", rgba_image.size, (255, 255, 255))
                rgb_image.paste(rgba_image, mask=rgba_image.split()[-1])
                return rgb_image
            except Exception:
                return image.convert("RGB")
        else:
            return image.convert("RGB")
    except Exception:
        try:
            return image.convert("RGB")
        except Exception:
            return image


def create_thumbnail(image: Image.Image, max_height: int = None) -> Image.Image:
    """
    创建缩略图

    Args:
        image: PIL Image 对象
        max_height: 最大高度（默认使用配置值）

    Returns:
        缩略图 PIL Image 对象
    """
    if max_height is None:
        max_height = Config.THUMBNAIL_MAX_HEIGHT

    width, height = image.size

    if height > max_height:
        ratio = max_height / height
        new_width = int(width * ratio)
        thumbnail = image.resize((new_width, max_height), Image.Resampling.LANCZOS)
    else:
        thumbnail = image.copy()

    # 确保是 RGB 模式
    return convert_to_rgb(thumbnail)


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """
    将图片转换为 base64 字符串

    Args:
        image: PIL Image 对象
        format: 图片格式（JPEG, PNG 等）

    Returns:
        base64 编码的字符串
    """
    image = convert_to_rgb(image)
    buffer = io.BytesIO()
    image.save(buffer, format=format, quality=Config.JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode()


def validate_image(image: Image.Image) -> tuple[bool, str]:
    """
    验证图片是否符合要求

    Args:
        image: PIL Image 对象

    Returns:
        (是否有效, 错误信息)
    """
    width, height = image.size
    max_dim = Config.MAX_IMAGE_DIMENSION

    if width > max_dim or height > max_dim:
        return False, f"图片尺寸过大（{width}x{height}），最大允许 {max_dim}x{max_dim}"

    if width < 10 or height < 10:
        return False, f"图片尺寸过小（{width}x{height}）"

    return True, ""


def validate_file_size(file_size: int) -> tuple[bool, str]:
    """
    验证文件大小是否符合要求

    Args:
        file_size: 文件大小（字节）

    Returns:
        (是否有效, 错误信息)
    """
    max_size = Config.get_max_file_size_bytes()

    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        return (
            False,
            f"文件过大（{size_mb:.1f}MB），最大允许 {Config.MAX_FILE_SIZE_MB}MB",
        )

    return True, ""


def concatenate_images(images: list[Image.Image]) -> Image.Image | None:
    """
    将多张图片垂直拼接成一张

    Args:
        images: PIL Image 对象列表

    Returns:
        拼接后的 PIL Image 对象，失败返回 None
    """
    if not images:
        return None

    if len(images) == 1:
        return convert_to_rgb(images[0])

    # 统一宽度
    max_width = max(img.size[0] for img in images)
    resized_images = []
    total_height = 0

    for img in images:
        try:
            img = convert_to_rgb(img)
            width, height = img.size

            if width != max_width:
                ratio = max_width / width
                new_height = int(height * ratio)
                resized_img = img.resize(
                    (max_width, new_height), Image.Resampling.LANCZOS
                )
            else:
                resized_img = img

            resized_images.append(resized_img)
            total_height += resized_img.size[1]
        except Exception:
            continue

    if not resized_images:
        return None

    # 创建拼接画布
    concatenated = Image.new("RGB", (max_width, total_height))
    y_offset = 0

    for img in resized_images:
        try:
            concatenated.paste(img, (0, y_offset))
            y_offset += img.size[1]
        except Exception:
            continue

    return concatenated
