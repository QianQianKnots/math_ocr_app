"""
多语言支持模块 (lang.py)
=======================

提供中英文双语支持，通过侧边栏切换语言。

使用方法：
    from lang import get_text, get_current_lang

    # 获取当前语言的文本
    title = get_text("title")

    # 获取当前语言
    lang = get_current_lang()

作者: Math OCR App
最后更新: 2026-01-14
"""

import streamlit as st

__all__ = ["LANGUAGES", "get_text", "get_current_lang", "render_language_selector"]

# ============================================================
# 语言配置
# ============================================================
LANGUAGES = {
    "中文": {
        # 通用
        "app_title": "一键式数学手稿 OCR",
        "app_subtitle": "将手写数学公式转换为 LaTeX 代码",
        # 数据收集说明
        "analytics_title": "📊 数据收集说明",
        "analytics_content": """
**本应用会收集匿名使用数据，仅用于优化和调试项目。**

✅ **收集的数据**：使用时间、操作类型、图片数量、处理结果

❌ **不会收集**：个人身份、图片内容、LaTeX 代码、API 密钥

📁 数据存储在本地 `analytics_data.json` 文件中

🚫 如需禁用，在 `.env` 文件中添加 `DISABLE_ANALYTICS=true`
""",
        # 上传区域
        "upload_header": "📸 上传手稿",
        "upload_hint": "选择公式图片（最多{max_files}张，将按顺序拼接识别）",
        "upload_warning": "最多只能上传{max_files}张图片，当前已选择{current}张，将只处理前{max_files}张",
        "upload_tip": "💡 提示：使用箭头按钮调整图片顺序",
        "image_label": "图片",
        "swap_help": "交换这两张图片的位置",
        # 识别按钮
        "start_btn": "🚀 开始识别",
        "remaining_label": "今日剩余次数",
        "limit_reached": "今日已用完 {limit} 次",
        "recognition_spinner": "正在解析数学逻辑...（已上传 {count} 张图片）",
        "recognition_success": "识别完成！",
        "upload_prompt": "👆 上传图片进行 OCR 识别，或直接在下方编辑区输入 LaTeX 代码",
        "api_limit_warning": "⚠️ {message}",
        # 编辑器
        "editor_header": "📝 LaTeX 代码",
        "copy_btn": "📋 复制",
        "editor_tip": "💡 编辑器支持行号显示，修改后点击外部区域更新预览",
        "copy_instruction": "👆 将鼠标悬停在下方代码框右上角，点击出现的复制图标即可复制",
        "collapse_btn": "收起",
        "clear_btn": "🗑️ 清除代码",
        "block_index_title": "📊 代码块索引 ({count} 块) - 与右侧预览对应",
        "block_formula": "公式",
        "block_text": "文本",
        "line_single": "行 {line}",
        "line_range": "行 {start}-{end}",
        "total_lines": "📏 共 {count} 行",
        "editor_placeholder": "在此输入或编辑 LaTeX 代码...",
        # 预览区域
        "preview_header": "✨ 公式预览",
        "preview_prompt": "👈 请先上传图片并点击识别按钮",
        "pdf_btn": "📥 PDF",
        "pdf_download_btn": "下载PDF",
        "pdf_generating": "正在生成PDF...",
        "pdf_source_title": "🔍 查看 PDF 源码",
        "pdf_source_chars": "共 {count} 字符",
        "pdf_need_latex": "需要LaTeX",
        "preview_warning": "⚠️ 检测到完整的 LaTeX 文档。**预览无法完美还原格式**（如居中、字体大小等），仅供参考。**完整排版效果请以 PDF 为准**。",
        "no_preview": "无内容可预览。",
        "formula_render_failed": "公式渲染失败（块 {id}），请检查 LaTeX 语法。",
        "empty_text_block": "*(空文本块 {id})*",
        # 数据统计页面
        "stats_title": "📊 数据统计",
        "stats_today_header": "📈 今日使用量",
        "stats_today_used": "今日已使用",
        "stats_today_remaining": "今日剩余",
        "stats_daily_limit": "每日上限",
        "stats_total_header": "📊 总体统计",
        "stats_no_data": "暂无数据。使用应用后会自动收集统计信息。",
        "stats_total_events": "总事件数",
        "stats_unique_sessions": "独立会话",
        "stats_success_rate": "成功率",
        "stats_date_range": "数据范围",
        "stats_event_dist": "📋 事件类型分布",
        "stats_daily": "📅 每日统计",
        "stats_data_mgmt": "⚙️ 数据管理",
        "stats_storage_location": "数据存储位置：`analytics_data.json`",
        "stats_local_only": "数据仅存储在本地，不会上传到任何服务器。",
        "stats_disabled": "数据收集已禁用。如需启用，请移除 `.env` 文件中的 `DISABLE_ANALYTICS=true`",
        # 事件类型
        "event_app_start": "应用启动",
        "event_ocr": "OCR 识别",
        "event_pdf": "PDF 下载",
        "event_edit": "LaTeX 编辑",
        "event_upload": "图片上传",
        "event_error": "错误",
        # 错误信息
        "error_upload": "图片上传处理失败，请检查图片格式后重试",
        "error_editor": "编辑器加载失败，请刷新页面重试",
        "error_preview": "预览加载失败，请刷新页面重试",
        "error_config": "⚠️ 配置错误：{error}",
        "error_config_hint": "请创建 `.env` 文件并添加：\n```\nAPI_KEY=your_api_key_here\n```",
        # 语言选择
        "language_label": "🌐 语言 / Language",
    },
    "English": {
        # General
        "app_title": "Math Handwriting OCR",
        "app_subtitle": "Convert handwritten math formulas to LaTeX code",
        # Analytics notice
        "analytics_title": "📊 Data Collection Notice",
        "analytics_content": """
**This app collects anonymous usage data for optimization and debugging only.**

✅ **Collected**: Usage time, operation type, image count, results

❌ **Not collected**: Personal identity, image content, LaTeX code, API keys

📁 Data stored locally in `analytics_data.json`

🚫 To disable, add `DISABLE_ANALYTICS=true` to `.env` file
""",
        # Upload section
        "upload_header": "📸 Upload Images",
        "upload_hint": "Select formula images (max {max_files}, will be concatenated)",
        "upload_warning": "Maximum {max_files} images allowed, {current} selected, only first {max_files} will be processed",
        "upload_tip": "💡 Tip: Use arrow buttons to reorder images",
        "image_label": "Image",
        "swap_help": "Swap these two images",
        # Recognition button
        "start_btn": "🚀 Start Recognition",
        "remaining_label": "Remaining Today",
        "limit_reached": "Daily limit of {limit} reached",
        "recognition_spinner": "Analyzing math... ({count} images uploaded)",
        "recognition_success": "Recognition complete!",
        "upload_prompt": "👆 Upload images for OCR, or enter LaTeX code directly below",
        "api_limit_warning": "⚠️ {message}",
        # Editor
        "editor_header": "📝 LaTeX Code",
        "copy_btn": "📋 Copy",
        "editor_tip": "💡 Editor supports line numbers, click outside to update preview",
        "copy_instruction": "👆 Hover over the code box and click the copy icon in the top-right corner",
        "collapse_btn": "Collapse",
        "clear_btn": "🗑️ Clear",
        "block_index_title": "📊 Block Index ({count} blocks) - Corresponds to preview",
        "block_formula": "Formula",
        "block_text": "Text",
        "line_single": "Line {line}",
        "line_range": "Lines {start}-{end}",
        "total_lines": "📏 Total {count} lines",
        "editor_placeholder": "Enter or edit LaTeX code here...",
        # Preview section
        "preview_header": "✨ Formula Preview",
        "preview_prompt": "👈 Please upload images and click recognition button first",
        "pdf_btn": "📥 PDF",
        "pdf_download_btn": "Download PDF",
        "pdf_generating": "Generating PDF...",
        "pdf_source_title": "🔍 View PDF Source",
        "pdf_source_chars": "{count} characters",
        "pdf_need_latex": "LaTeX required",
        "preview_warning": "⚠️ Full LaTeX document detected. **Preview cannot perfectly render formatting** (centering, font size, etc.). **Please refer to PDF for accurate layout.**",
        "no_preview": "No content to preview.",
        "formula_render_failed": "Formula rendering failed (block {id}), please check LaTeX syntax.",
        "empty_text_block": "*(Empty text block {id})*",
        # Stats page
        "stats_title": "📊 Statistics",
        "stats_today_header": "📈 Today's Usage",
        "stats_today_used": "Used Today",
        "stats_today_remaining": "Remaining",
        "stats_daily_limit": "Daily Limit",
        "stats_total_header": "📊 Overall Statistics",
        "stats_no_data": "No data yet. Statistics will be collected as you use the app.",
        "stats_total_events": "Total Events",
        "stats_unique_sessions": "Unique Sessions",
        "stats_success_rate": "Success Rate",
        "stats_date_range": "Date Range",
        "stats_event_dist": "📋 Event Distribution",
        "stats_daily": "📅 Daily Statistics",
        "stats_data_mgmt": "⚙️ Data Management",
        "stats_storage_location": "Storage location: `analytics_data.json`",
        "stats_local_only": "Data is stored locally only, never uploaded to any server.",
        "stats_disabled": "Data collection is disabled. To enable, remove `DISABLE_ANALYTICS=true` from `.env` file",
        # Event types
        "event_app_start": "App Start",
        "event_ocr": "OCR Recognition",
        "event_pdf": "PDF Download",
        "event_edit": "LaTeX Edit",
        "event_upload": "Image Upload",
        "event_error": "Error",
        # Error messages
        "error_upload": "Image upload failed, please check format and try again",
        "error_editor": "Editor failed to load, please refresh the page",
        "error_preview": "Preview failed to load, please refresh the page",
        "error_config": "⚠️ Configuration error: {error}",
        "error_config_hint": "Please create a `.env` file and add:\n```\nAPI_KEY=your_api_key_here\n```",
        # Language selector
        "language_label": "🌐 Language / 语言",
    },
}


def get_current_lang() -> str:
    """获取当前语言设置"""
    return st.session_state.get("lang", "中文")


def get_text(key: str, **kwargs) -> str:
    """
    获取当前语言的文本

    Args:
        key: 文本键名
        **kwargs: 格式化参数

    Returns:
        翻译后的文本
    """
    lang = get_current_lang()
    text = LANGUAGES.get(lang, LANGUAGES["中文"]).get(key, key)

    # 支持格式化参数
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def render_language_selector() -> str:
    """
    渲染语言选择器（放在侧边栏）

    Returns:
        当前选择的语言
    """
    with st.sidebar:
        lang = st.selectbox(
            "🌐 Language / 语言",
            options=list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(get_current_lang()),
            key="language_selector",
        )
        st.session_state.lang = lang
    return lang
