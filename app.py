import streamlit as st
import pydeck as pdk
import pandas as pd
import json, base64, random

def _style_data_url(style: dict) -> str:
    encoded = base64.b64encode(json.dumps(style).encode()).decode()
    return f"data:application/json;base64,{encoded}"


# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULTS = {
    "sid_map_style":        "Dark",
    "sid_arc_style":        "Arc",
    "sid_min_width":        1.0,
    "sid_max_width":        8.0,
    "sid_opacity":          0.8,
    "sid_src_hex":          "#7DD3FC",
    "sid_tgt_hex":          "#0284C7",
    "sid_show_nodes":       True,
    "sid_node_hex":         "#3DBF1E",
    "sid_node_opacity":     0.9,
    "sid_node_radius":      2.0,
    "sid_show_countries":   False,
    "sid_country_hex":      "#4A5568",
    "sid_country_opacity":  0.5,
    "sid_show_sea":         False,
    "sid_sea_hex":          "#1a3a5c",
    "sid_sea_opacity":      1.0,
}

for _k, _v in DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _random_hex() -> str:
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def _randomize():
    st.session_state["sid_arc_style"]       = random.choice(ARC_STYLES)
    mn = round(random.uniform(0.1, 2.0), 1)
    mx = round(random.uniform(max(mn, 1.0), 20.0), 1)
    st.session_state["sid_min_width"]       = mn
    st.session_state["sid_max_width"]       = mx
    st.session_state["sid_opacity"]         = round(random.uniform(0.1, 1.0), 2)
    st.session_state["sid_src_hex"]         = _random_hex()
    st.session_state["sid_tgt_hex"]         = _random_hex()
    st.session_state["sid_show_nodes"]      = random.choice([True, False])
    st.session_state["sid_node_hex"]        = _random_hex()
    st.session_state["sid_node_opacity"]    = round(random.uniform(0.2, 1.0), 2)
    st.session_state["sid_node_radius"]     = round(random.uniform(0.5, 5.0), 1)
    st.session_state["sid_show_countries"]  = random.choice([True, False])
    st.session_state["sid_country_hex"]     = _random_hex()
    st.session_state["sid_country_opacity"] = round(random.uniform(0.1, 0.9), 2)
    st.session_state["sid_show_sea"]        = random.choice([True, False])
    st.session_state["sid_sea_hex"]         = _random_hex()
    st.session_state["sid_sea_opacity"]     = round(random.uniform(0.2, 1.0), 2)


def _reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


@st.cache_data
def _fetch_and_patch_style(base_url: str, remove_borders: bool, sea_hex: str | None, sea_opacity: float = 1.0) -> str:
    import urllib.request
    try:
        with urllib.request.urlopen(base_url, timeout=10) as resp:
            style = json.loads(resp.read())
    except Exception:
        return base_url

    if remove_borders:
        style["layers"] = [
            layer for layer in style["layers"]
            if not any(kw in layer.get("id", "").lower()
                       for kw in ("admin", "boundary", "border"))
        ]

    if sea_hex:
        r = int(sea_hex[1:3], 16)
        g = int(sea_hex[3:5], 16)
        b = int(sea_hex[5:7], 16)
        rgba = f"rgba({r},{g},{b},{sea_opacity})"
        for layer in style.get("layers", []):
            lid   = layer.get("id", "").lower()
            ltype = layer.get("type", "")
            if any(kw in lid for kw in ("water", "ocean", "sea", "lake", "river")):
                paint = layer.setdefault("paint", {})
                if ltype == "fill":
                    paint["fill-color"] = rgba
                elif ltype == "line":
                    paint["line-color"] = rgba

    return _style_data_url(style)


