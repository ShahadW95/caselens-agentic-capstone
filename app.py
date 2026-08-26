"""Minimal Prompt A0 Streamlit checkpoint; no model call is made."""

from __future__ import annotations

import streamlit as st

from src.caselens.config import RuntimeConfig, safe_setup_message

st.set_page_config(page_title="CASE//LENS")
st.title("CASE//LENS — Beyond the Verdict")
st.caption("Foundation ready")
st.write(
    "A source-grounded multi-agent research and learning assistant for one "
    "curated closed case. This checkpoint defines contracts only and makes "
    "no live model call."
)

config = RuntimeConfig()
warning = safe_setup_message(config)
if warning:
    st.warning(warning)
else:
    st.info("Provider configuration was detected. Live calls remain disabled in A0.")

st.subheader("Five bounded roles")
roles = (
    ("Case Director", "Plans, delegates, joins findings, and owns the response."),
    ("Source & Evidence Specialist", "Retrieves and labels source-backed evidence."),
    ("Legal Explanation Specialist", "Explains the plea, judgment, and law with citations."),
    ("Timeline & What-If Specialist", "Queries timelines and bounded causal changes."),
    ("Editorial Integrity Reviewer", "Performs one citation and neutrality review."),
)
for name, responsibility in roles:
    st.markdown(f"**{name}** — {responsibility}")

st.caption("Educational research only — not legal advice.")
