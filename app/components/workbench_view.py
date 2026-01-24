from __future__ import annotations

import streamlit as st


def render_workbench_list(
    *,
    title: str,
    items: list[dict],
    label_key: str,
    id_key: str,
    search_key: str,
    new_label: str,
    new_placeholder: str,
    create_callback: callable | None = None,
    empty_hint: str = "No items yet.",
    selection_state_key: str = "selected_item_id",
) -> dict | None:
    st.markdown(f"### {title}")
    query = st.text_input("Search", key=search_key, placeholder="Type to filter")
    filtered = []
    for item in items:
        if not query or query.lower() in str(item[label_key]).lower():
            filtered.append(item)
    if not filtered:
        st.caption(empty_hint)
    selected_id = st.session_state.get(selection_state_key)

    for item in filtered:
        is_selected = item[id_key] == selected_id
        with st.container():
            st.markdown(
                f"**{item[label_key]}**" if not is_selected else f"**✅ {item[label_key]}**"
            )
            if st.button(
                "Select",
                key=f"select_{selection_state_key}_{item[id_key]}",
                disabled=is_selected,
            ):
                st.session_state[selection_state_key] = item[id_key]
                selected_id = item[id_key]
    if create_callback:
        st.divider()
        st.caption("Create new")
        new_name = st.text_input(
            new_label,
            key=f"{selection_state_key}_new_name",
            placeholder=new_placeholder,
        )
        if st.button(
            f"Create {title[:-1]}",
            key=f"{selection_state_key}_create",
            disabled=not new_name.strip(),
        ):
            created_id = create_callback(new_name.strip())
            st.session_state[selection_state_key] = created_id
            selected_id = created_id
            st.success(f"{title[:-1]} created.")
    if not selected_id:
        return None
    for item in items:
        if item[id_key] == selected_id:
            return item
    return None
