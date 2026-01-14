"""
LaTeX 代码编辑模块 (latex_editor.py)
===================================

负责 LaTeX 代码的编辑和显示，使用 Ace 编辑器。

主要功能：
    - render_latex_editor(): 渲染编辑器区域

功能特性：
    - 语法高亮
    - 行号显示
    - 代码块索引
    - 复制按钮

依赖模块：
    - streamlit: Web UI 框架
    - streamlit_ace: Ace 编辑器组件
    - config.py: 编辑器配置
    - latex_utils.py: LaTeX 解析

数据流：
    st.session_state.latex_output ←→ 编辑器内容

作者: Math OCR App
最后更新: 2026-01-14
"""

import streamlit as st
import re
from streamlit_ace import st_ace

from config import Config
from latex_utils import parse_latex_blocks
from lang import get_text

# 模块公共接口
__all__ = ["render_latex_editor"]


def _extract_renderable_content(latex_code):
    """
    从完整的 LaTeX 文档中提取可渲染的内容。
    与 preview_section.py 保持一致，确保索引对应。
    """
    is_full_document = (
        "\\documentclass" in latex_code or "\\begin{document}" in latex_code
    )

    if not is_full_document:
        return latex_code, False

    doc_match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}", latex_code, re.DOTALL
    )

    if doc_match:
        content = doc_match.group(1).strip()
    else:
        lines = latex_code.split("\n")
        content_lines = []
        in_preamble = True
        for line in lines:
            stripped = line.strip()
            if any(
                cmd in stripped
                for cmd in [
                    "\\documentclass",
                    "\\usepackage",
                    "\\geometry",
                    "\\pagestyle",
                    "\\title",
                    "\\author",
                    "\\date",
                    "\\maketitle",
                    "\\tableofcontents",
                ]
            ):
                continue
            if "\\begin{document}" in stripped:
                in_preamble = False
                continue
            if "\\end{document}" in stripped:
                break
            if not in_preamble or not stripped.startswith("\\"):
                content_lines.append(line)
        content = "\n".join(content_lines).strip()

    content = re.sub(r"\\section\*?\{([^}]*)\}", r"\\textbf{\\Large \1}", content)
    content = re.sub(r"\\subsection\*?\{([^}]*)\}", r"\\textbf{\1}", content)
    content = re.sub(r"\\paragraph\*?\{([^}]*)\}", r"\\textbf{\1}", content)
    content = re.sub(r"\\vspace\{[^}]*\}", "", content)
    content = re.sub(r"\\hspace\{[^}]*\}", "", content)
    content = re.sub(r"\\newpage", "", content)
    content = re.sub(r"\\clearpage", "", content)
    content = re.sub(r"\\label\{[^}]*\}", "", content)
    content = re.sub(r"\\ref\{[^}]*\}", "[ref]", content)
    content = re.sub(r"\\eqref\{[^}]*\}", "[eq]", content)
    content = re.sub(r"\\begin\{center\}", "", content)
    content = re.sub(r"\\end\{center\}", "", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip(), True


def render_latex_editor():
    """
    渲染 LaTeX 代码编辑器。
    读取和写入 st.session_state.latex_output。
    """
    L = get_text
    
    # 标题和复制按钮在同一行
    col_title, col_copy = st.columns([8, 2])
    with col_title:
        st.header(L("editor_header"))
    with col_copy:
        # 始终显示复制按钮
        if st.button(L("copy_btn"), key="copy_latex_btn"):
            if st.session_state.get("latex_output", "").strip():
                st.session_state.show_copy_code = True

    # 显示可复制的代码块（在标题下方）
    if st.session_state.get("show_copy_code") and st.session_state.get(
        "latex_output", ""
    ):
        st.info(L("copy_instruction"))
        st.code(st.session_state.latex_output, language="latex")
        if st.button(L("collapse_btn"), key="hide_copy_code"):
            st.session_state.show_copy_code = False
            st.rerun()

    # 显示编辑提示
    st.caption(L("editor_tip"))

    # 获取当前 LaTeX 内容
    current_latex = st.session_state.get("latex_output", "")

    # 使用内容的哈希作为 key 的一部分，确保内容变化时编辑器刷新
    # 这解决了 st_ace 不自动更新 value 的问题
    editor_key = f"latex_ace_editor_{hash(current_latex) % 10000}"

    # 使用 Ace 编辑器（支持行号）
    new_latex = st_ace(
        value=current_latex,
        language="latex",
        theme="tomorrow",  # 浅色主题
        height=Config.EDITOR_HEIGHT,
        font_size=Config.EDITOR_FONT_SIZE,
        show_gutter=True,  # 显示行号
        show_print_margin=False,
        wrap=True,  # 自动换行
        key=editor_key,
        placeholder=L("editor_placeholder"),
    )

    # 更新 session_state（st_ace 返回值可能为 None）
    if new_latex is not None and new_latex != current_latex:
        st.session_state.latex_output = new_latex
        current_latex = new_latex  # 更新当前内容

    # 清除按钮
    if current_latex.strip():
        if st.button(L("clear_btn"), key="clear_latex"):
            st.session_state.latex_output = ""
            st.session_state.show_copy_code = False
            st.rerun()

        # 显示代码块索引（使用与预览区相同的处理方式）
        processed_latex, is_full_doc = _extract_renderable_content(current_latex)
        blocks = parse_latex_blocks(processed_latex)

        if blocks:
            with st.expander(
                L("block_index_title", count=len(blocks)), expanded=False
            ):
                for block in blocks:
                    block_type_text = (
                        f"📐 {L('block_formula')}" if block["type"] == "environment" else f"📝 {L('block_text')}"
                    )
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(
                            f"<span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
                            f"color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; "
                            f"font-weight: bold;'>[{block['id']}]</span>",
                            unsafe_allow_html=True,
                        )
                    with col2:
                        # 单行显示"行 X"，多行显示"行 X-Y"
                        if block["start_line"] == block["end_line"]:
                            line_info = L("line_single", line=block["start_line"])
                        else:
                            line_info = L("line_range", start=block["start_line"], end=block["end_line"])
                        st.markdown(
                            f"<span style='color: #666; font-size: 13px;'>"
                            f"{block_type_text} · {line_info}</span>",
                            unsafe_allow_html=True,
                        )
                    # 显示代码预览（截断）
                    preview_text = block["content"][:80].replace("\n", " ")
                    if len(block["content"]) > 80:
                        preview_text += "..."
                    st.code(preview_text, language="latex")

        # 显示行数统计
        line_count = len(current_latex.split("\n"))
        st.caption(L("total_lines", count=line_count))
