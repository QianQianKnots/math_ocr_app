"""
OCR 识别模块 (ocr_module.py)
===========================

负责调用 Gemini API 进行数学公式 OCR 识别。

主要功能：
    - run_ocr(): 执行 OCR 识别，返回 LaTeX 代码

功能特性：
    - 自动重试机制（最多 3 次）
    - 指数退避（2s, 4s, 8s）
    - 区分可重试/不可重试错误

工作流程：
    1. 接收 PIL Image 列表
    2. 垂直拼接为单张图片
    3. 转换为 Base64
    4. 调用 Gemini API（带重试）
    5. 清理并返回 LaTeX 代码

依赖模块：
    - streamlit: 错误提示
    - http.client: API 调用
    - config.py: API 配置
    - image_utils.py: 图片处理

作者: Math OCR App
最后更新: 2026-01-14
"""

import streamlit as st
import http.client
import json
import time
import socket
from PIL import Image

from config import Config
from image_utils import concatenate_images, image_to_base64
from logger import logger

# 模块公共接口
__all__ = ["run_ocr"]

# 可重试的错误类型
RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    socket.timeout,
    ConnectionError,
    ConnectionResetError,
    http.client.HTTPException,
    http.client.RemoteDisconnected,
)

# 重试配置
MAX_RETRIES = 3
BASE_WAIT_TIME = 2  # 基础等待时间（秒）


def _build_prompt(num_images: int) -> str:
    """构建 OCR 提示词"""
    if num_images > 1:
        return f"""请**严格识别**图片中的所有数学公式和文字（图片由{num_images}张图片按顺序垂直拼接而成），转换为排版优美的完整 LaTeX 文档。

**最重要的原则**：
- **严格忠于原文**：不要添加、删减或修改任何内容
- **完整识别**：图片中的每一个字、每一个公式都必须识别并输出
- **保持原有结构**：按照图片从上到下的顺序，完整还原原文的结构和逻辑

**排版格式要求（非常重要）**：
1. **保持换行和留白**：原文中的每一个换行都要保留，不要把多行内容压缩成一行
2. **公式单独成段**：每个独立公式使用 equation 或 align 环境，公式前后各空一行
3. **段落之间留白**：不同段落之间使用空行或 \\vspace{{0.5em}} 分隔
4. **推导步骤清晰**：连续的推导步骤使用 align 环境，每步一行，用 \\\\ 换行
5. **文字和公式分离**：文字段落和公式块之间要有明显分隔

**文档结构要求**：
1. 使用 \\documentclass[12pt, a4paper]{{article}}
2. 必须包含宏包：amsmath, amsthm, amssymb, geometry
3. 如果有中文，使用 \\usepackage[UTF8]{{ctex}}
4. 页面布局：\\geometry{{left=2.5cm, right=2.5cm, top=2.5cm, bottom=2.5cm}}
5. 设置行距：\\linespread{{1.3}}

**输出要求**：
- 直接输出 LaTeX 代码，不要任何解释文字
- 确保文档完整，以 \\end{{document}} 结尾
- **不要遗漏任何内容**

请输出排版优美的完整 LaTeX 文档："""
    else:
        return """请**严格识别**图片中的所有数学公式和文字，转换为排版优美的完整 LaTeX 文档。

**最重要的原则**：
- **严格忠于原文**：不要添加、删减或修改任何内容
- **完整识别**：图片中的每一个字、每一个公式都必须识别并输出
- **保持原有结构**：完整还原原文的结构和逻辑

**排版格式要求（非常重要）**：
1. **保持换行和留白**：原文中的每一个换行都要保留，不要把多行内容压缩成一行
2. **公式单独成段**：每个独立公式使用 equation 或 align 环境，公式前后各空一行
3. **段落之间留白**：不同段落之间使用空行或 \\vspace{0.5em} 分隔
4. **推导步骤清晰**：连续的推导步骤使用 align 环境，每步一行，用 \\\\ 换行
5. **文字和公式分离**：文字段落和公式块之间要有明显分隔

**文档结构要求**：
1. 使用 \\documentclass[12pt, a4paper]{article}
2. 必须包含宏包：amsmath, amsthm, amssymb, geometry
3. 如果有中文，使用 \\usepackage[UTF8]{ctex}
4. 页面布局：\\geometry{left=2.5cm, right=2.5cm, top=2.5cm, bottom=2.5cm}
5. 设置行距：\\linespread{1.3}

**输出要求**：
- 直接输出 LaTeX 代码，不要任何解释文字
- 确保文档完整，以 \\end{document} 结尾
- **不要遗漏任何内容**

请输出排版优美的完整 LaTeX 文档："""


