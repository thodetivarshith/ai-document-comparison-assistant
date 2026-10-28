"""Streamlit UI for the AI Document Comparison Assistant."""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import ui
from comparison import ComparisonError, DEFAULT_MODEL, compare_documents, get_max_chars
from document_reader import DocumentError, extract_document
from report_generator import build_markdown, build_report

load_dotenv()

st.set_page_config(page_title="AI Document Comparison Assistant", page_icon="📄",
                   layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

SAMPLE_DIR = Path(__file__).parent / "sample_documents"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

ss = st.session_state
ss.setdefault("run_id", 0)         # bumping this resets the file uploaders
ss.setdefault("result", None)
ss.setdefault("docs", None)
ss.setdefault("use_samples", False)


def reset() -> None:
    ss.run_id += 1
    ss.result = None
    ss.docs = None
    ss.use_samples = False


def load_samples() -> None:
    ss.result = None
    ss.docs = None
    ss.use_samples = True


@st.cache_data(show_spinner=False)
def cached_extract(name: str, data: bytes):
    return extract_document(name, data)


def read_slot(name: str, data: bytes):
    try:
        return cached_extract(name, data), None
    except DocumentError as exc:
        return None, str(exc)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### Settings")
    if os.getenv("GEMINI_API_KEY"):
        st.success("API key loaded", icon="🔑")
    else:
        st.error("GEMINI_API_KEY missing. Copy `.env.example` to `.env` and add your key.", icon="🔒")
    st.caption(f"Model: `{os.getenv('GEMINI_MODEL', DEFAULT_MODEL)}`  \nInput limit: {get_max_chars():,} characters")
    st.divider()
    st.markdown("### Quick start")
    st.button("Try sample documents", on_click=load_samples, use_container_width=True,
              disabled=not SAMPLE_DIR.exists())
    st.button("Reset everything", on_click=reset, use_container_width=True, key="reset_side")
    st.divider()
    with st.expander("How it works"):
        st.markdown(
            "1. PDFs are validated and text is extracted page by page.\n"
            "2. The text goes to the LLM with strict rules: evidence only, no invention.\n"
            "3. The JSON reply is validated, and every quoted excerpt is checked against the source text.\n"
            "4. Review the tabs and download the report.")
    with st.expander("Limitations"):
        st.markdown("- No OCR: scanned PDFs are rejected.\n- Complex layouts and tables may extract poorly.\n"
                    "- AI output can contain mistakes; use the ✓ / ⚠ evidence flags.")

# --------------------------------------------------------------------- hero
ui.hero(os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
step_slot = st.empty()

# ------------------------------------------------------------------ uploads
if ss.use_samples:
    st.info("Using the built-in sample syllabi. Click **Reset everything** to upload your own files.", icon="🧪")

slots = []
for col, label, key in zip(st.columns(2), ("Document A", "Document B"), ("a", "b")):
    with col:
        if ss.use_samples:
            path = SAMPLE_DIR / f"document_{key}.pdf"
            name, data = path.name, path.read_bytes()
            ui.slot_label(label)
        else:
            f = st.file_uploader(label, type=["pdf"], key=f"{key}_{ss.run_id}")
            name, data = (f.name, f.getvalue()) if f else (None, None)
        doc = err = None
        if data is not None:
            doc, err = read_slot(name, data)
            if err:
                st.error(f"{label}: {err}")
            else:
                ui.file_chip(doc)
        slots.append((label, name, data, doc, err))

ready = all(s[3] is not None for s in slots)

b1, b2, _ = st.columns([1.3, 1, 4])
compare_clicked = b1.button("Compare Documents", type="primary", use_container_width=True)
b2.button("Reset", on_click=reset, use_container_width=True, key="reset_main")

# --------------------------------------------------------------- processing
if compare_clicked:
    ss.result = None
    if any(s[1] is None for s in slots):
        st.warning("Please upload both Document A and Document B.")
    elif not ready:
        st.warning("Fix the file problems above, then compare again.")
    elif slots[0][2] == slots[1][2]:
        st.warning("Both files are identical. Upload two different documents to compare.")
    else:
        doc_a, doc_b = slots[0][3], slots[1][3]
        loader = st.empty()
        ui.show_loader(loader)
        try:
            ss.result = compare_documents(doc_a, doc_b)
            ss.docs = (doc_a, doc_b)
        except ComparisonError as exc:
            loader.empty()
            st.error(str(exc))
            st.caption("Click **Compare Documents** to retry.")
        else:
            loader.empty()
            st.toast("Comparison complete", icon="✅")

with step_slot.container():
    ui.stepper(3 if ss.result else 2 if ready else 1)

# ------------------------------------------------------------------ results
if ss.result and ss.docs:
    result, (doc_a, doc_b) = ss.result, ss.docs
    st.divider()
    ui.metric_row(ui.compute_metrics(result))
    st.write("")

    tabs = st.tabs(["Summary A", "Summary B", "Similarities", "Differences", "Key Details", "Overall Conclusion"])

    for tab, d, key in ((tabs[0], doc_a, "document_a"), (tabs[1], doc_b, "document_b")):
        with tab:
            st.markdown(f"**{d.name}**")
            ui.text_block("summary", result[key]["summary"])
            if result[key]["main_points"]:
                st.markdown("**Main points**")
                for point in result[key]["main_points"]:
                    st.markdown(f"- {point}")
            with st.expander("Preview extracted text"):
                st.write(d.preview(1200))

    with tabs[2]:
        if not result["similarities"]:
            st.info("No similarities were identified.")
        for i, s in enumerate(result["similarities"]):
            ui.similarity_card(s, i)

    with tabs[3]:
        diffs = result["differences"]
        if not diffs:
            st.success("No differences were identified. The documents appear to match on the points checked.")
        else:
            f1, f2 = st.columns([2, 3])
            kinds = f1.multiselect("Show types", ["added", "removed", "changed", "conflicting"],
                                   default=["added", "removed", "changed", "conflicting"])
            query = f2.text_input("Search differences", placeholder="fee, deadline, instructor").strip().lower()
            shown = [d for d in diffs if d["type"] in kinds and
                     (not query or query in " ".join([d["topic"], d["document_a"], d["document_b"],
                                                      d["significance"]]).lower())]
            st.caption(f"Showing {len(shown)} of {len(diffs)} differences")
            for i, d in enumerate(shown):
                ui.diff_card(d, i)

    with tabs[4]:
        kd = result["key_details"]
        if not kd:
            st.info("No key details were identified.")
        else:
            import pandas as pd
            cats = sorted({k["category"] for k in kd})
            picked = st.multiselect("Categories", cats, default=cats)
            df = pd.DataFrame([{"Category": k["category"], "Item": k["item"], "Document A": k["document_a"],
                                "Document B": k["document_b"], "Status": ui.STATUS_LABELS[k["status"]]}
                               for k in kd if k["category"] in picked])
            if not df.empty:
                tint = {ui.STATUS_LABELS[s]: c for s, c in ui.STATUS_TINTS.items()}
                styler = df.style
                apply = getattr(styler, "map", None) or styler.applymap
                st.dataframe(apply(lambda v: f"background-color: {tint.get(v, '')}", subset=["Status"]),
                             use_container_width=True, hide_index=True)

    with tabs[5]:
        ui.text_block("conclusion", result["conclusion"])

    if result["limitations"]:
        with st.expander("Limitations", expanded=True):
            for item in result["limitations"]:
                st.markdown(f"- {item}")

    st.divider()
    st.markdown("#### Export")
    d1, d2, d3, _ = st.columns([1.5, 1, 1, 2])
    d1.download_button("Download Comparison Report", data=build_report(result, doc_a, doc_b),
                       file_name="comparison_report.docx", mime=DOCX_MIME, type="primary",
                       use_container_width=True)
    d2.download_button("Markdown", data=build_markdown(result, doc_a, doc_b),
                       file_name="comparison_report.md", mime="text/markdown", use_container_width=True)
    d3.download_button("JSON", data=json.dumps(result, indent=2, ensure_ascii=False),
                       file_name="comparison_result.json", mime="application/json", use_container_width=True)

ui.footer()
