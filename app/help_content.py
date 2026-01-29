"""Help content for StudyFlow AI UI.

This module provides in-app documentation that aligns with README.md content.
Supports English and Chinese languages.
"""
from __future__ import annotations

HELP_SECTIONS_EN = [
    {
        "title": "10-Minute Quick Start",
        "expanded": True,
        "bullets": [
            "Step 1: Launch the app (docker compose up or streamlit run app/main.py)",
            "Step 2: Configure your LLM in Settings (Base URL, Model, API Key)",
            "Step 3: Load Demo Data from the Start page",
            "Step 4: Go to Create → Course, link a document, and generate Course Overview",
            "Step 5: Export your output from Recent Activity",
        ],
        "code": "docker compose up --build\n# Open http://localhost:8501",
    },
    {
        "title": "Navigation Overview",
        "bullets": [
            "Start: Setup checklist, quick actions, and recent activity",
            "Library: Import, organize, and index documents by type (Course/Paper/Other)",
            "Create: Generate course materials, paper cards, and presentations",
            "Tools: Study coach, background tasks, settings, diagnostics",
            "Help: This documentation and troubleshooting guides",
        ],
    },
    {
        "title": "Importing Documents",
        "bullets": [
            "Upload PDFs directly or import from external sources",
            "Supported sources: Upload, Zotero, Folder Sync, arXiv, DOI, URL",
            "Documents are automatically chunked and indexed after import",
            "Duplicate files (same hash) are skipped automatically",
            "OCR modes: off (default), auto (low-text pages), on (all pages)",
            "Generate summaries: Click 'Generate Summary' in document details for LLM descriptions",
        ],
    },
    {
        "title": "Retrieval Modes",
        "bullets": [
            "Vector: Semantic search using embeddings (best for conceptual queries)",
            "BM25: Keyword-based lexical search (best for exact terms)",
            "Hybrid: Fused Vector + BM25 scores (best overall accuracy)",
            "Select your default mode in Settings; can override per query",
        ],
    },
    {
        "title": "Create: Course Materials",
        "bullets": [
            "Step 1: Select or create a course from the sidebar",
            "Step 2: Link lecture PDFs to the course",
            "Step 3: Generate outputs using the action buttons",
            "Available outputs: Course Overview, Exam Cheatsheet, Knowledge Q&A, Explain Selection",
            "All outputs include citations to source pages",
        ],
    },
    {
        "title": "Create: Paper Analysis",
        "bullets": [
            "Select a paper document from your library",
            "Generate Paper Card: Structured analysis with contributions, strengths, weaknesses",
            "Aggregate Papers: Compare multiple papers around a research question",
            "Citations link back to specific pages in source documents",
        ],
    },
    {
        "title": "Create: Presentations",
        "bullets": [
            "Select a source document (any type)",
            "Choose duration: 1-30 minutes",
            "Generates Marp-format slides with speaker notes",
            "Includes Q&A discussion questions",
            "Download as Markdown for use with Marp CLI or VS Code extension",
        ],
    },
    {
        "title": "Study Coach",
        "bullets": [
            "Two-phase learning approach for deeper understanding",
            "Phase A (Framework): Get key concepts, approach hints, and common pitfalls",
            "Phase B (Review): Submit your answer for feedback and rubric evaluation",
            "Coach deliberately avoids giving complete answers to encourage learning",
            "Sessions are saved with custom naming for easy reference",
            "Coach references all documents in your library by default",
        ],
    },
    {
        "title": "Background Tasks",
        "bullets": [
            "Long operations (ingest, index, generate) run in background",
            "View all tasks in Tools → Tasks with progress indicators",
            "Task controls: Run, Cancel, Retry, or Resume",
            "Page navigation allowed during task execution",
            "Write operations are locked while tasks are running (with indicator)",
        ],
    },
    {
        "title": "Settings",
        "bullets": [
            "UI Mode: Direct (local processing) or API (remote server)",
            "LLM Settings: Base URL, Model name, API Key, Temperature",
            "OCR Settings: Mode (off/auto/on) and text threshold",
            "Language: Interface and output language (English/Chinese)",
            "Test connections: Use Ping API and Test LLM buttons to verify",
        ],
    },
    {
        "title": "Plugins",
        "bullets": [
            "Importers: Batch import from folders, Zotero, arXiv, DOI, URL",
            "Exporters: Export assets to folders, export citations as JSON/TXT",
            "Run plugins from Tools → Plugins",
        ],
    },
    {
        "title": "Troubleshooting",
        "expanded": True,
        "bullets": [
            "LLM not configured: Set Base URL, Model, and API Key in Settings",
            "Buttons disabled: Check Setup Checklist on Start page for missing requirements",
            "Embedding error: Set STUDYFLOW_EMBED_MODEL env var or use BM25 mode",
            "Index not building: Use Diagnostics → Rebuild Index or CLI: studyflow index build",
            "Parse failed: Ensure PDFs are not encrypted and contain text layers",
            "OCR not working: Install Tesseract and set STUDYFLOW_OCR_MODE=auto",
            "API 503 error: Ensure backend is running if using API mode",
        ],
    },
    {
        "title": "CLI Commands",
        "bullets": [
            "studyflow doctor --deep: Full system health check",
            "studyflow workspace create <name>: Create new workspace",
            "studyflow ingest --workspace <id> file.pdf: Import document",
            "studyflow index build --workspace <id>: Build search index",
            "studyflow query --workspace <id> --mode hybrid 'question': Search documents",
            "studyflow gen --workspace <id> --type slides --source <id>: Generate content",
            "studyflow clean --workspace <id> --dry-run: Preview cleanup",
        ],
    },
    {
        "title": "Privacy & Data",
        "bullets": [
            "All data stays on your machine (local-first design)",
            "API keys are never written to disk",
            "No telemetry or usage data collection",
            "Data location: workspaces/<id>/ contains uploads, indexes, outputs",
            "Export all data: Use studyflow bundle export for portable backup",
        ],
    },
    {
        "title": "Keyboard Shortcuts",
        "bullets": [
            "Ctrl/Cmd + Enter: Submit forms and queries",
            "Escape: Close dialogs",
            "Tab: Navigate between form fields",
        ],
    },
]

