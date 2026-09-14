"""Typed Streamlit presentation boundary for CASE//LENS."""
from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import streamlit as st
from pydantic import BaseModel, ConfigDict

from .adapters import DevelopmentFakeAdapters, create_development_fake_adapters
from .contracts import (MVP_CASE_ID, CaseQuery, CaseResearchBrief, InteractionMode,
                        LanguageCode, MessageRole, ProceedingStatus, StableId,
                        WorkflowStatus)
from .graph import RoutingAdapters, run_case_query
from .memory import (SessionMemory, new_memory, remember_final_answer,
                     remember_finding, remember_query, reset_memory,
                     resolve_follow_up)
from .state import CaseLensState, new_session

_CSS = Path(__file__).resolve().parents[2] / "assets" / "caselens.css"


class CaseCard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    case_id: StableId
    title: str
    jurisdiction: str
    status: ProceedingStatus
    amount_cues: tuple[str, ...]


class CaseCardLoader(Protocol):
    def load(self) -> CaseCard: ...


class FixtureCaseCardLoader:
    def load(self) -> CaseCard:
        return CaseCard(
            case_id=MVP_CASE_ID,
            title="United States v. Bernard L. Madoff",
            jurisdiction="U.S. District Court, Southern District of New York",
            status=ProceedingStatus.CLOSED_FINAL,
            amount_cues=("Fictitious statement balances", "Estimated principal loss",
                         "Forfeiture orders", "Recovered or distributed funds"),
        )


@dataclass(frozen=True)
class WorkbenchServices:
    adapters: RoutingAdapters
    case_card_loader: CaseCardLoader
    development_fake: bool


@dataclass(frozen=True)
class TurnOutcome:
    state: CaseLensState
    memory: SessionMemory
    request_fingerprint: str
    duplicate: bool = False


def create_checkpoint_services() -> WorkbenchServices:
    adapters: DevelopmentFakeAdapters = create_development_fake_adapters()
    return WorkbenchServices(adapters, FixtureCaseCardLoader(), True)


def request_fingerprint(query: CaseQuery) -> str:
    return sha256(query.model_dump_json().encode()).hexdigest()


def execute_workbench_turn(query: CaseQuery, services: WorkbenchServices,
                           memory: SessionMemory, *,
                           previous_state: CaseLensState | None = None,
                           previous_fingerprint: str | None = None) -> TurnOutcome:
    fingerprint = request_fingerprint(query)
    if (fingerprint == previous_fingerprint and previous_state is not None
            and previous_state.status is WorkflowStatus.COMPLETED):
        return TurnOutcome(previous_state, memory, fingerprint, True)
    resolved = resolve_follow_up(query, memory).query
    memory = remember_query(memory, resolved)
    turn_state = new_session(resolved)
    if previous_state is not None:
        turn_state = turn_state.model_copy(update={
            "turn_count": previous_state.turn_count,
            "max_turns": previous_state.max_turns,
        })
    turn_state = turn_state.model_copy(update={"short_term_messages": memory.messages})
    result = run_case_query(resolved, services.adapters, state=turn_state)
    for finding in (result.evidence_finding, result.legal_finding,
                    result.timeline_finding, result.counterfactual_finding):
        if finding is not None:
            memory = remember_finding(memory, finding)
    if result.final_brief is not None:
        memory = remember_final_answer(memory, result.final_brief.concise_answer,
                                       language=result.final_brief.language)
    elif result.validation_errors:
        memory = remember_final_answer(memory, result.validation_errors[-1].user_message,
                                       language=resolved.language)
    return TurnOutcome(result, memory, fingerprint)


