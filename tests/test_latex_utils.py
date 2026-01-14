"""
LaTeX 工具模块测试 (test_latex_utils.py)
=======================================

测试 latex_utils.py 中的所有函数。

运行方式：
    pytest tests/test_latex_utils.py -v
"""
import pytest

from latex_utils import (
    process_latex_input,
    parse_latex_blocks,
    format_block_info,
    get_block_summary,
)


class TestProcessLatexInput:
    """测试 process_latex_input 函数"""

    def test_empty_input(self):
        """空输入应该返回空字符串"""
        pdf, preview, is_full = process_latex_input("")
        assert pdf == ""
        assert preview == ""
        assert is_full is False

    def test_whitespace_only(self):
        """纯空白输入应该返回空"""
        pdf, preview, is_full = process_latex_input("   \n\t  ")
        assert pdf == ""
        assert preview == ""
        assert is_full is False

    def test_simple_formula(self):
        """简单公式应该被自动包装成完整文档"""
        latex = r"E = mc^2"
        pdf, preview, is_full = process_latex_input(latex)

        assert is_full is False
        assert preview == r"E = mc^2"
        assert r"\documentclass" in pdf
        assert r"\begin{document}" in pdf
        assert r"E = mc^2" in pdf
        assert r"\end{document}" in pdf

    def test_full_document_detected(self):
        """完整文档应该被正确识别"""
        latex = r"""
\documentclass{article}
\begin{document}
E = mc^2
\end{document}
"""
        pdf, preview, is_full = process_latex_input(latex)

        assert is_full is True
        assert r"\documentclass" in pdf
        assert "E = mc^2" in preview

    def test_full_document_preview_extracted(self):
        """完整文档的预览应该只包含 document 内容"""
        latex = r"""
\documentclass{article}
\usepackage{amsmath}
\begin{document}
Hello World
\end{document}
"""
        pdf, preview, is_full = process_latex_input(latex)

        assert is_full is True
        # 预览不应包含 preamble
        assert r"\documentclass" not in preview
        assert r"\usepackage" not in preview
        assert "Hello World" in preview

    def test_formula_with_newlines(self):
        """多行公式应该保持格式"""
        latex = r"""
\begin{align}
a &= b \\
c &= d
\end{align}
"""
        pdf, preview, is_full = process_latex_input(latex)

        assert is_full is False
        assert r"\begin{align}" in preview
        assert r"\begin{align}" in pdf


class TestParseLatexBlocks:
    """测试 parse_latex_blocks 函数"""

    def test_empty_input(self):
        """空输入应该返回空列表"""
        blocks = parse_latex_blocks("")
        assert blocks == []

    def test_whitespace_only(self):
        """纯空白应该返回空列表"""
        blocks = parse_latex_blocks("   \n\n  ")
        assert blocks == []

    def test_single_text_line(self):
        """单行文本应该是一个文本块"""
        blocks = parse_latex_blocks("Hello World")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "text"
        assert blocks[0]["content"] == "Hello World"
        assert blocks[0]["id"] == 1

    def test_equation_environment(self):
        """equation 环境应该被识别为环境块"""
        latex = r"""
\begin{equation}
E = mc^2
\end{equation}
"""
        blocks = parse_latex_blocks(latex)

        env_blocks = [b for b in blocks if b["type"] == "environment"]
        assert len(env_blocks) == 1
        assert r"\begin{equation}" in env_blocks[0]["content"]
        assert r"\end{equation}" in env_blocks[0]["content"]

    def test_align_environment(self):
        """align 环境应该被识别"""
        latex = r"""
\begin{align}
a &= b \\
c &= d
\end{align}
"""
        blocks = parse_latex_blocks(latex)

        env_blocks = [b for b in blocks if b["type"] == "environment"]
        assert len(env_blocks) == 1

    def test_mixed_content(self):
        """混合内容应该正确分块"""
        latex = r"""
Some text here.

\begin{equation}
x = 1
\end{equation}

More text here.
"""
        blocks = parse_latex_blocks(latex)

        types = [b["type"] for b in blocks]
        assert "text" in types
        assert "environment" in types

    def test_block_ids_sequential(self):
        """块 ID 应该是从 1 开始的连续整数"""
        latex = r"""
Text 1

\begin{equation}
x = 1
\end{equation}

Text 2
"""
        blocks = parse_latex_blocks(latex)
        ids = [b["id"] for b in blocks]

        assert ids == list(range(1, len(blocks) + 1))

    def test_line_numbers_present(self):
        """每个块应该有起始和结束行号"""
        latex = "Line 1\nLine 2\nLine 3"
        blocks = parse_latex_blocks(latex)

        for block in blocks:
            assert "start_line" in block
            assert "end_line" in block
            assert block["start_line"] <= block["end_line"]

    def test_multiple_environments(self):
        """多个环境应该被分别识别"""
        latex = r"""
\begin{equation}
a = 1
\end{equation}

\begin{align}
b &= 2 \\
c &= 3
\end{align}
"""
        blocks = parse_latex_blocks(latex)

        env_blocks = [b for b in blocks if b["type"] == "environment"]
        assert len(env_blocks) == 2


class TestFormatBlockInfo:
    """测试 format_block_info 函数"""

    def test_environment_block(self):
        """环境块应该显示为公式"""
        block = {
            "id": 1,
            "type": "environment",
            "start_line": 1,
            "end_line": 3,
            "content": "test",
        }
        result = format_block_info(block)

        assert "[1]" in result
        assert "公式" in result
        assert "1-3" in result

    def test_text_block(self):
        """文本块应该显示为文本"""
        block = {
            "id": 2,
            "type": "text",
            "start_line": 5,
            "end_line": 5,
            "content": "test",
        }
        result = format_block_info(block)

        assert "[2]" in result
        assert "文本" in result


class TestGetBlockSummary:
    """测试 get_block_summary 函数"""

    def test_empty_blocks(self):
        """空块列表应该返回空摘要"""
        summary = get_block_summary([])
        assert summary == []

    def test_multiple_blocks(self):
        """多个块应该返回对应数量的摘要"""
        blocks = [
            {"id": 1, "type": "text", "start_line": 1, "end_line": 1, "content": "a"},
            {"id": 2, "type": "environment", "start_line": 2, "end_line": 4, "content": "b"},
        ]
        summary = get_block_summary(blocks)

        assert len(summary) == 2
        assert "[1]" in summary[0]
        assert "[2]" in summary[1]
