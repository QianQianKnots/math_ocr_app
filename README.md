# Math OCR App 📐

一键式数学手稿 OCR 识别工具，将手写数学公式转换为 LaTeX 代码。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

- 📸 **图片上传**：支持多图上传（最多 5 张），自动拼接识别
- 🤖 **AI 识别**：使用 Gemini 模型进行 OCR 识别
- ✏️ **实时编辑**：支持 LaTeX 代码编辑，带语法高亮和行号
- 👀 **实时预览**：KaTeX 渲染数学公式
- 📄 **PDF 导出**：一键下载排版精美的 PDF 文档
- 🔢 **使用限制**：每日最多调用 50 次 API

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/math_ocr_app.git
cd math_ocr_app
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API 密钥

创建 `.env` 文件：

```
API_KEY=你的API密钥
DEBUG=false
```

### 4. 运行应用

```bash
streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

## 📁 项目结构

```
math_ocr_app/
├── app.py                 # 主应用入口
├── config.py              # 配置管理
├── image_utils.py         # 图片处理工具
├── latex_utils.py         # LaTeX 处理工具
├── upload_section.py      # 上传模块
├── ocr_module.py          # OCR 识别模块
├── latex_editor.py        # 编辑器模块
├── preview_section.py     # 预览模块
├── requirements.txt       # 依赖清单
├── .gitignore             # Git 忽略规则
├── .env                   # API 密钥（不上传）
└── tests/                 # 测试脚本
    ├── test_api_connection.py
    └── test_image_recognition.py
```

## 🔧 PDF 功能

PDF 导出需要系统安装 LaTeX：

- **Windows**: 安装 [MiKTeX](https://miktex.org/)
- **macOS**: `brew install --cask mactex`
- **Linux**: `sudo apt install texlive-full`

## 📝 使用说明

1. 上传手写数学公式图片
2. 点击"开始识别"按钮
3. 在左侧编辑器中修改 LaTeX 代码
4. 右侧实时预览效果
5. 点击"PDF"按钮下载

## ⚠️ 注意事项

- 每日 API 调用次数限制为 50 次
- `.env` 文件包含敏感信息，请勿上传到公开仓库
- 预览效果与 PDF 可能略有差异，以 PDF 为准

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