def initialize_session_state(state: MutableMapping[str, object]) -> None:
    state.setdefault("case_language", "ar")
    state.setdefault("language_selector", state["case_language"])
    state.setdefault("case_session_id", f"session.{uuid4().hex}")
    state.setdefault("case_memory", new_memory(str(state["case_session_id"]), _lang(state)))
    for key, value in (("workflow_state", None), ("last_request_fingerprint", None),
                       ("session_started", False), ("in_flight", False),
                       ("confirm_reset", False),
                       ("interaction_mode", InteractionMode.ASK_CASE),
                       ("workbench_step", 1)):
        state.setdefault(key, value)


def reset_workbench_state(state: MutableMapping[str, object]) -> None:
    current = state.get("case_memory")
    memory = reset_memory(current) if isinstance(current, SessionMemory) else new_memory(
        f"session.{uuid4().hex}", _lang(state))
    state.update(case_session_id=memory.session_id, case_memory=memory,
                 workflow_state=None, last_request_fingerprint=None,
                 confirm_reset=False, in_flight=False, workbench_step=1)


def apply_visual_system(state: MutableMapping[str, object]) -> None:
    st.html(_CSS)
    selected = state.get("language_selector", state.get("case_language", "ar"))
    direction, align = ("ltr", "left") if selected == "en" else ("rtl", "right")
    st.html(f"<style>.stApp{{direction:{direction}}}.stApp p,.stApp li,.stApp label"
            f"{{text-align:{align}}}</style>")


def render_language_selector(state: MutableMapping[str, object]) -> LanguageCode:
    selected = st.segmented_control("اللغة | Language", ("ar", "en"),
        format_func=lambda v: "العربية" if v == "ar" else "English",
        key="language_selector", required=True, width="content", persist_state="session")
    language: LanguageCode = "en" if selected == "en" else "ar"
    state["case_language"] = language
    memory = state.get("case_memory")
    if isinstance(memory, SessionMemory) and memory.language != language:
        state["case_memory"] = memory.model_copy(update={"language": language})
    return language


def render_utility_header(state: MutableMapping[str, object],
                          services: WorkbenchServices) -> LanguageCode:
    current = _lang(state)
    left, middle, controls = st.columns([4, 2, 4], vertical_alignment="center")
    with left:
        st.html('<div class="caselens-wordmark">CASE//LENS</div>'
                '<div class="caselens-file-id">CASE FILE 001 · US_SDNY_09CR00213_DC</div>')
    with middle:
        if services.development_fake:
            st.badge(_T[current]["demo"], icon=":material/science:", color="orange")
    with controls:
        language = render_language_selector(state)
        if state.get("session_started") and st.button(_T[language]["reset"],
                icon=":material/restart_alt:", disabled=bool(state.get("in_flight")),
                key="utility_reset", width="stretch"):
            state["confirm_reset"] = True
    return language


def render_landing_case_file(services: WorkbenchServices, language: LanguageCode) -> bool:
    t, card = _T[language], services.case_card_loader.load()
    st.html('<section class="caselens-hero">'
            f'<div class="caselens-kicker">{escape(t["kicker"])}</div>'
            '<h1>CASE//LENS</h1><h2>Beyond the Verdict</h2>'
            f'<p>{escape(t["hero"])}</p></section>')
    st.html('<article class="caselens-case-file">'
            f'<div class="caselens-section-label">{escape(t["selected"])}</div>'
            f'<h3>{escape(card.title)}</h3><p><strong>{escape(t["jurisdiction"])}:'
            f'</strong> {escape(card.jurisdiction)}</p><p>{escape(t["reason"])}</p>'
            f'<div class="caselens-chip-row"><span class="caselens-chip">{escape(t["closed"])}</span>'
            f'<span class="caselens-chip">S.D.N.Y.</span><span class="caselens-chip">'
            f'{escape(t["education"])}</span></div></article>')
    st.caption(t["disclaimer"])
    return st.button(t["start"], type="primary", icon=":material/folder_open:",
                     key="open_case_file", width="content")


def render_case_briefing(services: WorkbenchServices, language: LanguageCode) -> bool:
    return render_landing_case_file(services, language)


