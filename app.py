"""
主应用文件 (app.py)
===================

Math OCR App 的入口文件，负责整合各模块并协调数据流。

应用结构：
    ┌─────────────────────────────────────────┐
    │            上传手稿区域                  │
    │  (upload_section.py)                    │
    ├─────────────────────────────────────────┤
    │         [🚀 开始识别按钮]                │
    ├───────────────┬─────────────────────────┤
    │  LaTeX 编辑器  │      公式预览           │
    │  (1/3 宽度)    │      (2/3 宽度)         │
    │ latex_editor  │   preview_section       │
    └───────────────┴─────────────────────────┘

数据流：
    用户上传图片 → OCR 识别 → LaTeX 代码 → 预览/PDF

核心状态：
    st.session_state.latex_output: 当前 LaTeX 代码

启动检查：
    - API 密钥验证

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

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Math OCR",
    page_icon="📐",
    layout="wide",
)

st.title("一键式数学手稿 OCR")

# ============================================================
# 数据收集告知
# ============================================================
if ANALYTICS_ENABLED:
    if "analytics_noticed" not in st.session_state:
        st.session_state.analytics_noticed = False

    if not st.session_state.analytics_noticed:
        with st.expander("📊 数据收集说明", expanded=False):
            st.info(
                """
                **本应用会收集匿名使用数据，仅用于优化和调试项目。**
                
                ✅ **收集的数据**：使用时间、操作类型、图片数量、处理结果
                
                ❌ **不会收集**：个人身份、图片内容、LaTeX 代码、API 密钥
                
                📁 数据存储在本地 `analytics_data.json` 文件中
                
                🚫 如需禁用，在 `.env` 文件中添加 `DISABLE_ANALYTICS=true`
                """
            )
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
    st.error(f"⚠️ 配置错误：{api_error}")
    st.info("请创建 `.env` 文件并添加：\n```\nAPI_KEY=your_api_key_here\n```")
    st.stop()

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
        st.error(f"上传模块出错：{str(e)}")
    else:
        st.error("图片上传处理失败，请检查图片格式后重试")
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
            label="今日剩余次数",
            value=f"{usage_info['remaining']}/{usage_info['limit']}",
        )
    else:
        st.error(f"今日已用完 {usage_info['limit']} 次")

with col_btn:
    if uploaded_files and images:
        # 检查是否还能调用 API
        api_available, api_message = can_use_api()

        if not api_available:
            st.warning(f"⚠️ {api_message}")
            st.button("🚀 开始识别", use_container_width=True, disabled=True)
        else:
            if st.button("🚀 开始识别", use_container_width=True):
                start_time = time.time()
                with st.spinner(f"正在解析数学逻辑...（已上传 {len(images)} 张图片）"):
                    result = run_ocr(images)
                    processing_time = round(time.time() - start_time, 2)

                    if result:
                        # 识别成功，增加使用次数
                        increment_usage()
                        st.session_state.latex_output = result

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

                        st.success("识别完成！")
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
        st.info("👆 上传图片进行 OCR 识别，或直接在下方编辑区输入 LaTeX 代码")

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
            st.error(f"编辑模块出错：{str(e)}")
        else:
            st.error("编辑器加载失败，请刷新页面重试")

with col3:
    try:
        render_preview_section()
    except Exception as e:
        if Config.DEBUG_MODE:
            st.error(f"预览模块出错：{str(e)}")
        else:
            st.error("预览加载失败，请刷新页面重试")
