"""MaestrosAI-inspired Streamlit chrome (CSS + header markup)."""

from __future__ import annotations

import streamlit as st

# Teal / sky / cream aligned with maestrosai.in enterprise landing aesthetic
MAESTROS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Inter:wght@400;500;600;700&display=swap');

.stApp, .stApp header, .main .block-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
  background: linear-gradient(125deg, #dbeafe 0%, #f0f9ff 38%, #fffbeb 100%) fixed;
}

[data-testid="stAppViewContainer"] > .main {
  background: transparent;
}

/* Hero/topbar: same horizontal bounds as tabs below (sidebar open or collapsed). */
section.main .block-container [data-testid="stMarkdownContainer"] {
  width: 100%;
}

section.main .block-container [data-testid="stMarkdownContainer"] > div {
  width: 100%;
}

section.main .block-container [data-testid="stMarkdownContainer"] .maestros-wrap {
  width: 100%;
  max-width: 100%;
  margin-left: 0;
  margin-right: 0;
  text-align: left;
}

[data-testid="stHeader"] {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.95) 100%);
  border-right: 1px solid rgba(15, 23, 42, 0.08);
}

section[data-testid="stSidebar"] .block-container {
  padding-top: 1.5rem;
}

.maestros-wrap {
  /* Left-align with Workstreams/tabs: do not use margin:auto + max-width (misaligns when sidebar collapses). */
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0 0 1.5rem 0;
  padding: 0;
}

.maestros-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.maestros-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.maestros-logo-mark {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(145deg, #0d9488 0%, #0f766e 100%);
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35);
}

.maestros-logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.maestros-logo-name {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.12em;
  color: #0f172a;
}

.maestros-logo-tag {
  font-size: 0.68rem;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.maestros-cta {
  display: inline-flex;
  align-items: center;
}

.maestros-hero {
  margin-bottom: 1.5rem;
}

.maestros-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: linear-gradient(90deg, #7c3aed 0%, #db2777 100%);
  color: #fff;
  margin-bottom: 0.85rem;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.25);
}

.maestros-h1 {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(1.75rem, 4vw, 2.35rem);
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
  margin: 0 0 0.65rem 0;
  letter-spacing: -0.02em;
}

.maestros-lead {
  font-size: 1.05rem;
  line-height: 1.65;
  color: #475569;
  max-width: 52ch;
  margin: 0;
}

.maestros-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(15, 23, 42, 0.12), transparent);
  margin: 1.75rem 0;
}

.maestros-footnote {
  font-size: 0.88rem;
  color: #64748b;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

/* Main content typography */
.main h1, .main h2, .main h3 {
  font-family: 'Inter', sans-serif !important;
  color: #0f172a !important;
}

.main h2 {
  font-weight: 600 !important;
  font-size: 1.15rem !important;
}

/* Primary actions: pill + teal */
div.stButton > button:first-child,
.stDownloadButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 999px !important;
  border: none !important;
  padding: 0.45rem 1.35rem !important;
  background: linear-gradient(180deg, #14b8a6 0%, #0d9488 100%) !important;
  color: #fff !important;
  box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

div.stButton > button:first-child:hover,
.stDownloadButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(13, 148, 136, 0.42) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.5);
  padding: 0.35rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.stTabs [data-baseweb="tab"] {
  border-radius: 999px !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
  padding: 0.4rem 0.95rem !important;
}

.stTabs [aria-selected="true"] {
  background: rgba(13, 148, 136, 0.15) !important;
  color: #0f766e !important;
}

/* Dataframes & expanders */
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.65);
  border-radius: 12px !important;
  border: 1px solid rgba(15, 23, 42, 0.08) !important;
}

/* Alerts */
.stAlert {
  border-radius: 12px !important;
}
"""


def inject_maestros_styles() -> None:
    st.markdown(f"<style>{MAESTROS_CSS}</style>", unsafe_allow_html=True)


def render_maestros_shell() -> None:
    """Top bar + hero (HTML)."""
    st.markdown(
        """
<div class="maestros-wrap">
  <div class="maestros-topbar">
    <div class="maestros-logo">
      <div class="maestros-logo-mark">AI</div>
      <div class="maestros-logo-text">
        <span class="maestros-logo-name">MAESTROSAI</span>
        <span class="maestros-logo-tag">Insurance AI systems</span>
      </div>
    </div>
    <div class="maestros-cta">
      <a href="https://maestrosai.in" target="_blank" rel="noopener noreferrer"
         style="display:inline-flex;align-items:center;gap:0.4rem;font-size:0.88rem;font-weight:600;
         color:#0f766e;text-decoration:none;padding:0.45rem 1.1rem;border-radius:999px;
         background:rgba(255,255,255,0.85);border:1px solid rgba(13,148,136,0.35);
         box-shadow:0 2px 8px rgba(13,148,136,0.12);">
        maestrosai.in →
      </a>
    </div>
  </div>
  <div class="maestros-hero">
    <div class="maestros-badge">Actuarial suite · Powered by aiactuaries.org</div>
    <h1 class="maestros-h1">AI systems actuaries can trust.</h1>
    <p class="maestros-lead">
      Practitioner decision-support for reserving, pricing, validation, pensions, IFRS narrative, and research—
      with explainable tooling and governance-minded defaults.
    </p>
  </div>
  <div class="maestros-divider"></div>
  <div class="maestros-footnote">
    <span style="flex-shrink:0;">⚖️</span>
    <span>Outputs are drafts for qualified review—not filings or sign-offs. Do not upload PHI or confidential data.</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
