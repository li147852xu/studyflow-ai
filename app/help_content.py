"""Help content for StudyFlow AI UI.

This module provides in-app documentation that aligns with README.md content.
Supports English and Chinese languages.
"""
from __future__ import annotations

HELP_SECTIONS_EN = [
    {
        "title": "Welcome to StudyFlow AI",
        "expanded": True,
        "paragraphs": [
            "StudyFlow AI is your local-first Course & Research OS. It helps you manage courses, research projects, and learning materials with AI-powered assistance.",
            "All your data stays on your machine - no cloud sync required. API keys are stored locally and never shared."
        ],
        "bullets": [
            "📚 Manage courses, lectures, and assignments",
            "🔬 Organize research projects and track ideas",
            "📅 Plan your schedule with timetable and todos",
            "🤖 Get AI assistance with RAG-powered Q&A",
            "📊 Generate presentations and study materials",
        ],
    },
    {
        "title": "10-Minute Onboarding Path",
        "expanded": True,
        "paragraphs": [
            "Follow this once to get your first cited output and see the full workflow."
        ],
        "bullets": [
            "1) Start: select or create a workspace in the sidebar.",
            "2) Settings: configure LLM (Base URL, Model, API Key) and choose retrieval mode.",
            "3) Library: import 1-2 files (PDF/DOCX/PPTX/TXT/HTML/Images if OCR is available).",
            "4) Courses: create a course and link materials from the library.",
            "5) Generate: create course overview, cheat sheet, or exam blueprint.",
            "6) View citations and export from Recent Activity.",
        ],
        "code": "streamlit run app/main.py\n# Open http://localhost:8501",
    },
    {
        "title": "Dashboard Overview",
        "paragraphs": [
            "The Dashboard is your daily command center showing today's schedule, pending tasks, and recent activity."
        ],
        "bullets": [
            "📅 Today's Schedule: Shows all events for today including course sessions",
            "✅ Today's Todos: Lists all pending tasks due today with quick completion toggle",
            "📊 Quick Stats: Overview of your courses, research projects, and materials",
            "🔔 Notifications: Real-time updates on task completion and system events",
            "💡 Setup Status: Shows if LLM and other configurations are complete",
        ],
    },
    {
        "title": "Courses: Complete Guide",
        "paragraphs": [
            "The Courses module is your hub for academic course management. Each course can have lectures, assignments, and associated materials."
        ],
        "bullets": [
            "📚 Create Course: Name, code, instructor, semester - all customizable",
            "📖 Lectures: Organize by lecture number, date, and topic",
            "📄 Materials: Link documents from Library to specific lectures",
            "📝 Assignments: Track specs, due dates, and completion status",
            "📊 Overview Tab: Auto-generated course summary with key concepts",
            "🎯 Exam Tab: Generate exam blueprint and coverage reports",
            "❓ Q&A Tab: Ask course-specific questions with cited answers",
        ],
        "subsections": [
            {
                "subtitle": "Linking Materials",
                "bullets": [
                    "Go to the Materials tab within any course",
                    "Click 'Link Material' and select documents from Library",
                    "Assign materials to specific lectures or keep as general course resources",
                ]
            },
            {
                "subtitle": "Generating Course Overview",
                "bullets": [
                    "Requires at least one linked material document",
                    "Click 'Generate Overview' button in the Overview tab",
                    "Wait for AI processing (notification will appear when complete)",
                    "View the generated summary with cited sources",
                ]
            },
            {
                "subtitle": "Exam Blueprint",
                "bullets": [
                    "Located in the Exam tab of each course",
                    "Generates comprehensive exam preparation guide",
                    "Includes: topics, formulas, question types, coverage report",
                    "Coverage report shows which lectures are included/missing",
                ]
            },
        ],
    },
    {
        "title": "Research Projects: Deep Dive",
        "paragraphs": [
            "The Research module supports your academic research from paper reading to idea development and experiment planning."
        ],
        "bullets": [
            "📄 Papers: Import and analyze research papers",
            "💡 Ideas: Track novel ideas and confirm innovation points",
            "🧪 Experiments: Plan from confirmed ideas with hypothesis/metrics",
            "📈 Progress: Timeline view of your research journey",
            "📊 Decks: Generate presentation materials",
        ],
        "subsections": [
            {
                "subtitle": "Paper Analysis",
                "bullets": [
                    "Import papers from Library (set type as 'Paper')",
                    "Generate Paper Card: summary, contributions, limitations",
                    "Compare multiple papers on a research question",
                ]
            },
            {
                "subtitle": "Idea Development",
                "bullets": [
                    "Create idea candidates from AI suggestions",
                    "Use multi-turn dialogue to refine and confirm ideas",
                    "Freeze confirmed ideas for experiment planning",
                ]
            },
            {
                "subtitle": "Experiment Planning",
                "bullets": [
                    "Link to a confirmed idea",
                    "AI generates: hypothesis, datasets, metrics, baselines",
                    "Track experiment runs and results",
                ]
            },
        ],
    },
    {
        "title": "Library: Document Management",
        "paragraphs": [
            "The Library is your central document repository. All materials imported here can be linked to courses and research projects."
        ],
        "bullets": [
            "📁 Supported formats: PDF, TXT/MD, DOCX, PPTX, HTML, PNG/JPG (with OCR)",
            "🏷️ Document types: Course, Paper, Other",
            "📥 Import sources: Upload, Zotero, Folder, arXiv, DOI, URL",
            "🔍 Search and filter by type, format, or keyword",
            "📋 Inspector panel shows document details and linked resources",
        ],
        "subsections": [
            {
                "subtitle": "Import Methods",
                "bullets": [
                    "Upload: Drag and drop or click to upload files",
                    "Folder: Batch import from a local folder",
                    "Zotero: Sync from your Zotero library",
                    "arXiv: Import by arXiv ID or URL",
                    "DOI: Import by DOI identifier",
                    "URL: Import from any web URL",
                ]
            },
            {
                "subtitle": "Document Types Explained",
                "bullets": [
                    "Course: Used in course workflows (overview, cheatsheet, Q&A)",
                    "Paper: Used in research workflows (paper card, comparison)",
                    "Other: General reference, still searchable and citable",
                ]
            },
            {
                "subtitle": "OCR for Images",
                "bullets": [
                    "Enable OCR in Settings for image text extraction",
                    "Supported: PNG, JPG, JPEG formats",
                    "Set OCR threshold for confidence filtering",
                ]
            },
        ],
    },
    {
        "title": "AI Assistant: Scoped Q&A",
        "paragraphs": [
            "The AI Assistant provides intelligent Q&A with automatic source retrieval and citation."
        ],
        "bullets": [
            "🎯 Always select a scope: Course, Project, or Mixed",
            "📚 Retrieves relevant content from your indexed documents",
            "📖 Provides cited answers with hover-preview snippets",
            "⚖️ Coverage reports show which documents were used",
            "💰 Token budget controls for cost management",
        ],
        "subsections": [
            {
                "subtitle": "Scope Selection",
                "bullets": [
                    "Course: Answer only from course materials",
                    "Project: Answer from research project documents",
                    "Mixed: Combine sources from multiple courses/projects",
                ]
            },
            {
                "subtitle": "Understanding Citations",
                "bullets": [
                    "Citations appear as [1], [2], etc. in answers",
                    "Hover over citations to see source snippets",
                    "Click to view full context",
                ]
            },
            {
                "subtitle": "Global Queries (Map-Reduce)",
                "bullets": [
                    "For broad questions like 'exam overview' or 'literature review'",
                    "System uses map-reduce across all documents",
                    "Coverage report shows which documents were included",
                ]
            },
        ],
    },
    {
        "title": "Timetable & Todos",
        "paragraphs": [
            "Manage your academic schedule and task list in one place."
        ],
        "bullets": [
            "📅 Events: Course sessions auto-sync, or add custom events",
            "✅ Todos: Global tasks or linked to specific courses/projects",
            "🔔 Due date reminders on Dashboard",
            "📊 Status tracking: todo/doing/done",
        ],
        "subsections": [
            {
                "subtitle": "Adding Events",
                "bullets": [
                    "Course events auto-created from course schedules",
                    "Custom events: title, date/time, location",
                    "Can link to specific courses for context",
                ]
            },
            {
                "subtitle": "Managing Todos",
                "bullets": [
                    "Quick add from Dashboard",
                    "Set due dates and priority",
                    "Link to courses or research projects",
                    "Filter by status or linked resource",
                ]
            },
        ],
    },
    {
        "title": "Tools: Tasks, Diagnostics, Activity",
        "paragraphs": [
            "The Tools section provides system utilities and operation history."
        ],
        "bullets": [
            "📋 Tasks: View and manage background operations",
            "🔧 Diagnostics: System health checks and maintenance",
            "📜 Activity: Recent 30 operations with export options",
            "📦 Exports: Create shareable bundles",
            "📊 Decks: Generate presentations from any scope",
            "❓ Help: This documentation",
        ],
        "subsections": [
            {
                "subtitle": "Task Management",
                "bullets": [
                    "Filter by status: queued, running, succeeded, failed",
                    "Retry failed tasks",
                    "Cancel running tasks",
                    "View progress and error messages",
                ]
            },
            {
                "subtitle": "Diagnostics Tools",
                "bullets": [
                    "Doctor: Check environment and dependencies",
                    "Rebuild Index: Repair vector/BM25 search state",
                    "Clean: Remove stale outputs (dry-run first)",
                ]
            },
        ],
    },
    {
        "title": "Settings: Configuration Guide",
        "paragraphs": [
            "Configure all aspects of StudyFlow AI from the Settings page."
        ],
        "bullets": [
            "🤖 LLM: Base URL, Model, API Key, Temperature",
            "🔍 Retrieval: Vector / BM25 / Hybrid mode",
            "📷 OCR: Enable/disable, threshold settings",
            "🎨 Theme: Light or Dark mode",
            "🌐 Language: English or Chinese interface",
            "📝 Output Language: Language for generated content",
            "💰 Token Budget: Control map/reduce token limits",
        ],
        "subsections": [
            {
                "subtitle": "LLM Configuration",
                "bullets": [
                    "Base URL: API endpoint (e.g., https://api.openai.com/v1)",
                    "Model: Model name (e.g., gpt-4, gpt-3.5-turbo)",
                    "API Key: Your provider's API key (stored locally)",
                    "Temperature: Creativity level (0.0 = deterministic, 1.0 = creative)",
                ]
            },
            {
                "subtitle": "Retrieval Modes",
                "bullets": [
                    "Vector: Semantic similarity search (best for concepts)",
                    "BM25: Keyword matching (best for exact terms)",
                    "Hybrid: Combines both (recommended for most use cases)",
                ]
            },
            {
                "subtitle": "Token Budget (Advanced)",
                "bullets": [
                    "Map Tokens: Per-document budget in map-reduce (default: 250)",
                    "Reduce Tokens: Final synthesis budget (default: 600)",
                    "Adjust based on document count and cost constraints",
                ]
            },
        ],
    },
    {
        "title": "Notifications & Task Status",
        "paragraphs": [
            "StudyFlow AI keeps you informed about long-running operations through notifications."
        ],
        "bullets": [
            "🔔 Notification Center: Located in the top bar, shows running and completed tasks",
            "⏳ Running Tasks: Yellow indicator with progress info",
            "✅ Completed: Green checkmark with summary",
            "❌ Failed: Red indicator with error details",
            "👁️ View: Jump to related content",
            "🗑️ Dismiss: Clear notification",
        ],
    },
    {
        "title": "Keyboard Shortcuts",
        "bullets": [
            "Ctrl/Cmd + Enter: Submit forms and queries",
            "Escape: Close dialogs and modals",
            "Tab: Navigate between form fields",
        ],
    },
    {
        "title": "Troubleshooting Common Issues",
        "bullets": [
            "❌ 'No documents found': Import files in Library first",
            "❌ 'LLM not configured': Set Base URL, Model, and API Key in Settings",
            "❌ 'Index not ready': Wait for indexing task to complete",
            "❌ 'Generation failed': Check API key validity and model availability",
            "❌ 'Missing materials': Link documents to courses/projects before generating",
        ],
        "subsections": [
            {
                "subtitle": "If Tasks are Stuck",
                "bullets": [
                    "Go to Tools → Tasks and check status",
                    "Try canceling and retrying the task",
                    "Check Diagnostics for system health",
                    "Rebuild index if search is not working",
                ]
            },
            {
                "subtitle": "If Citations are Missing",
                "bullets": [
                    "Ensure documents are properly indexed",
                    "Check retrieval mode in Settings",
                    "Try rebuilding the index",
                    "Verify documents contain relevant content",
                ]
            },
        ],
    },
    {
        "title": "Best Practices",
        "bullets": [
            "✨ Organize by semester: Create separate courses per term",
            "✨ Link materials early: Associate documents before generating",
            "✨ Use specific scopes: Avoid 'mixed' unless needed",
            "✨ Check coverage: Always review coverage reports for completeness",
            "✨ Export regularly: Save important outputs from Recent Activity",
            "✨ Keep backup: Your workspace folder contains all data",
        ],
    },
]

