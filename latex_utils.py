"""
LaTeX 工具模块 (latex_utils.py)
==============================

提供 LaTeX 处理的公共函数，被多个模块复用。

主要功能：
    - process_latex_input(): 统一处理 LaTeX 输入
    - parse_latex_blocks(): 将代码分割为块
    - format_block_info(): 格式化块信息
    - get_block_summary(): 获取块摘要

核心逻辑 - process_latex_input():
    输入可能是：
    1. 完整 LaTeX 文档（有 \\documentclass）
    2. 纯公式片段

    输出：
    - latex_for_pdf: 保证是完整文档
    - latex_for_preview: 可被 KaTeX 渲染的内容

依赖模块：
    - re: 正则表达式

作者: Math OCR App
最后更新: 2026-01-14
"""

import re

# 模块公共接口
__all__ = [
    "process_latex_input",
    "parse_latex_blocks",
    "format_block_info",
    "get_block_summary",
]


def process_latex_input(raw_latex):
    """
    统一处理 LaTeX 输入（无论来自 OCR 还是手动输入）。

    返回: (latex_for_pdf, latex_for_preview, is_full_document)
        - latex_for_pdf: 用于生成 PDF 的完整 LaTeX 文档
        - latex_for_preview: 用于预览的简化内容（纯公式/document 内容）
        - is_full_document: 是否为完整文档
    """
    if not raw_latex or not raw_latex.strip():
        return "", "", False

    raw_latex = raw_latex.strip()

    # 判断是否为完整文档
    is_full_document = (
        "\\documentclass" in raw_latex and "\\begin{document}" in raw_latex
    )

    if is_full_document:
        # 完整文档：PDF 用原文，预览提取 document 内容
        latex_for_pdf = raw_latex
        latex_for_preview = _extract_document_content(raw_latex)
    else:
        # 纯公式：预览用原文，PDF 自动包装
        latex_for_preview = raw_latex
        latex_for_pdf = _wrap_with_document(raw_latex)

    return latex_for_pdf, latex_for_preview, is_full_document


def _extract_document_content(full_latex):
    """
    从完整 LaTeX 文档中提取 \\begin{document} 到 \\end{document} 之间的内容。
    """
    # 使用正则提取 document 环境内容
    pattern = r"\\begin\{document\}(.*?)\\end\{document\}"
    match = re.search(pattern, full_latex, re.DOTALL)

    if match:
        content = match.group(1).strip()
        return content

    # 如果正则失败，尝试简单字符串分割
    try:
        start_marker = "\\begin{document}"
        end_marker = "\\end{document}"
        start_idx = full_latex.find(start_marker)
        end_idx = full_latex.find(end_marker)

        if start_idx != -1 and end_idx != -1:
            content = full_latex[start_idx + len(start_marker) : end_idx].strip()
            return content
    except Exception:
        pass

    # 都失败了，返回原文
    return full_latex


def _wrap_with_document(latex_content):
    """
    将纯公式包装成完整的 LaTeX 文档。
    """
    return f"""\\documentclass[12pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{amsfonts}}
\\usepackage{{ctex}}
\\pagestyle{{empty}}
\\begin{{document}}
{latex_content}
\\end{{document}}"""


def parse_latex_blocks(latex_code):
    """
    将 LaTeX 代码分割成多个块，每个块包含一个完整的环境或文本段落。

    返回: list of dict, 每个 dict 包含:
        - 'id': 块的编号 (从 1 开始)
        - 'content': 块的内容
        - 'type': 块的类型 ('environment' 或 'text')
        - 'start_line': 块在原始代码中的起始行号 (从 1 开始)
        - 'end_line': 块在原始代码中的结束行号
    """
    if not latex_code or not latex_code.strip():
        return []

    blocks = []
    current_block_lines = []
    current_block_start = 1
    in_environment = False
    environment_name = None
    block_id = 1

    lines = latex_code.split("\n")

    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()

        # 空行：结束当前块（如果不在环境中）
        if not stripped_line:
            if current_block_lines and not in_environment:
                blocks.append(
                    {
                        "id": block_id,
                        "content": "\n".join(current_block_lines),
                        "type": "text",
                        "start_line": current_block_start,
                        "end_line": line_num - 1,
                    }
                )
                block_id += 1
                current_block_lines = []
                current_block_start = line_num + 1
            continue

        # 检查是否开始一个环境
        begin_match = re.search(r"\\begin\{([^}]+)\}", stripped_line)
        if begin_match and not in_environment:
            # 如果当前有未保存的块，先保存
            if current_block_lines:
                blocks.append(
                    {
                        "id": block_id,
                        "content": "\n".join(current_block_lines),
                        "type": "text",
                        "start_line": current_block_start,
                        "end_line": line_num - 1,
                    }
                )
                block_id += 1
                current_block_lines = []

            in_environment = True
            environment_name = begin_match.group(1)
            current_block_start = line_num
            current_block_lines.append(line)
            continue

        # 检查是否结束一个环境
        if in_environment and environment_name:
            end_pattern = f"\\end{{{environment_name}}}"
            if end_pattern in stripped_line:
                current_block_lines.append(line)
                blocks.append(
                    {
                        "id": block_id,
                        "content": "\n".join(current_block_lines),
                        "type": "environment",
                        "start_line": current_block_start,
                        "end_line": line_num,
                    }
                )
                block_id += 1
                current_block_lines = []
                current_block_start = line_num + 1
                in_environment = False
                environment_name = None
                continue

        # 普通行：添加到当前块
        if not current_block_lines:
            current_block_start = line_num
        current_block_lines.append(line)

    # 添加剩余的块
    if current_block_lines:
        blocks.append(
            {
                "id": block_id,
                "content": "\n".join(current_block_lines),
                "type": "environment" if in_environment else "text",
                "start_line": current_block_start,
                "end_line": len(lines),
            }
        )

    return blocks


def format_block_info(block):
    """格式化块信息，用于显示"""
    block_type = "公式" if block["type"] == "environment" else "文本"
    return (
        f"[{block['id']}] {block_type} (行 {block['start_line']}-{block['end_line']})"
    )


def get_block_summary(blocks):
    """获取所有块的摘要信息"""
    summary = []
    for block in blocks:
        summary.append(format_block_info(block))
    return summary