HELP_SECTIONS_ZH = [
    {
        "title": "10分钟快速开始",
        "expanded": True,
        "bullets": [
            "步骤 1: 启动应用 (docker compose up 或 streamlit run app/main.py)",
            "步骤 2: 在设置中配置 LLM (Base URL, 模型, API Key)",
            "步骤 3: 从开始页面加载演示数据",
            "步骤 4: 进入创作 → 课程，关联文档并生成课程概览",
            "步骤 5: 从最近活动中导出输出",
        ],
        "code": "docker compose up --build\n# 打开 http://localhost:8501",
    },
    {
        "title": "导航概览",
        "bullets": [
            "开始: 设置检查清单、快捷操作和最近活动",
            "资料库: 按类型（课程/论文/其他）导入、整理和索引文档",
            "创作: 生成课程材料、论文卡片和演示文稿",
            "工具: 学习教练、后台任务、设置、诊断",
            "帮助: 本文档和故障排除指南",
        ],
    },
    {
        "title": "导入文档",
        "bullets": [
            "直接上传 PDF 或从外部来源导入",
            "支持来源: 上传、Zotero、文件夹同步、arXiv、DOI、URL",
            "导入后文档会自动分块和建立索引",
            "重复文件（相同哈希）会自动跳过",
            "OCR 模式: 关闭（默认）、自动（低文本页面）、开启（所有页面）",
            "生成简介: 在文档详情中点击「生成简介」获取 LLM 生成的描述",
        ],
    },
    {
        "title": "检索模式",
        "bullets": [
            "向量: 使用嵌入的语义搜索（适合概念性查询）",
            "BM25: 基于关键词的词汇搜索（适合精确术语）",
            "混合: 向量 + BM25 融合分数（综合准确度最佳）",
            "在设置中选择默认模式；可按查询覆盖",
        ],
    },
    {
        "title": "创作: 课程材料",
        "bullets": [
            "步骤 1: 从侧边栏选择或创建课程",
            "步骤 2: 将讲义 PDF 关联到课程",
            "步骤 3: 使用操作按钮生成输出",
            "可用输出: 课程概览、考试备忘、知识问答、解释选中内容",
            "所有输出都包含源页面引用",
        ],
    },
    {
        "title": "创作: 论文分析",
        "bullets": [
            "从资料库选择论文文档",
            "生成论文卡片: 包含贡献、优势、弱点的结构化分析",
            "聚合论文: 围绕研究问题比较多篇论文",
            "引用链接回源文档的具体页面",
        ],
    },
    {
        "title": "创作: 演示文稿",
        "bullets": [
            "选择源文档（任何类型）",
            "选择时长: 1-30 分钟",
            "生成带演讲笔记的 Marp 格式幻灯片",
            "包含问答讨论问题",
            "下载 Markdown 格式用于 Marp CLI 或 VS Code 扩展",
        ],
    },
    {
        "title": "学习教练",
        "bullets": [
            "两阶段学习方法促进深度理解",
            "阶段 A（框架）: 获取关键概念、方法提示和常见陷阱",
            "阶段 B（评审）: 提交答案获取反馈和评分标准评估",
            "教练故意避免给出完整答案以鼓励学习",
            "会话可自定义命名便于参考",
            "教练默认引用资料库中所有文档",
        ],
    },
    {
        "title": "后台任务",
        "bullets": [
            "长时间操作（导入、索引、生成）在后台运行",
            "在工具 → 任务中查看所有任务及进度",
            "任务控制: 运行、取消、重试或恢复",
            "任务执行期间允许页面导航",
            "任务运行时写操作被锁定（有指示器）",
        ],
    },
    {
        "title": "设置",
        "bullets": [
            "UI 模式: 本地（直接处理）或 API（远程服务器）",
            "LLM 设置: Base URL、模型名称、API Key、温度",
            "OCR 设置: 模式（关闭/自动/开启）和文本阈值",
            "语言: 界面和输出语言（英语/中文）",
            "测试连接: 使用 Ping API 和测试 LLM 按钮验证",
        ],
    },
    {
        "title": "插件",
        "bullets": [
            "导入器: 从文件夹、Zotero、arXiv、DOI、URL 批量导入",
            "导出器: 导出资产到文件夹，导出引用为 JSON/TXT",
            "在工具 → 插件中运行插件",
        ],
    },
    {
        "title": "故障排除",
        "expanded": True,
        "bullets": [
            "LLM 未配置: 在设置中设置 Base URL、模型和 API Key",
            "按钮禁用: 检查开始页面的设置检查清单查看缺失项",
            "嵌入错误: 设置 STUDYFLOW_EMBED_MODEL 环境变量或使用 BM25 模式",
            "索引未建立: 使用诊断 → 重建索引或 CLI: studyflow index build",
            "解析失败: 确保 PDF 未加密且包含文本层",
            "OCR 不工作: 安装 Tesseract 并设置 STUDYFLOW_OCR_MODE=auto",
            "API 503 错误: 如使用 API 模式确保后端正在运行",
        ],
    },
    {
        "title": "CLI 命令",
        "bullets": [
            "studyflow doctor --deep: 完整系统健康检查",
            "studyflow workspace create <名称>: 创建新工作区",
            "studyflow ingest --workspace <id> 文件.pdf: 导入文档",
            "studyflow index build --workspace <id>: 构建搜索索引",
            "studyflow query --workspace <id> --mode hybrid '问题': 搜索文档",
            "studyflow gen --workspace <id> --type slides --source <id>: 生成内容",
            "studyflow clean --workspace <id> --dry-run: 预览清理",
        ],
    },
    {
        "title": "隐私与数据",
        "bullets": [
            "所有数据保存在本地（本地优先设计）",
            "API 密钥不会写入磁盘",
            "无遥测或使用数据收集",
            "数据位置: workspaces/<id>/ 包含上传、索引、输出",
            "导出所有数据: 使用 studyflow bundle export 进行便携式备份",
        ],
    },
    {
        "title": "键盘快捷键",
        "bullets": [
            "Ctrl/Cmd + Enter: 提交表单和查询",
            "Escape: 关闭对话框",
            "Tab: 在表单字段间导航",
        ],
    },
]


def get_help_sections(language: str = "en") -> list[dict]:
    """Get help sections for the specified language."""
    if language.lower().startswith("zh"):
        return HELP_SECTIONS_ZH
    return HELP_SECTIONS_EN
