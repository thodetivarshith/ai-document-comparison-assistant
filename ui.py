"""Presentation layer: futuristic dark/neon theme with pure-CSS animation.

Streamlit strips <script>, so every effect (typing text, count-up numbers, gauge rings,
scan loader, staggered card entrances) is done with CSS @keyframes and @property.
All model/document text is passed through html.escape before being placed in HTML.
Animations are disabled automatically for users who prefer reduced motion.
"""
from __future__ import annotations

import html

import streamlit as st

from comparison import evidence_badge

TYPE_COLORS = {"added": "#34D399", "removed": "#FB7185", "changed": "#FBBF24", "conflicting": "#A78BFA"}
STATUS_LABELS = {"same": "Same", "different": "Different", "only_in_a": "Only in A",
                 "only_in_b": "Only in B", "not_found": "Not found"}
STATUS_TINTS = {"same": "rgba(52,211,153,.30)", "different": "rgba(251,191,36,.30)",
                "only_in_a": "rgba(34,211,238,.30)", "only_in_b": "rgba(244,114,182,.30)",
                "not_found": "rgba(148,163,184,.20)"}
METRIC_COLORS = ["#FBBF24", "#22D3EE", "#34D399", "#A78BFA"]

CSS = """
@property --ang{syntax:'<angle>';inherits:false;initial-value:0deg}
@property --n{syntax:'<integer>';inherits:false;initial-value:0}
@property --p{syntax:'<number>';inherits:false;initial-value:0}

@keyframes aurora{0%{transform:translate3d(-3%,-2%,0) scale(1)}100%{transform:translate3d(3%,2%,0) scale(1.12)}}
@keyframes gridmove{to{background-position:0 44px,44px 0}}
@keyframes spin{to{--ang:360deg}}
@keyframes shine{to{background-position:300% 0}}
@keyframes floaty{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-22px) scale(1.1)}}
@keyframes type{to{width:50ch}}
@keyframes caret{50%{border-color:transparent}}
@keyframes rise{from{opacity:0;transform:translateY(18px) scale(.98)}to{opacity:1;transform:none}}
@keyframes fadein{from{opacity:0}to{opacity:1}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(34,211,238,.55)}70%{box-shadow:0 0 0 12px rgba(34,211,238,0)}100%{box-shadow:0 0 0 0 rgba(34,211,238,0)}}
@keyframes blink{50%{opacity:.25}}
@keyframes sweep{to{left:120%}}
@keyframes count{from{--n:0}}
@keyframes fill{from{--p:0}}
@keyframes btnflow{to{background-position:200% 0}}
@keyframes dropglow{0%,100%{box-shadow:0 0 0 rgba(34,211,238,0)}50%{box-shadow:0 0 22px rgba(34,211,238,.25)}}
@keyframes orbit{to{transform:rotate(360deg)}}
@keyframes barmove{0%{transform:translateX(-100%)}100%{transform:translateX(250%)}}
@keyframes cyc{0%{opacity:0;transform:translateY(8px)}4%,22%{opacity:1;transform:none}27%,100%{opacity:0}}

.stApp{background:#050816}
.stApp::before{content:"";position:fixed;inset:-20%;z-index:0;pointer-events:none;
 background:radial-gradient(40% 40% at 18% 18%,rgba(34,211,238,.17),transparent 62%),
 radial-gradient(36% 36% at 82% 8%,rgba(139,92,246,.20),transparent 62%),
 radial-gradient(40% 40% at 72% 92%,rgba(244,114,182,.13),transparent 62%);animation:aurora 20s ease-in-out infinite alternate}
.stApp::after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
 background-image:linear-gradient(rgba(148,163,184,.075) 1px,transparent 1px),linear-gradient(90deg,rgba(148,163,184,.075) 1px,transparent 1px);
 background-size:44px 44px;-webkit-mask-image:radial-gradient(ellipse at 50% 25%,#000 15%,transparent 75%);mask-image:radial-gradient(ellipse at 50% 25%,#000 15%,transparent 75%);animation:gridmove 12s linear infinite}
[data-testid="stAppViewContainer"],[data-testid="stHeader"]{position:relative;z-index:1}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1150px;padding-top:1.6rem}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:rgba(34,211,238,.35);border-radius:9px}
::-webkit-scrollbar-track{background:transparent}

[data-testid="stSidebar"]{background:rgba(8,13,32,.82);backdrop-filter:blur(14px);border-right:1px solid rgba(34,211,238,.15)}
[data-testid="stAlert"]{border-radius:14px;backdrop-filter:blur(8px)}
[data-testid="stExpander"]{border:1px solid rgba(148,163,184,.2);border-radius:14px;background:rgba(15,23,42,.45)}
span[data-baseweb="tag"]{background:rgba(34,211,238,.16)!important;color:#A5F3FC!important;border:1px solid rgba(34,211,238,.4)}
.stTextInput input{border-radius:12px;background:rgba(15,23,42,.6)}

.stButton>button,.stDownloadButton>button{border-radius:12px;border:1px solid rgba(148,163,184,.3);background:rgba(15,23,42,.6);color:#E2E8F0;transition:all .25s ease;backdrop-filter:blur(6px)}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#22D3EE;color:#fff;box-shadow:0 0 20px rgba(34,211,238,.38);transform:translateY(-2px)}
.stButton>button:active,.stDownloadButton>button:active{transform:translateY(0) scale(.98)}
button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:linear-gradient(90deg,#06B6D4,#7C3AED,#06B6D4)!important;background-size:200% 100%!important;border:none!important;color:#fff!important;box-shadow:0 0 24px rgba(124,58,237,.5);animation:btnflow 5s linear infinite}
button[kind="primary"] p,button[data-testid="stBaseButton-primary"] p{color:#fff!important;font-weight:600}

button[data-baseweb="tab"]{font-weight:600;color:#94A3B8;transition:color .25s}
button[data-baseweb="tab"]:hover{color:#E2E8F0}
button[data-baseweb="tab"][aria-selected="true"]{color:#67E8F9}
div[data-baseweb="tab-highlight"]{background:linear-gradient(90deg,#22D3EE,#8B5CF6)!important;height:3px!important;box-shadow:0 0 14px #22D3EE}
[data-testid="stTabs"]{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}

[data-testid="stFileUploaderDropzone"]{border:1.5px dashed rgba(34,211,238,.55);background:rgba(34,211,238,.05);border-radius:18px;transition:all .3s;animation:dropglow 3.2s ease-in-out infinite}
[data-testid="stFileUploaderDropzone"]:hover{background:rgba(34,211,238,.12);border-color:#22D3EE}

.hero{position:relative;overflow:hidden;border-radius:24px;padding:30px 36px 28px;margin-bottom:18px;border:1.5px solid transparent;
 background:linear-gradient(rgba(8,13,34,.88),rgba(8,13,34,.88)) padding-box,conic-gradient(from var(--ang),#22D3EE,#8B5CF6,#F472B6,#22D3EE) border-box;animation:spin 7s linear infinite,rise .8s ease both}
.hero>*:not(.orb){position:relative;z-index:1}
.orb{position:absolute;border-radius:50%;filter:blur(46px);opacity:.5;animation:floaty 9s ease-in-out infinite}
.o1{width:220px;height:220px;background:#22D3EE;top:-80px;right:6%}
.o2{width:180px;height:180px;background:#8B5CF6;bottom:-90px;right:28%;animation-delay:-3s}
.o3{width:150px;height:150px;background:#F472B6;top:20px;left:-60px;animation-delay:-6s}
.hud-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.hud{display:inline-flex;align-items:center;gap:7px;font:600 .68rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#67E8F9;border:1px solid rgba(34,211,238,.4);background:rgba(34,211,238,.08);border-radius:999px;padding:6px 12px}
.hud .dot{width:7px;height:7px;border-radius:50%;background:#34D399;box-shadow:0 0 10px #34D399;animation:blink 1.4s infinite}
.hero h1{font-size:2.4rem!important;font-weight:800!important;margin:0 0 8px!important;padding:0!important;letter-spacing:-.01em;
 background:linear-gradient(90deg,#fff,#67E8F9,#C4B5FD,#F9A8D4,#fff);background-size:300% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shine 7s linear infinite}
.typed{display:block;width:0;max-width:100%;overflow:hidden;white-space:nowrap;border-right:2px solid #22D3EE;font:500 1.05rem/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;color:#67E8F9;animation:type 2.6s steps(50) .5s forwards,caret .8s step-end infinite}
.hero p{margin:10px 0 0;color:#B8C4E6;font-size:.98rem;line-height:1.55;animation:fadein 1.2s ease 3s both}

.stepper{display:flex;gap:12px;margin:0 0 18px;animation:rise .7s ease both}
.step{flex:1;display:flex;align-items:center;gap:11px;padding:11px 15px;border-radius:14px;border:1px solid rgba(148,163,184,.2);background:rgba(15,23,42,.5);opacity:.5;font-size:.9rem;transition:all .3s}
.step .n{width:28px;height:28px;border-radius:50%;background:rgba(148,163,184,.22);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.82rem;flex:none}
.step.active{opacity:1;border-color:#22D3EE;background:rgba(34,211,238,.09);animation:pulse 2.2s infinite}
.step.active .n{background:#22D3EE;color:#04111F}
.step.done{opacity:1;border-color:rgba(52,211,153,.55);background:rgba(52,211,153,.08)}
.step.done .n{background:#34D399;color:#04111F}

.slot-label{font:600 .72rem/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#67E8F9;margin-bottom:8px}
.filechip{position:relative;overflow:hidden;display:flex;align-items:center;gap:13px;margin:10px 0 16px;padding:12px 16px;border-radius:14px;border:1px solid rgba(52,211,153,.5);background:rgba(52,211,153,.07);animation:rise .6s ease both}
.filechip::after{content:"";position:absolute;top:0;bottom:0;left:-90px;width:70px;background:linear-gradient(90deg,transparent,rgba(103,232,249,.45),transparent);animation:sweep 1.5s ease-out .3s 1 both}
.filechip .ic{font-size:1.6rem}
.filechip .fn{font-weight:600;font-size:.93rem;word-break:break-all}
.filechip .meta{font-size:.78rem;color:#9FB0D6}

.scan{display:flex;align-items:center;gap:26px;margin:14px 0;padding:22px 28px;border-radius:20px;border:1px solid rgba(34,211,238,.35);background:rgba(8,13,34,.7);backdrop-filter:blur(10px);animation:rise .5s ease both}
.orbit{position:relative;width:78px;height:78px;flex:none;border-radius:50%;border:1.5px solid rgba(34,211,238,.25);animation:orbit 3s linear infinite}
.orbit span{position:absolute;width:12px;height:12px;border-radius:50%;background:#22D3EE;box-shadow:0 0 14px #22D3EE;top:-6px;left:33px}
.orbit span:nth-child(2){background:#A78BFA;box-shadow:0 0 14px #A78BFA;top:auto;bottom:-6px}
.orbit span:nth-child(3){background:#F472B6;box-shadow:0 0 14px #F472B6;top:33px;left:-6px}
.orbit .core{position:absolute;inset:24px;border-radius:50%;background:radial-gradient(circle,#67E8F9,#7C3AED);animation:blink 1.2s infinite}
.scan-text{flex:1;min-width:0}
.scan-text .st{font:700 .74rem/1 ui-monospace,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;color:#67E8F9;margin-bottom:10px}
.cycle{position:relative;height:1.5em;font-size:1.02rem;color:#E6ECFF}
.cycle span{position:absolute;left:0;opacity:0;animation:cyc 10s infinite}
.cycle span:nth-child(2){animation-delay:2.5s}.cycle span:nth-child(3){animation-delay:5s}.cycle span:nth-child(4){animation-delay:7.5s}
.bar{height:5px;border-radius:5px;background:rgba(148,163,184,.18);overflow:hidden;margin-top:12px}
.bar i{display:block;height:100%;width:40%;border-radius:5px;background:linear-gradient(90deg,#22D3EE,#8B5CF6,#F472B6);animation:barmove 1.5s ease-in-out infinite}

.metric{position:relative;min-height:122px;display:flex;align-items:center;justify-content:space-between;gap:10px;height:100%;padding:16px 18px;border-radius:16px;border:1px solid rgba(148,163,184,.2);background:rgba(15,23,42,.55);backdrop-filter:blur(8px);transition:all .3s;animation:rise .7s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i,0)*110ms)}
.metric:hover{transform:translateY(-3px);border-color:var(--c);box-shadow:0 0 26px -6px var(--c)}
.metric .l{font:600 .68rem/1 ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#9FB0D6}
.metric .v{font-size:2.1rem;font-weight:800;line-height:1.25;color:var(--c);text-shadow:0 0 18px var(--c)}
.metric .h{font-size:.76rem;color:#8193BE}
.cnt{counter-reset:n var(--n);animation:count 1.6s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i,0)*110ms + 250ms)}
.cnt::before{content:counter(n)}
.cnt.pct::after{content:"%"}
.ring{flex:none;width:62px;height:62px;border-radius:50%;background:conic-gradient(var(--c) calc(var(--p)*1%),rgba(148,163,184,.16) 0);
 -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 7px),#000 calc(100% - 6px));mask:radial-gradient(farthest-side,transparent calc(100% - 7px),#000 calc(100% - 6px));
 filter:drop-shadow(0 0 7px var(--c));animation:fill 1.8s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i,0)*110ms + 250ms)}

.card{position:relative;border-radius:16px;padding:16px 18px;margin-bottom:14px;border:1px solid rgba(148,163,184,.18);border-left:4px solid var(--c,#22D3EE);
 background:rgba(15,23,42,.55);backdrop-filter:blur(8px);transition:transform .3s,box-shadow .3s;animation:rise .65s cubic-bezier(.2,.8,.2,1) both;animation-delay:calc(var(--i,0)*90ms)}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 34px -10px var(--c)}
.card .ct{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:1.02rem}
.chip{display:inline-block;border-radius:999px;padding:2px 11px;font:700 .68rem/1.4 ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:#04111F;background:var(--c,#22D3EE);box-shadow:0 0 14px var(--c)}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.side{border-radius:12px;padding:11px 13px;font-size:.92rem;line-height:1.5}
.side.a{background:rgba(34,211,238,.08);border-left:2px solid #22D3EE}
.side.b{background:rgba(244,114,182,.08);border-left:2px solid #F472B6}
.side .t{font:700 .66rem/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px}
.side.a .t{color:#67E8F9}.side.b .t{color:#F9A8D4}
.quote{font-size:.78rem;color:#9FB0D6;font-style:italic;margin-top:7px}
.ok{color:#34D399;font-style:normal;font-weight:700}
.warn{color:#FBBF24;font-style:normal;font-weight:700}
.why{font-size:.8rem;color:#8193BE;margin-top:10px}

.conclusion,.summary{position:relative;border-radius:18px;padding:20px 24px;line-height:1.65;font-size:1.02rem;animation:rise .6s ease both}
.summary{border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.55)}
.conclusion{border:1.5px solid transparent;background:linear-gradient(rgba(10,16,40,.92),rgba(10,16,40,.92)) padding-box,conic-gradient(from var(--ang),#22D3EE,#8B5CF6,#F472B6,#22D3EE) border-box;animation:spin 8s linear infinite,rise .6s ease both}
.footer{text-align:center;font-size:.76rem;color:#7587B3;margin-top:30px}

@media (max-width:700px){.pair{grid-template-columns:1fr}.stepper{flex-direction:column}.scan{flex-direction:column;text-align:center}.hero h1{font-size:1.7rem!important}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.typed{width:auto;border-right:none}}
"""