COUNTRY_COORDS = {
    "AF": (33.94, 67.71), "AL": (41.15, 20.17), "DZ": (28.03, 1.66),
    "AO": (-11.20, 17.87), "AR": (-38.42, -63.62), "AM": (40.07, 45.04),
    "AU": (-25.27, 133.78), "AT": (47.52, 14.55), "AZ": (40.14, 47.58),
    "BH": (25.93, 50.64), "BD": (23.68, 90.36), "BY": (53.71, 27.95),
    "BE": (50.50, 4.47), "BJ": (9.31, 2.32), "BT": (27.51, 90.43),
    "BO": (-16.29, -63.59), "BA": (43.92, 17.68), "BW": (-22.33, 24.68),
    "BR": (-14.24, -51.93), "BN": (4.54, 114.73), "BG": (42.73, 25.49),
    "BF": (12.36, -1.56), "BI": (-3.37, 29.92), "KH": (12.57, 104.99),
    "CM": (3.85, 11.50), "CA": (56.13, -106.35), "CF": (6.61, 20.94),
    "CG": (-0.23, 15.83), "TD": (15.45, 18.73), "CL": (-35.68, -71.54), "CN": (35.86, 104.20),
    "CO": (4.57, -74.30), "CD": (-4.04, 21.76), "CR": (9.75, -83.75),
    "CI": (7.54, -5.55), "HR": (45.10, 15.20), "CU": (21.52, -77.78),
    "CY": (35.13, 33.43), "CZ": (49.82, 15.47), "DK": (56.26, 9.50),
    "DJ": (11.83, 42.59), "DM": (15.41, -61.37), "DO": (18.74, -70.16), "EC": (-1.83, -78.18),
    "EG": (26.82, 30.80), "SV": (13.79, -88.90), "ER": (15.18, 39.78),
    "EE": (58.60, 25.01), "ET": (9.15, 40.49), "FI": (61.92, 25.75), "FO": (62.00, -6.79),
    "FR": (46.23, 2.21), "GA": (-0.80, 11.61), "GM": (13.44, -15.31),
    "GE": (42.32, 43.36), "DE": (51.17, 10.45), "GH": (7.95, -1.02),
    "GR": (39.07, 21.82), "GT": (15.78, -90.23), "GN": (9.95, -9.70),
    "GW": (11.80, -15.18), "GY": (4.86, -58.93), "HT": (18.97, -72.29),
    "HN": (15.20, -86.24), "HK": (22.40, 114.11), "HU": (47.16, 19.50),
    "IS": (64.96, -19.02), "IN": (20.59, 78.96), "ID": (-0.79, 113.92),
    "IR": (32.43, 53.69), "IQ": (33.22, 43.68), "IE": (53.41, -8.24),
    "IL": (31.05, 34.85), "IT": (41.87, 12.57), "JM": (18.11, -77.30),
    "JP": (36.20, 138.25), "JO": (30.59, 36.24), "KZ": (48.02, 66.92),
    "KE": (-0.02, 37.91), "KP": (40.34, 127.51), "KR": (35.91, 127.77), "KW": (29.31, 47.48),
    "KG": (41.20, 74.77), "LA": (19.86, 102.50), "LV": (56.88, 24.60),
    "LB": (33.85, 35.86), "LY": (26.34, 17.23), "LT": (55.17, 23.88),
    "LU": (49.82, 6.13), "MK": (41.61, 21.75), "MG": (-18.77, 46.87),
    "MW": (-13.25, 34.30), "MY": (4.21, 101.98), "MV": (3.20, 73.22),
    "ML": (17.57, -3.996), "MT": (35.94, 14.38), "MR": (21.01, -10.94),
    "MU": (-20.35, 57.55), "MX": (23.63, -102.55), "MD": (47.41, 28.37),
    "MN": (46.86, 103.85), "ME": (42.71, 19.37), "MA": (31.79, -7.09),
    "MZ": (-18.67, 35.53), "MM": (21.91, 95.96), "NA": (-22.96, 18.49),
    "NP": (28.39, 84.12), "NL": (52.13, 5.29), "NZ": (-40.90, 174.89),
    "NI": (12.87, -85.21), "NE": (17.61, 8.08), "NG": (9.08, 8.68),
    "NO": (60.47, 8.47), "OM": (21.51, 55.92), "PK": (30.38, 69.35),
    "PA": (8.54, -80.78), "PY": (-23.44, -58.44), "PE": (-9.19, -75.02),
    "PH": (12.88, 121.77), "PL": (51.92, 19.15), "PT": (39.40, -8.22),
    "QA": (25.35, 51.18), "RO": (45.94, 24.97), "RU": (55.75, 37.62),
    "RW": (-1.94, 29.87), "SA": (23.89, 45.08), "SN": (14.50, -14.45),
    "RS": (44.02, 21.01), "SL": (8.46, -11.78), "SG": (1.35, 103.82),
    "SK": (48.67, 19.70), "SI": (46.15, 14.99), "SO": (5.15, 46.20),
    "ZA": (-30.56, 22.94), "SS": (4.85, 31.57), "ES": (40.46, -3.75),
    "LK": (7.87, 80.77), "SD": (12.86, 30.22), "SE": (60.13, 18.64),
    "CH": (46.82, 8.23), "SY": (34.80, 38.997), "TW": (23.70, 120.96),
    "TJ": (38.86, 71.28), "TZ": (-6.37, 34.89), "TH": (15.87, 100.99),
    "TL": (-8.87, 125.73), "TG": (8.62, 0.82), "TT": (10.69, -61.22),
    "TN": (33.89, 9.54), "TR": (38.96, 35.24), "TM": (38.97, 59.56),
    "UG": (1.37, 32.29), "UA": (48.38, 31.17), "AE": (23.42, 53.85),
    "GB": (55.38, -3.44), "UM": (19.28, 166.65), "US": (37.09, -95.71), "USA": (37.09, -95.71), "UY": (-32.52, -55.77),
    "UZ": (41.38, 64.59), "VE": (6.42, -66.59), "VN": (14.06, 108.28),
    "YE": (15.55, 48.52), "ZM": (-13.13, 27.85), "ZW": (-19.02, 29.15),
}

