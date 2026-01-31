"""Help content for StudyFlow AI UI.

This module provides in-app documentation that aligns with README.md content.
Supports English and Chinese languages.
"""
from __future__ import annotations

HELP_SECTIONS_EN = [
    {
        "title": "10-Minute Onboarding Path",
        "expanded": True,
        "paragraphs": [
            "Follow this once to get your first cited output and see the full workflow."
        ],
        "bullets": [
            "1) Start: select or create a project in the sidebar.",
            "2) Settings: configure LLM (Base URL, Model, API Key) and choose retrieval mode.",
            "3) Library: import 1-2 files (PDF/DOCX/PPTX/TXT/HTML/Images if OCR is available).",
            "4) Wait for ingest/index tasks to finish (watch Tasks or notification toasts).",
            "5) Create: run Course Sprint / Paper Review / Presentation Builder.",
            "6) Hover citations [1][2] to see snippets, then open Recent Activity to export.",
        ],
        "code": "streamlit run app/main.py\n# Open http://localhost:8501",
    },
    {
        "title": "Library: Import Formats & OCR",
        "bullets": [
            "Supported formats: PDF, TXT/MD, DOCX, PPTX, HTML, PNG/JPG.",
            "TXT/MD are treated as plain text; HTML is parsed from readable elements.",
            "Images require OCR; if OCR is unavailable, you will see a clear warning.",
            "Import sources: Upload, Zotero, Folder, arXiv, DOI, URL.",
            "Every document records: filename, file type, size, source, created time.",
        ],
    },
    {
        "title": "Material Type (Course / Paper / Other)",
        "bullets": [
            "Course: used by Course Sprint and Q&A workflows.",
            "Paper: used by Paper Review and paper comparison workflows.",
            "Other: reference-only, still searchable and citable.",
            "You can change material type in the Library inspector.",
        ],
    },
    {
        "title": "Create: Course Sprint",
        "bullets": [
            "Step 1: Choose a course and link relevant materials in the Library.",
            "Step 2: Run Course Overview / Cheat Sheet / Q&A / Explain Selection.",
            "Step 3: Use citations to verify sources and export from Recent Activity.",
        ],
    },
    {
        "title": "Create: Paper Review",
        "bullets": [
            "Step 1: Select one paper for a Paper Card.",
            "Step 2: Pick multiple papers and a research question for comparison.",
            "Step 3: Use citations to trace claims back to sources.",
        ],
    },
    {
        "title": "Create: Presentation Builder",
        "bullets": [
            "Step 1: Choose a source document (any type).",
            "Step 2: Set duration and generate slides.",
            "Step 3: Export the deck and check citations in the output.",
        ],
    },
    {
        "title": "Study Coach (Two Phases)",
        "bullets": [
            "Phase A: framework + key concepts + pitfalls (no full answer).",
            "Phase B: submit your answer, receive objective evaluation first, then feedback.",
            "Sessions are saved; select a session to view full transcripts.",
        ],
    },
    {
        "title": "Tasks, Notifications, Recent Activity",
        "bullets": [
            "Long tasks run in the background (ingest, index, generate).",
            "Completion triggers global notifications with View/Dismiss actions.",
            "Recent Activity stores the latest outputs and citations for export.",
        ],
    },
    {
        "title": "Settings: LLM, Retrieval, OCR, Theme, Language",
        "bullets": [
            "LLM: Base URL, Model name, API Key, Temperature.",
            "Retrieval: Vector / BM25 / Hybrid.",
            "OCR: Off / Auto / On with threshold.",
            "Theme: Light/Dark; Language: English/Chinese.",
        ],
    },
    {
        "title": "Diagnostics & Maintenance",
        "bullets": [
            "Doctor: check environment and dependencies.",
            "Rebuild index: repair search/index state.",
            "Clean: remove stale runs/exports (dry-run first).",
        ],
    },
    {
        "title": "Keyboard Shortcuts",
        "bullets": [
            "Ctrl/Cmd + Enter: Submit forms and queries.",
            "Escape: Close dialogs.",
        ],
    },
]

