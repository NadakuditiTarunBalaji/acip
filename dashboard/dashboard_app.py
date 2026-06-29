"""
ACIP-X1 — Streamlit Dashboard
Run with: streamlit run dashboard/app.py
"""
import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text
import requests
import json
import time
import math
import os
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pydeck as pdk
from datetime import datetime, timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)

# Real music playback for the "play a song" voice command (demo-purpose,
# royalty-free files only). Drop .mp3 files into this folder — e.g. from
# mixkit.co/free-stock-music (no signup needed) or pixabay.com/music
# (royalty-free, no attribution required) — and they'll show up
# automatically; nothing else needs to change.
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")
MUSIC_TRACKS = (
    [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav", ".ogg"))]
    if os.path.isdir(MUSIC_DIR) else []
)

# Day 15d — Preset destinations for the navigation demo (Chennai landmarks)
PRESET_DESTINATIONS = {
    "Chennai Central Railway Station": (13.0827, 80.2750),
    "Egmore Railway Station":          (13.0732, 80.2609),
    "Marina Beach":                    (13.0500, 80.2824),
    "T Nagar":                         (13.0418, 80.2341),
    "Anna Nagar Tower":                (13.0850, 80.2101),
}

# Hardcoded, demo-purpose points of interest placed roughly along the
# existing PRESET_DESTINATIONS routes (not from a real live places API —
# explicitly scoped this way for the demo). Each has a type used to pick
# an icon and a realistic-sounding name for the notification banner.
ROUTE_POIS = [
    {"name": "Saravana Bhavan",        "type": "restaurant", "lat": 13.06635, "lon": 80.27655},
    {"name": "Tata Power EV Charging", "type": "charging",   "lat": 13.06635, "lon": 80.27655 + 0.0015},
    {"name": "Adyar Ananda Bhavan",    "type": "restaurant", "lat": 13.05816, "lon": 80.24874},
    {"name": "ChargeZone Station",     "type": "charging",   "lat": 13.08362, "lon": 80.24646},
]


def km_distance(lat1, lon1, lat2, lon2):
    """Flat-earth distance in km — matches the simulator's calculation."""
    dlat_km = (lat2 - lat1) * 111.0
    dlon_km = (lon2 - lon1) * 111.0 * math.cos(math.radians(lat1))
    return math.sqrt(dlat_km ** 2 + dlon_km ** 2)


@st.cache_data(ttl=120, show_spinner=False)
def fetch_road_route(lat1, lon1, lat2, lon2):
    """
    Real road-following route via the free public OSRM demo server
    (router.project-osrm.org, no API key needed). Returns a list of
    [lon, lat] points for the actual road path, or None on any failure
    (no internet, server down, timeout) — callers should fall back to
    a straight line in that case rather than show nothing.
    Cached for 2 minutes since the route between two fixed points
    doesn't change tick to tick, only the vehicle's progress along it.
    """
    try:
        url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        )
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                return data["routes"][0]["geometry"]["coordinates"]
    except Exception:
        pass
    return None



def to_ist(timestamp_str):
    """Convert a UTC timestamp string from the backend (datetime.utcnow())
    into a human-readable IST string for display. Falls back to the raw
    string if parsing fails."""
    if not timestamp_str or timestamp_str == "N/A":
        return "N/A"
    ts = str(timestamp_str)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(ts, fmt)
            ist = dt + IST_OFFSET
            return ist.strftime("%Y-%m-%d %H:%M:%S") + " IST"
        except ValueError:
            continue
    return ts

BASE_URL = "http://localhost:8000"

# ── Theme state ───────────────────────────────────────────
# A real, functioning light/dark toggle. Streamlit's own theme.base
# can't be swapped at runtime from inside the app (confirmed: no
# Theme is locked to dark only — the light/dark toggle was removed per
# user request. _is_dark stays as a constant so the rest of the CSS
# (which all branches on this flag) doesn't need to be rewritten.
_is_dark = True

THEME = {
    "bg_page":        "#050B18" if _is_dark else "#f4f4f5",
    "bg_surface":      "#161b22" if _is_dark else "#ffffff",
    "bg_surface_alt":  "#11161f" if _is_dark else "#fafafa",
    "border":          "#30363d" if _is_dark else "#e4e4e7",
    "text_primary":    "#e6edf3" if _is_dark else "#18181b",
    "text_secondary":  "#8b949e" if _is_dark else "#71717a",
    "sidebar_grad_top": "#0d1117" if _is_dark else "#ffffff",
    "sidebar_grad_bot": "#161b22" if _is_dark else "#f4f4f5",
}


def theme_color(name: str) -> str:
    """Returns the current-theme hex for a named structural color —
    used in Python contexts (Plotly figures, f-strings) where CSS
    variables can't be referenced directly."""
    return THEME[name]


# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="ACIP-X1 | Automotive Cognitive Intelligence Platform",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Main background */
    .stApp {{ background-color: {THEME['bg_page']}; }}

    /* Fix white header bar at top */
    header[data-testid="stHeader"] {{
        background-color: {THEME['bg_page']} !important;
        border-bottom: 1px solid {THEME['border']};
    }}

    /* Fix top toolbar */
    .stToolbar {{ background-color: {THEME['bg_page']} !important; }}

    /* Fix deploy button area */
    [data-testid="stToolbar"] {{
        background-color: {THEME['bg_page']} !important;
    }}

    /* Fix main content padding */
    [data-testid="stAppViewContainer"] {{
        background-color: {THEME['bg_page']} !important;
    }}

    /* Fix block container — extra top padding so our custom top bar
       (ACIP-X1 title/mode/connectivity) isn't hidden underneath
       Streamlit's own fixed-position header bar, which sits above
       normal page content regardless of scroll position. */
    [data-testid="stMainBlockContainer"] {{
        background-color: {THEME['bg_page']} !important;
        padding-top: 3.5rem !important;
    }}

    /* Remove white gap at top */
    .main .block-container {{
        padding-top: 3.5rem !important;
        background-color: {THEME['bg_page']} !important;
    }}

    /* Fix top decoration bar */
    [data-testid="stDecoration"] {{
        background: linear-gradient(90deg, #1f6feb, #58a6ff) !important;
        height: 3px !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {THEME['sidebar_grad_top']} 0%, {THEME['sidebar_grad_bot']} 100%);
        border-right: 1px solid {THEME['border']};
    }}

    /* Cards */
    .glass-card {{
        background: {"rgba(22, 27, 34, 0.55)" if _is_dark else "rgba(255, 255, 255, 0.65)"};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {"rgba(255, 255, 255, 0.08)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
        border-radius: 16px;
        box-shadow: 0 8px 24px {"rgba(0, 0, 0, 0.35)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .glass-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 32px {"rgba(0, 0, 0, 0.45)" if _is_dark else "rgba(0, 0, 0, 0.10)"};
    }}
    div[class*="st-key-nav_glass_card"], div[class*="st-key-status_glass_card"] {{
        background: {"rgba(22, 27, 34, 0.55)" if _is_dark else "rgba(255, 255, 255, 0.65)"};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {"rgba(255, 255, 255, 0.08)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 8px 24px {"rgba(0, 0, 0, 0.35)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
    }}

    /* Force all 9 feature tiles to the same fixed height regardless of
       label length ("Talk to Your Car" wraps to more lines than
       "Emergency" otherwise, making tiles visually uneven heights). */
    div[class*="st-key-tile_"] button {{
        height: 64px !important;
        white-space: pre-line !important;
        line-height: 1.25 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    .metric-card {{
        background: {"rgba(22, 27, 34, 0.55)" if _is_dark else "rgba(255, 255, 255, 0.65)"};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {"rgba(255, 255, 255, 0.08)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin: 5px 0;
        box-shadow: 0 8px 24px {"rgba(0, 0, 0, 0.35)" if _is_dark else "rgba(0, 0, 0, 0.06)"};
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 32px {"rgba(0, 0, 0, 0.45)" if _is_dark else "rgba(0, 0, 0, 0.10)"};
    }}
    .metric-value {{
        font-size: 2.2rem;
        font-weight: 700;
        margin: 5px 0;
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: {THEME['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Status badges */
    .badge-healthy  {{ background:{"#1a4731" if _is_dark else "#dcfce7"}; color:#3fb950; border:1px solid #3fb950; border-radius:20px; padding:3px 12px; font-size:0.8rem; }}
    .badge-warning  {{ background:{"#3d2f0d" if _is_dark else "#fef3c7"}; color:#d29922; border:1px solid #d29922; border-radius:20px; padding:3px 12px; font-size:0.8rem; }}
    .badge-critical {{ background:{"#3d1a1a" if _is_dark else "#fee2e2"}; color:#f85149; border:1px solid #f85149; border-radius:20px; padding:3px 12px; font-size:0.8rem; }}

    /* Mode header */
    .mode-header {{
        background: {"linear-gradient(90deg, #1a2332 0%, #1c2535 100%)" if _is_dark else "linear-gradient(90deg, #eff6ff 0%, #e0e7ff 100%)"};
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 20px;
    }}

    /* Table styling */
    .dataframe {{ font-size: 0.85rem !important; }}

    /* Alert cards */
    .alert-critical {{
        background: {"#3d1a1a" if _is_dark else "#fee2e2"};
        border-left: 4px solid #f85149;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .alert-warning {{
        background: {"#3d2f0d" if _is_dark else "#fef3c7"};
        border-left: 4px solid #d29922;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .alert-info {{
        background: {"#1a2a3a" if _is_dark else "#dbeafe"};
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .alert-soon {{
        background: {"#2a1f3d" if _is_dark else "#ede9fe"};
        border-left: 4px solid #bc8cff;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .alert-monitor {{
        background: {"#1a2a2a" if _is_dark else "#cffafe"};
        border-left: 4px solid #56d4dd;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .breakdown-card {{
        background: {"#2a1a1a" if _is_dark else "#fee2e2"};
        border-left: 4px solid #f85149;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }}
    .chat-bubble-assistant {{
        background: {"#1a2a3a" if _is_dark else "#dbeafe"};
        border-radius: 12px;
        padding: 10px 14px;
        margin: 6px 0;
        max-width: 85%;
    }}
    .chat-bubble-user {{
        background: {"#2d3a4f" if _is_dark else "#e4e4e7"};
        border-radius: 12px;
        padding: 10px 14px;
        margin: 6px 0 6px auto;
        max-width: 85%;
        text-align: right;
    }}

    h1, h2, h3 {{ color: {THEME['text_primary']} !important; }}
    p, div {{ color: {THEME['text_primary'] if not _is_dark else "#c9d1d9"}; }}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────
def api_get(endpoint):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def api_post(endpoint, data):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def api_delete(endpoint):
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def api_patch(endpoint, data=None):
    try:
        r = requests.patch(f"{BASE_URL}{endpoint}", json=data or {}, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def health_color(score):
    if score >= 80: return "#3fb950"
    if score >= 60: return "#d29922"
    if score >= 40: return "#ff7b72"
    return "#f85149"


def live_map_fragment(nav_telemetry=None):
    """
    Renders the navigation/destination panel. Previously auto-refreshed
    on a timer via st.fragment(run_every=...), but that was removed per
    user request — everything on the page now updates only via the
    sidebar's manual "🔄 Refresh Now" button, with no separate timers.

    Accepts already-fetched telemetry from the caller instead of
    re-fetching it — the home view already loads this once, and calling
    the same endpoint three times per page render (here, the bottom
    bar, and the home view's own status panel) was a real, measurable
    contributor to slow page loads.
    """
    if nav_telemetry is None:
        nav_telemetry = api_get("/api/telemetry/latest/VEH001") or {}
    nav_destination = api_get("/api/telemetry/destination/VEH001")

    st.markdown(f"<div style='font-size:0.8rem;color:{theme_color('text_secondary')};margin-bottom:6px;'>📍 Location & Motion</div>", unsafe_allow_html=True)
    veh_lat = nav_telemetry.get('gps_lat') or 13.0827
    veh_lon = nav_telemetry.get('gps_lon') or 80.2707

    # Proximity notification for nearby points of interest along the
    # route (demo-purpose feature: ROUTE_POIS is a small hardcoded list,
    # not a live places API). Only relevant while actually driving to a
    # destination — a parked car isn't "approaching" anything.
    if nav_destination and (nav_telemetry.get('speed', 0) or 0) > 0:
        _poi_icons = {"restaurant": "🍽️", "charging": "⚡"}
        for poi in ROUTE_POIS:
            poi_dist = km_distance(veh_lat, veh_lon, poi["lat"], poi["lon"])
            if poi_dist <= 1.0:
                icon = _poi_icons.get(poi["type"], "📍")
                st.info(f"{icon} **{poi['name']}** is {poi_dist:.1f} km ahead.")
                break  # show only the single closest upcoming POI, not a stack

    point_data = [{"lat": veh_lat, "lon": veh_lon, "color": [63, 185, 80]}]
    layers = []

    if nav_destination:
        point_data.append({"lat": nav_destination['dest_lat'], "lon": nav_destination['dest_lon'], "color": [248, 81, 73]})

        # Real road-following route in blue, with a straight-line fallback
        # if OSRM is unreachable (no internet, demo server down, etc.) so
        # the route still shows something rather than nothing.
        route_coords = fetch_road_route(veh_lat, veh_lon, nav_destination['dest_lat'], nav_destination['dest_lon'])
        if not route_coords:
            route_coords = [[veh_lon, veh_lat], [nav_destination['dest_lon'], nav_destination['dest_lat']]]
        layers.append(pdk.Layer(
            "PathLayer",
            data=[{"path": route_coords}],
            get_path="path",
            get_color=[59, 130, 246],
            width_min_pixels=4,
        ))

    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=point_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius=70,
        radius_min_pixels=6,
    ))

    view_state = pdk.ViewState(latitude=veh_lat, longitude=veh_lon, zoom=12)
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, map_style=None), height=260)

    if nav_destination:
        dist_km = km_distance(veh_lat, veh_lon, nav_destination['dest_lat'], nav_destination['dest_lon'])
        speed_now = nav_telemetry.get('speed', 0) or 0
        if nav_destination['status'] == 'arrived' or dist_km <= 0.03:
            st.caption(f"🎉 Arrived at {nav_destination['dest_name']}")
            dist_km, eta_min = 0.0, 0.0
        else:
            eta_min = (dist_km / speed_now * 60) if speed_now > 5 else (dist_km / 40 * 60)
            st.caption(f"📍 {nav_destination['dest_name']} · {speed_now:.0f} km/h")
            if "ride_just_started" in st.session_state and st.session_state.ride_just_started == nav_destination['dest_name']:
                st.success(f"🚦 Ride started! Heading to {nav_destination['dest_name']}.")
        if st.button("❌ Clear destination", key="home_clear_dest"):
            st.session_state.pop("ride_just_started", None)
            api_delete("/api/telemetry/destination/VEH001")
            st.rerun()
        return nav_destination, dist_km, eta_min
    else:
        st.session_state.pop("ride_just_started", None)
        st.caption(f"No destination set · {nav_telemetry.get('speed', 0) or 0:.0f} km/h")
        home_dest_choice = st.selectbox(
            "Pick a destination",
            list(PRESET_DESTINATIONS.keys()),
            label_visibility="collapsed",
            key="home_dest_picker",
        )
        st.caption(f"Selected: {home_dest_choice} — tap Start Ride to confirm and begin.")
        if st.button("🚦 Start Ride", key="home_navigate_btn", type="primary"):
            _hd_lat, _hd_lon = PRESET_DESTINATIONS[home_dest_choice]
            api_post("/api/telemetry/destination", {
                "vehicle_id": "VEH001",
                "dest_name": home_dest_choice,
                "dest_lat": _hd_lat,
                "dest_lon": _hd_lon,
            })
            st.session_state.ride_just_started = home_dest_choice
            st.rerun()
        return None, None, None


def health_gauge(score, title="Health Score"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"color": "#e6edf3", "size": 16}},
        number={"suffix": "%", "font": {"color": health_color(score), "size": 36}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8b949e"},
            "bar": {"color": health_color(score), "thickness": 0.3},
            "bgcolor": "#161b22",
            "bordercolor": "#30363d",
            "steps": [
                {"range": [0,  40], "color": "#3d1a1a"},
                {"range": [40, 60], "color": "#3d2a0d"},
                {"range": [60, 80], "color": "#2d3a1a"},
                {"range": [80,100], "color": "#1a3a2a"},
            ],
            "threshold": {
                "line": {"color": health_color(score), "width": 3},
                "thickness": 0.8,
                "value": score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# ── Shared connection check (used by both sidebar and top bar) ──
_backend_home = api_get("/")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 ACIP-X1")
    st.markdown("*Automotive Cognitive Intelligence*")
    st.markdown("---")

    mode = st.radio(
        "Select Mode",
        ["🏭 Engineering Mode", "👤 Customer Mode"],
        index=0
    )
    st.markdown("---")

    # Connection status
    home = _backend_home
    if home:
        st.success("🟢 Server Connected")
        st.caption(f"Version: {home.get('version', '1.0.0')}")
    else:
        st.error("🔴 Server Offline")
        st.caption("Start: uvicorn backend.main:app")

    st.markdown("---")
    refresh_rate = 2
    if st.button("🔄 Refresh Now"):
        st.rerun()

    st.markdown("---")
    st.caption("© 2026 ACIP-X1 Platform")


# ── Top Bar (shared across both modes) ───────────────────
# ACIP-X1 title (left) · current mode (middle) · connectivity dot + time (right)
# Green = backend reachable, Red = backend unreachable. (A "connecting/yellow"
# state would need an async check Streamlit's synchronous rerun model doesn't
# support cleanly — the check above already resolves before this renders, so
# showing yellow here would be cosmetic rather than a real interim state.)
_conn_dot = "🟢" if _backend_home else "🔴"
_conn_text = "Connected" if _backend_home else "Offline"
_now_ist = (datetime.utcnow() + IST_OFFSET).strftime("%H:%M")
tb_left, tb_mid, tb_right = st.columns([1, 1.4, 1])
with tb_left:
    st.markdown(f'<div style="font-size:1.3rem;font-weight:600;color:{THEME["text_primary"]};padding-top:6px;">🚗 ACIP-X1</div>', unsafe_allow_html=True)
with tb_mid:
    st.markdown(f'<div style="text-align:center;padding-top:10px;color:{THEME["text_secondary"]};font-size:0.95rem;">{mode}</div>', unsafe_allow_html=True)
with tb_right:
    st.markdown(
        f'<div style="text-align:right;padding-top:8px;color:{THEME["text_secondary"]};font-size:0.85rem;">'
        f'{_conn_dot} {_conn_text} · {_now_ist} IST</div>',
        unsafe_allow_html=True
    )
st.markdown("---")


# ══════════════════════════════════════════════════════════
# ENGINEERING MODE
# ══════════════════════════════════════════════════════════
if mode == "🏭 Engineering Mode":

    st.markdown("""
    <div class="mode-header">
        <h2 style="margin:0">🏭 Engineering Mode</h2>
        <p style="margin:0;color:#8b949e">Requirement Intelligence · Traceability · Failure Prevention</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Requirements",
        "🔗 Traceability",
        "🧠 KG Analysis",
        "📊 System Overview",
        "🤖 AI Parser",
        "💬 Ask the KG"
    ])

    # ── Tab 1: Requirements ───────────────────────────────
    with tab1:
        st.subheader("📋 Requirements Dashboard")

        stats = api_get("/api/engineering/requirements/stats")
        reqs  = api_get("/api/requirements/")

        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Requirements</div>
                    <div class="metric-value" style="color:#58a6ff">{stats['total_requirements']}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                safety = stats['by_category'].get('Safety', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Safety Requirements</div>
                    <div class="metric-value" style="color:#f85149">{safety}</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                functional = stats['by_category'].get('Functional', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Functional Requirements</div>
                    <div class="metric-value" style="color:#3fb950">{functional}</div>
                </div>""", unsafe_allow_html=True)
            with col4:
                systems = len(stats['by_system'])
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Systems Covered</div>
                    <div class="metric-value" style="color:#d29922">{systems}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if stats['by_category']:
                    fig = px.pie(
                        values=list(stats['by_category'].values()),
                        names=list(stats['by_category'].keys()),
                        title="Requirements by Category",
                        color_discrete_sequence=["#f85149","#3fb950","#58a6ff","#d29922"]
                    )
                    fig.update_layout(
                        paper_bgcolor="#0a0e1a",
                        plot_bgcolor="#0a0e1a",
                        font_color="#e6edf3",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                if stats['by_system']:
                    fig = px.bar(
                        x=list(stats['by_system'].keys()),
                        y=list(stats['by_system'].values()),
                        title="Requirements by System",
                        color=list(stats['by_system'].values()),
                        color_continuous_scale="Blues"
                    )
                    fig.update_layout(
                        paper_bgcolor="#0a0e1a",
                        plot_bgcolor="#0a0e1a",
                        font_color="#e6edf3",
                        height=300,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)

        if reqs:
            st.markdown("### All Requirements")
            df = pd.DataFrame(reqs)
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                column_config={
                    "req_id":      st.column_config.TextColumn("ID", width=100),
                    "description": st.column_config.TextColumn("Description", width=500),
                    "category":    st.column_config.TextColumn("Category", width=120),
                    "system":      st.column_config.TextColumn("System", width=120),
                }
            )

    # ── Tab 2: Traceability ───────────────────────────────
    with tab2:
        st.subheader("🔗 Auto Traceability Matrix")
        st.caption("Requirement → Signal → Calibration → DTC → Fault → Test Case")

        gaps = api_get("/api/kg/requirements/gaps")
        if gaps:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Requirements</div>
                    <div class="metric-value" style="color:#58a6ff">{gaps['total_requirements']}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                complete = gaps['total_requirements'] - gaps['total_gaps']
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Fully Traced</div>
                    <div class="metric-value" style="color:#3fb950">{complete}</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Gaps Found</div>
                    <div class="metric-value" style="color:#f85149">{gaps['total_gaps']}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Requirement Traceability")

        reqs = api_get("/api/requirements/")
        if reqs:
            selected_req = st.selectbox(
                "Select Requirement to Trace",
                [f"{r['req_id']} — {r['description'][:60]}..." for r in reqs]
            )
            req_id = selected_req.split(" — ")[0]

            if st.button("🔗 Trace This Requirement"):
                trace = api_get(f"/api/kg/requirement/{req_id}/trace")
                if trace:
                    st.markdown(f"### Traceability Chain for {req_id}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**📋 Requirement**")
                        st.info(trace.get('requirement', 'N/A'))
                    with col2:
                        st.markdown("**📡 Mapped Signals**")
                        if trace['mapped_signals']:
                            for s in trace['mapped_signals']:
                                st.success(f"✅ {s['signal_id']} — {s['signal_name']}")
                        else:
                            st.error("❌ No signal mapped!")
                    with col3:
                        st.markdown("**🧪 Test Cases**")
                        if trace['test_cases']:
                            for tc in trace['test_cases']:
                                st.success(f"✅ {tc['tc_id']}")
                        else:
                            st.error("❌ No test case!")

                    complete = trace['traceability_complete']
                    if complete:
                        st.success("✅ Traceability COMPLETE — This requirement is fully covered!")
                    else:
                        st.error("❌ Traceability INCOMPLETE — Risk of test case failure!")

    # ── Tab 3: KG Analysis ────────────────────────────────
    with tab3:
        st.subheader("🧠 Knowledge Graph Analysis")

        kg_summary = api_get("/api/kg/summary")
        if kg_summary:
            cols = st.columns(5)
            items = [
                ("Nodes", kg_summary['total_nodes'], "#58a6ff"),
                ("Edges", kg_summary['total_edges'], "#3fb950"),
                ("ECUs",  kg_summary['breakdown']['ecus'],  "#d29922"),
                ("Signals", kg_summary['breakdown']['signals'], "#a371f7"),
                ("Faults", kg_summary['breakdown']['faults'], "#f85149"),
            ]
            for col, (label, value, color) in zip(cols, items):
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value" style="color:{color}">{value}</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔴 Fault Analysis")
            faults = api_get("/api/faults/")
            if faults:
                fault_id = st.selectbox(
                    "Select Fault",
                    [f"{f['fault_id']} — {f['fault_name']}" for f in faults],
                    key="fault_select"
                )
                fid = fault_id.split(" — ")[0]
                analysis = api_get(f"/api/kg/fault/{fid}")
                if analysis:
                    st.markdown(f"**Fault:** {analysis['fault_name']}")
                    st.markdown("**Root Causes:**")
                    for rc in analysis['root_causes']:
                        st.markdown(f"""
                        <div class="alert-warning">⚠️ {rc}</div>
                        """, unsafe_allow_html=True)
                    st.markdown("**Recommended Actions:**")
                    for action in analysis['recommended_actions']:
                        st.markdown(f"""
                        <div class="alert-info">🔧 {action}</div>
                        """, unsafe_allow_html=True)

        with col2:
            st.markdown("### 🟡 DTC Analysis")
            dtcs = api_get("/api/dtcs/")
            if dtcs:
                dtc_id = st.selectbox(
                    "Select DTC",
                    [f"{d['dtc_id']} — {d['description']}" for d in dtcs],
                    key="dtc_select"
                )
                did = dtc_id.split(" — ")[0]
                dtc_analysis = api_get(f"/api/kg/dtc/{did}")
                if dtc_analysis:
                    st.markdown(f"**DTC:** {dtc_analysis['dtc_name']}")
                    st.markdown("**Related Faults:**")
                    for fault in dtc_analysis['faults']:
                        st.markdown(f"""
                        <div class="alert-critical">🔴 {fault}</div>
                        """, unsafe_allow_html=True)
                    st.markdown("**Actions:**")
                    for action in dtc_analysis['recommended_actions']:
                        st.markdown(f"""
                        <div class="alert-info">🔧 {action}</div>
                        """, unsafe_allow_html=True)

    # ── Tab 4: System Overview ────────────────────────────
    with tab4:
        st.subheader("📊 System Overview")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ECUs")
            ecus = api_get("/api/ecus/")
            if ecus:
                df = pd.DataFrame(ecus)
                st.dataframe(df, use_container_width=True, height=300)

        with col2:
            st.markdown("### Calibration Limits")
            cals = api_get("/api/dashboard/calibration-limits")
            if cals:
                df = pd.DataFrame(cals['limits'])
                st.dataframe(df, use_container_width=True, height=300)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Active DTCs")
            active_dtcs = api_get("/api/dashboard/active-dtcs")
            if active_dtcs:
                for dtc in active_dtcs['dtcs']:
                    color = "#f85149" if dtc['severity'] == "Critical" else "#d29922"
                    st.markdown(f"""
                    <div class="alert-critical">
                        <b>{dtc['dtc_id']}</b> — {dtc['description']}
                        <span style="color:{color};float:right">{dtc['severity']}</span>
                    </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("### Active Faults")
            active_faults = api_get("/api/dashboard/active-faults")
            if active_faults:
                for fault in active_faults['faults']:
                    color = "#f85149" if fault['severity'] == "Critical" else "#d29922"
                    st.markdown(f"""
                    <div class="alert-warning">
                        <b>{fault['fault_id']}</b> — {fault['name']}
                        <span style="color:{color};float:right">{fault['severity']}</span>
                    </div>""", unsafe_allow_html=True)

    # ── Tab 5: AI Parser ──────────────────────────────────
    with tab5:
        st.subheader("🤖 AI Requirement Parser")
        st.caption("Upload any file — PDF, Excel, Word, CSV, TXT — AI extracts all requirements automatically")

        upload_tab, text_tab, demo_tab = st.tabs(["📁 Upload File", "✍️ Paste Text", "🎯 Demo"])

        with upload_tab:
            uploaded = st.file_uploader(
                "Drop your requirements file here",
                type=["pdf", "xlsx", "xls", "docx", "doc", "csv", "txt"]
            )
            save_db = st.checkbox("Save to Database", value=False)
            if uploaded and st.button("🚀 Parse Requirements"):
                with st.spinner("AI is reading your file..."):
                    files = {"file": (uploaded.name, uploaded.getvalue())}
                    try:
                        r = requests.post(
                            f"{BASE_URL}/api/engineering/requirements/parse/file?save_to_db={save_db}",
                            files=files, timeout=30
                        )
                        if r.status_code == 200:
                            result = r.json()
                            st.success(f"✅ Found {result['total_found']} requirements!")
                            df = pd.DataFrame(result['requirements'])
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with text_tab:
            text_input = st.text_area(
                "Paste your requirements here (one per line)",
                height=200,
                placeholder="The battery voltage shall not exceed 420V...\nThe motor speed shall not exceed 12000 RPM..."
            )
            save_db2 = st.checkbox("Save to Database", value=False, key="save2")
            if st.button("🚀 Parse Text"):
                if text_input:
                    with st.spinner("Parsing..."):
                        result = api_post(
                            "/api/engineering/requirements/parse/text",
                            {"text": text_input, "save_to_db": save_db2}
                        )
                        if result:
                            st.success(f"✅ Found {result['total_found']} requirements!")
                            df = pd.DataFrame(result['requirements'])
                            st.dataframe(df, use_container_width=True)

        with demo_tab:
            if st.button("🎯 Run Demo Parser"):
                with st.spinner("Running demo..."):
                    result = api_get("/api/engineering/requirements/parse/demo")
                    if result:
                        st.success(f"✅ Found {result['total_found']} requirements!")
                        df = pd.DataFrame(result['requirements'])
                        st.dataframe(
                            df,
                            use_container_width=True,
                            column_config={
                                "req_id":      "ID",
                                "description": "Requirement",
                                "category":    "Category",
                                "system":      "System",
                                "confidence":  "Confidence",
                            }
                        )

    # ── Tab 6: AI Chat Assistant for Engineers (Day 22 / E9) ──
    with tab6:
        st.subheader("💬 Ask the Knowledge Graph")
        st.caption(
            "Ask natural-language questions — the AI searches the real "
            "Knowledge Graph and impact analysis to answer, grounded in "
            "actual project data. Try: \"What requirements relate to "
            "battery temperature?\" or \"What will fail if I change CAL001?\""
        )

        if "eng_chat_history" not in st.session_state:
            st.session_state.eng_chat_history = []

        for entry in st.session_state.eng_chat_history:
            icon = "👷" if entry["role"] == "user" else "🤖"
            st.markdown(
                f'<div class="chat-bubble-{"user" if entry["role"]=="user" else "assistant"}">{icon} {entry["content"]}</div>',
                unsafe_allow_html=True
            )

        eng_question = st.text_input(
            "Ask a question",
            key="eng_chat_input",
            placeholder="e.g. What requirements relate to battery temperature?"
        )
        col_ask, col_reset = st.columns([3, 1])
        with col_ask:
            if st.button("Ask", key="eng_chat_ask") and eng_question:
                with st.spinner("🔍 Searching the Knowledge Graph..."):
                    try:
                        r = requests.post(
                            f"{BASE_URL}/api/engineer-chat/ask/engineer1",
                            json={"question": eng_question},
                            timeout=20,
                        )
                        result = r.json() if r.status_code == 200 else None
                    except Exception:
                        result = None

                if result is None:
                    st.error("No response — the request may have timed out. Try again.")
                else:
                    st.session_state.eng_chat_history.append({"role": "user", "content": eng_question})
                    st.session_state.eng_chat_history.append({"role": "assistant", "content": result["answer"]})
                    if not result.get("ai_available", True):
                        st.warning("AI connection isn't available right now (check GEMINI_API_KEY in .env).")
                    if result.get("tool_calls"):
                        with st.expander("🔧 What the AI looked up"):
                            for tc in result["tool_calls"]:
                                st.markdown(f"- `{tc['function']}({tc['args']})`")
                st.rerun()
        with col_reset:
            if st.button("🔄 Clear", key="eng_chat_reset"):
                st.session_state.eng_chat_history = []
                requests.delete(f"{BASE_URL}/api/engineer-chat/reset/engineer1", timeout=5)
                st.rerun()


# ══════════════════════════════════════════════════════════
# CUSTOMER MODE
# ══════════════════════════════════════════════════════════
elif mode == "👤 Customer Mode":

    st.markdown("""
    <div class="mode-header">
        <h2 style="margin:0">👤 Customer Mode</h2>
        <p style="margin:0;color:#8b949e">Live Vehicle Health · Alerts · Diagnostics · AI Assistance</p>
    </div>
    """, unsafe_allow_html=True)

    if "customer_view" not in st.session_state:
        st.session_state.customer_view = "home"
    if "customer_pending_view" in st.session_state:
        st.session_state.customer_view = st.session_state.pop("customer_pending_view")

    def _go_home():
        st.session_state.customer_pending_view = "home"

    _view = st.session_state.customer_view

    if _view == "home":
        greeting_data = api_get("/api/personality/greeting/VEH001")
        if greeting_data and greeting_data.get("messages"):
            for msg in greeting_data["messages"]:
                st.markdown(
                    f'<div class="breakdown-card" style="border-left-color:#58a6ff;background:#1a2332;">🚗 {msg}</div>',
                    unsafe_allow_html=True
                )

        summary = api_get("/api/dashboard/summary")
        cc_telemetry = api_get("/api/telemetry/latest/VEH001")

        if summary and cc_telemetry:
            cc_t = {k: (0 if v is None else v) for k, v in cc_telemetry.items()}
            cc_destination = api_get("/api/telemetry/destination/VEH001")

            # ── Infotainment-style Command Center (40:60 split) ──
            left_col, right_col = st.columns([0.8, 1.2])  # 40:60 ratio

            with left_col:
                # Illustrative media-style card (styling only, no real audio)
                st.markdown(f"""
                <div class="glass-card" style="padding:12px;margin-bottom:12px;display:flex;align-items:center;gap:10px;">
                    <div style="width:40px;height:40px;border-radius:8px;background:{theme_color('bg_surface_alt')};display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🎵</div>
                    <div>
                        <div style="font-size:0.85rem;color:{theme_color('text_primary')};">Car personality</div>
                        <div style="font-size:0.75rem;color:{theme_color('text_secondary')};">{(greeting_data['messages'][0][:40] + '…') if greeting_data and greeting_data.get('messages') else 'All systems normal'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 3x3 grid of real Customer Mode features
                features = [
                    ("🎙️", "Talk to Your Car"),
                    ("🚗", "Live Dashboard"),
                    ("🔴", "Alerts & Issues"),
                    ("🤖", "AI Diagnostics"),
                    ("📊", "Health Trend"),
                    ("🔮", "Invisible Mechanic"),
                    ("🚨", "Emergency"),
                    ("🛠️", "Breakdown Assist"),
                    ("📈", "Resale Value"),
                ]
                for row_start in range(0, 9, 3):
                    grid_cols = st.columns(3)
                    for i, gcol in enumerate(grid_cols):
                        icon, label = features[row_start + i]
                        with gcol:
                            if st.button(f"{icon}\n{label}", key=f"tile_{label}", use_container_width=True):
                                st.session_state.customer_pending_view = label
                                st.rerun()
                st.caption("Tap a tile to open that feature.")

                # Real status strip — fills the remaining left-column space
                # with genuinely useful data instead of leaving it empty,
                # since the right column (map + status) runs taller.
                if summary:
                    _issues_n = summary.get('total_issues', 0)
                    _warn_n = summary.get('total_warnings', 0)
                    st.markdown(f"""
                    <div class="glass-card" style="padding:12px;margin-top:10px;">
                        <div style="font-size:0.75rem;color:{theme_color('text_secondary')};margin-bottom:6px;">QUICK STATUS</div>
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:{theme_color('text_primary')};margin-bottom:4px;">
                            <span>Active issues</span><span style="color:{'#f85149' if _issues_n else '#3fb950'}">{_issues_n}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:{theme_color('text_primary')};margin-bottom:4px;">
                            <span>Warnings</span><span style="color:{'#d29922' if _warn_n else '#3fb950'}">{_warn_n}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;color:{theme_color('text_primary')};">
                            <span>Odometer</span><span>{cc_t.get('odometer_km', 0) or 0:,.0f} km</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with right_col:
                nav_subcol, status_subcol = st.columns([1, 1])

                with nav_subcol:
                    nav_container = st.container(key="nav_glass_card")
                    with nav_container:
                        _nav_dest_result, _nav_dist_km, _nav_eta_min = live_map_fragment(cc_t)

                with status_subcol:
                    status_container = st.container(key="status_glass_card")
                    with status_container:
                        st.markdown(f"<div style='font-size:0.8rem;color:{theme_color('text_secondary')};margin-bottom:6px;'>🚗 Vehicle Status</div>", unsafe_allow_html=True)

                    # Derived gear-style status — ACIP-X1 is a single-motor EV with
                    # no real P/R/N/D signal, so this is honestly derived from real
                    # speed data: P (parked, speed=0) or D (driving, speed>0).
                    # Charging is shown as its own separate badge, not folded into
                    # the gear letter, since charging isn't really a "gear."
                    _speed = cc_t.get('speed', 0) or 0
                    _charging = cc_t.get('charging_status', 0) or 0
                    _active_gear = "D" if _speed > 0 else "P"

                    # Door/lock status — derived: a parked, non-charging vehicle is
                    # shown as locked; charging or driving implies recently accessed.
                    lock_label = "Locked" if (_active_gear == "P" and not _charging) else "Unlocked"

                    st.markdown(f"""
                    <svg viewBox="0 0 200 140" style="width:100%;height:140px;">
                        <ellipse cx="100" cy="128" rx="75" ry="6" fill="#000000" opacity="0.3"/>
                        <path d="M40,120 L40,75 Q40,55 55,45 L70,32 Q80,25 100,25 Q120,25 130,32 L145,45 Q160,55 160,75 L160,120 Z"
                              fill="#0c0c0e" stroke="#3a3a3f" stroke-width="1.2"/>
                        <path d="M58,46 Q68,34 100,34 Q132,34 142,46 L138,58 L62,58 Z" fill="#16161a" stroke="#3a3a3f" stroke-width="1"/>
                        <rect x="45" y="62" width="110" height="6" rx="2" fill="#1c1c20"/>
                        <rect x="44" y="70" width="20" height="12" rx="3" fill="#d8d8da"/>
                        <rect x="136" y="70" width="20" height="12" rx="3" fill="#d8d8da"/>
                        <rect x="80" y="100" width="40" height="14" rx="3" fill="#0a0a0c" stroke="#2e2e32" stroke-width="1"/>
                        <circle cx="55" cy="120" r="14" fill="#0a0a0c" stroke="#3a3a3f" stroke-width="2"/>
                        <circle cx="145" cy="120" r="14" fill="#0a0a0c" stroke="#3a3a3f" stroke-width="2"/>
                    </svg>
                    """, unsafe_allow_html=True)

                    # Real P/D gear-letter indicator, styled like a car's gear
                    # selector. R and N are added in standard P-R-N-D order
                    # for visual completeness only — per explicit user request
                    # they are decorative, never active/clickable, since ACIP-X1
                    # is a single-motor EV with no real reverse/neutral signal.
                    _gear_letters_html = ""
                    for letter in ["P", "R", "N", "D"]:
                        is_active = (letter in ("P", "D")) and (letter == _active_gear)
                        _gear_letters_html += (
                            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                            f'width:28px;height:28px;border-radius:50%;margin-right:6px;font-weight:700;'
                            f'background:{"#3fb950" if is_active else theme_color("bg_surface_alt")};'
                            f'color:{"#0a0e1a" if is_active else theme_color("text_secondary")};">{letter}</span>'
                        )
                    st.markdown(f'<div style="margin-bottom:10px;">{_gear_letters_html}</div>', unsafe_allow_html=True)

                    badge_row = f"""
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">"""
                    if _charging:
                        badge_row += f'<span style="font-size:0.7rem;background:{theme_color("bg_surface_alt")};color:#58a6ff;padding:3px 10px;border-radius:10px;">⚡ Charging</span>'
                    badge_row += f"""
                        <span style="font-size:0.7rem;background:{theme_color('bg_surface_alt')};color:{theme_color('text_secondary')};padding:3px 10px;border-radius:10px;">{lock_label}</span>
                    </div>"""
                    st.markdown(badge_row, unsafe_allow_html=True)

                    soc = cc_t.get('soc', 0) or 0
                    range_km = cc_t.get('estimated_range_km', 0) or 0
                    soc_color = "#3fb950" if soc > 20 else "#f85149"

                    driving_style_data = api_get("/api/dashboard/invisible-mechanic")
                    ds = (driving_style_data or {}).get("driver_score") or {}
                    style_label = ds.get("style", "Not enough data")
                    style_color = ds.get("style_color", theme_color('text_secondary'))

                    st.markdown(f"""
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;margin-bottom:4px;"><span>Battery</span><span style="color:{soc_color}">{soc:.0f}%</span></div>
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;margin-bottom:4px;"><span>Range</span><span>{range_km:.0f} km</span></div>
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;margin-bottom:4px;"><span>Health</span><span>{summary['health_score']:.0f}%</span></div>
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;margin-bottom:4px;"><span>Driving style</span><span style="color:{style_color}">{style_label}</span></div>
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;margin-bottom:4px;"><span>Battery temp</span><span>{cc_t.get('battery_temp', 0) or 0:.1f}°C</span></div>
                    <div style="font-size:0.8rem;color:{theme_color('text_primary')};display:flex;justify-content:space-between;"><span>Brake pad wear</span><span>{cc_t.get('brake_pad_wear_pct', 0) or 0:.0f}%</span></div>
                    """, unsafe_allow_html=True)

                    if _nav_dest_result and _nav_dist_km is not None and _nav_dist_km > 0.03:
                        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
                        eta_c1, eta_c2 = st.columns(2)
                        with eta_c1:
                            st.markdown(f"""
                            <div class="metric-card" style="padding:8px;">
                                <div class="metric-label" style="font-size:0.7rem;">Distance</div>
                                <div class="metric-value" style="font-size:1rem;color:{theme_color('text_primary')}">{_nav_dist_km:.1f} <small style="font-size:0.65rem">km</small></div>
                            </div>""", unsafe_allow_html=True)
                        with eta_c2:
                            st.markdown(f"""
                            <div class="metric-card" style="padding:8px;">
                                <div class="metric-label" style="font-size:0.7rem;">ETA</div>
                                <div class="metric-value" style="font-size:1rem;color:{theme_color('text_primary')}">{_nav_eta_min:.0f} <small style="font-size:0.65rem">min</small></div>
                            </div>""", unsafe_allow_html=True)

    # ── Bottom bar: illustrative climate controls + real outdoor temp + search ──
    # Lives OUTSIDE the view router so it stays visible no matter which
    # feature page is open, per the user's explicit requirement that the
    # top and bottom bars "should remain constant" while only the body swaps.
    # AC temp, fan speed, and volume are illustrative only — no real climate
    # control data exists in current telemetry. Outdoor temp uses the real
    # ambient_temp field. Per spec: docs/infotainment_redesign_spec.md
    if "bb_ac_temp" not in st.session_state:
        st.session_state.bb_ac_temp = 22
    if "bb_fan" not in st.session_state:
        st.session_state.bb_fan = 2
    if "bb_volume" not in st.session_state:
        st.session_state.bb_volume = 60

    _bb_telemetry = api_get("/api/telemetry/latest/VEH001") or {}
    real_outdoor_temp = _bb_telemetry.get('ambient_temp', None)

    bb1, bb2, bb3, bb4, bb5 = st.columns([1, 1, 1, 1, 2])
    with bb1:
        st.session_state.bb_ac_temp = st.number_input("AC °C", min_value=16, max_value=30, value=st.session_state.bb_ac_temp, step=1, key="bb_ac_input", label_visibility="visible")
    with bb2:
        st.session_state.bb_fan = st.number_input("Fan", min_value=0, max_value=5, value=st.session_state.bb_fan, step=1, key="bb_fan_input")
    with bb3:
        st.session_state.bb_volume = st.number_input("Vol %", min_value=0, max_value=100, value=st.session_state.bb_volume, step=5, key="bb_vol_input")
    with bb4:
        if real_outdoor_temp is not None:
            st.markdown(f"""
            <div style="text-align:center;padding-top:1.6rem;">
                <div style="font-size:0.7rem;color:{theme_color('text_secondary')};">OUTSIDE</div>
                <div style="font-size:1.1rem;color:{theme_color('text_primary')};">{real_outdoor_temp:.0f}°C</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.caption("Outside temp unavailable")
    with bb5:
        search_query = st.text_input("Search features", placeholder="e.g. battery, resale, talk…", key="bb_search", label_visibility="visible")
        if search_query:
            feature_keywords = {
                "Talk to Your Car": ["talk", "voice", "assistant", "chat", "speak"],
                "Live Dashboard": ["live", "dashboard", "telemetry", "speed", "rpm"],
                "Alerts & Issues": ["alert", "issue", "problem", "warning", "fault"],
                "AI Diagnostics": ["diagnos", "ai", "cause", "fix"],
                "Health Trend": ["health", "trend", "history", "score"],
                "Invisible Mechanic": ["mechanic", "predict", "wear", "brake", "tyre", "battery health"],
                "Emergency": ["emergency", "accident", "crash", "sos"],
                "Breakdown Assist": ["breakdown", "stuck", "stranded", "tow"],
                "Resale Value": ["resale", "value", "sell", "price", "worth", "certificate"],
            }
            q = search_query.lower().strip()
            matches = [
                name for name, kws in feature_keywords.items()
                if q in name.lower() or any(q in kw or kw in q for kw in kws)
            ]
            if matches:
                st.caption(f"Matches: {', '.join(matches)} — tap that tile on the home screen.")
            else:
                st.caption("No matching feature — try a different word.")

    st.markdown("---")

    if _view == "Live Dashboard":
        st.button("⬅️ Back", key="back_live_dashboard", on_click=_go_home)
        summary = api_get("/api/dashboard/summary")
        if summary:
            # Health gauge + key metrics
            col1, col2 = st.columns([1, 2])
            with col1:
                fig = health_gauge(summary['health_score'])
                st.plotly_chart(fig, use_container_width=True)

                status = summary['status']
                badge_class = f"badge-{status.lower()}"
                st.markdown(f"""
                <div style="text-align:center">
                    <span class="{badge_class}">{status}</span>
                </div>""", unsafe_allow_html=True)

            with col2:
                readings = summary.get('latest_readings', {}) or {}
                metrics = [
                    ("⚡ RPM",          readings.get('rpm') or 0,          "RPM",  "#58a6ff", 6000),
                    ("🚀 Speed",         readings.get('speed') or 0,        "km/h", "#3fb950", 200),
                    ("🌡️ Coolant Temp",  readings.get('coolant_temp') or 0, "°C",   "#d29922", 95),
                    ("🔋 Battery Temp",  readings.get('battery_temp') or 0, "°C",   "#a371f7", 45),
                ]
                col_a, col_b = st.columns(2)
                for i, (label, value, unit, color, limit) in enumerate(metrics):
                    with (col_a if i % 2 == 0 else col_b):
                        value = value if value is not None else 0
                        pct = min((value / limit * 100) if limit > 0 else 0, 100)
                        warn = "⚠️" if pct > 80 else ""
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{label} {warn}</div>
                            <div class="metric-value" style="color:{color}">{value} <small style="font-size:1rem">{unit}</small></div>
                        </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # Stats row — driven by the Day 16 Problem/Solution/Cost engine
            diagnostics = api_get("/api/dashboard/diagnostics") or {}
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🔍 Systems Checked</div>
                    <div class="metric-value" style="color:#58a6ff">{diagnostics.get('total_checks', 0)}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">✅ All Normal</div>
                    <div class="metric-value" style="color:#3fb950">{diagnostics.get('ok_count', 0)}</div>
                </div>""", unsafe_allow_html=True)
            with col3:
                attention = diagnostics.get('critical_count', 0) + diagnostics.get('warning_count', 0)
                attn_color = "#f85149" if diagnostics.get('critical_count', 0) > 0 else ("#d29922" if attention > 0 else "#3fb950")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">⚠️ Need Attention</div>
                    <div class="metric-value" style="color:{attn_color}">{attention}</div>
                </div>""", unsafe_allow_html=True)

            st.caption(
                f"📡 Live reading as of {to_ist(summary.get('timestamp'))} · "
                f"ACIP-X1 checks {diagnostics.get('total_checks', 0)} vehicle systems against real engineering "
                f"calibration limits every {refresh_rate}s — see the Alerts & Issues tab for full details on anything that needs attention."
            )

            st.markdown("---")

            # ── Live EV Telemetry (CAN Bus / Day 15) ─────────────
            st.subheader("🔋 Live EV Telemetry (CAN Bus)")
            telemetry = api_get("/api/telemetry/latest/VEH001")
            if telemetry:
                # .get(key, default) only applies the default when the key is
                # missing, not when it's present but None — sanitize once here
                # so every metric below can safely format/divide without
                # crashing on a field that hasn't been populated yet.
                # GPS lat/lon are excluded: zeroing them would draw the map
                # at the equator/prime-meridian, which is more misleading
                # than just falling back to a sensible default later.
                gps_keep = {"gps_lat": telemetry.get("gps_lat"), "gps_lon": telemetry.get("gps_lon")}
                telemetry = {k: (0 if v is None else v) for k, v in telemetry.items()}
                telemetry.update(gps_keep)

            if not telemetry:
                st.info("📡 No live telemetry yet — start the CAN simulator: `python hardware/can/can_simulator.py`")
            else:
                # Battery row
                bcol1, bcol2, bcol3, bcol4 = st.columns(4)
                with bcol1:
                    st.plotly_chart(health_gauge(telemetry.get('soc', 0), "Battery SOC"), use_container_width=True)
                with bcol2:
                    st.plotly_chart(health_gauge(telemetry.get('soh', 0), "Battery SOH"), use_container_width=True)
                with bcol3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🔌 Battery Voltage</div>
                        <div class="metric-value" style="color:#3fb950">{telemetry.get('battery_voltage', 0):.1f} <small style="font-size:1rem">V</small></div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ Battery Current</div>
                        <div class="metric-value" style="color:#58a6ff">{telemetry.get('battery_current', 0):.1f} <small style="font-size:1rem">A</small></div>
                    </div>""", unsafe_allow_html=True)
                with bcol4:
                    imbalance = (telemetry.get('cell_voltage_max', 0) - telemetry.get('cell_voltage_min', 0)) * 1000
                    imb_color = "#f85149" if imbalance > 50 else "#3fb950"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🌡️ Battery Temp</div>
                        <div class="metric-value" style="color:#a371f7">{telemetry.get('battery_temp', 0):.1f} <small style="font-size:1rem">°C</small></div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🔋 Cell Imbalance</div>
                        <div class="metric-value" style="color:{imb_color}">{imbalance:.1f} <small style="font-size:1rem">mV</small></div>
                    </div>""", unsafe_allow_html=True)

                # Motor / Powertrain row
                st.markdown("##### ⚙️ Motor & Powertrain")
                mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                motor_metrics = [
                    ("🔄 Motor RPM",     telemetry.get('rpm', 0),          "RPM",  "#58a6ff"),
                    ("🔧 Motor Torque",  telemetry.get('motor_torque', 0), "Nm",   "#d29922"),
                    ("🚀 Speed",         telemetry.get('speed', 0),        "km/h", "#3fb950"),
                    ("🌡️ Inverter Temp", telemetry.get('inverter_temp', 0), "°C", "#ff7b72"),
                ]
                for i, (label, value, unit, color) in enumerate(motor_metrics):
                    with [mcol1, mcol2, mcol3, mcol4][i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value" style="color:{color}">{value:.1f} <small style="font-size:1rem">{unit}</small></div>
                        </div>""", unsafe_allow_html=True)

                with mcol5:
                    # Power = Voltage x Current — the headline number on every EV dash.
                    # Sign convention matches battery_current: + = drawing from
                    # battery (driving), - = returning to battery (regen/charging).
                    power_kw = telemetry.get('battery_voltage', 0) * telemetry.get('battery_current', 0) / 1000
                    if power_kw > 0.5:
                        power_color, power_state = "#58a6ff", "Drawing"
                    elif power_kw < -0.5:
                        power_color, power_state = "#3fb950", "Charging/Regen"
                    else:
                        power_color, power_state = "#8b949e", "Idle"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ Power ({power_state})</div>
                        <div class="metric-value" style="color:{power_color}">{power_kw:+.1f} <small style="font-size:1rem">kW</small></div>
                    </div>""", unsafe_allow_html=True)

                # Pedal / Regen row
                pcol1, pcol2 = st.columns(2)
                with pcol1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🦶 Accelerator Position</div>
                        <div class="metric-value" style="color:#58a6ff">{telemetry.get('accelerator_position', 0):.1f} <small style="font-size:1rem">%</small></div>
                    </div>""", unsafe_allow_html=True)
                with pcol2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🔋 Regen Braking Level</div>
                        <div class="metric-value" style="color:#3fb950">{telemetry.get('regen_brake_level', 0):.1f} <small style="font-size:1rem">%</small></div>
                    </div>""", unsafe_allow_html=True)

                # Tyre pressures row
                st.markdown("##### 🛞 Tyre Pressures")
                tcol1, tcol2, tcol3, tcol4 = st.columns(4)
                tyres = [
                    ("Front Left",  telemetry.get('tyre_pressure_fl', 0)),
                    ("Front Right", telemetry.get('tyre_pressure_fr', 0)),
                    ("Rear Left",   telemetry.get('tyre_pressure_rl', 0)),
                    ("Rear Right",  telemetry.get('tyre_pressure_rr', 0)),
                ]
                for i, (label, value) in enumerate(tyres):
                    with [tcol1, tcol2, tcol3, tcol4][i]:
                        t_color = "#3fb950" if 30 <= value <= 35 else "#f85149"
                        warn = "" if 30 <= value <= 35 else " ⚠️"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{label}{warn}</div>
                            <div class="metric-value" style="color:{t_color}">{value:.1f} <small style="font-size:1rem">PSI</small></div>
                        </div>""", unsafe_allow_html=True)

                # ── Location & Motion (Day 15b/15d) ──────────────
                st.markdown("##### 📍 Location & Motion")

                # Fetch current destination (if any) — Day 15d
                destination = api_get("/api/telemetry/destination/VEH001")

                veh_lat = telemetry.get('gps_lat', 13.0827)
                veh_lon = telemetry.get('gps_lon', 80.2707)

                lcol1, lcol2 = st.columns([1, 2])
                with lcol1:
                    map_rows = {
                        'lat': [veh_lat],
                        'lon': [veh_lon],
                        'color': ['#3fb950'],   # green = vehicle
                        'size':  [60],
                    }
                    if destination:
                        map_rows['lat'].append(destination['dest_lat'])
                        map_rows['lon'].append(destination['dest_lon'])
                        map_rows['color'].append('#f85149')  # red = destination
                        map_rows['size'].append(80)

                    st.map(
                        pd.DataFrame(map_rows),
                        zoom=13,
                        size='size',
                        color='color',
                        height=340,
                    )
                    st.caption(f"📍 {veh_lat:.5f}, {veh_lon:.5f}")
                with lcol2:
                    gcol1, gcol2, gcol3, gcol4 = st.columns(4)
                    with gcol1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">🧭 Heading</div>
                            <div class="metric-value" style="color:#58a6ff">{telemetry.get('heading', 0):.0f}<small style="font-size:1rem">°</small></div>
                        </div>""", unsafe_allow_html=True)
                    g_metrics = [
                        ("↔️ G-Force (X)", telemetry.get('accel_x', 0), gcol2),
                        ("↕️ G-Force (Y)", telemetry.get('accel_y', 0), gcol3),
                        ("⬆️ G-Force (Z)", telemetry.get('accel_z', 1), gcol4),
                    ]
                    for label, value, col in g_metrics:
                        with col:
                            g_color = "#f85149" if abs(value) > 0.4 else "#3fb950"
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value" style="color:{g_color}">{value:+.2f} <small style="font-size:1rem">g</small></div>
                            </div>""", unsafe_allow_html=True)

                    # Driving Style — derived from G-force magnitude (preview of Invisible Mechanic, Day 17)
                    accel_x = telemetry.get('accel_x', 0)
                    accel_y = telemetry.get('accel_y', 0)
                    g_mag = max(abs(accel_x), abs(accel_y))
                    if g_mag < 0.15:
                        style_text, style_color = "🟢 Smooth Driving", "#3fb950"
                        style_desc = "Gentle acceleration & cornering — easy on brakes, tyres & battery"
                    elif g_mag < 0.35:
                        style_text, style_color = "🟡 Moderate Driving", "#d29922"
                        style_desc = "Normal acceleration & cornering"
                    else:
                        style_text, style_color = "🔴 Aggressive Driving", "#f85149"
                        style_desc = "Hard acceleration/braking detected — increases wear on brakes & tyres"

                    st.markdown(f"""
                    <div class="metric-card" style="margin-top:0.5rem">
                        <div class="metric-label">🚦 Driving Style</div>
                        <div class="metric-value" style="color:{style_color}; font-size:1.4rem">{style_text}</div>
                        <div style="color:#8b949e; font-size:0.8rem; margin-top:4px">{style_desc}</div>
                    </div>""", unsafe_allow_html=True)

                # ── Navigation / Destination (Day 15d) ───────────
                st.markdown("##### 🗺️ Navigation")

                if destination:
                    dist_km = km_distance(veh_lat, veh_lon, destination['dest_lat'], destination['dest_lon'])
                    speed = telemetry.get('speed', 0) or 0

                    if destination['status'] == 'arrived' or dist_km <= 0.03:
                        soc_now = telemetry.get('soc', 0)
                        if soc_now >= 99.9:
                            st.success(f"🎉 **Arrived at {destination['dest_name']}!** The vehicle is parked and fully charged.")
                        else:
                            st.success(f"🎉 **Arrived at {destination['dest_name']}!** The vehicle is parked and charging ({soc_now:.1f}% battery).")
                    else:
                        if speed > 5:
                            eta_min = dist_km / speed * 60
                            eta_str = f"~{eta_min:.0f} min"
                        else:
                            eta_min = dist_km / 40 * 60  # fallback: average city speed
                            eta_str = f"~{eta_min:.0f} min (estimated)"

                        ncol1, ncol2, ncol3 = st.columns(3)
                        with ncol1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">🎯 Destination</div>
                                <div class="metric-value" style="color:#58a6ff; font-size:1.2rem">{destination['dest_name']}</div>
                            </div>""", unsafe_allow_html=True)
                        with ncol2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">📏 Distance Remaining</div>
                                <div class="metric-value" style="color:#3fb950">{dist_km:.2f} <small style="font-size:1rem">km</small></div>
                            </div>""", unsafe_allow_html=True)
                        with ncol3:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">⏱️ ETA</div>
                                <div class="metric-value" style="color:#d29922">{eta_str}</div>
                            </div>""", unsafe_allow_html=True)

                        st.caption("The vehicle is driving towards this destination — speed and odometer update automatically.")

                    if st.button("❌ Clear Destination"):
                        api_delete("/api/telemetry/destination/VEH001")
                        st.rerun()

                else:
                    st.caption("No destination set. Pick a place and the vehicle will drive there — speed, odometer, and ETA will update live.")
                    dcol1, dcol2, dcol3 = st.columns([2, 2, 1])
                    with dcol1:
                        dest_choice = st.selectbox(
                            "Choose a destination",
                            list(PRESET_DESTINATIONS.keys()) + ["📌 Custom location..."],
                            label_visibility="collapsed",
                        )
                    if dest_choice == "📌 Custom location...":
                        with dcol2:
                            custom_lat = st.number_input("Latitude", value=13.0827, format="%.4f")
                            custom_lon = st.number_input("Longitude", value=80.2707, format="%.4f")
                        dest_lat, dest_lon, dest_name = custom_lat, custom_lon, "Custom Location"
                    else:
                        dest_lat, dest_lon = PRESET_DESTINATIONS[dest_choice]
                        dest_name = dest_choice

                    with dcol3:
                        if st.button("🚗 Navigate", type="primary"):
                            api_post("/api/telemetry/destination", {
                                "vehicle_id": "VEH001",
                                "dest_name": dest_name,
                                "dest_lat": dest_lat,
                                "dest_lon": dest_lon,
                            })
                            st.rerun()

                # ── Odometer & Trip (Day 15b) ────────────────────
                st.markdown("##### 🛣️ Odometer & Trip")
                ocol1, ocol2, ocol3 = st.columns(3)
                with ocol1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📊 Odometer</div>
                        <div class="metric-value" style="color:#e6edf3">{telemetry.get('odometer_km', 0):,.1f} <small style="font-size:1rem">km</small></div>
                    </div>""", unsafe_allow_html=True)
                with ocol2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🛤️ Trip Distance</div>
                        <div class="metric-value" style="color:#58a6ff">{telemetry.get('trip_distance_km', 0):.2f} <small style="font-size:1rem">km</small></div>
                    </div>""", unsafe_allow_html=True)
                with ocol3:
                    trip_min = telemetry.get('trip_duration_min', 0) or 0
                    hours, mins = divmod(int(trip_min), 60)
                    duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⏱️ Trip Duration</div>
                        <div class="metric-value" style="color:#58a6ff">{duration_str}</div>
                    </div>""", unsafe_allow_html=True)

                ocol4, ocol5 = st.columns(2)
                with ocol4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📈 Average Speed</div>
                        <div class="metric-value" style="color:#3fb950">{telemetry.get('avg_speed_kmh', 0):.1f} <small style="font-size:1rem">km/h</small></div>
                    </div>""", unsafe_allow_html=True)
                with ocol5:
                    epk = telemetry.get('energy_per_100km', 0)
                    epk_color = "#3fb950" if epk >= 0 else "#7ee787"
                    epk_label = "Energy Use" if epk >= 0 else "Energy Recovered"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ {epk_label} /100km</div>
                        <div class="metric-value" style="color:{epk_color}">{epk:.1f} <small style="font-size:1rem">kWh</small></div>
                    </div>""", unsafe_allow_html=True)

                # ── Brake System (Day 15b) ───────────────────────
                st.markdown("##### 🛑 Brake System")
                brcol1, brcol2 = st.columns(2)
                with brcol1:
                    wear = telemetry.get('brake_pad_wear_pct', 0)
                    wear_color = "#3fb950" if wear < 60 else ("#d29922" if wear < 80 else "#f85149")
                    wear_warn = "" if wear < 80 else " ⚠️"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🛞 Brake Pad Wear{wear_warn}</div>
                        <div class="metric-value" style="color:{wear_color}">{wear:.1f} <small style="font-size:1rem">% worn</small></div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(min(wear / 100, 1.0))
                with brcol2:
                    fluid = telemetry.get('brake_fluid_level_pct', 0)
                    fluid_color = "#3fb950" if fluid >= 70 else "#f85149"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🛢️ Brake Fluid Level</div>
                        <div class="metric-value" style="color:{fluid_color}">{fluid:.1f} <small style="font-size:1rem">%</small></div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(min(max(fluid / 100, 0.0), 1.0))

                # ── Charging, Range & Environment (Day 15b) ──────
                st.markdown("##### ⚡ Charging, Range & Environment")
                ecol1, ecol2, ecol3, ecol4 = st.columns(4)
                with ecol1:
                    charging = telemetry.get('charging_status', 0)
                    soc_val = telemetry.get('soc', 0)
                    ttf = telemetry.get('time_to_full_min', 0) or 0
                    if charging == 1 and soc_val >= 99.9:
                        charge_text, charge_color = "✅ Fully Charged", "#3fb950"
                        sub_line = ""
                    elif charging == 1:
                        charge_text, charge_color = "🔌 Charging...", "#d29922"
                        h, m = divmod(int(ttf), 60)
                        ttf_str = f"{h}h {m}m" if h > 0 else f"{m}m"
                        sub_line = f'<div style="color:#8b949e; font-size:0.8rem; margin-top:4px">⏱️ ~{ttf_str} to full</div>'
                    else:
                        charge_text, charge_color = "🚘 Driving", "#58a6ff"
                        sub_line = ""
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Charging Status</div>
                        <div class="metric-value" style="color:{charge_color}; font-size:1.4rem">{charge_text}</div>
                        {sub_line}
                    </div>""", unsafe_allow_html=True)
                with ecol2:
                    cc = telemetry.get('charging_current', 0)
                    cc_label = "🔋 Charging Current" if cc > 0 else "🔋 Charge Current (idle)"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{cc_label}</div>
                        <div class="metric-value" style="color:#58a6ff">{cc:.1f} <small style="font-size:1rem">A</small></div>
                    </div>""", unsafe_allow_html=True)
                with ecol3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🛣️ Estimated Range</div>
                        <div class="metric-value" style="color:#3fb950">{telemetry.get('estimated_range_km', 0):.0f} <small style="font-size:1rem">km</small></div>
                    </div>""", unsafe_allow_html=True)
                with ecol4:
                    amb = telemetry.get('ambient_temp', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🌤️ Ambient Temp</div>
                        <div class="metric-value" style="color:#d29922">{amb:.1f} <small style="font-size:1rem">°C</small></div>
                    </div>""", unsafe_allow_html=True)

                # ── Auxiliary Systems & Climate (Day 15c) ────────
                st.markdown("##### 🔌 Auxiliary Systems & Climate")
                acol1, acol2, acol3, acol4 = st.columns(4)
                with acol1:
                    aux_v = telemetry.get('aux_battery_voltage', 0)
                    aux_color = "#3fb950" if aux_v >= 12.0 else "#f85149"
                    aux_warn = "" if aux_v >= 12.0 else " ⚠️"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🔋 12V Battery{aux_warn}</div>
                        <div class="metric-value" style="color:{aux_color}">{aux_v:.2f} <small style="font-size:1rem">V</small></div>
                    </div>""", unsafe_allow_html=True)
                with acol2:
                    dcdc = telemetry.get('dcdc_converter_temp', 0)
                    dcdc_color = "#3fb950" if dcdc < 65 else "#f85149"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🔌 DC-DC Converter</div>
                        <div class="metric-value" style="color:{dcdc_color}">{dcdc:.1f} <small style="font-size:1rem">°C</small></div>
                    </div>""", unsafe_allow_html=True)
                with acol3:
                    hl = telemetry.get('headlamp_status', 0)
                    hl_text = "✅ OK" if hl == 0 else "⚠️ Fault"
                    hl_color = "#3fb950" if hl == 0 else "#f85149"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💡 Headlamps</div>
                        <div class="metric-value" style="color:{hl_color}; font-size:1.4rem">{hl_text}</div>
                    </div>""", unsafe_allow_html=True)
                with acol4:
                    wf = telemetry.get('washer_fluid_level_pct', 0)
                    wf_color = "#3fb950" if wf >= 20 else "#f85149"
                    wf_warn = "" if wf >= 20 else " ⚠️"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💧 Washer Fluid{wf_warn}</div>
                        <div class="metric-value" style="color:{wf_color}">{wf:.0f} <small style="font-size:1rem">%</small></div>
                    </div>""", unsafe_allow_html=True)

                # Cabin climate row
                clcol1, clcol2 = st.columns(2)
                with clcol1:
                    cabin = telemetry.get('cabin_temp', 0)
                    setpoint = telemetry.get('ac_setpoint_temp', 0)
                    diff = abs(cabin - setpoint)
                    cabin_color = "#3fb950" if diff <= 2 else "#d29922"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">❄️ Cabin Temperature</div>
                        <div class="metric-value" style="color:{cabin_color}">{cabin:.1f} <small style="font-size:1rem">°C</small></div>
                    </div>""", unsafe_allow_html=True)
                with clcol2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🎛️ AC Setpoint</div>
                        <div class="metric-value" style="color:#58a6ff">{setpoint:.1f} <small style="font-size:1rem">°C</small></div>
                    </div>""", unsafe_allow_html=True)

                st.caption(f"Last update: {to_ist(telemetry.get('timestamp'))} · Source: CAN Simulator → POST /api/telemetry/")

    # ── Alerts & Issues (Day 16 C2 + Day 17 C3) ──
    elif _view == "Alerts & Issues":
        st.button("⬅️ Back", key="back_alerts", on_click=_go_home)
        st.subheader("🔴 Active Alerts & Issues")

        # ── Predictive Alerts (C3) — forward-looking, urgency-tiered ──
        pred = api_get("/api/dashboard/predictive-alerts")
        if pred and pred.get("samples_used", 0) > 0:
            psum = pred["summary"]
            st.markdown("#### 🔮 Predictive Alerts")
            st.caption("Based on trends in your vehicle's history, not just today's snapshot — these flag things worth planning for before they become a problem.")

            if psum["soon"] > 0:
                badge_msg = f"🟣 {psum['soon']} need attention soon"
            elif psum["monitor"] > 0:
                badge_msg = f"🔵 {psum['monitor']} worth monitoring"
            else:
                badge_msg = "✅ Nothing on the horizon needs attention"
            st.info(badge_msg)

            for a in pred["alerts"]:
                if a["severity"] == "soon":
                    css_class, icon = "alert-soon", "🟣"
                elif a["severity"] == "monitor":
                    css_class, icon = "alert-monitor", "🔵"
                else:
                    css_class, icon = "alert-info", "✅"

                eta_str = ""
                if a.get("days_until") is not None:
                    eta_str = f"<br><small>📅 <b>Estimated time until threshold:</b> ~{a['days_until']:.0f} days" + \
                               (f" (~{a['eta_km']:.0f} km)" if a.get("eta_km") else "") + "</small>"

                card_html = (
                    f'<div class="{css_class}">'
                    f'<b>{icon} {a["title"]}</b> <span style="color:#8b949e;float:right">{a["category"]}</span><br>'
                    f'{a["message"]}'
                    f'{eta_str}'
                    f'<br><small>💡 <b>Action:</b> {a["action"]}</small>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

            st.markdown("---")

        diag = api_get("/api/dashboard/diagnostics")

        if not diag or diag.get("total_checks", 0) == 0:
            st.info("📡 No live telemetry yet — start the CAN simulator: `python hardware/can/can_simulator.py`")
        else:
            critical = [c for c in diag["checks"] if c["status"] == "critical"]
            warning = [c for c in diag["checks"] if c["status"] == "warning"]
            healthy = [c for c in diag["checks"] if c["status"] == "ok"]

            total = diag["total_checks"]
            if not critical and not warning:
                st.success(f"✅ All {total} systems checked — everything is operating normally.")
            else:
                msg = []
                if critical:
                    msg.append(f"🔴 {len(critical)} need immediate attention")
                if warning:
                    msg.append(f"🟡 {len(warning)} worth keeping an eye on")
                st.warning(f"{total} systems checked: " + ", ".join(msg) + f", ✅ {len(healthy)} normal.")

            st.caption("Each item below shows what's wrong, what to do, the estimated cost, and what happens if it's ignored — based on your vehicle's live data compared against real engineering safety limits.")

            # ── Critical issues ───────────────────────────────────
            if critical:
                st.markdown("#### 🔴 Needs Attention Now")
                for c in critical:
                    st.markdown(f"""
                    <div class="alert-critical">
                        <b>🔴 {c['title']}</b> <span style="color:#8b949e;float:right">{c['category']}</span><br>
                        {c['problem']}<br>
                        <small>Current: <b>{c['value']} {c['unit']}</b> &nbsp;|&nbsp; Normal: <b>{c['normal_range']}</b></small><br>
                        <small>💡 <b>What to do:</b> {c['solution']}</small><br>
                        <small>💰 <b>Estimated Cost:</b> {c['cost']}</small><br>
                        <small>⚠️ <b>If ignored:</b> {c['impact']}</small>
                    </div>""", unsafe_allow_html=True)

            # ── Warnings ───────────────────────────────────────────
            if warning:
                st.markdown("#### 🟡 Worth Keeping an Eye On")
                for c in warning:
                    st.markdown(f"""
                    <div class="alert-warning">
                        <b>🟡 {c['title']}</b> <span style="color:#8b949e;float:right">{c['category']}</span><br>
                        {c['problem']}<br>
                        <small>Current: <b>{c['value']} {c['unit']}</b> &nbsp;|&nbsp; Normal: <b>{c['normal_range']}</b></small><br>
                        <small>💡 <b>What to do:</b> {c['solution']}</small><br>
                        <small>💰 <b>Estimated Cost:</b> {c['cost']}</small><br>
                        <small>ℹ️ <b>If ignored:</b> {c['impact']}</small>
                    </div>""", unsafe_allow_html=True)

            # ── Healthy systems ──────────────────────────────────
            st.markdown("#### ✅ Everything Else Looks Good")
            with st.expander(f"Show all {len(healthy)} systems checked — all normal"):
                # Group by category for readability
                categories = {}
                for c in healthy:
                    categories.setdefault(c['category'], []).append(c)
                for cat, items in categories.items():
                    st.markdown(f"**{cat}**")
                    for c in items:
                        st.markdown(f"""
                        <div class="alert-info">
                            ✅ {c['parameter']}: <b>{c['value']} {c['unit']}</b>
                            <span style="color:#8b949e;float:right">Normal: {c['normal_range']}</span>
                        </div>""", unsafe_allow_html=True)

    # ── AI Diagnostics ──────────────────────────────────────
    elif _view == "AI Diagnostics":
        st.button("⬅️ Back", key="back_diagnostics", on_click=_go_home)
        st.subheader("🤖 AI Vehicle Diagnosis — What-If Simulator")
        st.caption("Enter hypothetical sensor readings to see what ACIP-X1 would say about them. "
                   "This is a sandbox for testing scenarios — it does NOT change your Live Dashboard, "
                   "which always reflects your vehicle's real, current data.")

        col1, col2 = st.columns(2)
        with col1:
            rpm           = st.slider("Motor RPM",                0, 12000, 2500, 100)
            speed         = st.slider("Speed (km/h)",              0, 200,   60,   5)
            coolant_temp  = st.slider("Coolant Temperature (°C)",  0, 120,   35,   1)
        with col2:
            battery_volts = st.slider("Battery Pack Voltage (V)", 260, 420,  380,  5)
            soc           = st.slider("Battery SOC (%)",           0, 100,   80,   5)

        if st.button("🔍 Diagnose Now", type="primary"):
            with st.spinner("AI is analyzing your vehicle..."):
                result = api_post("/api/ai/diagnose", {
                    "vehicle_id":      "VEH001",
                    "rpm":             rpm,
                    "speed":           speed,
                    "coolant_temp":    coolant_temp,
                    "battery_voltage": battery_volts,
                    "soc":             soc
                })
                if result:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        fig = health_gauge(result['health_score'], "Diagnosis Score")
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        st.markdown(f"### Status: **{result['status']}**")
                        st.markdown(f"**Issues Found:** {result['total_issues']}")
                        if result['issues']:
                            for issue in result['issues']:
                                st.markdown(f"""
                                <div class="alert-critical">
                                    🔴 <b>{issue['parameter']}</b>: {issue['message']}<br>
                                    <small>💡 {issue.get('solution', '')}</small>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.success("✅ Vehicle is in good health!")

                        if result['recommendations']:
                            st.markdown("### Recommendations")
                            for rec in result['recommendations']:
                                st.markdown(f"""
                                <div class="alert-info">💡 {rec}</div>
                                """, unsafe_allow_html=True)

    # ── Health Trend ────────────────────────────────────────
    elif _view == "Health Trend":
        st.button("⬅️ Back", key="back_trend", on_click=_go_home)
        st.subheader("📊 Vehicle Health Trend")
        trend = api_get("/api/dashboard/health-trend?limit=20")

        if trend:
            df = pd.DataFrame(trend)
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['health_score'],
                    mode='lines+markers',
                    name='Health Score',
                    line=dict(color='#3fb950', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(63,185,80,0.1)'
                ))
                fig.update_layout(
                    title="Health Score Over Time",
                    xaxis_title="Reading",
                    yaxis_title="Health Score (%)",
                    yaxis_range=[0, 105],
                    paper_bgcolor="#0a0e1a",
                    plot_bgcolor="#161b22",
                    font_color="#e6edf3",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        y=df['rpm'], mode='lines',
                        name='RPM', line=dict(color='#58a6ff')
                    ))
                    fig2.update_layout(
                        title="RPM History",
                        paper_bgcolor="#0a0e1a",
                        plot_bgcolor="#161b22",
                        font_color="#e6edf3",
                        height=250
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                with col2:
                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(
                        y=df['coolant_temp'], mode='lines',
                        name='Coolant Temp', line=dict(color='#f85149')
                    ))
                    fig3.update_layout(
                        title="Coolant Temperature History",
                        paper_bgcolor="#0a0e1a",
                        plot_bgcolor="#161b22",
                        font_color="#e6edf3",
                        height=250
                    )
                    st.plotly_chart(fig3, use_container_width=True)

    # ── Invisible Mechanic (Day 17 — C3 + C7) ────────────────
    elif _view == "Invisible Mechanic":
        st.button("⬅️ Back", key="back_mechanic", on_click=_go_home)
        st.subheader("🔮 Invisible Mechanic")
        st.caption("While Alerts & Issues checks your CURRENT readings, this tracks TRENDS over time to predict what will need attention before it becomes a problem.")

        im = api_get("/api/dashboard/invisible-mechanic")

        if not im or im.get("samples_used", 0) == 0:
            st.info("📡 No telemetry history yet — start the CAN simulator to begin building trend data.")
        else:
            st.caption(f"Based on your last {im['samples_used']} telemetry readings.")

            category_icons = {"Brakes": "🛑", "Battery": "🔋", "Tyres": "🛞"}
            for insight in im["insights"]:
                icon = category_icons.get(insight["category"], "🔧")
                st.markdown(f"""
                <div class="alert-info">
                    <b>{icon} {insight['title']}</b> <span style="color:#8b949e;float:right">{insight['category']}</span><br>
                    {insight['observation']}<br>
                    <small>🔮 <b>Prediction:</b> {insight['prediction']}</small><br>
                    <small>💡 <b>Recommendation:</b> {insight['recommendation']}</small><br>
                    <small style="color:#8b949e">📐 {insight['basis']}</small>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("🚗 Your Driving Score")

            ds = im["driver_score"]
            col1, col2 = st.columns([1, 2])
            with col1:
                fig = health_gauge(ds["score"], "Driver Score")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Driving Style</div>
                    <div class="metric-value" style="color:{ds['style_color']}; font-size:1.4rem">{ds['style']}</div>
                </div>""", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="alert-info" style="margin-top:0.5rem">
                    💡 {ds['tip']}
                </div>""", unsafe_allow_html=True)
                st.caption(
                    f"Based on {ds['samples']} recent readings · "
                    f"{ds['harsh_events']} harsh acceleration/braking events ({ds['harsh_pct']}%) · "
                    f"average energy use {ds['avg_energy_per_100km']} kWh/100km"
                )

    # ── Emergency Response (Day 18 — C4) ─────────────────────
    elif _view == "Emergency":
        st.button("⬅️ Back", key="back_emergency", on_click=_go_home)
        st.subheader("🚨 Accident Detection & Emergency Response")
        st.caption("Every live telemetry sample is checked for a crash-level G-force spike. If detected, emergency contacts are notified and any vehicles within 1km are alerted — all shown below.")

        vehicle_id = "VEH001"

        # ── Demo trigger (since we can't cause a real crash) ──
        with st.expander("🎯 Demo: Simulate a crash to see the response", expanded=False):
            st.caption("This posts one real telemetry sample with a high G-force value through the actual detection code — not a fake record — so you can see the full pipeline run.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚠️ Simulate Moderate Impact (4g)", use_container_width=True):
                    result = api_post(f"/api/emergency/demo-trigger/{vehicle_id}?severity=Moderate", {})
                    if result and result.get("triggered"):
                        st.success(f"Crash detected — {result['severity']} ({result['combined_g']}g). Emergency response triggered.")
                    else:
                        st.warning("Could not trigger — is the server running and has the simulator posted at least one sample?")
                    st.rerun()
            with col2:
                if st.button("🔴 Simulate Severe Impact (7g)", use_container_width=True):
                    result = api_post(f"/api/emergency/demo-trigger/{vehicle_id}?severity=Severe", {})
                    if result and result.get("triggered"):
                        st.success(f"Crash detected — {result['severity']} ({result['combined_g']}g). Emergency response triggered.")
                    else:
                        st.warning("Could not trigger — is the server running and has the simulator posted at least one sample?")
                    st.rerun()

        st.markdown("---")

        # ── Emergency contacts ─────────────────────────────
        st.markdown("#### 📇 Emergency Contacts")
        contacts = api_get(f"/api/emergency/contacts/{vehicle_id}")
        if contacts:
            for c in contacts:
                st.markdown(f"""
                <div class="alert-info">
                    <b>{c['priority']}. {c['name']}</b> <span style="color:#8b949e;float:right">{c['relationship']}</span><br>
                    📞 {c['phone']}
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No emergency contacts configured yet for this vehicle.")

        st.markdown("---")

        # ── Accident history ────────────────────────────────
        st.markdown("#### 📋 Incident History")
        history = api_get(f"/api/emergency/accidents/{vehicle_id}")

        if not history or not history.get("events"):
            st.success("✅ No accidents detected — clean record.")
        else:
            events = history["events"]
            active = [e for e in events if e["status"] != "Resolved" and e["status"] != "False Alarm"]
            if active:
                st.warning(f"⚠️ {len(active)} incident(s) not yet marked resolved.")

            for e in events:
                severity_color = "#f85149" if e["severity"] == "Severe" else "#d29922"
                demo_tag = " <i>(demo)</i>" if e["is_demo"] else ""

                st.markdown(f"""
                <div class="alert-critical" style="border-left-color:{severity_color}">
                    <b>🚨 {e['severity']} Impact{demo_tag}</b>
                    <span style="color:#8b949e;float:right">{e['detected_at']}</span><br>
                    <small>Combined G-force: <b>{e['combined_g_force']}g</b> &nbsp;|&nbsp; Speed at impact: <b>{e['speed_at_impact']:.0f} km/h</b> &nbsp;|&nbsp; Status: <b>{e['status']}</b></small><br>
                    <small>📍 Location: {e['gps_lat']:.5f}, {e['gps_lon']:.5f}</small>
                </div>""", unsafe_allow_html=True)

                with st.expander(f"Response details — Incident #{e['id']}"):
                    if e["contacts_notified"]:
                        st.markdown("**Emergency contacts notified:**")
                        for c in e["contacts_notified"]:
                            st.markdown(f"- {c['name']} ({c['relationship']}) — {c['phone']} via {c['channel']}")
                    else:
                        st.caption("No emergency contacts were configured at the time.")

                    if e["nearby_vehicles_alerted"]:
                        st.markdown("**Nearby alerted (within 1km):**")
                        for v in e["nearby_vehicles_alerted"]:
                            if v.get("type") == "phone":
                                st.markdown(f"- 📱 {v['name']} ({v.get('phone', '')}) — {v['distance_km']} km away")
                            else:
                                st.markdown(f"- 🚗 {v.get('name', v.get('vehicle_id', 'Unknown'))} — {v['distance_km']} km away")
                    else:
                        st.caption("No one else (vehicles or nearby phones) was within 1km at the time.")

                    # Real Twilio SMS (+ WhatsApp fallback) delivery status —
                    # shows exactly what succeeded/failed and why, instead of
                    # leaving failures invisible. This is the actual error
                    # Twilio returned, not a guess.
                    sms_res = e.get("sms_results")
                    if sms_res:
                        st.markdown("**Real message delivery status:**")
                        if not sms_res.get("sms_enabled", True) and not sms_res.get("whatsapp_enabled", False):
                            st.caption(f"SMS and WhatsApp were both disabled in .env, or failed before sending: {sms_res.get('error', '')}")
                        else:
                            sent_sms = sms_res.get('total_sent_via_sms', sms_res.get('total_sent', 0))
                            sent_wa = sms_res.get('total_sent_via_whatsapp', 0)
                            st.caption(f"{sms_res.get('total_sent', 0)} of {sms_res.get('total_attempted', 0)} messages actually delivered ({sent_sms} via SMS, {sent_wa} via WhatsApp fallback).")
                            for r in sms_res.get("results", []):
                                if r["sent"] and r.get("delivered_via") != "whatsapp":
                                    st.markdown(f"- ✅ {r['recipient']} ({r['to']}) — delivered via SMS (SID: {r.get('sid', '')})")
                                elif r.get("delivered_via") == "whatsapp":
                                    st.markdown(f"- ✅ {r['recipient']} ({r['to']}) — SMS failed, but delivered via **WhatsApp fallback** (SID: {r['whatsapp_fallback'].get('sid', '')})")
                                else:
                                    st.markdown(f"- ❌ {r['recipient']} ({r['to']}) — SMS **failed**: {r.get('reason', 'unknown reason')}")
                                    wa_attempt = r.get("whatsapp_fallback")
                                    if wa_attempt:
                                        st.caption(f"  ↳ WhatsApp fallback also failed: {wa_attempt.get('reason', 'unknown reason')}")
                    else:
                        st.caption("No SMS/WhatsApp attempt was recorded for this incident.")

                    if e["status"] not in ("Resolved", "False Alarm"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Mark Resolved", key=f"resolve_{e['id']}"):
                                api_patch(f"/api/emergency/accidents/{e['id']}/resolve?mark_as=Resolved")
                                st.rerun()
                        with col_b:
                            if st.button("🚫 Mark False Alarm", key=f"falsealarm_{e['id']}"):
                                api_patch(f"/api/emergency/accidents/{e['id']}/resolve?mark_as=False Alarm")
                                st.rerun()

    # ── Breakdown AI Assistance (Day 19 / C5) ────────────────
    elif _view == "Breakdown Assist":
        st.button("⬅️ Back", key="back_breakdown", on_click=_go_home)
        st.subheader("🛠️ Breakdown AI Assistance")
        st.caption(
            "Automatically detected when the vehicle stops with an active critical "
            "fault (and isn't simply charging). Diagnoses the cause, guides you "
            "step by step, and connects you with the nearest help — chat with the "
            "AI assistant below for anything specific to your situation."
        )

        breakdown_data = api_get("/api/breakdown/history/VEH001")

        if not breakdown_data or not breakdown_data.get("events"):
            st.info("✅ No breakdowns recorded. The system is watching automatically — nothing to do here.")
        else:
            active_events = [e for e in breakdown_data["events"] if e["status"] == "Active"]
            past_events = [e for e in breakdown_data["events"] if e["status"] != "Active"]

            if active_events:
                st.markdown("#### 🔴 Active Breakdown")
            for e in active_events:
                root_cause = e.get("root_cause")
                title = root_cause["title"] if root_cause else "Breakdown reported — no specific fault identified"
                problem = root_cause["problem"] if root_cause else "No electrical fault was detected; this may be mechanical (e.g. a flat tyre)."

                card_html = (
                    '<div class="breakdown-card">'
                    f'<b>🛑 {title}</b> <span style="color:#8b949e;float:right">{e["trigger"]}</span><br>'
                    f'{problem}'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                with st.expander("📋 Step-by-step guidance", expanded=True):
                    for i, step in enumerate(e["guidance"], 1):
                        st.markdown(f"{i}. {step}")

                with st.expander("📍 Nearest help"):
                    for h in e["nearest_help"]:
                        st.markdown(f"**{h['name']}** ({h['type']}) — {h['distance_km']} km away — 📞 {h['phone']}")

                st.markdown("##### 💬 Talk to the AI Assistant")
                chat_resp = api_get(f"/api/breakdown/chat/{e['id']}")
                conversation = chat_resp["conversation"] if chat_resp else []

                chat_container = st.container()
                with chat_container:
                    for msg in conversation:
                        bubble_class = "chat-bubble-assistant" if msg["role"] == "assistant" else "chat-bubble-user"
                        icon = "🤖" if msg["role"] == "assistant" else "🧑"
                        st.markdown(
                            f'<div class="{bubble_class}">{icon} {msg["content"]}</div>',
                            unsafe_allow_html=True
                        )

                user_input = st.text_input(
                    "Ask the assistant anything about this breakdown",
                    key=f"breakdown_chat_input_{e['id']}",
                    placeholder="e.g. Is it safe to wait here? How much will this cost?"
                )
                if st.button("Send", key=f"breakdown_chat_send_{e['id']}") and user_input:
                    result = api_post(f"/api/breakdown/chat/{e['id']}", {"message": user_input})
                    if result and not result.get("ai_available", True):
                        st.warning("The AI assistant isn't responding right now (check GEMINI_API_KEY in .env) — guidance and nearest help above are still accurate.")
                    st.rerun()

                if st.button("✅ Mark Resolved", key=f"breakdown_resolve_{e['id']}"):
                    api_patch(f"/api/breakdown/resolve/{e['id']}")
                    st.rerun()

            if past_events:
                st.markdown("#### 📜 Past Breakdowns")
                for e in past_events:
                    root_cause = e.get("root_cause")
                    title = root_cause["title"] if root_cause else "Breakdown reported"
                    with st.expander(f"{e['detected_at']} — {title} ({e['status']})"):
                        st.markdown(f"**Trigger:** {e['trigger']}")
                        if root_cause:
                            st.markdown(f"**Diagnosis:** {root_cause['problem']}")
                        st.markdown("**Guidance given:**")
                        for step in e["guidance"]:
                            st.markdown(f"- {step}")

    # ── Unified Voice Assistant (Day 20 — normal chat, ───────
    # ── breakdown assistance, and emergency assistance, all in one) ──
    elif _view == "Talk to Your Car":
        st.button("⬅️ Back", key="back_talk", on_click=_go_home)
        st.subheader("🎙️ Talk to Your Car")
        st.caption(
            "Speak to your car anytime. It's always grounded in what's "
            "actually happening — a casual chat, a breakdown, or an "
            "emergency — so it always knows the real situation. "
            "Note: most browsers block automatic audio until you've "
            "clicked something on the page at least once — so the very "
            "first spoken message of a session may need one click first."
        )

        voice_resp = api_get("/api/personality/voice/VEH001")
        situation_type = voice_resp.get("situation_type", "normal") if voice_resp else "normal"
        conversation = voice_resp["conversation"] if voice_resp else []

        if situation_type == "accident":
            st.markdown(
                '<div style="background:#f8514922;border:2px solid #f85149;border-radius:8px;'
                'padding:14px 18px;margin-bottom:10px;animation:pulse 1.5s infinite;">'
                '<b style="color:#f85149;font-size:1.1em;">🚨 CRASH DETECTED — Emergency contacts are being notified</b>'
                '</div>'
                '<style>@keyframes pulse {0%{opacity:1;}50%{opacity:0.6;}100%{opacity:1;}}</style>',
                unsafe_allow_html=True
            )

        situation_badges = {
            "accident": ("🚨 Emergency — accident detected", "#f85149"),
            "breakdown": ("🛠️ Breakdown in progress", "#d29922"),
            "normal": ("✅ Everything normal", "#3fb950"),
        }
        badge_text, badge_color = situation_badges.get(situation_type, situation_badges["normal"])
        st.markdown(
            f'<span style="background:{badge_color}22;color:{badge_color};'
            f'padding:4px 12px;border-radius:12px;font-size:0.85em;">{badge_text}</span>',
            unsafe_allow_html=True
        )
        st.write("")

        for msg in conversation:
            bubble_class = "chat-bubble-assistant" if msg["role"] == "assistant" else "chat-bubble-user"
            icon = "🚗" if msg["role"] == "assistant" else "🧑"
            st.markdown(
                f'<div class="{bubble_class}">{icon} {msg["content"]}</div>',
                unsafe_allow_html=True
            )

        # Speak the most recent assistant message aloud using the
        # browser's built-in SpeechSynthesis API — no extra packages,
        # no server round-trip needed since this only reads text
        # that's already on the page.
        last_assistant_msg = next(
            (m["content"] for m in reversed(conversation) if m["role"] == "assistant"), None
        )
        if last_assistant_msg:
            safe_text = json.dumps(last_assistant_msg)
            # Keyed by message count so it only speaks once per new
            # reply, not on every rerun/refresh of an unchanged tab.
            components.html(
                f"""
                <script>
                    const text = {safe_text};
                    const msgCount = {len(conversation)};
                    const lastSpoken = window.parent._acipLastSpoken || 0;
                    if (msgCount !== lastSpoken) {{
                        window.parent._acipLastSpoken = msgCount;
                        if ('speechSynthesis' in window.parent) {{
                            const utter = new SpeechSynthesisUtterance(text);
                            utter.rate = 1.0;
                            utter.pitch = 1.0;
                            window.parent.speechSynthesis.cancel();
                            window.parent.speechSynthesis.speak(utter);
                        }}
                    }}
                </script>
                """,
                height=0,
            )

        st.write("")
        st.markdown("**🎤 Press to speak:**")
        spoken_text = speech_to_text(
            language="en",
            start_prompt="🎙️ Start talking",
            stop_prompt="⏹️ Stop",
            just_once=True,
            use_container_width=True,
            key="voice_stt",
        )

        # Also allow typing, for noisy environments or when the
        # owner prefers it — the mic is the primary path, not the
        # only one.
        typed_text = st.text_input(
            "Or type your message",
            key="voice_chat_input",
            placeholder="e.g. Are you okay? How far is help?"
        )

        send_clicked = st.button("Send", key="voice_chat_send")

        message_to_send = None
        if spoken_text:
            message_to_send = spoken_text
        elif send_clicked and typed_text:
            message_to_send = typed_text

        if message_to_send:
            # Real music playback — simple keyword detection (no AI
            # involved in this decision, per explicit preference: fast
            # and reliable over flexible phrasing support). Files live
            # in dashboard/assets/music/ — see MUSIC_TRACKS below.
            _lower_msg = message_to_send.lower()
            if "play" in _lower_msg and ("song" in _lower_msg or "music" in _lower_msg):
                st.session_state.play_song_requested = True

            with st.spinner("🚗 Thinking..."):
                try:
                    r = requests.post(
                        f"{BASE_URL}/api/personality/voice/VEH001",
                        json={"message": message_to_send},
                        timeout=20,
                    )
                    result = r.json() if r.status_code == 200 else None
                except Exception:
                    result = None
            if result is None:
                st.error("No response — the request may have timed out. Try again.")
            elif not result.get("ai_available", True):
                st.warning("AI connection isn't available right now (check GEMINI_API_KEY in .env).")
            st.rerun()

        # Real audio playback, triggered by the keyword match above.
        # Files are royalty-free demo tracks placed in
        # dashboard/assets/music/ — see MUSIC_TRACKS for the list.
        if st.session_state.get("play_song_requested"):
            if MUSIC_TRACKS:
                track = random.choice(MUSIC_TRACKS)
                track_path = os.path.join(MUSIC_DIR, track)
                if os.path.exists(track_path):
                    st.markdown(f"🎵 **Now playing:** {os.path.splitext(track)[0].replace('_', ' ').title()}")
                    st.audio(track_path, autoplay=True)
                else:
                    st.warning(f"Couldn't find {track} in dashboard/assets/music/ — add some royalty-free mp3 files there.")
            else:
                st.info(
                    "I'd play something, but there aren't any music files set up yet. "
                    "Add royalty-free mp3s to `dashboard/assets/music/` "
                    "(e.g. from mixkit.co/free-stock-music — no signup needed) "
                    "and they'll show up here."
                )
            if st.button("⏹️ Stop music", key="stop_music"):
                st.session_state.play_song_requested = False
                st.rerun()

        if st.button("🔄 New conversation", key="voice_chat_reset"):
            api_delete("/api/personality/voice/VEH001")
            st.rerun()

    # ── Resale Value Maximizer + Health Certificate (Day 21 / C9) ──
    elif _view == "Resale Value":
        st.button("⬅️ Back", key="back_resale", on_click=_go_home)
        st.subheader("📈 Resale Value Maximizer")
        st.caption(
            "Your car's real-time resale value, grounded in actual health "
            "data — not a generic depreciation guess."
        )

        resale = api_get("/api/resale/estimate/VEH001")

        if resale and resale.get("needs_base_price"):
            st.info(
                "Enter your vehicle's current market/purchase price once — "
                "we don't have access to live used-car market data, so this "
                "is the one number we need from you. Everything else below "
                "is calculated from your car's real health data."
            )
            base_price_input = st.number_input(
                "Current market value (₹)", min_value=0, step=10000, value=0, key="base_price_input"
            )
            if st.button("Save", key="save_base_price") and base_price_input > 0:
                api_post("/api/resale/base-price/VEH001", {"base_price": int(base_price_input)})
                st.rerun()
        elif resale:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Estimated Value", f"₹{resale['current_estimated_value']:,}")
            with col2:
                st.metric("Value If All Fixed", f"₹{resale['potential_value_if_all_fixed']:,}")
            with col3:
                st.metric("Recoverable", f"₹{resale['total_value_recoverable']:,}")

            st.markdown(f"**Health score:** {resale['health_score']}% ({resale['health_status']})")
            if resale.get("odometer_km"):
                st.markdown(
                    f"**Odometer:** {resale['odometer_km']:,.0f} km "
                    f"(₹{resale['odometer_deduction']:,} wear deduction applied)"
                )

            if resale["fixable_issues"]:
                st.markdown("#### 🔧 Fix these to raise your value")
                for issue in resale["fixable_issues"]:
                    st.markdown(
                        f'<div class="breakdown-card">'
                        f'<b>{issue["parameter"]}</b> — {issue["message"]}<br>'
                        f'Repair cost: ₹{issue["estimated_repair_cost"]:,} → '
                        f'recovers ₹{issue["value_recovered_if_fixed"]:,} in resale value'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("No active issues dragging down your resale value right now.")

            with st.expander("Update base price"):
                new_price = st.number_input(
                    "Current market value (₹)", min_value=0, step=10000,
                    value=resale["base_price"], key="update_base_price_input"
                )
                if st.button("Update", key="update_base_price_btn"):
                    api_post("/api/resale/base-price/VEH001", {"base_price": int(new_price)})
                    st.rerun()

            st.markdown("---")
            st.markdown("#### 📜 AI Health Certificate")
            st.caption("Shareable with a buyer — every figure here traces back to real recorded data.")

            cert = api_get("/api/resale/certificate/VEH001")
            if cert:
                info = cert["vehicle_info"]
                incidents = cert["incident_history"]
                cert_text = (
                    f"ACIP-X1 AI HEALTH CERTIFICATE\n"
                    f"Generated: {cert['generated_at']}\n\n"
                    f"Vehicle: {info.get('manufacturer', 'N/A')} {info.get('model', 'N/A')} ({info.get('year', 'N/A')})\n"
                    f"VIN: {info.get('vin', 'N/A')}\n"
                    f"Odometer: {cert.get('odometer_km', 'N/A')} km\n\n"
                    f"CURRENT HEALTH\n"
                    f"  Score: {cert['current_health']['score']}% ({cert['current_health']['status']})\n"
                    f"  Active issues: {cert['current_health']['active_issues']}\n"
                    f"  Active warnings: {cert['current_health']['active_warnings']}\n\n"
                    f"INCIDENT HISTORY (AI-verified, not seller-reported)\n"
                    f"  Breakdowns: {incidents['total_breakdowns']} total, {incidents['resolved_breakdowns']} resolved\n"
                    f"  Accidents: {incidents['total_accidents']} total, "
                    f"{incidents['severe_accidents']} severe, {incidents['resolved_accidents']} resolved\n\n"
                    f"ESTIMATED RESALE VALUE: ₹{cert['resale_estimate'].get('current_estimated_value', 'N/A'):,}\n"
                )
                st.text_area("Certificate preview", cert_text, height=300, key="cert_preview")
                st.download_button(
                    "⬇️ Download Certificate (.txt)",
                    cert_text,
                    file_name=f"ACIP-X1_Health_Certificate_{cert['vehicle_id']}.txt",
                    key="download_cert"
                )

# ── Auto refresh ──────────────────────────────────────────
# Auto-refresh was removed per user request — manual "🔄 Refresh Now"
# in the sidebar is the only refresh mechanism now.