# Base URLs — never modified; _fetch_and_patch_style patches on-the-fly
_MAP_BASE_URLS = {
    "Dark":              "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Dark (No Labels)":  "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
    "Dark (No Borders)": "https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
    "Light":             "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Light (No Labels)": "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json",
    "Satellite":         "mapbox://styles/mapbox/satellite-v9",
}

MAP_STYLES = list(_MAP_BASE_URLS.keys())

ARC_STYLES = ["Arc", "Flat Arc", "Great Circle", "Straight Line", "Arrow", "Bidirectional"]

COUNTRIES_GEOJSON_URL = (
    "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
)


def hex_to_rgba(hex_color: str, alpha: int) -> list[int]:
    h = hex_color.lstrip("#")
    return [int(h[i:i+2], 16) for i in (0, 2, 4)] + [alpha]


def resolve_map_style(style_name: str, show_sea: bool, sea_hex: str, sea_opacity: float) -> str:
    base_url = _MAP_BASE_URLS[style_name]
    if style_name == "Satellite":
        return base_url
    remove_borders = style_name == "Dark (No Borders)"
    sea = sea_hex if show_sea else None
    return _fetch_and_patch_style(base_url, remove_borders, sea, sea_opacity if show_sea else 1.0)


@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.upper()

    bad_origin_mask    = ~df["ORIGIN"].isin(COUNTRY_COORDS)
    bad_delivery_mask  = ~df["DELIVERY"].isin(COUNTRY_COORDS)
    bad_mask           = bad_origin_mask | bad_delivery_mask
    bad_df             = df[bad_mask][["ORIGIN", "DELIVERY", "COUNT"]].copy()

    bad_origin_codes   = sorted(set(df.loc[bad_origin_mask,   "ORIGIN"]))
    bad_delivery_codes = sorted(set(df.loc[bad_delivery_mask, "DELIVERY"]))

    df = df[~bad_mask].copy()
    df["src_lon"] = df["ORIGIN"].map(lambda c: COUNTRY_COORDS[c][1])
    df["src_lat"] = df["ORIGIN"].map(lambda c: COUNTRY_COORDS[c][0])
    df["tgt_lon"] = df["DELIVERY"].map(lambda c: COUNTRY_COORDS[c][1])
    df["tgt_lat"] = df["DELIVERY"].map(lambda c: COUNTRY_COORDS[c][0])

    return df, bad_df, bad_origin_codes, bad_delivery_codes


# ── Page setup ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Global Shipping Flows", layout="wide")
st.title("Global Shipping Flows")

tab_main, tab_map, tab_data = st.tabs(["Main", "Map", "Data"])

# ── Main tab ────────────────────────────────────────────────────────────────
with tab_main:
    st.markdown(
        "Visualise shipping routes on a world map. "
        "Upload a CSV with **ORIGIN**, **DELIVERY**, and **COUNT** columns "
        "(2-letter ISO country codes, case-insensitive), then open the **Map** tab."
    )
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        st.success("File uploaded — open the **Map** tab to view results.")

# ── Load & validate data ────────────────────────────────────────────────────
df = bad_df = None
bad_origin_codes = bad_delivery_codes = []

if uploaded_file is not None:
    df, bad_df, bad_origin_codes, bad_delivery_codes = load_data(uploaded_file)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.subheader("Map")