def render_workbench(state: MutableMapping[str, object], services: WorkbenchServices,
                     language: LanguageCode) -> None:
    t, card = _T[language], services.case_card_loader.load()
    st.html('<section class="caselens-active-case">'
            f'<div class="caselens-section-label">{escape(t["active"])}</div>'
            f'<h1>{escape(card.title)}</h1><div class="caselens-meta">{escape(t["closed"])} · '
            f'{escape(card.jurisdiction)} · {escape(t["language"])}</div></section>')
    if services.development_fake:
        st.html(f'<div class="caselens-demo-note">{escape(t["demo_message"])}</div>')
        with st.expander(t["dev"], icon=":material/build:"):
            st.caption(t["dev_copy"])
    else:
        st.error(t["provider"])
    _steps(state, language)
    _reset_confirmation(state, language)
    query = _mode_form(state, language)
    if query is not None:
        _submit(state, services, query, language)
    workflow = state.get("workflow_state")
    if isinstance(workflow, CaseLensState):
        _case_brief(workflow, language)
    _conversation(state, language)


def _steps(state: MutableMapping[str, object], language: LanguageCode) -> None:
    active = int(state.get("workbench_step", 1))
    items = "".join(f'<div class="caselens-step{" is-active" if i == active else ""}">'
                    f'<strong>{i:02d}</strong>{escape(label)}</div>'
                    for i, label in enumerate(_STEPS[language], 1))
    st.html(f'<div class="caselens-steps">{items}</div>')


def _reset_confirmation(state: MutableMapping[str, object], language: LanguageCode) -> None:
    if not state.get("confirm_reset"):
        return
    t = _T[language]
    st.warning(t["reset_confirm"])
    with st.container(horizontal=True):
        if st.button(t["confirm"], type="primary", key="confirm_reset_button"):
            reset_workbench_state(state); state["session_started"] = False; st.rerun()
        if st.button(t["cancel"], key="cancel_reset_button"):
            state["confirm_reset"] = False; st.rerun()


def _mode_form(state: MutableMapping[str, object], language: LanguageCode) -> CaseQuery | None:
    t = _T[language]
    st.html(f'<div class="caselens-section-label">{escape(t["route"])}</div>')
    mode = st.segmented_control(t["mode"], tuple(InteractionMode),
        format_func=lambda item: _MODE_LABELS[language][item], key="interaction_mode",
        required=True, width="stretch", persist_state="session")
    mode = mode if isinstance(mode, InteractionMode) else InteractionMode.ASK_CASE
    if int(state.get("workbench_step", 1)) < 2:
        state["workbench_step"] = 2
    st.html(f'<div class="caselens-mode-intro"><h3>{escape(_MODE_LABELS[language][mode])}</h3>'
            f'<p>{escape(_MODE_INTROS[language][mode])}</p></div>')
    query, claim, event, change = "", None, None, None
    with st.form("case_query_form", border=False):
        if mode is InteractionMode.ASK_CASE:
            query = st.text_area(t["question"], key="ask_case_question",
                                 placeholder=t["ask_example"]) or ""
        elif mode is InteractionMode.VIEW_TIMELINE:
            query = st.text_input(t["timeline_filter"], key="timeline_filter",
                                  placeholder=t["timeline_example"]) or ""
        elif mode is InteractionMode.CHECK_CLAIM:
            claim = st.selectbox(t["claim"], tuple(_CLAIMS), index=None,
                format_func=lambda item: _CLAIMS[item][language],
                placeholder=t["claim_placeholder"], key="claim_selection")
        elif mode is InteractionMode.EXPLAIN_VERDICT:
            query = st.text_area(t["judgment_question"], key="judgment_question",
                                 placeholder=t["judgment_example"], help=t["judgment_help"]) or ""
        else:
            event = st.selectbox(t["event"], tuple(_EVENTS), index=None,
                format_func=lambda item: _EVENTS[item][language],
                placeholder=t["event_placeholder"], key="event_selection")
            change = st.selectbox(t["change"], tuple(_CHANGES), index=None,
                format_func=lambda item: _CHANGES[item][language],
                placeholder=t["change_placeholder"], key="change_selection")
        submitted = st.form_submit_button(t["run"], type="primary",
            icon=":material/manage_search:", disabled=bool(state.get("in_flight")), width="stretch")
    if not submitted:
        return None
    return CaseQuery(session_id=str(state["case_session_id"]), mode=mode, language=language,
                     user_query=query, selected_claim_id=claim, selected_event_id=event,
                     allowed_change_id=change)


