"""
OCR 识别模块 (ocr_module.py)
===========================

负责调用 Gemini API 进行数学公式 OCR 识别。

主要功能：
    - run_ocr(): 执行 OCR 识别，返回 LaTeX 代码

工作流程：
    1. 接收 PIL Image 列表
    2. 垂直拼接为单张图片
    3. 转换为 Base64
    4. 调用 Gemini API
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
from PIL import Image

from config import Config
from image_utils import concatenate_images, image_to_base64

# 模块公共接口
__all__ = ["run_ocr"]


def run_ocr(images: list[Image.Image]) -> str | None:
    """
    执行 OCR 识别

    Args:
        images: PIL Image 对象列表

    Returns:
        识别出的 LaTeX 代码，失败返回 None
    """
    # 拼接所有图片
    try:
        concatenated_image = concatenate_images(images)
    except Exception as e:
        st.error(f"图片拼接失败：{str(e)}")
        return None

    if concatenated_image is None:
        st.error("图片拼接失败：无法处理上传的图片")
        return None

    # 将拼接后的图片转为 base64
    try:
        img_base64 = image_to_base64(concatenated_image)
    except Exception as e:
        st.error(f"图片转换失败：{str(e)}")
        return None

    # 构建提示词
    num_images = len(images)
    if num_images > 1:
        prompt = f"""请**严格识别**图片中的所有数学公式和文字（图片由{num_images}张图片按顺序垂直拼接而成），转换为排版优美的完整 LaTeX 文档。

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
        prompt = """请**严格识别**图片中的所有数学公式和文字，转换为排版优美的完整 LaTeX 文档。

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

    # 使用 http.client 调用 API
    try:
        conn = http.client.HTTPSConnection(Config.API_HOST, timeout=Config.API_TIMEOUT)
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
        conn.request("POST", Config.API_ENDPOINT, payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))

        # 解析 API 响应
        if "choices" in response_json and len(response_json["choices"]) > 0:
            raw_output = response_json["choices"][0]["message"]["content"].strip()
        else:
            error_msg = response_json.get("error", {}).get("message", "未知错误")
            st.error(f"API 返回错误：{error_msg}")
            return None

        # 只移除 markdown 代码块标记，保留完整的 LaTeX 文档结构
        # （后续由 latex_utils.process_latex_input() 统一处理）
        if raw_output.startswith("```"):
            lines = raw_output.split("\n")
            if len(lines) > 2:
                # 移除首行（```latex 或 ```）和末行（```）
                raw_output = "\n".join(lines[1:-1])

        return raw_output.strip()

    except Exception as e:
        st.error(f"识别出错：{str(e)}")
        return None
