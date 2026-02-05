from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.ui.components import (
    push_generation_start_notification,
    push_notification,
    render_answer_with_citations,
    render_content_box,
    render_doc_citations,
    render_empty_state,
    render_header_card,
    render_section_with_help,
    section_title,
)
from app.ui.labels import L
from app.ui.locks import running_task_summary
from core.domains.research import (
    add_paper,
    add_idea_dialogue,
    create_project,
    list_experiment_plans,
    list_experiment_runs,
    list_idea_dialogue,
    list_ideas,
    list_project_papers,
    list_projects,
)
from service.document_service import list_documents
from service.rag_service import project_query
from service.research_v3_service import (
    add_experiment_run,
    confirm_idea_version,
    create_idea_from_prompt,
    generate_deck,
    generate_experiment_plan_from_idea,
    generate_paper_card,
)


def _select_project(workspace_id: str) -> dict | None:
    projects = list_projects(workspace_id)
    options = {project["title"]: project for project in projects}
    selected = st.selectbox(
        L("选择项目", "Select Project"),
        options=list(options.keys()),
        index=0 if options else None,
        key="research_main_project_select",
    )
    return options.get(selected) if selected else None


def render_research(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("科研平台", "Research Platform"), "research")
        
        if not workspace_id:
            render_empty_state(
                "🔬",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以开始科研。", "Select or create a workspace in the sidebar to start research."),
            )
            return

        locked, _ = running_task_summary(workspace_id)
        if locked:
            st.warning(L("⏳ 正在处理任务，请等待...", "⏳ Processing task, please wait..."))

        # Create project section
        col1, col2 = st.columns([3, 1])
        with col1:
            project = _select_project(workspace_id)
        with col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            create_new = st.button(L("➕ 新建项目", "➕ New Project"), key="btn_new_project_top")
        
        if create_new:
            st.session_state["show_create_project"] = True
        
        if st.session_state.get("show_create_project", False):
            with st.expander(L("新建项目", "Create Project"), expanded=True):
                title = st.text_input(
                    L("项目名称", "Title"),
                    key="project_title",
                    placeholder=L("例如：注意力机制研究", "e.g. Attention Mechanism Study"),
                )
                goal = st.text_area(
                    L("研究目标", "Goal"),
                    key="project_goal",
                    placeholder=L("描述项目的主要研究目标...", "Describe the main research objective..."),
                    height=100,
                )
                scope = st.text_area(
                    L("研究范围", "Scope"),
                    key="project_scope",
                    placeholder=L("约束或聚焦范围...", "Constraints or focus areas..."),
                    height=80,
                )
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(L("创建", "Create"), disabled=locked or not title.strip(), key="btn_create_project", type="primary"):
                        create_project(workspace_id=workspace_id, title=title.strip(), goal=goal, scope=scope)
                        st.success(L("✓ 项目已创建", "✓ Project created"))
                        st.session_state["show_create_project"] = False
                        st.rerun()
                with col2:
                    if st.button(L("取消", "Cancel"), key="btn_cancel_create_project"):
                        st.session_state["show_create_project"] = False
                        st.rerun()

        if not project:
            render_empty_state(
                "📂",
                L("暂无研究项目", "No Research Projects"),
                L("点击「新建项目」开始你的科研旅程。", "Click 'New Project' to start your research journey."),
            )
            return

        # Project header
        render_header_card(
            f"🔬 {project['title']}",
            project.get("goal") or L("暂无目标描述", "No goal description"),
        )

        # Tabs
        tabs = st.tabs([
            f"📄 {L('论文', 'Papers')}",
            f"💡 {L('创新点', 'Ideas')}",
            f"🧪 {L('实验', 'Experiments')}",
            f"📈 {L('进度', 'Progress')}",
            f"📊 {L('汇报', 'Decks')}",
        ])

        # Papers Tab
        with tabs[0]:
            _render_papers_tab(project, workspace_id, locked)

        # Ideas Tab
        with tabs[1]:
            _render_ideas_tab(project, workspace_id, locked)

        # Experiments Tab
        with tabs[2]:
            _render_experiments_tab(project, workspace_id, locked)

        # Progress Tab
        with tabs[3]:
            _render_progress_tab(project, workspace_id)

        # Decks Tab
        with tabs[4]:
            _render_decks_tab(project, workspace_id, locked)

    with inspector_col:
        st.markdown(f"### {L('项目信息', 'Project Info')}")
        if project:
            st.markdown(f"**{L('标题', 'Title')}:** {project['title']}")
            if project.get("goal"):
                st.markdown(f"**{L('目标', 'Goal')}:** {project['goal']}")
            if project.get("scope"):
                st.markdown(f"**{L('范围', 'Scope')}:** {project['scope']}")
            st.caption(f"{L('创建于', 'Created')}: {project.get('created_at', '-')[:10]}")