def _submit(state: MutableMapping[str, object], services: WorkbenchServices,
            query: CaseQuery, language: LanguageCode) -> None:
    t = _T[language]
    if state.get("in_flight"):
        st.warning(t["already"]); return
    memory = state.get("case_memory")
    memory = memory if isinstance(memory, SessionMemory) else new_memory(query.session_id, language)
    previous = state.get("workflow_state")
    previous = previous if isinstance(previous, CaseLensState) else None
    state["in_flight"] = True
    try:
        with st.status(t["running"], expanded=True) as status:
            for stage in _PROGRESS[language]: st.write(stage)
            outcome = execute_workbench_turn(query, services, memory,
                previous_state=previous,
                previous_fingerprint=_optional(state.get("last_request_fingerprint")))
            status.update(label=t["duplicate"] if outcome.duplicate else t["complete"],
                state="complete" if outcome.state.status is WorkflowStatus.COMPLETED else "error",
                expanded=False)
        state.update(workflow_state=outcome.state, case_memory=outcome.memory,
                     last_request_fingerprint=outcome.request_fingerprint, workbench_step=3)
    finally:
        state["in_flight"] = False


def _case_brief(state: CaseLensState, language: LanguageCode) -> None:
    t = _T[language]
    if state.status is not WorkflowStatus.COMPLETED or state.final_brief is None:
        message = state.validation_errors[-1].user_message if state.validation_errors else t["unavailable"]
        (st.warning if state.status is WorkflowStatus.NEEDS_CLARIFICATION else st.error)(message)
        _trace(state, language, False); return
    brief = state.final_brief
    st.html('<section class="caselens-brief-head">'
        f'<div class="caselens-section-label">{escape(t["brief"])}</div>'
        f'<div class="caselens-status-line"><span class="caselens-chip">'
        f'{escape(_MODE_LABELS[language][state.mode])}</span><span class="caselens-chip">'
        f'{escape(t["complete"])}</span><span class="caselens-chip">{len(brief.citations)} '
        f'{escape(t["source_count"])}</span><span class="caselens-chip">{escape(t["demo"])}</span></div>'
        f'<h2>{escape(t["answer"])}</h2><p>{escape(brief.concise_answer)}</p></section>')
    st.caption(f'{t["confidence"]}: {_confidence(brief.confidence.value, language)}')
    findings, sources, limits, trace = st.tabs([t["findings"], t["sources"], t["limits"], t["trace"]])
    with findings: _findings(brief, language)
    with sources: _sources(brief, language)
    with limits:
        for item in brief.limitations: st.markdown(f"- {item}")
        st.caption(brief.educational_disclaimer)
    with trace: _trace(state, language, True)


