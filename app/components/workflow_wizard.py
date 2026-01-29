from __future__ import annotations

import streamlit as st

WORKFLOW_LABELS = {
    "courses": "Course Sprint",
    "papers": "Paper Review",
    "presentations": "Presentation Builder",
}


def render_workflow_selector() -> str:
    st.subheader("Workflows")
    selection = st.radio(
        "Choose a workflow",
        options=list(WORKFLOW_LABELS.keys()),
        format_func=lambda key: WORKFLOW_LABELS[key],
    )
    st.caption("Use the center panel to complete the steps.")
    return selection


def render_workflow_steps(center: st.delta_generator.DeltaGenerator, workflow_key: str) -> None:
    steps_map = {
        "courses": [
            "1. Add course PDFs or syllabi in Library.",
            "2. Choose documents and generate course assets.",
            "3. Review citations + export in the Inspector.",
        ],
        "papers": [
            "1. Import papers in Library.",
            "2. Select papers and run summaries or review questions.",
            "3. Compare versions and export citations.",
        ],
        "presentations": [
            "1. Import materials in Library.",
            "2. Build slides and Q&A with retrieval.",
            "3. Export Marp deck and citations.",
        ],
    }
    with center:
        st.markdown("### Steps")
        for step in steps_map.get(workflow_key, []):
            st.write(step)