LOADER_HTML = (
    '<div class="scan"><div class="orbit"><span></span><span></span><span></span><div class="core"></div></div>'
    '<div class="scan-text"><div class="st">Neural scan in progress</div>'
    '<div class="cycle"><span>Extracting text layers…</span><span>Aligning sections and clauses…</span>'
    '<span>Comparing dates, names and amounts…</span><span>Verifying quotes against the source…</span></div>'
    '<div class="bar"><i></i></div></div></div>'
)


def e(value) -> str:
    return html.escape(str(value or ""))


def md(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def inject_css() -> None:
    md(f"<style>{CSS}</style>")


def hero(model: str = "") -> None:
    model_pill = f'<span class="hud">{e(model)}</span>' if model else ""
    md('<div class="hero"><div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>'
       '<div class="hud-row"><span class="hud"><i class="dot"></i>Engine online</span>'
       f'<span class="hud">Evidence check · on</span>{model_pill}</div>'
       "<h1>AI Document Comparison Assistant</h1>"
       '<span class="typed">Upload two PDFs. Get evidence-checked differences.</span>'
       "<p>Summaries, similarities, differences and key details for policies, syllabi, specs, "
       "product sheets and manuals, grounded in the extracted text and verified against it.</p></div>")


def stepper(current: int) -> None:
    labels = ["Upload documents", "Analyze with AI", "Review and export"]
    parts = []
    for i, label in enumerate(labels, 1):
        cls = "done" if i < current else "active" if i == current else ""
        mark = "✓" if i < current else str(i)
        parts.append(f'<div class="step {cls}"><div class="n">{mark}</div><div>{label}</div></div>')
    md(f'<div class="stepper">{"".join(parts)}</div>')


def show_loader(placeholder) -> None:
    placeholder.markdown(LOADER_HTML, unsafe_allow_html=True)


def slot_label(text: str) -> None:
    md(f'<div class="slot-label">{e(text)}</div>')


def file_chip(doc) -> None:
    warn = ""
    if doc.unreadable_pages:
        warn = f" · ⚠ no text on page(s) {', '.join(map(str, doc.unreadable_pages))}"
    md(f'<div class="filechip"><div class="ic">📄</div><div><div class="fn">{e(doc.name)}</div>'
       f'<div class="meta">{doc.page_count} page(s) · {doc.char_count:,} characters extracted{e(warn)}</div></div></div>')


def compute_metrics(result: dict) -> list[tuple[str, str, str]]:
    kd = [k for k in result["key_details"] if k["status"] != "not_found"]
    same = sum(1 for k in kd if k["status"] == "same")
    match = f"{round(100 * same / len(kd))}%" if kd else "—"
    quotes = [v for s in ("similarities", "differences") for it in result[s]
              for v in (it.get("evidence_a_verified"), it.get("evidence_b_verified")) if v is not None]
    verified = f"{round(100 * sum(quotes) / len(quotes))}%" if quotes else "—"
    return [
        ("Differences", str(len(result["differences"])), "changed, added or removed"),
        ("Similarities", str(len(result["similarities"])), "points in both documents"),
        ("Detail match", match, f"{same} of {len(kd)} compared" if kd else "none compared"),
        ("Quotes verified", verified, f"{len(quotes)} excerpt(s) checked"),
    ]


def metric_html(label: str, value: str, hint: str, color: str, index: int = 0) -> str:
    """One metric card. Numbers count up and percentages also get an animated gauge ring."""
    number = value.rstrip("%")
    is_pct = value.endswith("%")
    if number.isdigit():
        n = int(number)
        value_html = (f'<div class="v cnt{" pct" if is_pct else ""}" style="--n:{n}" '
                      f'role="text" aria-label="{e(value)}"></div>')
        ring = f'<div class="ring" style="--p:{min(n, 100)}" aria-hidden="true"></div>' if is_pct else ""
    else:
        value_html, ring = f'<div class="v">{e(value)}</div>', ""
    return (f'<div class="metric" style="--c:{color};--i:{index}"><div><div class="l">{e(label)}</div>'
            f'{value_html}<div class="h">{e(hint)}</div></div>{ring}</div>')


def metric_row(items: list[tuple[str, str, str]]) -> None:
    for i, (col, (label, value, hint)) in enumerate(zip(st.columns(len(items)), items)):
        with col:
            md(metric_html(label, value, hint, METRIC_COLORS[i % len(METRIC_COLORS)], i))


def _quote(text: str, verified) -> str:
    if not text:
        return ""
    badge = evidence_badge(verified)
    cls = "ok" if verified else "warn"
    tag = f' <span class="{cls}">{e(badge)}</span>' if badge else ""
    return f'<div class="quote">“{e(text)}”{tag}</div>'


def _pair(a_text: str, b_text: str, a_quote: str, b_quote: str) -> str:
    return ('<div class="pair">'
            f'<div class="side a"><div class="t">Document A</div>{e(a_text)}{a_quote}</div>'
            f'<div class="side b"><div class="t">Document B</div>{e(b_text)}{b_quote}</div></div>')


def diff_card(d: dict, index: int = 0) -> None:
    color = TYPE_COLORS.get(d["type"], "#FBBF24")
    why = f'<div class="why">Why it matters: {e(d["significance"])}</div>' if d["significance"] else ""
    md(f'<div class="card" style="--c:{color};--i:{min(index, 12)}"><div class="ct"><b>{e(d["topic"])}</b>'
       f'<span class="chip">{e(d["type"])}</span></div>'
       + _pair(d["document_a"], d["document_b"],
               _quote(d["evidence_a"], d.get("evidence_a_verified")),
               _quote(d["evidence_b"], d.get("evidence_b_verified")))
       + why + "</div>")


def similarity_card(s: dict, index: int = 0) -> None:
    md(f'<div class="card" style="--c:#818CF8;--i:{min(index, 12)}"><div class="ct"><b>{e(s["topic"])}</b></div>'
       f'<div style="margin-top:6px">{e(s["detail"])}</div>'
       + _pair("Appears in A", "Appears in B",
               _quote(s["evidence_a"], s.get("evidence_a_verified")),
               _quote(s["evidence_b"], s.get("evidence_b_verified")))
       + "</div>")


def text_block(css_class: str, text: str) -> None:
    md(f'<div class="{css_class}">{e(text)}</div>')


def footer() -> None:
    md('<div class="footer">Informational comparison generated by an AI model from the extracted text. '
       "Not legal advice; does not certify that any document is compliant, safe or equivalent. "
       "Always check important details in the source PDFs.</div>")
