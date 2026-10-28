import io
import json
import sys
from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import comparison as cmp
from document_reader import DocumentData, DocumentError, extract_document
from report_generator import build_report


def make_pdf(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


def blank_pdf():
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


A = DocumentData("a.pdf", ["The course fee is $400. Classes start on 3 March 2025."])
B = DocumentData("b.pdf", ["The course fee is $450. Classes start on 14 April 2025."])

GOOD = {
    "document_a": {"summary": "Fee $400.", "main_points": ["fee"]},
    "document_b": {"summary": "Fee $450.", "main_points": ["fee"]},
    "similarities": [],
    "differences": [{"topic": "Fee", "type": "changed", "document_a": "$400", "document_b": "$450",
                     "evidence_a": "The course fee is $400 (p. 1)", "evidence_b": "The course fee is $999",
                     "significance": "Cost rises."}],
    "key_details": [{"category": "amount", "item": "Fee", "document_a": "$400", "document_b": "$450", "status": "different"}],
    "conclusion": "The fee increased.",
    "limitations": [],
}


# ---- document_reader
def test_rejects_wrong_type():
    with pytest.raises(DocumentError, match="not a PDF"):
        extract_document("notes.txt", b"hello")


def test_rejects_empty():
    with pytest.raises(DocumentError, match="empty"):
        extract_document("a.pdf", b"")


def test_rejects_fake_pdf():
    with pytest.raises(DocumentError, match="valid PDF"):
        extract_document("a.pdf", b"just text pretending")


def test_rejects_corrupt_pdf():
    with pytest.raises(DocumentError):
        extract_document("a.pdf", b"%PDF-1.4 garbage garbage")


def test_scanned_pdf_has_no_text():
    with pytest.raises(DocumentError, match="No readable text"):
        extract_document("scan.pdf", blank_pdf())


def test_extracts_text_and_pages():
    doc = extract_document("a.pdf", make_pdf(["Hello world this is a test document."]))
    assert doc.page_count == 1 and "Hello world" in doc.text and "[Page 1]" in doc.text


# ---- comparison
def test_parse_json_with_fences():
    assert cmp.parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_malformed():
    with pytest.raises(cmp.MalformedResponseError):
        cmp.parse_json("not json at all")


def test_validate_requires_summary():
    with pytest.raises(cmp.MalformedResponseError):
        cmp.validate_result({"document_a": {}, "document_b": {}})


def test_full_compare_and_evidence_check():
    res = cmp.compare_documents(A, B, call_fn=lambda s, p: json.dumps(GOOD))
    d = res["differences"][0]
    assert d["evidence_a_verified"] is True      # real excerpt
    assert d["evidence_b_verified"] is False     # invented excerpt flagged
    assert any("could not be found" in x for x in res["limitations"])


def test_repair_retry_on_malformed_json():
    replies = iter(["oops", json.dumps(GOOD)])
    res = cmp.compare_documents(A, B, call_fn=lambda s, p: next(replies))
    assert res["conclusion"] == "The fee increased."


def test_gives_up_after_two_bad_replies():
    with pytest.raises(cmp.MalformedResponseError):
        cmp.compare_documents(A, B, call_fn=lambda s, p: "nope")


def test_api_failure_becomes_friendly_error():
    def boom(s, p):
        raise RuntimeError("kaboom")
    with pytest.raises(cmp.ComparisonError, match="AI request failed"):
        cmp.compare_documents(A, B, call_fn=boom, sleep=lambda x: None)


def test_transient_error_is_retried():
    calls = {"n": 0}

    class Flaky(Exception):
        code = 503

    def flaky(s, p):
        calls["n"] += 1
        if calls["n"] < 3:
            raise Flaky("busy")
        return json.dumps(GOOD)

    cmp.compare_documents(A, B, call_fn=flaky, sleep=lambda x: None)
    assert calls["n"] == 3


def test_too_long(monkeypatch):
    monkeypatch.setenv("MAX_TOTAL_CHARS", "10")
    with pytest.raises(cmp.DocumentTooLongError):
        cmp.compare_documents(A, B, call_fn=lambda s, p: "{}")


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(cmp.ComparisonError, match="API key"):
        cmp.compare_documents(A, B)


def test_unreadable_pages_added_to_limitations():
    partial = DocumentData("p.pdf", ["Some text here for the doc.", ""], unreadable_pages=[2])
    res = cmp.compare_documents(partial, B, call_fn=lambda s, p: json.dumps(GOOD))
    assert any("page(s) 2" in x for x in res["limitations"])


# ---- report
def test_report_contains_all_sections():
    res = cmp.compare_documents(A, B, call_fn=lambda s, p: json.dumps(GOOD))
    data = build_report(res, A, B)
    text = "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    for heading in ("Document A", "Document B", "Similarities", "Differences",
                    "Key Details Comparison", "Overall Conclusion", "Limitations"):
        assert heading in text
