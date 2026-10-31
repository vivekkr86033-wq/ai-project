"""
ui_theme.py — Commercial Enterprise UI/UX Design System for Smart Energy Management OS.

Provides:
1. inject_custom_css(): Futuristic cyber-clean dark glassmorphic styling, responsive
   Google fonts, glowing neon accents, and interactive controls.
2. apply_plotly_theme(fig): High-contrast, dark-mode Plotly chart layout.
3. render_hero_banner(title, subtitle, badges): Premium glassmorphic hero container.
4. render_kpi_card(label, value, subtext, delta_type, icon): Glassmorphic KPI card.
5. render_interactive_energy_topology(...): Live 4-node residential microgrid power flow diagram.
6. render_smart_devices_matrix(appliances, schedule): Connected smart device status cards.
7. render_sidebar_header(): Commercial branding and status in the sidebar.
8. render_sidebar_footer(): User profile, system telemetry, and platform diagnostics.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional, Tuple, Dict, Any


def inject_custom_css():
    """Inject universal modern futuristic dark glassmorphic styling across all Streamlit pages."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── Root & Global Reset ───────────────────────────────── */
    :root {
        --bg-main: #070b14;
        --bg-surface: #0d1527;
        --bg-card: rgba(13, 21, 39, 0.75);
        --border-glass: rgba(255, 255, 255, 0.08);
        --accent-green: #00f59b;
        --accent-cyan: #00e5ff;
        --accent-purple: #8b5cf6;
        --accent-amber: #fbbf24;
        --accent-red: #f43f5e;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
    }

    html, body, [class*="css"], .stMarkdown, p, span, label, div {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, .outfit-font {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.025em;
    }

    code, pre, .mono-font {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Streamlit Background Override */
    .stApp {
        background-color: var(--bg-main);
        background-image: 
            radial-gradient(circle at 15% 15%, rgba(0, 229, 255, 0.04) 0%, transparent 40%),
            radial-gradient(circle at 85% 30%, rgba(0, 245, 155, 0.04) 0%, transparent 45%),
            radial-gradient(circle at 50% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
        background-attachment: fixed;
    }

    /* Container padding */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 4rem;
        max-width: 1400px;
    }

    /* Modern Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 7px;
        height: 7px;
    }
    ::-webkit-scrollbar-track {
        background: #070b14;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }

    /* ── Glassmorphic Hero Banner ──────────────────────────── */
    .hero-container {
        background: linear-gradient(135deg, rgba(0, 245, 155, 0.08) 0%, rgba(0, 229, 255, 0.09) 40%, rgba(139, 92, 246, 0.08) 100%);
        border: 1px solid rgba(0, 229, 255, 0.22);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 45px -15px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(18px);
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -80px;
        right: -80px;
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, rgba(0, 229, 255, 0.2) 0%, rgba(0, 0, 0, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 2.65rem;
        font-weight: 800;
        line-height: 1.15;
        background: linear-gradient(135deg, #00f59b 0%, #00e5ff 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
    }

    .hero-subtitle {
        font-size: 1.08rem;
        color: #94a3b8;
        font-weight: 400;
        line-height: 1.6;
        margin-bottom: 1.25rem;
        max-width: 980px;
    }

    /* ── Client KPI Cards ──────────────────────────────────── */
    .kpi-card {
        background: #0d1527 !important;
        background: rgba(13, 21, 39, 0.88) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 16px;
        padding: 1.35rem 1.25rem;
        text-align: center;
        box-shadow: 0 10px 28px -8px rgba(0, 0, 0, 0.55);
        backdrop-filter: blur(14px);
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    }

    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));
        opacity: 0.7;
        transition: opacity 0.25s ease;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 36px -8px rgba(0, 229, 255, 0.25);
        border-color: rgba(0, 229, 255, 0.4);
    }

    .kpi-card:hover::after {
        opacity: 1;
        height: 4px;
    }

    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }

    .kpi-val {
        font-family: 'Outfit', sans-serif !important;
        font-size: 2.15rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
        margin: 0.35rem 0;
        letter-spacing: -0.02em;
    }

    .kpi-sub {
        font-size: 0.82rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }

    /* ── Feature Cards / Launchpad ─────────────────────────── */
    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 10px 28px -6px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(14px);
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
        height: calc(100% - 1.1rem);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .feature-card:hover {
        border-color: rgba(0, 229, 255, 0.45);
        box-shadow: 0 16px 40px -8px rgba(0, 229, 255, 0.2);
        transform: translateY(-4px);
    }

    .feature-card h4 {
        color: #f1f5f9;
        font-size: 1.18rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .feature-card p {
        color: #94a3b8;
        font-size: 0.9rem;
        line-height: 1.55;
        margin-bottom: 1.1rem;
    }

    .feature-action {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--accent-cyan);
        font-weight: 600;
        font-size: 0.92rem;
        text-decoration: none;
        transition: all 0.2s ease;
        padding: 4px 0;
    }

    .feature-action:hover {
        color: #a5f3fc;
        transform: translateX(4px);
    }

    /* ── Semantic Badges & Pills ───────────────────────────── */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 0.45rem;
        margin-bottom: 0.45rem;
        letter-spacing: 0.3px;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .badge-solar { background: rgba(251, 191, 36, 0.14); color: #fbbf24; border-color: rgba(251, 191, 36, 0.35); }
    .badge-battery { background: rgba(0, 245, 155, 0.14); color: #00f59b; border-color: rgba(0, 245, 155, 0.35); }
    .badge-peak { background: rgba(244, 63, 94, 0.14); color: #f43f5e; border-color: rgba(244, 63, 94, 0.35); }
    .badge-agent { background: rgba(139, 92, 246, 0.14); color: #c084fc; border-color: rgba(139, 92, 246, 0.35); }
    .badge-ai { background: rgba(0, 229, 255, 0.14); color: #00e5ff; border-color: rgba(0, 229, 255, 0.35); }

    /* ── Interactive Live Energy Topology ──────────────────── */
    .energy-topology {
        background: rgba(13, 21, 39, 0.85);
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 18px;
        padding: 1.6rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(16px);
        box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.55);
    }

    .node-box {
        background: rgba(18, 28, 51, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .node-box:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 229, 255, 0.5);
        box-shadow: 0 12px 28px -6px rgba(0, 229, 255, 0.22);
    }

    .node-icon { font-size: 2.1rem; margin-bottom: 0.35rem; }
    .node-title { font-size: 0.84rem; font-weight: 700; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.6px; }
    .node-metric { font-family: 'Outfit', sans-serif !important; font-size: 1.65rem; font-weight: 800; color: #f8fafc; margin: 0.25rem 0; }
    .node-status { font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px; }

    /* ── Connected Smart Devices Matrix ────────────────────── */
    .device-card {
        background: rgba(18, 28, 51, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        transition: all 0.25s ease;
        margin-bottom: 0.75rem;
    }

    .device-card:hover {
        border-color: rgba(0, 245, 155, 0.4);
        box-shadow: 0 8px 24px -6px rgba(0, 245, 155, 0.18);
        transform: translateY(-2px);
    }

    /* ── Streamlit Tabs Polish ─────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 11px 20px;
        font-weight: 700;
        font-size: 0.92rem;
        color: #94a3b8;
        background: transparent;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9;
        background: rgba(255, 255, 255, 0.04);
    }

    .stTabs [aria-selected="true"] {
        color: var(--accent-cyan) !important;
        background: rgba(0, 229, 255, 0.12) !important;
        border-bottom: 2px solid var(--accent-cyan) !important;
    }

    /* ── Streamlit Buttons & Controls ──────────────────────── */
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
        transition: all 0.22s ease;
        border: 1px solid rgba(255, 255, 255, 0.12);
        letter-spacing: 0.2px;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 25px -4px rgba(0, 229, 255, 0.4);
        border-color: rgba(0, 229, 255, 0.5);
    }

    /* ── Sidebar Custom Polish ─────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #090e1a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0.2rem;
        padding-bottom: 0.8rem;
    }

    [data-testid="stSidebarNav"] ul {
        gap: 6px;
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        padding: 9px 14px !important;
        transition: all 0.22s ease !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        background: transparent !important;
        border: 1px solid transparent !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(0, 229, 255, 0.08) !important;
        color: #00e5ff !important;
        border-color: rgba(0, 229, 255, 0.2) !important;
        transform: translateX(4px);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a.active {
        background: linear-gradient(90deg, rgba(0, 229, 255, 0.16), rgba(0, 245, 155, 0.1)) !important;
        color: #00f59b !important;
        border-left: 3px solid #00f59b !important;
        border-color: rgba(0, 245, 155, 0.3) !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px -3px rgba(0, 245, 155, 0.25) !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.5rem 0 1.2rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 1.2rem;
    }

    .sidebar-logo {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #00f59b 0%, #00e5ff 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        font-weight: 900;
        color: #070b14;
        box-shadow: 0 0 16px rgba(0, 229, 255, 0.5);
    }

    .sidebar-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.2rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .sidebar-subtitle {
        font-size: 0.72rem;
        color: var(--accent-cyan);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }

    .sidebar-profile {
        background: rgba(18, 28, 51, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-top: 1.5rem;
    }

    /* ── Live Pulse Indicator ──────────────────────────────── */
    .status-pulse {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        margin-right: 7px;
        animation: pulse-glow 2s infinite;
    }

    .pulse-green { background: #00f59b; box-shadow: 0 0 12px #00f59b; }
    .pulse-amber { background: #fbbf24; box-shadow: 0 0 12px #fbbf24; }
    .pulse-cyan { background: #00e5ff; box-shadow: 0 0 12px #00e5ff; }

    @keyframes pulse-glow {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 245, 155, 0.7); }
        70% { transform: scale(1.15); box-shadow: 0 0 0 8px rgba(0, 245, 155, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 245, 155, 0); }
    }
</style>
""", unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure, height: int = 400, title: str = "", show_legend: bool = True) -> go.Figure:
    """Standardize Plotly figures with a futuristic, client-grade dark glassmorphic layout."""
    fig.update_layout(
        height=height,
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Outfit, sans-serif", size=16, color="#f1f5f9"),
            x=0.01,
            y=0.97,
        ) if title else None,
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
        margin=dict(l=40, r=40, t=40 if title else 25, b=35),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color="#cbd5e1"),
            bgcolor="rgba(13, 21, 39, 0.75)",
            bordercolor="rgba(255, 255, 255, 0.08)",
            borderwidth=1,
        ) if show_legend else dict(visible=False),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            linecolor="rgba(255, 255, 255, 0.12)",
            tickfont=dict(color="#94a3b8", size=11),
            title=dict(font=dict(color="#cbd5e1", size=12)),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            linecolor="rgba(255, 255, 255, 0.12)",
            tickfont=dict(color="#94a3b8", size=11),
            title=dict(font=dict(color="#cbd5e1", size=12)),
            zeroline=False,
        ),
    )
    return fig


def render_hero_banner(title: str, subtitle: str, badges: Optional[List[Tuple[str, str]]] = None):
    """Render a modern futuristic glassmorphic hero banner with glowing badges."""
    badge_html = ""
    if badges:
        for badge_text, badge_type in badges:
            badge_html += f'<span class="badge-pill badge-{badge_type}">{badge_text}</span>'

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
        <div>{badge_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, subtext: str = "", delta_type: str = "positive", icon: str = "⚡"):
    """Render an individual glassmorphic KPI card with trend pill and glowing top line."""
    sub_color = "#00f59b" if delta_type == "positive" else ("#f43f5e" if delta_type == "negative" else "#94a3b8")
    st.markdown(f"""
    <div class="kpi-card" style="background: rgba(13, 21, 39, 0.88); border: 1px solid rgba(255, 255, 255, 0.09); border-radius: 16px; padding: 1.35rem 1.25rem;">
        <div class="kpi-label" style="color: #94a3b8; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.35rem; display: flex; align-items: center; justify-content: center; gap: 6px;">
            <span>{icon}</span> {label}
        </div>
        <div class="kpi-val" style="font-family: 'Outfit', sans-serif; font-size: 2.15rem; font-weight: 800; color: #f8fafc; line-height: 1.1; margin: 0.35rem 0; letter-spacing: -0.02em;">
            {value}
        </div>
        <div class="kpi-sub" style="color: {sub_color}; font-size: 0.82rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 4px;">
            {subtext}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_interactive_energy_topology(
    solar_kw: float,
    baseload_kw: float,
    scheduled_kw: float,
    battery_soc_pct: float,
    battery_power_kw: float,
    grid_kw: float,
    tariff_price: float,
    is_peak: bool,
):
    """
    Render an interactive real-time physical power dispatch topology card.
    Visualizes the live 4-node residential microgrid:
    Solar PV ↔ Battery BESS ↔ Smart Home Loads ↔ Utility Grid.
    """
    total_home_load = baseload_kw + scheduled_kw
    bess_charging = battery_power_kw < 0
    bess_discharging = battery_power_kw > 0
    grid_import = grid_kw > 0.05
    grid_export = grid_kw < -0.05

    tariff_color = "#f43f5e" if is_peak else ("#fbbf24" if tariff_price >= 0.20 else "#00f59b")
    tariff_badge = f'<span class="node-status" style="background: rgba(244,63,94,0.18); color: {tariff_color}; border: 1px solid {tariff_color}40;">${tariff_price:.2f} / kWh {"(PEAK TARIFF)" if is_peak else "(OFF-PEAK)"}</span>'

    st.markdown(f"""
    <div class="energy-topology">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; flex-wrap:wrap; gap:8px;">
            <div style="font-size:1.15rem; font-weight:800; color:#f8fafc; font-family:'Outfit', sans-serif; display:flex; align-items:center; gap:8px;">
                <span class="status-pulse pulse-cyan"></span> Real-Time Microgrid Dispatch Topology
            </div>
            <div>
                {tariff_badge}
            </div>
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;">
            <div class="node-box" style="border-top: 3px solid #fbbf24;">
                <div class="node-icon">☀️</div>
                <div class="node-title">Solar PV Array</div>
                <div class="node-metric">{solar_kw:.2f} <span style="font-size:0.9rem; color:#94a3b8;">kW</span></div>
                <div class="node-status" style="background: rgba(251, 191, 36, 0.18); color:#fbbf24;">
                    {'Generating' if solar_kw > 0.1 else 'Standby Mode'}
                </div>
            </div>
            <div class="node-box" style="border-top: 3px solid #00e5ff;">
                <div class="node-icon">🔋</div>
                <div class="node-title">10 kWh BESS</div>
                <div class="node-metric">{battery_soc_pct:.0f}% <span style="font-size:0.85rem; color:#94a3b8;">SOC</span></div>
                <div class="node-status" style="background: rgba(0, 229, 255, 0.18); color:#00e5ff;">
                    {'⚡ Discharging ' + f'{abs(battery_power_kw):.1f} kW' if bess_discharging else ('🔌 Charging ' + f'{abs(battery_power_kw):.1f} kW' if bess_charging else 'Idle Buffer')}
                </div>
            </div>
            <div class="node-box" style="border-top: 3px solid #00f59b;">
                <div class="node-icon">🏠</div>
                <div class="node-title">Smart Home Load</div>
                <div class="node-metric">{total_home_load:.2f} <span style="font-size:0.9rem; color:#94a3b8;">kW</span></div>
                <div class="node-status" style="background: rgba(0, 245, 155, 0.18); color:#00f59b;">
                    Base {baseload_kw:.1f} kW + Smart {scheduled_kw:.1f} kW
                </div>
            </div>
            <div class="node-box" style="border-top: 3px solid #8b5cf6;">
                <div class="node-icon">🌐</div>
                <div class="node-title">Utility Grid Intertie</div>
                <div class="node-metric">{abs(grid_kw):.2f} <span style="font-size:0.9rem; color:#94a3b8;">kW</span></div>
                <div class="node-status" style="background: rgba(139, 92, 246, 0.18); color:#c084fc;">
                    {'⬇️ Importing from Grid' if grid_import else ('⬆️ Net Metering Export' if grid_export else 'Zero Net Grid')}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_smart_devices_matrix(appliances, schedule):
    """Render a modern connected smart appliances matrix with real-time operational status."""
    st.markdown("### 🔌 Connected Smart Energy Devices (6 Online)")
    st.caption("Active IoT appliance telemetry, scheduled runtime windows, and rated continuous power consumption.")

    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]

    icons = {
        "ev_charger": "🚗",
        "water_heater": "♨️",
        "dishwasher": "🍽️",
        "washing_machine": "🧺",
        "hvac_heatpump": "❄️",
        "refrigerator": "🧊",
    }

    for idx, app in enumerate(appliances):
        col = cols[idx % 3]
        start_hour = schedule.get(app.id, None)
        icon = icons.get(app.id, "⚡")

        if start_hour is not None:
            sched_str = f"{start_hour:02d}:00 – {(start_hour + app.duration_hours) % 24:02d}:00"
            status_chip = f'<span style="background:rgba(0, 245, 155, 0.16); color:#00f59b; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:9999px;">SCHEDULED</span>'
        else:
            sched_str = "Continuous Modulation" if app.category == "critical" else "On Demand"
            status_chip = f'<span style="background:rgba(0, 229, 255, 0.16); color:#00e5ff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:9999px;">ACTIVE</span>'

        with col:
            st.markdown(f"""
            <div class="device-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.4rem;">{icon}</span>
                        <span style="font-weight:700; font-size:0.92rem; color:#f8fafc;">{app.name}</span>
                    </div>
                    {status_chip}
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; margin-top:8px; font-size:0.82rem; color:#94a3b8;">
                    <div>Power: <b style="color:#f8fafc;">{app.power_kw:.1f} kW</b></div>
                    <div>Duration: <b style="color:#f8fafc;">{app.duration_hours}h</b></div>
                    <div>Window: <b style="color:#38bdf8;">{sched_str}</b></div>
                    <div>Priority: <b style="color:#c084fc;">P{app.priority}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_sidebar_header():
    """Render professional AI Smart Energy System branding in the sidebar."""
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">⚡</div>
        <div>
            <div class="sidebar-title">AETHER // ENERGY</div>
            <div class="sidebar-subtitle">Smart Energy Management OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render system status and platform diagnostics at the bottom of the sidebar."""
    st.sidebar.markdown("""
    <div class="sidebar-profile">
        <div style="font-size:0.75rem; font-weight:700; color:#00e5ff; text-transform:uppercase; letter-spacing:0.8px;">SYSTEM ENVIRONMENT</div>
        <div style="font-size:0.86rem; font-weight:700; color:#f8fafc; margin-top:2px;">Residence 04A • Smart Microgrid</div>
        <div style="font-size:0.78rem; color:#94a3b8; margin-top:4px;">
            Core Stack: A* • CSP • Rete • MAS<br>
            Runtime: Cross-Platform (Render/Win)
        </div>
    </div>
    """, unsafe_allow_html=True)
