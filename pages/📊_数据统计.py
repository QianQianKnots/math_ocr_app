"""
数据统计页面
============

显示应用使用数据的统计信息。

注意：此页面仅供开发者/管理员使用。
"""

import streamlit as st

st.set_page_config(
    page_title="数据统计 - Math OCR",
    page_icon="📊",
    layout="wide",
)

st.title("📊 数据统计")

# 尝试导入分析模块
try:
    from analytics import get_analytics_summary, get_daily_stats, ANALYTICS_ENABLED
    from usage_tracker import get_usage_info
except ImportError as e:
    st.error(f"无法加载分析模块：{e}")
    st.stop()

# 检查是否启用
if not ANALYTICS_ENABLED:
    st.warning(
        "数据收集已禁用。如需启用，请移除 `.env` 文件中的 `DISABLE_ANALYTICS=true`"
    )
    st.stop()

# 使用量信息
st.header("📈 今日使用量")
usage = get_usage_info()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("今日已使用", usage["today"])
with col2:
    st.metric("今日剩余", usage["remaining"])
with col3:
    st.metric("每日上限", usage["limit"])

st.markdown("---")

# 分析数据摘要
st.header("📊 总体统计")
summary = get_analytics_summary()

if summary["total_events"] == 0:
    st.info("暂无数据。使用应用后会自动收集统计信息。")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总事件数", summary["total_events"])
    with col2:
        st.metric("独立会话", summary["unique_sessions"])
    with col3:
        st.metric("成功率", f"{summary['success_rate']}%")
    with col4:
        if summary["date_range"]["start"]:
            st.metric(
                "数据范围",
                f"{summary['date_range']['start']} ~ {summary['date_range']['end']}",
            )

    # 事件类型分布
    st.subheader("📋 事件类型分布")
    events = summary["events_by_type"]
    if events:
        # 翻译事件类型
        event_names = {
            "app_start": "应用启动",
            "ocr_recognition": "OCR 识别",
            "pdf_download": "PDF 下载",
            "latex_edit": "LaTeX 编辑",
            "image_upload": "图片上传",
            "error": "错误",
        }

        for event_type, count in sorted(
            events.items(), key=lambda x: x[1], reverse=True
        ):
            display_name = event_names.get(event_type, event_type)
            st.write(f"- **{display_name}**: {count} 次")

    # 每日统计
    st.subheader("📅 每日统计")
    daily = get_daily_stats()
    if daily:
        # 显示最近 7 天
        sorted_dates = sorted(daily.keys(), reverse=True)[:7]

        for date in sorted_dates:
            stats = daily[date]
            with st.expander(f"📅 {date}", expanded=(date == sorted_dates[0])):
                cols = st.columns(4)
                with cols[0]:
                    st.metric("总操作", stats["total"])
                with cols[1]:
                    st.metric("成功", stats["success"])
                with cols[2]:
                    st.metric("OCR", stats["ocr"])
                with cols[3]:
                    st.metric("PDF", stats["pdf"])

st.markdown("---")

# 数据管理
st.header("⚙️ 数据管理")

st.caption("数据存储位置：`analytics_data.json`")
st.caption("数据仅存储在本地，不会上传到任何服务器。")