HELP_SECTIONS_ZH = [
    {
        "title": "欢迎使用 StudyFlow AI",
        "expanded": True,
        "paragraphs": [
            "StudyFlow AI 是您的本地优先课程与研究操作系统。它帮助您管理课程、科研项目和学习资料，并提供 AI 辅助。",
            "所有数据都保存在您的本地设备上——无需云同步。API 密钥仅存储在本地，绝不会被共享。"
        ],
        "bullets": [
            "📚 管理课程、讲座和作业",
            "🔬 组织科研项目并跟踪创意",
            "📅 通过课程表和待办事项规划日程",
            "🤖 获取基于 RAG 的 AI 问答辅助",
            "📊 生成演示文稿和学习材料",
        ],
    },
    {
        "title": "10分钟上手路径",
        "expanded": True,
        "paragraphs": [
            "走一遍完整流程，即可得到首个带引用的输出。"
        ],
        "bullets": [
            "1) 开始：在侧边栏选择或创建工作区。",
            "2) 设置：配置 LLM（Base URL、模型、API Key）并选择检索模式。",
            "3) 资料库：导入 1-2 个文件（PDF/DOCX/PPTX/TXT/HTML/图片 OCR）。",
            "4) 课程：创建课程并从资料库关联材料。",
            "5) 生成：创建课程概览、速记表或考试大纲。",
            "6) 查看引用并从最近活动导出。",
        ],
        "code": "streamlit run app/main.py\n# 打开 http://localhost:8501",
    },
    {
        "title": "仪表盘概览",
        "paragraphs": [
            "仪表盘是您的每日指挥中心，显示今日日程、待办事项和最近活动。"
        ],
        "bullets": [
            "📅 今日日程：显示今天的所有事件，包括课程安排",
            "✅ 今日待办：列出今天到期的所有待办任务，支持快速完成切换",
            "📊 快速统计：课程、科研项目和资料的概览",
            "🔔 通知：任务完成和系统事件的实时更新",
            "💡 设置状态：显示 LLM 和其他配置是否完成",
        ],
    },
    {
        "title": "课程：完整指南",
        "paragraphs": [
            "课程模块是您学术课程管理的中心。每门课程可以包含讲座、作业和相关材料。"
        ],
        "bullets": [
            "📚 创建课程：名称、代码、讲师、学期——全部可自定义",
            "📖 讲座：按讲座编号、日期和主题组织",
            "📄 材料：从资料库链接文档到特定讲座",
            "📝 作业：跟踪规格、截止日期和完成状态",
            "📊 概览标签页：自动生成的课程摘要和关键概念",
            "🎯 考试标签页：生成考试大纲和覆盖率报告",
            "❓ 问答标签页：提出课程相关问题获取带引用的答案",
        ],
        "subsections": [
            {
                "subtitle": "关联材料",
                "bullets": [
                    "进入任意课程的「材料」标签页",
                    "点击「关联材料」并从资料库选择文档",
                    "将材料分配给特定讲座或保持为通用课程资源",
                ]
            },
            {
                "subtitle": "生成课程概览",
                "bullets": [
                    "需要至少一个关联的材料文档",
                    "在概览标签页点击「生成概览」按钮",
                    "等待 AI 处理（完成时会出现通知）",
                    "查看带有引用来源的生成摘要",
                ]
            },
            {
                "subtitle": "考试大纲",
                "bullets": [
                    "位于每门课程的考试标签页",
                    "生成全面的考试准备指南",
                    "包括：主题、公式、题型、覆盖率报告",
                    "覆盖率报告显示哪些讲座被包含/遗漏",
                ]
            },
        ],
    },
    {
        "title": "科研项目：深入了解",
        "paragraphs": [
            "科研模块支持您从论文阅读到创意开发和实验规划的整个学术研究过程。"
        ],
        "bullets": [
            "📄 论文：导入和分析研究论文",
            "💡 创意：跟踪新创意并确认创新点",
            "🧪 实验：从已确认的创意规划实验，包含假设/指标",
            "📈 进度：研究旅程的时间线视图",
            "📊 汇报：生成演示材料",
        ],
        "subsections": [
            {
                "subtitle": "论文分析",
                "bullets": [
                    "从资料库导入论文（类型设为「论文」）",
                    "生成论文卡片：摘要、贡献、局限性",
                    "基于研究问题比较多篇论文",
                ]
            },
            {
                "subtitle": "创意开发",
                "bullets": [
                    "从 AI 建议创建候选创意",
                    "使用多轮对话完善和确认创意",
                    "冻结已确认的创意用于实验规划",
                ]
            },
            {
                "subtitle": "实验规划",
                "bullets": [
                    "链接到已确认的创意",
                    "AI 生成：假设、数据集、指标、基线",
                    "跟踪实验运行和结果",
                ]
            },
        ],
    },
    {
        "title": "资料库：文档管理",
        "paragraphs": [
            "资料库是您的中央文档仓库。所有导入的材料都可以链接到课程和科研项目。"
        ],
        "bullets": [
            "📁 支持格式：PDF、TXT/MD、DOCX、PPTX、HTML、PNG/JPG（需 OCR）",
            "🏷️ 文档类型：课程、论文、其他",
            "📥 导入来源：上传、Zotero、文件夹、arXiv、DOI、URL",
            "🔍 按类型、格式或关键词搜索和筛选",
            "📋 检查器面板显示文档详情和关联资源",
        ],
        "subsections": [
            {
                "subtitle": "导入方法",
                "bullets": [
                    "上传：拖放或点击上传文件",
                    "文件夹：从本地文件夹批量导入",
                    "Zotero：从 Zotero 库同步",
                    "arXiv：通过 arXiv ID 或 URL 导入",
                    "DOI：通过 DOI 标识符导入",
                    "URL：从任意网址导入",
                ]
            },
            {
                "subtitle": "文档类型说明",
                "bullets": [
                    "课程：用于课程工作流（概览、速记表、问答）",
                    "论文：用于科研工作流（论文卡片、比较）",
                    "其他：一般参考资料，仍可搜索和引用",
                ]
            },
            {
                "subtitle": "图片 OCR",
                "bullets": [
                    "在设置中启用 OCR 进行图片文本提取",
                    "支持：PNG、JPG、JPEG 格式",
                    "设置 OCR 阈值进行置信度过滤",
                ]
            },
        ],
    },
    {
        "title": "AI 助手：范围问答",
        "paragraphs": [
            "AI 助手提供智能问答，自动检索来源并生成引用。"
        ],
        "bullets": [
            "🎯 始终选择范围：课程、项目或混合",
            "📚 从您的索引文档中检索相关内容",
            "📖 提供带引用的答案，悬停可预览片段",
            "⚖️ 覆盖率报告显示使用了哪些文档",
            "💰 Token 预算控制以管理成本",
        ],
        "subsections": [
            {
                "subtitle": "范围选择",
                "bullets": [
                    "课程：仅从课程材料回答",
                    "项目：从科研项目文档回答",
                    "混合：结合多个课程/项目的来源",
                ]
            },
            {
                "subtitle": "理解引用",
                "bullets": [
                    "引用以 [1]、[2] 等形式出现在答案中",
                    "悬停引用查看来源片段",
                    "点击查看完整上下文",
                ]
            },
            {
                "subtitle": "全局查询（Map-Reduce）",
                "bullets": [
                    "用于广泛问题如「考试概览」或「文献综述」",
                    "系统跨所有文档使用 map-reduce",
                    "覆盖率报告显示包含了哪些文档",
                ]
            },
        ],
    },
    {
        "title": "课程表与待办",
        "paragraphs": [
            "在一处管理您的学术日程和任务列表。"
        ],
        "bullets": [
            "📅 事件：课程自动同步，或添加自定义事件",
            "✅ 待办：全局任务或链接到特定课程/项目",
            "🔔 仪表盘显示截止日期提醒",
            "📊 状态跟踪：待办/进行中/已完成",
        ],
        "subsections": [
            {
                "subtitle": "添加事件",
                "bullets": [
                    "课程事件从课程时间表自动创建",
                    "自定义事件：标题、日期/时间、地点",
                    "可链接到特定课程以提供上下文",
                ]
            },
            {
                "subtitle": "管理待办",
                "bullets": [
                    "从仪表盘快速添加",
                    "设置截止日期和优先级",
                    "链接到课程或科研项目",
                    "按状态或关联资源筛选",
                ]
            },
        ],
    },
    {
        "title": "工具：任务、诊断、活动",
        "paragraphs": [
            "工具部分提供系统工具和操作历史。"
        ],
        "bullets": [
            "📋 任务：查看和管理后台操作",
            "🔧 诊断：系统健康检查和维护",
            "📜 活动：最近 30 次操作，支持导出",
            "📦 导出：创建可分享的包",
            "📊 汇报：从任意范围生成演示文稿",
            "❓ 帮助：本文档",
        ],
        "subsections": [
            {
                "subtitle": "任务管理",
                "bullets": [
                    "按状态筛选：排队中、运行中、成功、失败",
                    "重试失败的任务",
                    "取消运行中的任务",
                    "查看进度和错误信息",
                ]
            },
            {
                "subtitle": "诊断工具",
                "bullets": [
                    "Doctor：检查环境和依赖项",
                    "重建索引：修复向量/BM25 搜索状态",
                    "清理：移除过期输出（先试运行）",
                ]
            },
        ],
    },
    {
        "title": "设置：配置指南",
        "paragraphs": [
            "在设置页面配置 StudyFlow AI 的所有方面。"
        ],
        "bullets": [
            "🤖 LLM：Base URL、模型、API Key、温度",
            "🔍 检索：向量 / BM25 / 混合模式",
            "📷 OCR：启用/禁用、阈值设置",
            "🎨 主题：明亮或暗黑模式",
            "🌐 语言：英文或中文界面",
            "📝 输出语言：生成内容的语言",
            "💰 Token 预算：控制 map/reduce token 限制",
        ],
        "subsections": [
            {
                "subtitle": "LLM 配置",
                "bullets": [
                    "Base URL：API 端点（如 https://api.openai.com/v1）",
                    "Model：模型名称（如 gpt-4、gpt-3.5-turbo）",
                    "API Key：您的提供商 API 密钥（本地存储）",
                    "Temperature：创造性级别（0.0=确定性，1.0=创造性）",
                ]
            },
            {
                "subtitle": "检索模式",
                "bullets": [
                    "向量：语义相似性搜索（最适合概念）",
                    "BM25：关键词匹配（最适合精确术语）",
                    "混合：结合两者（大多数情况下推荐）",
                ]
            },
            {
                "subtitle": "Token 预算（高级）",
                "bullets": [
                    "Map Tokens：map-reduce 中每个文档的预算（默认：250）",
                    "Reduce Tokens：最终综合预算（默认：600）",
                    "根据文档数量和成本约束调整",
                ]
            },
        ],
    },
    {
        "title": "通知与任务状态",
        "paragraphs": [
            "StudyFlow AI 通过通知让您了解长时间运行的操作。"
        ],
        "bullets": [
            "🔔 通知中心：位于顶部栏，显示运行中和已完成的任务",
            "⏳ 运行中任务：黄色指示器带进度信息",
            "✅ 已完成：绿色勾号带摘要",
            "❌ 失败：红色指示器带错误详情",
            "👁️ 查看：跳转到相关内容",
            "🗑️ 忽略：清除通知",
        ],
    },
    {
        "title": "键盘快捷键",
        "bullets": [
            "Ctrl/Cmd + Enter：提交表单和查询",
            "Escape：关闭对话框和模态框",
            "Tab：在表单字段间导航",
        ],
    },
    {
        "title": "常见问题排查",
        "bullets": [
            "❌ '未找到文档'：先在资料库导入文件",
            "❌ 'LLM 未配置'：在设置中设置 Base URL、模型和 API Key",
            "❌ '索引未就绪'：等待索引任务完成",
            "❌ '生成失败'：检查 API 密钥有效性和模型可用性",
            "❌ '缺少材料'：在生成前将文档链接到课程/项目",
        ],
        "subsections": [
            {
                "subtitle": "如果任务卡住",
                "bullets": [
                    "进入工具 → 任务查看状态",
                    "尝试取消并重试任务",
                    "检查诊断以了解系统健康状况",
                    "如果搜索不工作，重建索引",
                ]
            },
            {
                "subtitle": "如果缺少引用",
                "bullets": [
                    "确保文档已正确索引",
                    "检查设置中的检索模式",
                    "尝试重建索引",
                    "验证文档包含相关内容",
                ]
            },
        ],
    },
    {
        "title": "最佳实践",
        "bullets": [
            "✨ 按学期组织：为每个学期创建单独的课程",
            "✨ 提前关联材料：在生成前关联文档",
            "✨ 使用特定范围：除非需要，否则避免「混合」",
            "✨ 检查覆盖率：始终查看覆盖率报告以确保完整性",
            "✨ 定期导出：从最近活动保存重要输出",
            "✨ 保留备份：您的工作区文件夹包含所有数据",
        ],
    },
]


def get_help_sections(language: str = "en") -> list[dict]:
    """Get help sections for the specified language."""
    if language.lower().startswith("zh"):
        return HELP_SECTIONS_ZH
    return HELP_SECTIONS_EN
