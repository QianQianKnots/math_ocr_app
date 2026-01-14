"""
公式预览模块 (preview_section.py)
================================

负责 LaTeX 公式渲染和 PDF 生成。

主要功能：
    - render_preview_section(): 渲染预览区域

功能特性：
    - KaTeX 公式渲染
    - 分块显示（数学环境 vs 文本）
    - PDF 生成和下载
    - 查看 PDF 源码

PDF 生成：
    - 优先使用 xelatex（支持中文）
    - 备用 pdflatex
    - 超时保护

依赖模块：
    - streamlit: Web UI 框架
    - subprocess: 调用 LaTeX 编译器
    - config.py: 超时配置
    - latex_utils.py: LaTeX 处理

作者: Math OCR App
最后更新: 2026-01-14
"""

import streamlit as st
import subprocess
import tempfile
import re
from pathlib import Path

from config import Config
from latex_utils import parse_latex_blocks, process_latex_input
from analytics import log_event

# 模块公共接口
__all__ = ["render_preview_section"]


def _extract_renderable_content(latex_code):
    """
    从完整的 LaTeX 文档中提取可以被 KaTeX 渲染的内容。
    KaTeX 只支持数学公式，不支持文档结构命令。
    """
    # 检测是否是完整的 LaTeX 文档
    is_full_document = (
        "\\documentclass" in latex_code or "\\begin{document}" in latex_code
    )

    if not is_full_document:
        return latex_code, False

    # 提取 \begin{document} 和 \end{document} 之间的内容
    doc_match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}", latex_code, re.DOTALL
    )

    if doc_match:
        content = doc_match.group(1).strip()
    else:
        # 如果没有找到 document 环境，移除文档头部分
        lines = latex_code.split("\n")
        content_lines = []
        in_preamble = True
        for line in lines:
            stripped = line.strip()
            # 跳过前导命令
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

    # 转换不被 KaTeX 支持的命令
    # 1. 章节命令直接提取标题文字（不转为 \textbf，避免后续处理出错）
    content = re.sub(r"\\section\*?\{([^}]*)\}", r"\n\n【\1】\n\n", content)
    content = re.sub(r"\\subsection\*?\{([^}]*)\}", r"\n\n\1\n\n", content)
    content = re.sub(r"\\paragraph\*?\{([^}]*)\}", r"\n\n\1\n\n", content)

    # 2. 移除排版命令
    content = re.sub(r"\\vspace\{[^}]*\}", "", content)
    content = re.sub(r"\\hspace\{[^}]*\}", "", content)
    content = re.sub(r"\\newpage", "", content)
    content = re.sub(r"\\clearpage", "", content)
    content = re.sub(r"\\label\{[^}]*\}", "", content)
    content = re.sub(r"\\ref\{[^}]*\}", "[ref]", content)
    content = re.sub(r"\\eqref\{[^}]*\}", "[eq]", content)

    # 3. 处理 center 环境和其他文本格式
    content = re.sub(r"\\begin\{center\}", "", content)
    content = re.sub(r"\\end\{center\}", "", content)

    # 4. 移除 \Large, \textbf 等格式命令，保留内容
    content = re.sub(r"\\Large\s*", "", content)
    content = re.sub(r"\\large\s*", "", content)
    content = re.sub(r"\\textbf\{([^}]*)\}", r"\1", content)
    content = re.sub(r"\\textit\{([^}]*)\}", r"\1", content)

    # 5. 移除 \\ 换行和 \vspace 等
    content = re.sub(r"\\\\", " ", content)
    content = re.sub(r"\{([^{}]*)\}", r"\1", content)  # 移除单层花括号

    # 4. 移除空行过多的情况
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip(), True


def _latex_text_to_markdown(latex_text):
    """
    将 LaTeX 文本块转换为 Markdown 格式显示。
    保护内联数学公式 $...$ 不被处理。
    注意：此转换不完美，完整效果请以 PDF 为准。
    """
    text = latex_text

    # 1. 先提取并保护所有内联数学公式 $...$
    math_placeholders = []

    def save_math(match):
        math_placeholders.append(match.group(0))
        return f"__MATH_{len(math_placeholders) - 1}__"

    # 保护 $...$ 内联公式（非贪婪匹配）
    text = re.sub(r"\$[^$]+\$", save_math, text)

    # 2. 简化处理：只做基本转换，避免复杂正则导致错误
    # 移除 LaTeX 换行符 \\
    text = re.sub(r"\\\\", " ", text)
    # 转换 \textbf{} 为 **粗体**
    text = re.sub(r"\\textbf\{([^}]*)\}", r"**\1**", text)
    # 转换 \textit{} 为 *斜体*
    text = re.sub(r"\\textit\{([^}]*)\}", r"*\1*", text)
    # 转换 \emph{} 为 *斜体*
    text = re.sub(r"\\emph\{([^}]*)\}", r"*\1*", text)
    # 移除 \text{} 但保留内容
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)

    # 移除常见的格式命令（保守处理）
    text = re.sub(r"\\(Large|large|small|tiny|huge|Huge|normalsize)\b\s*", "", text)
    text = re.sub(r"\\(centering|raggedright|raggedleft)\b\s*", "", text)

    # 移除剩余的 \command 形式（不带参数的）
    text = re.sub(r"\\[a-zA-Z]+\s*(?![{])", " ", text)

    # 移除花括号（保守：只移除空花括号或单层）
    text = re.sub(r"\{\s*\}", "", text)  # 空花括号
    text = re.sub(r"\{([^{}]+)\}", r"\1", text)  # 单层花括号

    # 3. 恢复数学公式
    for i, math in enumerate(math_placeholders):
        text = text.replace(f"__MATH_{i}__", math)

    # 清理多余空格和换行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"  +", " ", text)
    text = text.strip()

    return text if text else "(空文本块)"


