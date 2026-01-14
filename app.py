"""
主应用文件 (app.py)
===================

Math OCR App 的入口文件，负责整合各模块并协调数据流。

支持中英文双语切换。

作者: Math OCR App
最后更新: 2026-01-14
"""

import streamlit as st
import time

# 导入配置和模块
from config import Config
from upload_section import render_upload_section
from ocr_module import run_ocr
from latex_editor import render_latex_editor
from preview_section import render_preview_section
from usage_tracker import can_use_api, get_usage_info, increment_usage
from analytics import log_event, ANALYTICS_ENABLED
from lang import get_text, render_language_selector
from logger import logger

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Math OCR",
    page_icon="📐",
    layout="wide",
)

# ============================================================
# 语言选择（侧边栏）
# ============================================================
render_language_selector()

# 简化获取文本的函数
L = get_text

st.title(L("app_title"))

# ============================================================
# 数据收集告知
# ============================================================
if ANALYTICS_ENABLED:
    if "analytics_noticed" not in st.session_state:
        st.session_state.analytics_noticed = False

    if not st.session_state.analytics_noticed:
        with st.expander(L("analytics_title"), expanded=False):
            st.info(L("analytics_content"))
        st.session_state.analytics_noticed = True

    # 记录应用启动事件（每个会话只记录一次）
    if "app_started_logged" not in st.session_state:
        log_event("app_start")
        st.session_state.app_started_logged = True

# ============================================================
# 启动检查：验证 API 密钥
# ============================================================
api_valid, api_error = Config.validate_api_key()
if not api_valid:
    logger.error(f"API 密钥验证失败: {api_error}")
    st.error(L("error_config", error=api_error))
    st.info(L("error_config_hint"))
    st.stop()

logger.debug("应用启动，API 密钥验证通过")

# ============================================================
# 初始化 session_state
# ============================================================
if "latex_output" not in st.session_state:
    st.session_state.latex_output = ""

# ============================================================
# 第一部分：数据输入区（上传图片 + OCR 识别）
# ============================================================
try:
    uploaded_files, images = render_upload_section()
except Exception as e:
    if Config.DEBUG_MODE:
        st.error(f"Upload error: {str(e)}")
    else:
        st.error(L("error_upload"))
    uploaded_files, images = None, None

# ============================================================
# 使用量显示和 OCR 识别按钮
# ============================================================
usage_info = get_usage_info()
col_btn, col_usage = st.columns([3, 1])

with col_usage:
    # 显示今日使用量
    if usage_info["can_use"]:
        st.metric(
            label=L("remaining_label"),
            value=f"{usage_info['remaining']}/{usage_info['limit']}",
        )
    else:
        st.error(L("limit_reached", limit=usage_info["limit"]))

with col_btn:
    if uploaded_files and images:
        # 检查是否还能调用 API
        api_available, api_message = can_use_api()

        if not api_available:
            st.warning(L("api_limit_warning", message=api_message))
            st.button(L("start_btn"), use_container_width=True, disabled=True)
        else:
            if st.button(L("start_btn"), use_container_width=True):
                start_time = time.time()
                with st.spinner(L("recognition_spinner", count=len(images))):
                    result = run_ocr(images)
                    processing_time = round(time.time() - start_time, 2)

                    if result:
                        # 识别成功，增加使用次数
                        increment_usage()
                        st.session_state.latex_output = result
                        logger.info(
                            f"用户 OCR 成功，图片数: {len(images)}，耗时: {processing_time}s"
                        )

                        # 记录成功事件
                        log_event(
                            "ocr_recognition",
                            success=True,
                            details={
                                "image_count": len(images),
                                "processing_time": processing_time,
                                "latex_length": len(result),
                            },
                        )

                        st.success(L("recognition_success"))
                        st.rerun()
                    else:
                        # 记录失败事件
                        log_event(
                            "ocr_recognition",
                            success=False,
                            details={
                                "image_count": len(images),
                                "processing_time": processing_time,
                                "error_type": "api_failed",
                            },
                        )
    else:
        st.info(L("upload_prompt"))

st.markdown("---")

# ============================================================
# 第二、三部分：编辑区 + 预览区
# ============================================================
col2, col3 = st.columns([1, 2])

with col2:
    try:
        render_latex_editor()
    except Exception as e:
        if Config.DEBUG_MODE:
            st.error(f"Editor error: {str(e)}")
        else:
            st.error(L("error_editor"))

with col3:
    try:
        render_preview_section()
    except Exception as e:
        if Config.DEBUG_MODE:
            st.error(f"Preview error: {str(e)}")
        else:
            st.error(L("error_preview"))