def _render_papers_tab(project: dict, workspace_id: str, locked: bool) -> None:
    """Render the papers management tab."""
    papers = list_project_papers(project["id"])
    
    st.markdown(f"#### 📄 {L('论文库', 'Paper Library')}")
    
    if papers:
        for paper in papers:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"**{paper['title']}**")
                st.caption(f"{paper.get('authors', '-')} · {paper['year']}")
            with col2:
                if paper.get("venue"):
                    st.caption(paper["venue"])
            with col3:
                if st.button(L("生成卡片", "Card"), key=f"btn_card_{paper['id']}"):
                    task_id = push_generation_start_notification(
                        workspace_id=workspace_id,
                        task_type="generate_paper_card",
                        title=f"{L('论文卡片', 'Paper Card')}: {paper['title'][:30]}...",
                    )
                    with st.spinner(L("正在生成论文卡片...", "Generating paper card...")):
                        result = generate_paper_card(
                            workspace_id=workspace_id,
                            paper_id=paper["id"],
                            doc_id=paper["doc_id"],
                        )
                        push_notification(
                            workspace_id=workspace_id,
                            task_type="generate_paper_card",
                            title=L("论文卡片", "Paper Card"),
                            status="succeeded",
                            summary=L("论文卡片生成完成", "Paper card generated"),
                            target={"nav": "Research"},
                            task_id=task_id,
                        )
                        st.session_state[f"paper_card_{paper['id']}"] = result["content"]
                        st.rerun()
        
        # Show paper cards if generated
        for paper in papers:
            card_content = st.session_state.get(f"paper_card_{paper['id']}")
            if card_content:
                with st.expander(f"📋 {paper['title']} - {L('论文卡片', 'Paper Card')}", expanded=True):
                    render_content_box(card_content)
    else:
        render_empty_state(
            "📄",
            L("暂无论文", "No Papers"),
            L("从资料库关联论文以开始分析。", "Link papers from the library to start analysis."),
        )

    # Add paper from library
    with st.expander(L("➕ 从资料库关联论文", "➕ Link Paper from Library"), expanded=False):
        docs = list_documents(workspace_id)
        doc_map = {doc["filename"]: doc for doc in docs}
        
        if not doc_map:
            st.info(L("资料库为空。请先在资料库页面导入文档。", "Library is empty. Import documents in the Library page first."))
        else:
            doc_name = st.selectbox(
                L("选择文档", "Select Document"),
                options=list(doc_map.keys()),
                key="research_attach_paper_doc_select",
            )
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input(L("论文标题", "Paper Title"), key="paper_title", placeholder=L("可选，默认用文件名", "Optional, defaults to filename"))
                authors = st.text_input(L("作者", "Authors"), key="paper_authors", placeholder=L("用逗号分隔", "Comma-separated"))
            with col2:
                year = st.text_input(L("年份", "Year"), key="paper_year", placeholder="2025")
                venue = st.text_input(L("会议/期刊", "Venue"), key="paper_venue", placeholder=L("可选", "Optional"))
            
            if st.button(L("添加论文", "Add Paper"), disabled=locked or not doc_name, key="btn_add_paper", type="primary"):
                paper_id = add_paper(
                    workspace_id=workspace_id,
                    doc_id=doc_map[doc_name]["id"],
                    title=title.strip() or doc_name,
                    authors=authors.strip() or "-",
                    year=year.strip() or "-",
                    venue=venue.strip() or None,
                    project_id=project["id"],
                )
                st.success(L("✓ 论文已添加", "✓ Paper added"))
                st.rerun()

    # Related work generation
    if papers:
        with st.expander(L("📚 生成项目相关工作", "📚 Generate Related Work"), expanded=False):
            if st.button(L("生成相关工作", "Generate Related Work"), disabled=locked, key="btn_gen_related_work", type="primary"):
                result = project_query(
                    workspace_id=workspace_id,
                    project_id=project["id"],
                    query="Project related work",
                    doc_ids=[paper["doc_id"] for paper in papers],
                )
                if result.get("query_type") == "global":
                    render_content_box(result["answer"], L("相关工作", "Related Work"))
                    coverage = result.get("coverage") or {}
                    if coverage:
                        st.caption(L("覆盖率报告", "Coverage Report"))
                        col1, col2, col3 = st.columns(3)
                        col1.metric(L("已包含", "Included"), coverage.get("included_docs", 0))
                        col2.metric(L("缺失", "Missing"), len(coverage.get("missing_docs", [])))
                        col3.metric(L("总数", "Total"), coverage.get("total_docs", 0))
                        
                        if coverage.get("missing_docs"):
                            st.warning(L("⚠️ 覆盖不完整", "⚠️ Coverage incomplete"))
                    render_doc_citations(result.get("citations"), workspace_id)
                else:
                    render_answer_with_citations(
                        text=result["answer"],
                        citations=result.get("citations"),
                        workspace_id=workspace_id,
                    )