def render_preview_section():
    """渲染公式预览部分"""
    st.header("✨ 公式预览")

    # 获取原始 LaTeX 代码
    raw_latex = st.session_state.get("latex_output", "").strip()

    if raw_latex:
        # 使用统一处理函数获取预览和 PDF 内容
        latex_for_pdf, latex_for_preview, is_full_doc = process_latex_input(raw_latex)

        # 将处理后的内容存入 session_state（供 PDF 生成使用）
        st.session_state.latex_for_pdf = latex_for_pdf

        # 对预览内容做进一步的 KaTeX 兼容处理
        processed_latex, _ = _extract_renderable_content(latex_for_preview)

        if is_full_doc:
            st.warning(
                "⚠️ 检测到完整的 LaTeX 文档。**预览无法完美还原格式**（如居中、字体大小等），"
                "仅供参考。**完整排版效果请以 PDF 为准**。"
            )

        # 标题和下载按钮在同一行
        col_title, col_download = st.columns([10, 1])
        with col_title:
            pass  # 标题已经在上面了
        with col_download:
            # PDF下载按钮
            # 初始化PDF数据存储
            if "pdf_data" not in st.session_state:
                st.session_state.pdf_data = None

            if st.button("📥 PDF", key="download_pdf_btn", help="下载渲染后的PDF"):
                with st.spinner("正在生成PDF..."):
                    # 使用原始 LaTeX 代码生成 PDF（不是处理后的）
                    # 如果是完整文档，直接使用；否则用自动包装的
                    st.session_state.pdf_data = _generate_pdf(latex_for_pdf)

                    # 记录 PDF 生成事件
                    if st.session_state.pdf_data:
                        log_event(
                            "pdf_download",
                            success=True,
                            details={
                                "latex_length": len(latex_for_pdf),
                            },
                        )
                    else:
                        log_event(
                            "pdf_download",
                            success=False,
                            details={
                                "error_type": "compilation_failed",
                            },
                        )

                    st.rerun()

            if st.session_state.pdf_data:
                st.download_button(
                    label="下载PDF",
                    data=st.session_state.pdf_data,
                    file_name="formula.pdf",
                    mime="application/pdf",
                    key="pdf_download",
                )
            elif st.session_state.get("pdf_generation_failed", False):
                st.caption("需要LaTeX")

        # 查看 PDF 源码（放在列外面，全宽显示）
        with st.expander("🔍 查看 PDF 源码", expanded=False):
            st.code(latex_for_pdf, language="latex")
            st.caption(f"共 {len(latex_for_pdf)} 字符")

        # 添加CSS样式确保LaTeX渲染能够适应宽度，并去掉公式边框
        st.markdown(
            """
        <style>
        /* 确保KaTeX公式容器适应宽度 */
        .katex-display {
            display: block;
            margin: 0.5em 0;
            text-align: center;
            max-width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
        }
        
        .katex {
            font-size: 1.1em !important;
            max-width: 100%;
        }
        
        /* 确保公式可以横向滚动而不是破坏布局 */
        .katex-display > .katex {
            display: inline-block;
            max-width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
        }
        
        /* 确保Streamlit的Markdown容器适应宽度 */
        div[data-testid="stMarkdownContainer"] {
            max-width: 100% !important;
            overflow-x: auto;
        }
        
        /* 确保整个预览区域适应宽度 */
        .element-container {
            max-width: 100% !important;
        }
        
        /* 去掉 st.latex 的边框和背景 */
        div[data-testid="stLatex"],
        div[data-testid="stLatex"] > div,
        div[data-testid="stLatex"] > div > div,
        .stLatex,
        .stLatex > div,
        [class*="stLatex"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* 针对 Streamlit 新版本的选择器 */
        .element-container:has(.katex) {
            background: transparent !important;
            border: none !important;
        }
        
        /* 移除公式块之间的分隔样式 */
        .stMarkdown + div[data-testid="stLatex"],
        div[data-testid="stLatex"] + .stMarkdown {
            margin-top: 0.5em !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # 使用共享的分块函数解析处理后的 LaTeX 代码
        latex_blocks = parse_latex_blocks(processed_latex)

        # 将分块信息存储到 session_state，供编辑区使用
        st.session_state.latex_blocks = latex_blocks

        # 显示分块数量提示
        if len(latex_blocks) > 1:
            st.caption(f"📊 共 {len(latex_blocks)} 个代码块，编号与左侧编辑区对应")

        # 逐个渲染每个块
        for block in latex_blocks:
            content = block["content"].strip()
            if content:
                block_type = "📐" if block["type"] == "environment" else "📝"

                # 显示块编号标签
                st.markdown(
                    f"<span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
                    f"color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; "
                    f"font-weight: bold;'>"
                    f"{block_type} [{block['id']}]</span>",
                    unsafe_allow_html=True,
                )

                # 根据块类型选择渲染方式
                if block["type"] == "environment":
                    # 数学环境使用 st.latex 渲染
                    try:
                        st.latex(content)
                    except Exception:
                        # 如果渲染失败，显示为代码块
                        st.code(content, language="latex")
                else:
                    # 普通文本块：转换并显示为 Markdown
                    text_content = _latex_text_to_markdown(content)
                    st.markdown(text_content)
    else:
        st.info("👈 请先上传图片并点击识别按钮")


def _generate_pdf(latex_document):
    """
    将完整的 LaTeX 文档编译为 PDF。

    注意：传入的 latex_document 应该已经是完整文档（由 process_latex_input 处理过）。
    """
    try:
        # 检测是否需要 xelatex（中文文档优先使用 xelatex）
        needs_xelatex = "ctex" in latex_document or "\\setCJK" in latex_document

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "formula.tex"
            pdf_file = Path(tmpdir) / "formula.pdf"

            # 写入LaTeX文件
            tex_file.write_text(latex_document, encoding="utf-8")

            # 确定编译器顺序：中文文档优先 xelatex，否则优先 pdflatex
            if needs_xelatex:
                compilers = ["xelatex", "pdflatex"]
            else:
                compilers = ["pdflatex", "xelatex"]

            last_error = None
            # 尝试编译
            for compiler in compilers:
                try:
                    result = subprocess.run(
                        [
                            compiler,
                            "-interaction=nonstopmode",
                            "-output-directory",
                            tmpdir,
                            str(tex_file),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=Config.PDF_COMPILE_TIMEOUT,
                        cwd=tmpdir,
                    )

                    # 检查 PDF 是否生成（即使 returncode 不是 0，有时也能生成 PDF）
                    if pdf_file.exists():
                        return pdf_file.read_bytes()

                    # 保存错误信息
                    last_error = result.stderr or result.stdout

                except FileNotFoundError:
                    # 该编译器未安装，尝试下一个
                    last_error = f"{compiler} 未安装"
                    continue
                except subprocess.TimeoutExpired:
                    last_error = f"{compiler} 编译超时"
                    continue

            # 所有编译器都失败了，显示错误信息
            st.session_state.pdf_generation_failed = True
            if last_error:
                st.error(f"PDF 生成失败: {last_error[:200]}")
            return None

    except Exception as e:
        st.session_state.pdf_generation_failed = True
        st.error(f"PDF 生成异常: {str(e)}")
        return None


# =============================================================================
# 测试模式代码（已注释，需要时取消注释）
# =============================================================================
#
# 在 render_preview_section() 函数中，st.header() 之后添加以下代码：
#
# # 添加测试模式
# with st.expander("🧪 测试模式（快速测试预览功能）", expanded=False):
#     # 初始化测试代码存储
#     if "test_latex_code" not in st.session_state:
#         st.session_state.test_latex_code = ""
#     if "load_example_flag" not in st.session_state:
#         st.session_state.load_example_flag = False
#
#     # 示例 LaTeX 代码
#     example_latex = r"""\begin{align*}
# \lim_{x \to 0} \frac{f(x)-f(x^3)}{x^3} &= \lim_{x \to 0} \frac{x^2\sin(1/x)}{x^3} \\
# &= \lim_{x \to 0} \frac{1}{x} \sin(1/x)
# \end{align*}
#
# \text{这是一个测试公式。}"""
#
#     if st.session_state.load_example_flag:
#         st.session_state.test_latex_code = example_latex
#         st.session_state.load_example_flag = False
#
#     col_test1, col_test2 = st.columns([3, 1])
#     with col_test1:
#         test_latex = st.text_area(
#             "直接输入 LaTeX 代码进行测试：",
#             value=st.session_state.test_latex_code,
#             height=200,
#             key="test_latex_input",
#         )
#     with col_test2:
#         if st.button("📋 加载示例", use_container_width=True):
#             st.session_state.load_example_flag = True
#             st.rerun()
#         if st.button("✅ 使用测试代码", use_container_width=True):
#             if test_latex.strip():
#                 st.session_state.latex_output = test_latex.strip()
#                 st.rerun()
#
# # 同时需要修改 latex_code_to_use 的判断逻辑：
# # if st.session_state.get("test_latex_code", "").strip():
# #     latex_code_to_use = st.session_state.test_latex_code.strip()
# # elif st.session_state.get("latex_output", "").strip():
# #     latex_code_to_use = st.session_state.latex_output.strip()
# =============================================================================
