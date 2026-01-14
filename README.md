# Math OCR App 📐

[中文](#中文) | [English](#english)

---

## 中文

一键式数学手稿 OCR 识别工具，将手写数学公式转换为 LaTeX 代码。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

### ✨ 功能特性

- 📸 **图片上传**：支持多图上传（最多 5 张），自动拼接识别
- 🤖 **AI 识别**：使用 Gemini 模型进行 OCR 识别
- ✏️ **实时编辑**：支持 LaTeX 代码编辑，带语法高亮和行号
- 👀 **实时预览**：KaTeX 渲染数学公式
- 📄 **PDF 导出**：一键下载排版精美的 PDF 文档
- 🌐 **双语支持**：支持中英文界面切换
- 🔢 **使用限制**：每日最多调用 50 次 API

### 🚀 快速开始

#### 1. 克隆项目

```bash
git clone https://github.com/QianQianKnots/math_ocr_app.git
cd math_ocr_app
```

#### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置 API 密钥

创建 `.env` 文件：

```
API_KEY=你的API密钥
DEBUG=false
```

#### 4. 运行应用

```bash
streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

### 📁 项目结构

```
math_ocr_app/
├── app.py                 # 主应用入口
├── config.py              # 配置管理
├── lang.py                # 多语言支持
├── image_utils.py         # 图片处理工具
├── latex_utils.py         # LaTeX 处理工具
├── upload_section.py      # 上传模块
├── ocr_module.py          # OCR 识别模块
├── latex_editor.py        # 编辑器模块
├── preview_section.py     # 预览模块
├── analytics.py           # 数据分析模块
├── usage_tracker.py       # 使用量追踪
├── requirements.txt       # 依赖清单
├── .gitignore             # Git 忽略规则
└── tests/                 # 测试脚本
```

### 🔧 PDF 功能

PDF 导出需要系统安装 LaTeX：

- **Windows**: 安装 [MiKTeX](https://miktex.org/)
- **macOS**: `brew install --cask mactex`
- **Linux**: `sudo apt install texlive-full`

### ⚠️ 注意事项

- 每日 API 调用次数限制为 50 次
- `.env` 文件包含敏感信息，请勿上传到公开仓库
- 预览效果与 PDF 可能略有差异，以 PDF 为准

---

## English

A one-click math handwriting OCR tool that converts handwritten math formulas to LaTeX code.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

### ✨ Features

- 📸 **Image Upload**: Support multiple images (up to 5), auto-concatenation
- 🤖 **AI Recognition**: OCR powered by Gemini model
- ✏️ **Real-time Editing**: LaTeX editor with syntax highlighting and line numbers
- 👀 **Live Preview**: KaTeX rendering for math formulas
- 📄 **PDF Export**: One-click download of beautifully formatted PDF
- 🌐 **Bilingual**: Chinese/English interface switching
- 🔢 **Usage Limit**: Maximum 50 API calls per day

### 🚀 Quick Start

#### 1. Clone the repository

```bash
git clone https://github.com/QianQianKnots/math_ocr_app.git
cd math_ocr_app
```

#### 2. Install dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure API key

Create a `.env` file:

```
API_KEY=your_api_key_here
DEBUG=false
```

#### 4. Run the app

```bash
streamlit run app.py
```

Browser will automatically open http://localhost:8501

### 📁 Project Structure

```
math_ocr_app/
├── app.py                 # Main application
├── config.py              # Configuration
├── lang.py                # Multi-language support
├── image_utils.py         # Image processing
├── latex_utils.py         # LaTeX processing
├── upload_section.py      # Upload module
├── ocr_module.py          # OCR module
├── latex_editor.py        # Editor module
├── preview_section.py     # Preview module
├── analytics.py           # Analytics module
├── usage_tracker.py       # Usage tracking
├── requirements.txt       # Dependencies
├── .gitignore             # Git ignore rules
└── tests/                 # Test scripts
```

### 🔧 PDF Feature

PDF export requires LaTeX installed on your system:

- **Windows**: Install [MiKTeX](https://miktex.org/)
- **macOS**: `brew install --cask mactex`
- **Linux**: `sudo apt install texlive-full`

### ⚠️ Notes

- Daily API call limit: 50 times
- `.env` file contains sensitive info, do not upload to public repositories
- Preview may differ slightly from PDF, PDF is the authoritative source

---

## 📄 License

MIT License

## 🤝 Contributing

Issues and Pull Requests are welcome!
