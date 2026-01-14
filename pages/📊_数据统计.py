"""
数据统计页面 / Statistics Page
==============================

显示应用使用数据的统计信息。

注意：此页面仅供开发者/管理员使用。
"""

import streamlit as st

st.set_page_config(
    page_title="Statistics - Math OCR",
    page_icon="📊",
    layout="wide",
)

# 尝试导入分析模块
try:
    from analytics import get_analytics_summary, get_daily_stats, ANALYTICS_ENABLED
    from usage_tracker import get_usage_info
    from lang import get_text, render_language_selector
except ImportError as e:
    st.error(f"Cannot load modules: {e}")
    st.stop()

# 渲染语言选择器
render_language_selector()

# 简化获取文本
L = get_text

st.title(L("stats_title"))

# 检查是否启用
if not ANALYTICS_ENABLED:
    st.warning(L("stats_disabled"))
    st.stop()

# 使用量信息
st.header(L("stats_today_header"))
usage = get_usage_info()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(L("stats_today_used"), usage["today"])
with col2:
    st.metric(L("stats_today_remaining"), usage["remaining"])
with col3:
    st.metric(L("stats_daily_limit"), usage["limit"])

st.markdown("---")

# 分析数据摘要
st.header(L("stats_total_header"))
summary = get_analytics_summary()

if summary["total_events"] == 0:
    st.info(L("stats_no_data"))
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(L("stats_total_events"), summary["total_events"])
    with col2:
        st.metric(L("stats_unique_sessions"), summary["unique_sessions"])
    with col3:
        st.metric(L("stats_success_rate"), f"{summary['success_rate']}%")
    with col4:
        if summary["date_range"]["start"]:
            st.metric(
                L("stats_date_range"),
                f"{summary['date_range']['start']} ~ {summary['date_range']['end']}",
            )

    # 事件类型分布
    st.subheader(L("stats_event_dist"))
    events = summary["events_by_type"]
    if events:
        # 翻译事件类型
        event_keys = {
            "app_start": "event_app_start",
            "ocr_recognition": "event_ocr",
            "pdf_download": "event_pdf",
            "latex_edit": "event_edit",
            "image_upload": "event_upload",
            "error": "event_error",
        }

        for event_type, count in sorted(
            events.items(), key=lambda x: x[1], reverse=True
        ):
            display_name = L(event_keys.get(event_type, event_type))
            st.write(f"- **{display_name}**: {count}")

    # 每日统计
    st.subheader(L("stats_daily"))
    daily = get_daily_stats()
    if daily:
        # 显示最近 7 天
        sorted_dates = sorted(daily.keys(), reverse=True)[:7]

        for date in sorted_dates:
            stats = daily[date]
            with st.expander(f"📅 {date}", expanded=(date == sorted_dates[0])):
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total", stats["total"])
                with cols[1]:
                    st.metric("Success", stats["success"])
                with cols[2]:
                    st.metric("OCR", stats["ocr"])
                with cols[3]:
                    st.metric("PDF", stats["pdf"])

st.markdown("---")

# 数据管理
st.header(L("stats_data_mgmt"))

st.caption(L("stats_storage_location"))
st.caption(L("stats_local_only"))