HELP_SECTIONS_ZH = [
    {
        "title": "10分钟上手路径",
        "expanded": True,
        "paragraphs": [
            "走一遍完整流程，即可得到首个带引用的输出。"
        ],
        "bullets": [
            "1) 开始：在侧边栏选择或创建项目。",
            "2) 设置：配置 LLM（Base URL、模型、API Key）并选择检索模式。",
            "3) 资料库：导入 1-2 个文件（PDF/DOCX/PPTX/TXT/HTML/图片 OCR）。",
            "4) 等待导入/索引完成（查看任务或通知）。",
            "5) 创作：运行课程速成 / 论文分析 / 汇报生成。",
            "6) 悬停引用 [1][2] 查看片段，并在最近活动导出。",
        ],
        "code": "streamlit run app/main.py\n# 打开 http://localhost:8501",
    },
    {
        "title": "资料库：导入格式与 OCR",
        "bullets": [
            "支持格式：PDF、TXT/MD、DOCX、PPTX、HTML、PNG/JPG。",
            "TXT/MD 作为纯文本解析；HTML 提取正文元素。",
            "图片需要 OCR，若 OCR 不可用会提示原因。",
            "导入来源：上传、Zotero、文件夹、arXiv、DOI、URL。",
            "每个文档会记录：文件名、类型、大小、来源、入库时间。",
        ],
    },
    {
        "title": "资料类型（课程 / 论文 / 其他）",
        "bullets": [
            "课程：用于课程速成与问答类输出。",
            "论文：用于论文分析与多论文对比。",
            "其他：仅作为参考资料，依然可检索与引用。",
            "可在资料库检查器中修改类型。",
        ],
    },
    {
        "title": "创作：课程速成",
        "bullets": [
            "步骤 1：选择课程并在资料库中关联材料。",
            "步骤 2：生成课程概览 / 速记小抄 / 问答 / 选段讲解。",
            "步骤 3：通过引用核对来源并在最近活动导出。",
        ],
    },
    {
        "title": "创作：论文分析",
        "bullets": [
            "步骤 1：选择单篇论文生成论文卡片。",
            "步骤 2：选择多篇论文并输入研究问题进行对比。",
            "步骤 3：通过引用定位到具体来源。",
        ],
    },
    {
        "title": "创作：汇报生成",
        "bullets": [
            "步骤 1：选择任意来源文档。",
            "步骤 2：设置时长并生成演示稿。",
            "步骤 3：导出并查看引用。",
        ],
    },
    {
        "title": "学习教练（两阶段）",
        "bullets": [
            "阶段 A：框架与关键点提示（不直接给答案）。",
            "阶段 B：提交答案后先给客观评价，再提供反馈。",
            "会话会保存，可查看完整对话内容。",
        ],
    },
    {
        "title": "任务、通知、最近活动",
        "bullets": [
            "导入、索引、生成等任务后台运行。",
            "完成后出现全局通知，支持查看/忽略。",
            "最近活动保存可导出的最新输出与引用。",
        ],
    },
    {
        "title": "设置：LLM、检索、OCR、主题、语言",
        "bullets": [
            "LLM：Base URL、模型、API Key、温度。",
            "检索：向量 / BM25 / 混合。",
            "OCR：关闭 / 自动 / 开启 与阈值。",
            "主题：明/暗；语言：中文/English。",
        ],
    },
    {
        "title": "诊断与维护",
        "bullets": [
            "Doctor：检查依赖与环境。",
            "重建索引：修复检索状态。",
            "清理：移除过期输出（先 dry-run）。",
        ],
    },
    {
        "title": "键盘快捷键",
        "bullets": [
            "Ctrl/Cmd + Enter：提交表单与查询。",
            "Escape：关闭对话框。",
        ],
    },
]


def get_help_sections(language: str = "en") -> list[dict]:
    """Get help sections for the specified language."""
    if language.lower().startswith("zh"):
        return HELP_SECTIONS_ZH
    return HELP_SECTIONS_EN