def _render_ideas_tab(project: dict, workspace_id: str, locked: bool) -> None:
    """Render the ideas management tab."""
    ideas = list_ideas(project["id"])
    
    st.markdown(f"#### 💡 {L('创新点管理', 'Ideas Management')}")
    
    if ideas:
        for idea in ideas:
            status_icon = "✅" if idea['status'] == 'confirmed' else "📝"
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{status_icon} {idea['title']}**")
                st.caption(idea["claim"])
            with col2:
                st.caption(f"v{idea['version']}")
                st.caption(idea['status'])
    else:
        render_empty_state(
            "💡",
            L("暂无创新点", "No Ideas"),
            L("生成候选创新点或手动添加。", "Generate candidate ideas or add manually."),
        )

    # Generate idea
    with st.expander(L("🔮 AI 生成候选创新点", "🔮 AI Generate Candidate Idea"), expanded=False):
        prompt = st.text_area(
            L("方向描述", "Direction / Prompt"),
            key="research_idea_prompt",
            placeholder=L("描述要探索的创新方向...", "Describe the novelty direction to explore..."),
            height=100,
        )
        if st.button(L("生成创新点", "Generate Idea"), disabled=locked or not prompt.strip(), key="btn_gen_idea", type="primary"):
            result = create_idea_from_prompt(project_id=project["id"], prompt=prompt)
            st.success(f"✓ {L('已创建', 'Created')}: {result['title']}")
            st.rerun()

    # Confirm idea
    if ideas:
        with st.expander(L("✓ 确认创新点版本", "✓ Confirm Idea Version"), expanded=False):
            idea_map = {idea["title"]: idea for idea in ideas}
            selected = st.selectbox(
                L("选择创新点", "Select Idea"),
                options=list(idea_map.keys()),
                key="research_confirm_idea_select",
            )
            version = st.number_input(
                L("确认版本", "Confirm Version"),
                min_value=1,
                value=idea_map[selected]["version"],
                key="research_confirm_idea_version",
            )
            if st.button(L("确认", "Confirm"), disabled=locked, key="btn_confirm_idea", type="primary"):
                confirm_idea_version(idea_id=idea_map[selected]["id"], version=int(version))
                st.success(L("✓ 创新点已确认", "✓ Idea confirmed"))
                st.rerun()

        # Idea dialogue
        with st.expander(L("💬 创新点讨论对话", "💬 Idea Discussion Dialogue"), expanded=False):
            idea_map = {idea["title"]: idea for idea in ideas}
            selected = st.selectbox(L("选择创新点", "Select Idea"), options=list(idea_map.keys()), key="idea_dialogue")
            dialogue = list_idea_dialogue(idea_map[selected]["id"])
            
            if dialogue:
                for turn in dialogue:
                    role_icon = "👤" if turn['role'] == 'user' else "🤖"
                    st.markdown(f"**{role_icon} {turn['role']}:** {turn['content']}")
            else:
                st.caption(L("暂无对话记录。", "No dialogue yet."))
            
            st.divider()
            new_turn = st.text_area(L("新增对话", "Add Message"), key="idea_dialogue_turn", height=80)
            col1, col2 = st.columns([1, 3])
            with col1:
                role = st.selectbox(L("角色", "Role"), options=["user", "assistant"], key="idea_dialogue_role")
            with col2:
                if st.button(L("发送", "Send"), disabled=locked or not new_turn.strip(), key="btn_add_dialogue_turn", type="primary"):
                    add_idea_dialogue(
                        idea_id=idea_map[selected]["id"],
                        turn_no=len(dialogue) + 1,
                        role=role,
                        content=new_turn.strip(),
                    )
                    st.success(L("✓ 对话已更新", "✓ Dialogue updated"))
                    st.rerun()