def _findings(brief: CaseResearchBrief, language: LanguageCode) -> None:
    t = _T[language]
    groups = ((t["verified"], "verified", brief.established_facts),
              (t["allegation"], "allegation", brief.allegations),
              (t["interpretation"], "disputed", brief.disputed_items),
              (t["insufficient"], "unknown", brief.unknowns))
    for label, css, statements in groups:
        for statement in statements:
            st.html(f'<div class="caselens-finding"><div class="caselens-finding-label {css}">'
                    f'◆ {escape(label)}</div><div>{escape(statement.text)}</div></div>')
    if brief.unknowns and not brief.established_facts: st.warning(t["evidence_missing"])
    if brief.legal_explanation: st.subheader(t["legal"]); st.write(brief.legal_explanation)
    if brief.timeline_events:
        st.subheader(t["timeline"])
        for event in brief.timeline_events:
            st.html(f'<div class="caselens-finding"><div class="caselens-finding-label verified">'
                    f'{event.event_date.isoformat()} · {escape(event.track.value)}</div>'
                    f'<strong>{escape(event.title)}</strong><div>{escape(event.summary)}</div></div>')
    if brief.counterfactual:
        item = brief.counterfactual
        st.html(f'<div class="caselens-finding"><div class="caselens-finding-label hypothetical">'
                f'◆ {escape(t["hypothetical"])}</div><strong>{escape(t["assumption"])}:</strong> '
                f'{escape(item.changed_assumption)}</div>')
        for value in item.downstream_possible_effects + item.unknowns: st.markdown(f"- {value}")
        st.warning(item.mandatory_hypothetical_disclaimer)


def _sources(brief: CaseResearchBrief, language: LanguageCode) -> None:
    t = _T[language]; st.caption(t["sources_intro"])
    for citation in brief.citations:
        demo = "fictional" in citation.source_type.lower() or "example.invalid" in str(citation.original_url)
        title, status = ((t["demo_citation"], t["demo_unavailable"])
                         if demo else (citation.title, t["source_available"]))
        st.html(f'<div class="caselens-source-slip"><div class="caselens-finding-label '
                f'{"hypothetical" if demo else "verified"}">{escape(status)}</div>'
                f'<strong>{escape(title)}</strong><div class="caselens-source-meta">'
                f'{escape(citation.source_type)} · {escape(t["tier"])} {escape(citation.source_tier.value)} · '
                f'{escape(citation.heading)}</div></div>')
        if not demo and citation.original_url is not None:
            st.link_button(t["open"], str(citation.original_url), icon=":material/open_in_new:")


def _conversation(state: MutableMapping[str, object], language: LanguageCode) -> None:
    memory = state.get("case_memory")
    if not isinstance(memory, SessionMemory) or not memory.messages: return
    with st.expander(_T[language]["history"], icon=":material/history:"):
        with st.container(height=260):
            for message in memory.messages:
                with st.chat_message("user" if message.role is MessageRole.USER else "assistant"):
                    st.write(message.content)


def safe_trace_rows(state: CaseLensState, language: LanguageCode) -> list[dict[str, str]]:
    t = _T[language]
    titles = ", ".join(c.title for c in state.final_brief.citations) if state.final_brief else ""
    return [{t["phase"]: _PHASE[language].get(e.phase.split(":")[0], e.phase),
             t["status"]: _STATUS[language].get(e.status.value, e.status.value),
             t["agent"]: _AGENT[language].get(e.actor, e.actor),
             t["summary"]: e.safe_summary,
             t["source_col"]: titles if e.event_type.value in {"RETRIEVAL", "TOOL"} else ""}
            for e in state.audit_events]


def _trace(state: CaseLensState, language: LanguageCode, expanded: bool) -> None:
    t = _T[language]
    def body() -> None:
        st.caption(t["trace_note"])
        for row in safe_trace_rows(state, language):
            st.html(f'<div class="caselens-trace-step"><div class="caselens-trace-label">'
                    f'{escape(row[t["phase"]])} · {escape(row[t["status"]])}</div>'
                    f'<strong>{escape(row[t["agent"]])}</strong><div class="caselens-trace-summary">'
                    f'{escape(row[t["summary"]])}</div></div>')
    if expanded: body()
    else:
        with st.expander(t["trace"], icon=":material/account_tree:"): body()


def _lang(state: MutableMapping[str, object]) -> LanguageCode:
    return "en" if state.get("case_language") == "en" else "ar"