def _call_api(payload: str, headers: dict) -> dict:
    """
    执行单次 API 调用

    Args:
        payload: JSON 格式的请求体
        headers: 请求头

    Returns:
        解析后的 JSON 响应

    Raises:
        各种网络相关异常
    """
    conn = http.client.HTTPSConnection(Config.API_HOST, timeout=Config.API_TIMEOUT)
    conn.request("POST", Config.API_ENDPOINT, payload, headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    return json.loads(data.decode("utf-8"))


def _call_api_with_retry(
    payload: str, headers: dict, status_placeholder
) -> dict | None:
    """
    带重试机制的 API 调用

    Args:
        payload: JSON 格式的请求体
        headers: 请求头
        status_placeholder: Streamlit 占位符，用于显示重试状态

    Returns:
        成功时返回 JSON 响应，失败返回 None
    """
    last_error = None

    logger.info(f"开始 API 调用，模型: {Config.API_MODEL}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 显示当前尝试次数（第一次不显示）
            if attempt > 1:
                logger.info(f"API 重试 {attempt}/{MAX_RETRIES}")
                status_placeholder.info(f"🔄 第 {attempt}/{MAX_RETRIES} 次尝试...")

            response_json = _call_api(payload, headers)

            # 检查 API 返回的业务错误
            if "error" in response_json:
                error_msg = response_json["error"].get("message", "未知错误")

                # 判断是否是可重试的错误（如限流）
                if any(
                    keyword in error_msg.lower()
                    for keyword in ["rate limit", "quota", "overloaded", "busy"]
                ):
                    if attempt < MAX_RETRIES:
                        wait_time = BASE_WAIT_TIME * (2 ** (attempt - 1))
                        status_placeholder.warning(
                            f"⏳ 服务繁忙，{wait_time} 秒后重试..."
                        )
                        time.sleep(wait_time)
                        continue

                # 不可重试的业务错误
                return response_json

            # 成功
            logger.info(f"API 调用成功（第 {attempt} 次尝试）")
            if attempt > 1:
                status_placeholder.success(f"✅ 第 {attempt} 次尝试成功！")
            return response_json

        except RETRYABLE_EXCEPTIONS as e:
            last_error = e
            error_type = type(e).__name__

            if attempt < MAX_RETRIES:
                # 指数退避：2s, 4s, 8s
                wait_time = BASE_WAIT_TIME * (2 ** (attempt - 1))
                logger.warning(f"API 调用失败 ({error_type}: {e})，{wait_time}s 后重试")
                status_placeholder.warning(
                    f"⚠️ 连接失败 ({error_type})，{wait_time} 秒后重试 ({attempt}/{MAX_RETRIES})..."
                )
                time.sleep(wait_time)
            else:
                # 最后一次也失败了
                logger.error(
                    f"API 调用失败，已重试 {MAX_RETRIES} 次: {error_type}: {e}"
                )
                status_placeholder.error(f"❌ 连接失败，已重试 {MAX_RETRIES} 次")

        except json.JSONDecodeError as e:
            # JSON 解析错误，可能是响应不完整，可重试
            last_error = e
            if attempt < MAX_RETRIES:
                wait_time = BASE_WAIT_TIME * (2 ** (attempt - 1))
                status_placeholder.warning(f"⚠️ 响应解析失败，{wait_time} 秒后重试...")
                time.sleep(wait_time)

        except Exception as e:
            # 其他不可重试的错误
            status_placeholder.error(f"❌ 发生错误: {type(e).__name__}: {str(e)}")
            return None

    # 所有重试都失败
    if last_error:
        st.error(f"识别失败，请稍后重试。错误: {type(last_error).__name__}")
    return None


def _clean_output(raw_output: str) -> str:
    """清理 API 输出，移除 markdown 代码块标记"""
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        if len(lines) > 2:
            # 移除首行（```latex 或 ```）和末行（```）
            raw_output = "\n".join(lines[1:-1])
    return raw_output.strip()


def run_ocr(images: list[Image.Image]) -> str | None:
    """
    执行 OCR 识别（带自动重试）

    Args:
        images: PIL Image 对象列表

    Returns:
        识别出的 LaTeX 代码，失败返回 None
    """
    logger.info(f"开始 OCR 识别，图片数量: {len(images)}")

    # 拼接所有图片
    try:
        concatenated_image = concatenate_images(images)
        logger.debug(
            f"图片拼接完成，尺寸: {concatenated_image.size if concatenated_image else 'None'}"
        )
    except Exception as e:
        logger.error(f"图片拼接失败: {e}", exc_info=True)
        st.error(f"图片拼接失败：{str(e)}")
        return None

    if concatenated_image is None:
        logger.error("图片拼接返回 None")
        st.error("图片拼接失败：无法处理上传的图片")
        return None

    # 将拼接后的图片转为 base64
    try:
        img_base64 = image_to_base64(concatenated_image)
        logger.debug(f"Base64 编码完成，长度: {len(img_base64)}")
    except Exception as e:
        logger.error(f"图片转换失败: {e}", exc_info=True)
        st.error(f"图片转换失败：{str(e)}")
        return None

    # 构建请求
    prompt = _build_prompt(len(images))
    payload = json.dumps(
        {
            "model": Config.API_MODEL,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            },
                        },
                    ],
                }
            ],
        }
    )
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {Config.get_api_key()}",
        "Content-Type": "application/json",
    }

    # 创建状态占位符（用于显示重试信息）
    status_placeholder = st.empty()

    # 调用 API（带重试）
    response_json = _call_api_with_retry(payload, headers, status_placeholder)

    # 清除状态信息
    status_placeholder.empty()

    if response_json is None:
        return None

    # 解析 API 响应
    if "choices" in response_json and len(response_json["choices"]) > 0:
        raw_output = response_json["choices"][0]["message"]["content"].strip()
        result = _clean_output(raw_output)
        logger.info(f"OCR 识别成功，LaTeX 长度: {len(result)} 字符")
        return result
    else:
        error_msg = response_json.get("error", {}).get("message", "未知错误")
        logger.error(f"API 返回业务错误: {error_msg}")
        st.error(f"API 返回错误：{error_msg}")
        return None