def _render_experiments_tab(project: dict, workspace_id: str, locked: bool) -> None:
    """Render the experiments management tab."""
    plans = list_experiment_plans(project["id"])
    ideas = list_ideas(project["id"])
    
    st.markdown(f"#### 🧪 {L('实验管理', 'Experiment Management')}")
    
    # Show existing plans
    if plans:
        st.markdown(f"**{L('实验计划', 'Experiment Plans')}**")
        for plan in plans:
            with st.expander(f"Plan #{plan['id']} - {plan['created_at'][:10]}", expanded=False):
                if plan.get("plan_json"):
                    st.json(json.loads(plan["plan_json"]) if isinstance(plan["plan_json"], str) else plan["plan_json"])
    else:
        st.caption(L("暂无实验计划。", "No experiment plans yet."))

    # Generate plan from idea
    if ideas:
        with st.expander(L("🔮 从创新点生成实验计划", "🔮 Generate Plan from Idea"), expanded=False):
            idea_map = {idea["title"]: idea for idea in ideas}
            selected = st.selectbox(L("选择创新点", "Select Idea"), options=list(idea_map.keys()), key="idea_plan")
            if st.button(L("生成计划", "Generate Plan"), disabled=locked, key="btn_gen_exp_plan", type="primary"):
                task_id = push_generation_start_notification(
                    workspace_id=workspace_id,
                    task_type="generate_experiment_plan",
                    title=L("实验计划", "Experiment Plan"),
                )
                with st.spinner(L("正在生成实验计划...", "Generating experiment plan...")):
                    result = generate_experiment_plan_from_idea(
                        project_id=project["id"],
                        idea_id=idea_map[selected]["id"],
                        idea_claim=idea_map[selected]["claim"],
                    )
                    push_notification(
                        workspace_id=workspace_id,
                        task_type="generate_experiment_plan",
                        title=L("实验计划", "Experiment Plan"),
                        status="succeeded",
                        summary=L("实验计划生成完成", "Experiment plan generated"),
                        target={"nav": "Research"},
                        task_id=task_id,
                    )
                    st.success(L("✓ 计划已生成", "✓ Plan generated"))
                    st.json(result["plan"])
                    st.rerun()

    # Add experiment run
    with st.expander(L("➕ 新增实验记录", "➕ Add Experiment Run"), expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input(
                L("日期", "Date"),
                key="run_date",
                placeholder=datetime.now().strftime("%Y-%m-%d"),
            )
        with col2:
            plan_id_options = ["-"] + [str(p["id"]) for p in plans]
            plan_select = st.selectbox(L("关联计划", "Link to Plan"), options=plan_id_options, key="run_plan_select")
        
        result_text = st.text_area(L("实验结果", "Result"), key="run_result", height=80, placeholder=L("描述实验结果...", "Describe the outcome..."))
        notes = st.text_area(L("备注与观察", "Notes & Observations"), key="run_notes", height=80)
        next_action = st.text_input(L("下一步行动", "Next Action"), key="run_next")
        
        if st.button(L("添加记录", "Add Run"), disabled=locked or not date.strip(), key="btn_add_exp_run", type="primary"):
            add_experiment_run(
                project_id=project["id"],
                plan_id=int(plan_select) if plan_select != "-" else (plans[0]["id"] if plans else None),
                date=date.strip(),
                result=result_text.strip(),
                notes=notes.strip(),
                next_action=next_action.strip(),
            )
            st.success(L("✓ 实验记录已添加", "✓ Experiment run added"))
            st.rerun()


def _render_progress_tab(project: dict, workspace_id: str) -> None:
    """Render the progress timeline tab."""
    runs = list_experiment_runs(project["id"])
    
    st.markdown(f"#### 📈 {L('进度时间线', 'Progress Timeline')}")
    
    if not runs:
        render_empty_state(
            "📈",
            L("暂无进度记录", "No Progress Records"),
            L("在「实验」页签添加实验记录以追踪进度。", "Add experiment runs in the Experiments tab to track progress."),
        )
        return

    # Timeline view
    for run in runs:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"**{run['date']}**")
        with col2:
            if run.get("result"):
                st.write(f"📊 {run['result']}")
            if run.get("notes"):
                st.caption(run["notes"])
            if run.get("next_action"):
                st.caption(f"➡️ {L('下一步', 'Next')}: {run['next_action']}")
        st.divider()