map_style_name = st.sidebar.selectbox("Map Style", MAP_STYLES, key="sid_map_style")
arc_style      = st.sidebar.selectbox("Arc Style", ARC_STYLES, key="sid_arc_style")

if map_style_name == "Satellite":
    st.sidebar.caption("Requires a Mapbox token via `pdk.settings.mapbox_key`.")

st.sidebar.divider()
st.sidebar.subheader("Arc Appearance")
min_width = st.sidebar.slider("Min Line Width", min_value=0.1, max_value=2.0,  step=0.1, key="sid_min_width")
max_width = st.sidebar.slider("Max Line Width", min_value=1.0, max_value=20.0, step=0.5, key="sid_max_width")
if max_width < min_width:
    max_width = min_width
opacity   = st.sidebar.slider("Arc Opacity",    min_value=0.0, max_value=1.0,  step=0.01, key="sid_opacity")
src_hex   = st.sidebar.color_picker("Arc Start Color", key="sid_src_hex")
tgt_hex   = st.sidebar.color_picker("Arc End Color",   key="sid_tgt_hex")

st.sidebar.divider()
st.sidebar.subheader("Node Markers")
show_nodes   = st.sidebar.checkbox("Show location nodes", key="sid_show_nodes")
node_hex     = st.sidebar.color_picker("Node Color",    key="sid_node_hex")
node_opacity = st.sidebar.slider("Node Opacity",  0.0, 1.0, step=0.01, key="sid_node_opacity")
node_radius  = st.sidebar.slider("Node Radius (px)", min_value=0.1, max_value=5.0, step=0.1, key="sid_node_radius")

st.sidebar.divider()
st.sidebar.subheader("Colors")
show_countries   = st.sidebar.checkbox("Color countries", key="sid_show_countries")
country_hex      = st.sidebar.color_picker("Country Color",   key="sid_country_hex")
country_opacity  = st.sidebar.slider("Country Opacity", 0.0, 1.0, step=0.01, key="sid_country_opacity")
show_sea = st.sidebar.checkbox("Color sea", key="sid_show_sea")
sea_hex  = st.sidebar.color_picker("Sea Color", key="sid_sea_hex")
sea_opacity = st.sidebar.slider("Sea Opacity", 0.0, 1.0, step=0.01, key="sid_sea_opacity")
if show_sea and map_style_name == "Satellite":
    st.sidebar.caption("Sea coloring is not available for the Satellite style.")

st.sidebar.divider()
col_rand, col_reset = st.sidebar.columns(2)
col_rand.button("Randomize", on_click=_randomize, use_container_width=True)
col_reset.button("Reset",     on_click=_reset,     use_container_width=True)

