HELP_SECTIONS_EN = [
    {
        "title": "Quickstart",
        "expanded": True,
        "bullets": [
            "Create or select a project on the left.",
            "Upload PDFs in Library or within a workflow.",
            "Build the vector index if you plan to use Vector/Hybrid retrieval.",
            "Use Create page to generate outputs.",
        ],
        "code": "streamlit run app/main.py",
    },
    {
        "title": "Navigation",
        "bullets": [
            "Start: Quick overview and one-click workflows.",
            "Library: Import, organize, and index documents. Filter by document type (Course/Paper/Other) and specific courses.",
            "Create: Generate course overviews, paper cards, and presentations. Each tab shows only its own generation progress and latest output.",
            "Tools: Coach, tasks, settings, and diagnostics.",
        ],
    },
    {
        "title": "Importing PDFs",
        "bullets": [
            "Use Library to ingest one or multiple PDFs.",
            "Each upload extracts text, chunks it, and stores metadata in SQLite.",
            "Re-ingesting the same file hash is skipped automatically.",
            "OCR modes: off, auto (low-text pages), on (all pages).",
            "Import from: Upload, Zotero, Folder, arXiv, DOI, or URL.",
            "Document summaries: Click 'Generate Summary' in document details to create an LLM-generated one-line description.",
        ],
    },
    {
        "title": "Indexing & Retrieval Modes",
        "bullets": [
            "Vector: embeddings-based semantic search.",
            "BM25: lexical match without embeddings.",
            "Hybrid: fused scores from Vector + BM25.",
            "Vector index is built on demand per workspace.",
        ],
    },
    {
        "title": "Create: Course",
        "bullets": [
            "Step 1: Select or create a course.",
            "Step 2: Link lecture PDFs to the course.",
            "Step 3: Generate outputs - Course Overview, Cheat Sheet, Knowledge Q&A, or Explain selections.",
            "Knowledge Q&A: Ask questions about course content and get answers based on linked materials.",
        ],
    },
    {
        "title": "Create: Paper",
        "bullets": [
            "Select a paper source document.",
            "Generate Paper Card for a single paper.",
            "Aggregate Papers to compare multiple papers.",
        ],
    },
    {
        "title": "Create: Presentation",
        "bullets": [
            "Filter documents by type (All, Course, Paper, Other).",
            "For course documents, further filter by specific course.",
            "Set duration from 1-30 minutes.",
            "Generate Marp-format slides and Q&A lists.",
        ],
    },
    {
        "title": "Study Coach",
        "bullets": [
            "Phase A: Get framework, key concepts, and pitfalls.",
            "Phase B: Submit your answer for review with hints and rubric.",
            "Coach avoids giving full final answers by default.",
            "Session naming: Name your sessions for easy identification, or use default names (Session 1, 2, etc.).",
            "Session history: View and revisit all past coaching sessions.",
            "Coach references all PDFs in your library by default.",
        ],
    },
    {
        "title": "Tasks Center",
        "bullets": [
            "View all background tasks (ingest, index, generate).",
            "Tasks show progress, status, and errors.",
            "Use Run, Cancel, Retry, or Resume buttons.",
        ],
    },
    {
        "title": "Settings",
        "bullets": [
            "UI Mode: Direct (local) or API (remote server).",
            "LLM settings: Base URL, Model, API Key, Temperature.",
            "OCR settings: Mode and threshold.",
            "Language: UI and output language.",
        ],
    },
    {
        "title": "Plugins",
        "bullets": [
            "Importer: Batch ingest PDFs from a folder.",
            "Exporter: Export assets to folders and citations.",
        ],
    },
    {
        "title": "Troubleshooting",
        "bullets": [
            "Missing LLM Base URL/Model/Key: Set in Settings or env variables.",
            "Embedding model missing: Set STUDYFLOW_EMBED_MODEL or switch to BM25.",
            "Index not built: Click Build/Refresh Vector Index in Library.",
            "Parse failed: Ensure PDFs are not encrypted and contain text layers.",
            "API error 503: Check if backend server is running (API mode).",
        ],
    },
]