def _optional(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _confidence(value: str, language: LanguageCode) -> str:
    return {"ar": {"LOW": "منخفضة", "MEDIUM": "متوسطة", "HIGH": "مرتفعة"},
            "en": {"LOW": "Low", "MEDIUM": "Medium", "HIGH": "High"}}[language].get(value, value)


_MODE_LABELS = {
 "ar": {InteractionMode.ASK_CASE:"اسأل عن القضية",InteractionMode.VIEW_TIMELINE:"اعرض الخط الزمني",InteractionMode.CHECK_CLAIM:"تحقّق من ادعاء",InteractionMode.EXPLAIN_VERDICT:"اشرح الحكم",InteractionMode.WHAT_IF:"ماذا لو؟"},
 "en": {InteractionMode.ASK_CASE:"Ask the Case",InteractionMode.VIEW_TIMELINE:"View Timeline",InteractionMode.CHECK_CLAIM:"Check a Claim",InteractionMode.EXPLAIN_VERDICT:"Explain the Verdict",InteractionMode.WHAT_IF:"What If?"}}
_MODE_INTROS = {
 "ar": {InteractionMode.ASK_CASE:"اكتب سؤالاً مركزاً عن القضية.",InteractionMode.VIEW_TIMELINE:"استخدم مرشحاً اختيارياً لتسلسل الأحداث.",InteractionMode.CHECK_CLAIM:"اختر ادعاءً لمقارنته بسجل الأدلة.",InteractionMode.EXPLAIN_VERDICT:"اطلب شرحاً للحكم والأدلة الداعمة.",InteractionMode.WHAT_IF:"اختر حدثاً وتغييراً لافتراض محدود."},
 "en": {InteractionMode.ASK_CASE:"Enter a focused question about the case record.",InteractionMode.VIEW_TIMELINE:"Optionally filter the relevant case events.",InteractionMode.CHECK_CLAIM:"Choose a claim to compare with the evidence record.",InteractionMode.EXPLAIN_VERDICT:"Ask about the plea, judgment, and evidence.",InteractionMode.WHAT_IF:"Choose one event and allowed change."}}
_STEPS={"ar":("اختر نوع البحث.","أدخل سؤالك.","راجع ملف النتائج."),"en":("Choose a mode.","Enter the question.","Review the case brief.")}
_PROGRESS={"ar":("التحقق من الطلب.","اختيار المتخصصين.","مراجعة الأدلة.","بناء ملف النتائج.","المراجعة التحريرية."),"en":("Validating request.","Selecting specialists.","Reviewing evidence.","Building case brief.","Editorial review.")}
_CLAIMS={"claim.madoff.amount.65b":{"ar":"سرق ميدوف 65 مليار دولار نقدًا","en":"Madoff stole USD 65 billion in cash"},"claim.madoff.regulators.bribed":{"ar":"كانت جميع الجهات الرقابية مرتشية","en":"All regulators were bribed"}}
_EVENTS={"event.madoff.early_complaint":{"ar":"شكوى مبكرة إلى SEC","en":"An early complaint to the SEC"},"event.madoff.2008_collapse":{"ar":"انهيار المخطط عام 2008","en":"The scheme's 2008 collapse"}}
_CHANGES={"change.sec.independent_trade_verification":{"ar":"تحقق SEC بصورة مستقلة من التداولات","en":"SEC independently verifies trading"},"change.custody.independent_confirmation":{"ar":"تأكيد مستقل لحفظ الأصول","en":"Independent custody confirmation"}}
_AGENT={"ar":{"CASE_DIRECTOR":"مشرف القضية","SOURCE_AND_EVIDENCE":"متخصص الأدلة","LEGAL_ANALYSIS":"المتخصص القانوني","TIMELINE_ANALYSIS":"متخصص الخط الزمني","EDITORIAL_INTEGRITY_REVIEWER":"المراجع التحريري"},"en":{"CASE_DIRECTOR":"Case Supervisor","SOURCE_AND_EVIDENCE":"Evidence Specialist","LEGAL_ANALYSIS":"Legal Specialist","TIMELINE_ANALYSIS":"Timeline Specialist","EDITORIAL_INTEGRITY_REVIEWER":"Editorial Reviewer"}}
_PHASE={"ar":{"validation":"التحقق من الطلب","route":"اختيار المسار","delegation":"تكليف المتخصص","retrieval":"مراجعة الأدلة","tool":"فحص منظّم","join":"تجميع النتائج","draft":"بناء ملف النتائج","review":"المراجعة التحريرية","final_validation":"التحقق النهائي","completion":"الاكتمال","error":"توقف آمن"},"en":{"validation":"Request validation","route":"Route selection","delegation":"Specialist assignment","retrieval":"Evidence review","tool":"Structured check","join":"Findings joined","draft":"Case brief built","review":"Editorial review","final_validation":"Final validation","completion":"Completed","error":"Safe stop"}}
_STATUS={"ar":{"RUNNING":"قيد التنفيذ","REVIEWING":"قيد المراجعة","COMPLETED":"مكتمل","NEEDS_CLARIFICATION":"يحتاج توضيحاً","INSUFFICIENT_OR_ESCALATED":"أدلة غير كافية","FAILED":"توقف بأمان"},"en":{"RUNNING":"In progress","REVIEWING":"Reviewing","COMPLETED":"Complete","NEEDS_CLARIFICATION":"Needs clarification","INSUFFICIENT_OR_ESCALATED":"Insufficient evidence","FAILED":"Stopped safely"}}

_T={
"ar":{"demo":"بيانات تجريبية","kicker":"أرشيف تحليلي · قضية جنائية مغلقة","hero":"ملف قضية ذكي يربط الأحداث والأدلة والحكم بمصادرها.","selected":"ملف القضية المختار","jurisdiction":"الاختصاص","reason":"اختيرت القضية لتوضيح الفرق بين الوقائع والادعاءات عبر مصادر قابلة للتتبّع.","closed":"قضية مغلقة","education":"للبحث والتعليم","disclaimer":"للبحث والتعليم فقط — ليست استشارة قانونية.","start":"افتح ملف القضية","active":"ملف قضية نشط","language":"العربية","demo_message":"وضع العرض التجريبي — تستخدم هذه النسخة بيانات اختبار، ولا تتصل حالياً بمزوّد مباشر.","dev":"تفاصيل التطوير","dev_copy":"محولات تطوير صريحة واستشهادات خيالية متوافقة مع v1؛ لا اتصال حي ولا انتقال صامت.","provider":"المزوّد غير متاح.","reset":"إعادة ضبط الجلسة","reset_confirm":"إنشاء جلسة جديدة ومسح الذاكرة؟","confirm":"تأكيد إعادة الضبط","cancel":"إلغاء","route":"مسار التحقيق","mode":"وضع البحث","question":"سؤالك عن القضية","ask_example":"كيف استمر المخطط رغم التحذيرات؟","timeline_filter":"مرشح اختياري للخط الزمني","timeline_example":"المسار التنظيمي أو سنة 2009","claim":"الادعاء","claim_placeholder":"اختر ادعاءً","judgment_question":"سؤال مركز عن الحكم (اختياري)","judgment_example":"لماذا أُدين برنارد ميدوف، وما الأدلة التي دعمت الحكم؟","judgment_help":"سيُستخدم سؤال افتراضي عند تركه فارغًا.","event":"حدث القضية","event_placeholder":"اختر حدثًا","change":"التغيير المسموح","change_placeholder":"اختر تغييرًا","run":"حلّل القضية","already":"هناك طلب قيد التنفيذ.","running":"يجري إعداد ملف القضية…","duplicate":"تم منع إرسال مكرر.","complete":"مكتمل","unavailable":"توقف المسار بأمان.","brief":"ملف النتائج","source_count":"مصدر/مصادر","answer":"الإجابة الموجزة","confidence":"الثقة","findings":"النتائج","sources":"الأدلة والمصادر","limits":"القيود","trace":"تتبّع الوكلاء","verified":"واقعة موثقة","allegation":"ادعاء","interpretation":"تفسير أو عنصر متنازع عليه","insufficient":"أدلة غير كافية","evidence_missing":"لا تتوفر أدلة كافية لإثبات الادعاء.","legal":"الشرح القانوني (Legal explanation)","timeline":"الخط الزمني","hypothetical":"نتيجة افتراضية","assumption":"الافتراض المتغير","sources_intro":"نوع المصدر والادعاء وحالة الإتاحة دون اختلاق روابط.","demo_citation":"استشهاد تجريبي","demo_unavailable":"مصدر اختبار · لا رابط عام","source_available":"مصدر متاح","tier":"الفئة","open":"فتح المصدر","history":"سجل الجلسة الآمن","trace_note":"مراحل عامة وأسماء وكلاء ودية فقط؛ لا مطالبات أو تفكير خفي.","phase":"المرحلة","status":"الحالة","agent":"الوكيل","summary":"ملخص آمن","source_col":"المصادر"},
"en":{"demo":"Demo data","kicker":"Analytical archive · closed criminal case","hero":"An intelligent case file connecting events, evidence, and the verdict to their sources.","selected":"Selected case file","jurisdiction":"Jurisdiction","reason":"This closed case demonstrates how facts and claims trace to distinct sources.","closed":"Closed case","education":"Educational research","disclaimer":"Educational research only — not legal advice.","start":"Open case file","active":"Active case file","language":"English","demo_message":"Demo mode — this build uses test data and is not currently connected to a live provider.","dev":"Development details","dev_copy":"Explicit development adapters and fictional v1 citations; no live call or silent fallback.","provider":"Provider unavailable.","reset":"Reset session","reset_confirm":"Create a new session and clear short-term memory?","confirm":"Confirm reset","cancel":"Cancel","route":"Investigation route","mode":"Research mode","question":"Your case question","ask_example":"How did the scheme continue despite warnings?","timeline_filter":"Optional timeline filter","timeline_example":"Regulatory track or year 2009","claim":"Claim","claim_placeholder":"Select a claim","judgment_question":"Focused verdict question (optional)","judgment_example":"Why was Bernard Madoff convicted, and what evidence supported the verdict?","judgment_help":"Leave blank to use the default verdict question.","event":"Case event","event_placeholder":"Select an event","change":"Allowed change","change_placeholder":"Select a change","run":"Analyze case","already":"A request is already running.","running":"Preparing the case brief…","duplicate":"Duplicate submission prevented.","complete":"Complete","unavailable":"The workflow stopped safely.","brief":"Case Brief","source_count":"cited source(s)","answer":"Concise answer","confidence":"Confidence","findings":"Findings","sources":"Evidence & Sources","limits":"Limitations","trace":"Agent Trace","verified":"Verified fact","allegation":"Allegation","interpretation":"Interpretation or disputed item","insufficient":"Insufficient evidence","evidence_missing":"Evidence is insufficient to establish the claim.","legal":"Legal explanation","timeline":"Timeline","hypothetical":"Hypothetical result","assumption":"Changed assumption","sources_intro":"Source type, relevant claim, and availability without invented links.","demo_citation":"Demo citation","demo_unavailable":"Test source · no public link","source_available":"Source available","tier":"Tier","open":"Open source","history":"Safe session history","trace_note":"Public stages and friendly agent names only—not prompts or hidden reasoning.","phase":"Phase","status":"Status","agent":"Agent","summary":"Safe summary","source_col":"Sources"}}