# ── Map tab ──────────────────────────────────────────────────────────────────
with tab_map:
    if df is None:
        st.info("Upload a CSV file on the **Main** tab to see the map.")
    elif df.empty:
        st.error("No valid rows remaining after filtering. Check your ISO codes.")
    else:
        if not bad_df.empty:
            lines = [f"**{len(bad_df)} row(s) skipped** due to unrecognised ISO codes:"]
            if bad_origin_codes:
                lines.append(f"- Unknown **ORIGIN** codes: `{'`, `'.join(bad_origin_codes)}`")
            if bad_delivery_codes:
                lines.append(f"- Unknown **DELIVERY** codes: `{'`, `'.join(bad_delivery_codes)}`")
            with st.expander("⚠️ " + lines[0] + " — click to expand"):
                for line in lines[1:]:
                    st.markdown(line)
                st.dataframe(bad_df, use_container_width=True)

        df_view = df.copy()

        alpha     = int(opacity * 255)
        src_color = hex_to_rgba(src_hex, alpha)
        tgt_color = hex_to_rgba(tgt_hex, alpha)

        max_count   = df_view["COUNT"].max()
        min_count_v = df_view["COUNT"].min()
        count_range = max_count - min_count_v
        if count_range == 0:
            df_view["arc_width"] = (min_width + max_width) / 2
        else:
            df_view["arc_width"] = min_width + (df_view["COUNT"] - min_count_v) / count_range * (max_width - min_width)

        layers = []

        # Country fill layer (rendered first, below everything else)
        if show_countries:
            country_color = hex_to_rgba(country_hex, int(country_opacity * 255))
            layers.append(pdk.Layer(
                "GeoJsonLayer",
                data=COUNTRIES_GEOJSON_URL,
                filled=True,
                stroked=False,
                get_fill_color=country_color,
                pickable=False,
            ))

        if show_nodes:
            node_color   = hex_to_rgba(node_hex, int(node_opacity * 255))
            active_codes = set(df_view["ORIGIN"]) | set(df_view["DELIVERY"])
            node_data    = [
                {"lon": COUNTRY_COORDS[c][1], "lat": COUNTRY_COORDS[c][0]}
                for c in active_codes if c in COUNTRY_COORDS
            ]
            layers.append(pdk.Layer(
                "ScatterplotLayer", data=node_data,
                get_position=["lon", "lat"], get_radius=1,
                radius_min_pixels=node_radius, radius_max_pixels=node_radius,
                get_fill_color=node_color, pickable=False, stroked=False,
            ))

        if arc_style == "Arc":
            layers.append(pdk.Layer(
                "ArcLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width", get_tilt=15,
                get_source_color=src_color, get_target_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))

        elif arc_style == "Flat Arc":
            layers.append(pdk.Layer(
                "ArcLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width", get_tilt=0,
                get_source_color=src_color, get_target_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))

        elif arc_style == "Great Circle":
            layers.append(pdk.Layer(
                "GreatCircleLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width",
                get_source_color=src_color, get_target_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))

        elif arc_style == "Straight Line":
            layers.append(pdk.Layer(
                "LineLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width",
                get_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))

        elif arc_style == "Arrow":
            layers.append(pdk.Layer(
                "ArcLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width", get_tilt=10,
                get_source_color=src_color, get_target_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))
            layers.append(pdk.Layer(
                "ScatterplotLayer", data=df_view,
                get_position=["tgt_lon", "tgt_lat"],
                get_radius=80000,
                get_fill_color=tgt_color,
                pickable=False, stroked=False,
            ))

        elif arc_style == "Bidirectional":
            layers.append(pdk.Layer(
                "ArcLayer", data=df_view,
                get_source_position=["src_lon", "src_lat"],
                get_target_position=["tgt_lon", "tgt_lat"],
                get_width="arc_width", get_tilt=15,
                get_source_color=src_color, get_target_color=tgt_color,
                pickable=True, auto_highlight=True,
            ))
            layers.append(pdk.Layer(
                "ArcLayer", data=df_view,
                get_source_position=["tgt_lon", "tgt_lat"],
                get_target_position=["src_lon", "src_lat"],
                get_width="arc_width", get_tilt=-15,
                get_source_color=tgt_color, get_target_color=src_color,
                pickable=True, auto_highlight=True,
            ))

        zoom_current = st.session_state.get("map_zoom", 1.5)

        active_map_style = resolve_map_style(map_style_name, show_sea, sea_hex, sea_opacity)

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(
                latitude=20.0, longitude=10.0,
                zoom=zoom_current, pitch=0, bearing=0,
            ),
            map_style=active_map_style,
            tooltip={"text": "{ORIGIN} → {DELIVERY}\nShipments: {COUNT}"},
            views=[pdk.View(type="MapView", controller=True)],
        )

        st.markdown("""
        <style>
        section[data-testid="stMain"] .element-container:has([data-testid="stSlider"]) {
            position: relative;
            margin-top: -52px;
            z-index: 1000;
            display: flex;
            justify-content: flex-end;
            padding-right: 16px;
        }
        section[data-testid="stMain"] [data-testid="stSlider"] {
            width: 260px;
            background: rgba(15, 15, 15, 0.65);
            border-radius: 8px;
            padding: 6px 12px 2px;
            backdrop-filter: blur(4px);
        }
        </style>
        """, unsafe_allow_html=True)

        st.pydeck_chart(deck, use_container_width=True, height=900)
        st.slider(
            "Zoom", min_value=1.0, max_value=2.0,
            value=zoom_current, step=0.01,
            key="map_zoom", label_visibility="collapsed",
        )

# ── Data tab ─────────────────────────────────────────────────────────────────
with tab_data:
    if df is None:
        st.info("Upload a CSV file on the **Main** tab to see the data.")
    elif df.empty:
        st.error("No valid rows remaining after filtering. Check your ISO codes.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Routes",      len(df))
        col2.metric("Total count", int(df["COUNT"].sum()))
        col3.metric("Max count",   int(df["COUNT"].max()))
        st.dataframe(
            df[["ORIGIN", "DELIVERY", "COUNT"]].sort_values("COUNT", ascending=False),
            use_container_width=True,
        )
