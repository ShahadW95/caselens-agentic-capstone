"""CASE//LENS Streamlit entry point; product logic lives in caselens.ui."""

from __future__ import annotations

import streamlit as st

from src.caselens.ui import (
    apply_visual_system,
    create_checkpoint_services,
    initialize_session_state,
    render_landing_case_file,
    render_utility_header,
    render_workbench,
)

st.set_page_config(
    page_title="CASE//LENS — Beyond the Verdict",
    page_icon=":material/folder_open:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
initialize_session_state(st.session_state)
services = create_checkpoint_services()
apply_visual_system(st.session_state)
language = render_utility_header(st.session_state, services)

if not st.session_state["session_started"]:
    if render_landing_case_file(services, language):
        st.session_state["session_started"] = True
        st.rerun()
else:
    render_workbench(st.session_state, services, language)
