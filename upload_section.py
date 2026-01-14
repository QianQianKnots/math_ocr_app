"""
上传手稿模块 (upload_section.py)
===============================

负责图片上传、验证、缩略图显示和顺序调整。

主要功能：
    - render_upload_section(): 渲染上传区域，返回图片列表

功能特性：
    - 支持多图上传（最多 5 张）
    - 自动验证文件大小和图片尺寸
    - 缩略图预览
    - 拖拽调整图片顺序

依赖模块：
    - streamlit: Web UI 框架
    - PIL: 图片处理
    - config.py: 配置常量
    - image_utils.py: 图片工具函数

作者: Math OCR App
最后更新: 2026-01-14
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import streamlit as st
from PIL import Image

from config import Config
from image_utils import (
    convert_to_rgb,
    create_thumbnail,
    image_to_base64,
    validate_image,
    validate_file_size,
)

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile

# 模块公共接口
__all__ = ["render_upload_section"]


def render_upload_section() -> tuple[
    list[UploadedFile] | None, list[Image.Image] | None
]:
    """
    渲染上传手稿部分

    显示文件上传器，处理图片验证，生成缩略图预览。

    Returns:
        (ordered_files, ordered_images): 按用户调整后的顺序排列
        如果没有上传文件，返回 (None, None)
    """
    st.header("📸 上传手稿")

    max_files = Config.MAX_UPLOAD_FILES
    uploaded_files = st.file_uploader(
        f"选择公式图片（最多{max_files}张，将按顺序拼接识别）",
        type=Config.ALLOWED_EXTENSIONS,
        accept_multiple_files=True,
    )

    # 限制最多上传数量
    if uploaded_files and len(uploaded_files) > max_files:
        st.warning(
            f"最多只能上传{max_files}张图片，当前已选择{len(uploaded_files)}张，将只处理前{max_files}张"
        )
        uploaded_files = uploaded_files[:max_files]

    if uploaded_files:
        # 初始化图片顺序
        if "image_order" not in st.session_state:
            st.session_state.image_order = list(range(len(uploaded_files)))

        # 如果上传的图片数量变化，重置顺序
        if len(st.session_state.image_order) != len(uploaded_files):
            st.session_state.image_order = list(range(len(uploaded_files)))

        # 按照顺序重新排列文件
        ordered_files = [uploaded_files[i] for i in st.session_state.image_order]
        ordered_images = []

        for uploaded_file in ordered_files:
            try:
                # 验证文件大小
                file_size = uploaded_file.size
                size_valid, size_error = validate_file_size(file_size)
                if not size_valid:
                    st.warning(f"跳过文件 {uploaded_file.name}：{size_error}")
                    continue

                # 加载图片
                image = Image.open(uploaded_file)

                # 验证图片尺寸
                img_valid, img_error = validate_image(image)
                if not img_valid:
                    st.warning(f"跳过文件 {uploaded_file.name}：{img_error}")
                    continue

                # 转换为 RGB 模式
                image = convert_to_rgb(image)
                ordered_images.append(image)
            except Exception as e:
                st.error(f"图片加载失败（{uploaded_file.name}）：{str(e)}")

        if ordered_images:
            # 显示提示信息
            st.caption("💡 提示：使用箭头按钮调整图片顺序")

            # 显示所有图片的缩略图（支持按钮调整顺序）
            num_images = len(ordered_images)

            # 创建列布局：图片和按钮交替排列
            # 对于n张图片，需要n个图片列和n-1个按钮列，总共2n-1列
            # 列比例：图片列宽一些(5)，按钮列窄一些(1)
            col_ratios = []
            for i in range(num_images):
                col_ratios.append(5)  # 图片列
                if i < num_images - 1:
                    col_ratios.append(1)  # 按钮列（在图片之间）

            cols = st.columns(col_ratios)

            col_idx = 0
            for display_idx, (original_idx, image) in enumerate(
                zip(st.session_state.image_order, ordered_images)
            ):
                # 显示图片
                with cols[col_idx]:
                    try:
                        # 创建缩略图并转换为 base64
                        thumbnail = create_thumbnail(image)
                        thumb_base64 = image_to_base64(thumbnail)

                    except Exception as e:
                        st.error(f"图片处理失败（图片 {display_idx + 1}）：{str(e)}")
                        col_idx += 1
                        if display_idx < num_images - 1:
                            col_idx += 1
                        continue

                    # 显示缩略图（使用 HTML 显示固定尺寸的缩略图）
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin-bottom: 10px;">
                            <div style="display: inline-block; border: 2px solid #e0e0e0; border-radius: 8px; padding: 4px; background: white;">
                                <img src="data:image/jpeg;base64,{thumb_base64}" 
                                     style="max-width: 100%; max-height: 150px; display: block;"
                                     alt="图片 {display_idx + 1}">
                                <div style="position: relative; top: -24px; right: -80%; background: rgba(0,0,0,0.6); color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; display: inline-block;">{display_idx + 1}</div>
                            </div>
                            <p style="margin-top: 4px; color: #666; font-size: 12px;">图片 {display_idx + 1}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # ===================================================================
                    # 【已移除功能】点击缩略图查看大图（模态框）
                    #
                    # 原因：Streamlit 的 st.markdown 中嵌入的 JavaScript 无法可靠执行。
                    #      addEventListener 绑定的事件在 Streamlit 重新渲染后失效，
                    #      导致点击缩略图无法打开模态框。这是 Streamlit 框架的限制，
                    #      因为它会频繁重新渲染 DOM，破坏 JavaScript 事件绑定。
                    #
                    # 原计划实现：
                    # - 点击缩略图弹出全屏模态框显示原图（高清）
                    # - 点击×或背景关闭模态框
                    # - 按 ESC 键关闭模态框
                    #
                    # 替代方案：
                    # - 用户可以右键点击缩略图 → "在新标签页中打开图片" 查看
                    # - 或安装 streamlit-modal 等第三方组件
                    # ===================================================================

                col_idx += 1

                # 在图片之间显示交换按钮
                if display_idx < num_images - 1:
                    with cols[col_idx]:
                        # 添加垂直间距，使按钮与图片中心对齐
                        # 图片高度约150px，标题约20px，按钮应该在中间位置（约75px处）
                        st.markdown("<br><br>", unsafe_allow_html=True)  # 上方间距
                        if st.button(
                            "↔️",
                            key=f"swap_{display_idx}",
                            help="交换这两张图片的位置",
                            use_container_width=True,
                        ):
                            # 与右边位置交换
                            order = st.session_state.image_order.copy()
                            order[display_idx], order[display_idx + 1] = (
                                order[display_idx + 1],
                                order[display_idx],
                            )
                            st.session_state.image_order = order
                            st.rerun()
                        st.markdown("<br><br>", unsafe_allow_html=True)  # 下方间距
                    col_idx += 1

            return ordered_files, ordered_images

    return None, None