HELP_SECTIONS_ZH = [
    {
        "title": "快速开始",
        "expanded": True,
        "bullets": [
            "在左侧创建或选择一个项目。",
            "在资料库或工作流中上传 PDF 文件。",
            "如果使用向量/混合检索，需要构建向量索引。",
            "使用创作页面生成输出内容。",
        ],
        "code": "streamlit run app/main.py",
    },
    {
        "title": "导航说明",
        "bullets": [
            "开始：快速概览和一键工作流。",
            "资料库：导入、整理和索引文档。可按文档类型（课程/论文/其他）和具体课程筛选。",
            "创作：生成课程总览、论文卡片和演示文稿。每个标签页只显示该模块的生成进度和最新输出。",
            "工具：学习教练、任务、设置和诊断。",
        ],
    },
    {
        "title": "导入 PDF",
        "bullets": [
            "使用资料库导入一个或多个 PDF。",
            "每次上传会提取文本、分块并存储元数据。",
            "相同文件哈希的重复导入会自动跳过。",
            "OCR 模式：关闭、自动（低文本页面）、开启（所有页面）。",
            "导入来源：上传、Zotero、文件夹、arXiv、DOI 或 URL。",
            "文档简介：在文档详情中点击「生成简介」，为文档创建 LLM 生成的一句话描述。",
        ],
    },
    {
        "title": "索引与检索模式",
        "bullets": [
            "向量：基于嵌入的语义搜索。",
            "BM25：不需要嵌入的词汇匹配。",
            "混合：向量 + BM25 融合得分。",
            "向量索引按工作区按需构建。",
        ],
    },
    {
        "title": "创作：课程",
        "bullets": [
            "步骤 1：选择或创建课程。",
            "步骤 2：将课程 PDF 关联到课程。",
            "步骤 3：生成输出 - 课程总览、复习备忘、知识问答或解释选中内容。",
            "知识问答：提出关于课程内容的问题，基于关联的材料获取答案。",
        ],
    },
    {
        "title": "创作：论文",
        "bullets": [
            "选择一个论文源文档。",
            "为单篇论文生成论文卡片。",
            "聚合论文以比较多篇论文。",
        ],
    },
    {
        "title": "创作：演示",
        "bullets": [
            "按类型筛选文档（全部、课程、论文、其他）。",
            "对于课程文档，可进一步按具体课程筛选。",
            "设置时长从 1-30 分钟。",
            "生成 Marp 格式幻灯片和问答列表。",
        ],
    },
    {
        "title": "学习教练",
        "bullets": [
            "阶段 A：获取框架、关键概念和陷阱。",
            "阶段 B：提交答案获取提示和评分标准。",
            "教练默认避免给出完整最终答案。",
            "会话命名：为会话命名以便识别，或使用默认名称（会话 1、2 等）。",
            "会话历史：查看和回顾所有过往的教练会话。",
            "教练默认引用资料库中所有 PDF。",
        ],
    },
    {
        "title": "任务中心",
        "bullets": [
            "查看所有后台任务（导入、索引、生成）。",
            "任务显示进度、状态和错误。",
            "使用运行、取消、重试或恢复按钮。",
        ],
    },
    {
        "title": "设置",
        "bullets": [
            "UI 模式：本地或 API（远程服务器）。",
            "LLM 设置：Base URL、模型、API Key、温度。",
            "OCR 设置：模式和阈值。",
            "语言：界面语言和输出语言。",
        ],
    },
    {
        "title": "插件",
        "bullets": [
            "导入器：从文件夹批量导入 PDF。",
            "导出器：将资产导出到文件夹和引用。",
        ],
    },
    {
        "title": "故障排除",
        "bullets": [
            "缺少 LLM Base URL/模型/密钥：在设置或环境变量中设置。",
            "缺少嵌入模型：设置 STUDYFLOW_EMBED_MODEL 或切换到 BM25。",
            "未构建索引：在资料库中点击构建/刷新向量索引。",
            "解析失败：确保 PDF 未加密且包含文本层。",
            "API 错误 503：检查后端服务器是否运行（API 模式）。",
        ],
    },
]


def get_help_sections(language: str = "en") -> list[dict]:
    if language.lower().startswith("zh"):
        return HELP_SECTIONS_ZH
    return HELP_SECTIONS_EN