def _render_decks_tab(project: dict, workspace_id: str, locked: bool) -> None:
    """Render the presentation decks tab."""
    papers = list_project_papers(project["id"])
    
    st.markdown(f"#### 📊 {L('汇报生成', 'Deck Generation')}")
    
    query = st.text_input(
        L("汇报重点", "Deck Focus"),
        key="deck_focus",
        placeholder=L("例如：注意力机制的最新进展", "e.g. Recent advances in attention mechanisms"),
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        duration = st.number_input(L("时长（分钟）", "Duration (min)"), min_value=5, max_value=60, value=10, key="deck_duration")
    
    if st.button(L("生成汇报", "Generate Deck"), disabled=locked, key="btn_gen_deck", type="primary"):
        if not papers:
            st.warning(L("请先添加论文以生成汇报。", "Please add papers first to generate a deck."))
        else:
            task_id = push_generation_start_notification(
                workspace_id=workspace_id,
                task_type="generate_deck",
                title=L("汇报生成", "Deck Generation"),
            )
            with st.spinner(L("正在生成汇报...", "Generating deck...")):
                result = project_query(
                    workspace_id=workspace_id,
                    project_id=project["id"],
                    query=query or "Project summary deck",
                    doc_ids=[paper["doc_id"] for paper in papers],
                )
                coverage = result.get("coverage")
                deck = generate_deck(
                    workspace_id=workspace_id,
                    source_kind="project",
                    source_ids=[project["id"]],
                    duration=duration,
                    coverage=coverage,
                )
                push_notification(
                    workspace_id=workspace_id,
                    task_type="generate_deck",
                    title=L("汇报生成", "Deck Generation"),
                    status="succeeded",
                    summary=L("汇报生成完成", "Deck generated"),
                    target={"nav": "Research"},
                    task_id=task_id,
                )
            
            st.markdown(f"**{L('生成的汇报', 'Generated Deck')} (Marp)**")
            render_content_box(deck["content"])
            
            if coverage:
                st.markdown(f"**{L('覆盖率报告', 'Coverage Report')}**")
                col1, col2, col3 = st.columns(3)
                col1.metric(L("已包含", "Included"), coverage.get("included_docs", 0))
                col2.metric(L("缺失", "Missing"), len(coverage.get("missing_docs", [])))
                col3.metric(L("总数", "Total"), coverage.get("total_docs", 0))
    
    if not papers:
        st.info(L("💡 提示：先在「论文」页签添加论文，才能生成覆盖完整的汇报。", "💡 Tip: Add papers in the Papers tab first to generate comprehensive decks."))
