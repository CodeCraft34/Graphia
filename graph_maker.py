import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import io

# Page config 
st.set_page_config(
    page_title="Graphia",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Minimal professional css
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #f7f7f7; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stMultiSelect label { font-size: 0.82rem; font-weight: 600; color: #222; }
    h1 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.5px; color: #111; }
    h3 { font-size: 1rem; font-weight: 600; color: #333; margin-top: 0.2rem; }
    .block-container { padding-top: 2rem; }
    hr { margin: 0.6rem 0; border: none; border-top: 1px solid #ddd; }
    .stButton > button { background: #111; color: #fff; border: none;
        border-radius: 4px; padding: 0.45rem 1.2rem; font-size: 0.85rem;
        font-weight: 600; cursor: pointer; }
    .stButton > button:hover { background: #333; }
    .stDownloadButton > button { background: #1a6f3c; color: #fff; border: none;
        border-radius: 4px; padding: 0.45rem 1.2rem; font-size: 0.85rem; font-weight: 600; }
    .stDownloadButton > button:hover { background: #145530; }
</style>
""", unsafe_allow_html=True)

# Helpers
MARKERS   = ["None", "o", "s", "^", "D", "x", "+", "*", "v", "p", "h"]
LINESTYLES = ["solid", "dashed", "dotted", "dashdot", "None"]
COLORMAPS  = ["tab10", "Set1", "Set2", "Dark2", "Paired", "Accent"]

def parse_series(text):
    """Parse comma-separated numbers from text input."""
    try:
        return [float(v.strip()) for v in text.split(",") if v.strip()]
    except:
        return []

def apply_common(ax, xlabel, ylabel, title, grid, legend):
    if title:   ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
    if xlabel:  ax.set_xlabel(xlabel, fontsize=9)
    if ylabel:  ax.set_ylabel(ylabel, fontsize=9)
    if grid:    ax.grid(True, linestyle='--', alpha=0.5, linewidth=0.7)
    else:       ax.grid(False)
    if legend:  ax.legend(fontsize=8, framealpha=0.9)
    ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)
        spine.set_color('#aaa')

def fig_to_bytes(fig, fmt, dpi):
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    return buf.read()

def color_cycle(cmap_name, n):
    cmap = plt.get_cmap(cmap_name)
    return [cmap(i / max(n - 1, 1)) for i in range(n)]

# Sidebar
with st.sidebar:
    st.markdown("# Graphia")
    st.markdown("Make quality graphs with Mathplotlib.")
    st.markdown("<hr>", unsafe_allow_html=True)

    # -- Data source
    st.markdown("**Data Source**")
    data_source = st.radio("", ["Manual Entry", "Upload CSV"], label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    df_csv = None
    if data_source == "Upload CSV":
        uploaded = st.file_uploader("CSV File", type=["csv"])
        if uploaded:
            df_csv = pd.read_csv(uploaded)
            st.success(f"{df_csv.shape[0]} rows, {df_csv.shape[1]} cols")
        st.markdown("<hr>", unsafe_allow_html=True)

    # -- Chart type
    st.markdown("**Chart Type**")
    chart_type = st.selectbox("", [
        "Line", "Scatter", "Bar", "Histogram",
        "Pie", "Multiple Lines", "Subplot Grid"
    ], label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    # -- Style
    st.markdown("**Style**")
    color_map   = st.selectbox("Color palette", COLORMAPS)
    mpl_style   = st.selectbox("Theme", ["default", "seaborn-v0_8-whitegrid", "ggplot", "bmh", "fivethirtyeight", "dark_background"])
    fig_w       = st.slider("Figure width",  4, 16, 9)
    fig_h       = st.slider("Figure height", 3, 12, 5)
    dpi         = st.selectbox("DPI", [100, 150, 200, 300], index=1)
    st.markdown("<hr>", unsafe_allow_html=True)

    # -- Labels / decorations
    st.markdown("**Labels & Decorations**")
    fig_title = st.text_input("Figure title", "")
    x_label   = st.text_input("X-axis label", "X")
    y_label   = st.text_input("Y-axis label", "Y")
    show_grid   = st.checkbox("Grid", value=True)
    show_legend = st.checkbox("Legend", value=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # -- Download
    st.markdown("**Export**")
    dl_fmt = st.selectbox("Format", ["png", "pdf", "svg", "jpeg"])

#Main area
st.markdown(f"## {chart_type} Graph")

# Helper column selector for CSV
def col_select(label, df, default_idx=0):
    cols = list(df.columns)
    return st.selectbox(label, cols, index=min(default_idx, len(cols)-1))

# ── Per chart configuration + plotting 
cfg_col, preview_col = st.columns([1, 2], gap="large")

with cfg_col:
    st.markdown("### Configuration")

    # Line
    if chart_type == "Line":
        if df_csv is not None:
            xc = col_select("X column", df_csv, 0)
            yc = col_select("Y column", df_csv, 1)
        else:
            x_raw = st.text_input("X values (comma-separated)", "1,2,3,4,5")
            y_raw = st.text_input("Y values (comma-separated)", "2,4,1,5,3")
        lbl   = st.text_input("Series label", "Series 1")
        ls    = st.selectbox("Line style", LINESTYLES)
        mk    = st.selectbox("Marker", MARKERS)
        lw    = st.slider("Line width", 0.5, 5.0, 1.5, 0.5)
        color = st.color_picker("Color", "#1a6f3c")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        x_vals = df_csv[xc].values
                        y_vals = df_csv[yc].values
                    else:
                        x_vals = parse_series(x_raw)
                        y_vals = parse_series(y_raw)
                    ax.plot(x_vals, y_vals,
                            label=lbl,
                            linestyle=ls if ls != "None" else "None",
                            marker=mk if mk != "None" else None,
                            linewidth=lw, color=color)
                    apply_common(ax, x_label, y_label, fig_title or "Line Graph", show_grid, show_legend)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"line_graph.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # SCATTER 
    elif chart_type == "Scatter":
        if df_csv is not None:
            xc = col_select("X column", df_csv, 0)
            yc = col_select("Y column", df_csv, 1)
            size_c = st.selectbox("Size column (optional)", ["None"] + list(df_csv.columns))
        else:
            x_raw = st.text_input("X values", "1,2,3,4,5,6,7")
            y_raw = st.text_input("Y values", "3,1,4,1,5,9,2")
        lbl   = st.text_input("Series label", "Points")
        mk    = st.selectbox("Marker", [m for m in MARKERS if m != "None"], index=0)
        pt_sz = st.slider("Point size", 10, 200, 50)
        alpha = st.slider("Opacity", 0.1, 1.0, 0.8, 0.05)
        color = st.color_picker("Color", "#1a4fa0")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        x_vals = df_csv[xc].values
                        y_vals = df_csv[yc].values
                        sz = df_csv[size_c].values if size_c != "None" else pt_sz
                    else:
                        x_vals = parse_series(x_raw)
                        y_vals = parse_series(y_raw)
                        sz = pt_sz
                    ax.scatter(x_vals, y_vals, label=lbl, marker=mk,
                               s=sz, alpha=alpha, color=color, edgecolors='white', linewidths=0.5)
                    apply_common(ax, x_label, y_label, fig_title or "Scatter Plot", show_grid, show_legend)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"scatter.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # BAR 
    elif chart_type == "Bar":
        if df_csv is not None:
            xc = col_select("Category column", df_csv, 0)
            yc = col_select("Value column", df_csv, 1)
        else:
            x_raw = st.text_input("Categories (comma-separated)", "A,B,C,D,E")
            y_raw = st.text_input("Values (comma-separated)", "5,3,8,4,7")
        orientation = st.radio("Orientation", ["Vertical", "Horizontal"])
        bar_w = st.slider("Bar width", 0.2, 1.0, 0.6, 0.05)
        edge  = st.checkbox("Edge color", value=True)
        color = st.color_picker("Color", "#2c5f8a")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        cats   = df_csv[xc].astype(str).tolist()
                        vals   = df_csv[yc].values
                    else:
                        cats = [v.strip() for v in x_raw.split(",")]
                        vals = parse_series(y_raw)
                    ec = '#222' if edge else 'none'
                    if orientation == "Vertical":
                        ax.bar(cats, vals, width=bar_w, color=color, edgecolor=ec, linewidth=0.7)
                    else:
                        ax.barh(cats, vals, height=bar_w, color=color, edgecolor=ec, linewidth=0.7)
                    apply_common(ax, x_label, y_label, fig_title or "Bar Chart", show_grid, show_legend)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"bar_chart.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # ── HISTOGRAM ───────────────────────────────────────────────────────────
    elif chart_type == "Histogram":
        if df_csv is not None:
            yc = col_select("Data column", df_csv, 0)
        else:
            y_raw = st.text_input("Data values (comma-separated)",
                                   "1,2,2,3,3,3,4,4,4,4,5,5,5,6,7,8,9,9,10")
        bins  = st.slider("Number of bins", 5, 100, 20)
        kde   = st.checkbox("Density (normalize)", value=False)
        edge  = st.checkbox("Edge color", value=True)
        color = st.color_picker("Bar color", "#8a2c2c")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        vals = df_csv[yc].dropna().values
                    else:
                        vals = np.array(parse_series(y_raw))
                    ec = '#111' if edge else 'none'
                    ax.hist(vals, bins=bins, density=kde, color=color,
                            edgecolor=ec, linewidth=0.6, label="Distribution")
                    if kde:
                        ax.set_ylabel("Density")
                    apply_common(ax, x_label, y_label, fig_title or "Histogram", show_grid, show_legend)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"histogram.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # Pie
    elif chart_type == "Pie":
        if df_csv is not None:
            label_c = col_select("Labels column", df_csv, 0)
            val_c   = col_select("Values column", df_csv, 1)
        else:
            x_raw = st.text_input("Labels (comma-separated)", "Alpha,Beta,Gamma,Delta,Epsilon")
            y_raw = st.text_input("Values (comma-separated)", "30,20,25,15,10")
        donut    = st.checkbox("Donut style", value=False)
        pct_fmt  = st.selectbox("Percentage format", ["%.1f%%", "%.0f%%", "None"])
        explode_all = st.slider("Explode slices", 0.0, 0.2, 0.0, 0.01)
        start_angle = st.slider("Start angle", 0, 360, 90)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        labels = df_csv[label_c].astype(str).tolist()
                        vals   = df_csv[val_c].values
                    else:
                        labels = [v.strip() for v in x_raw.split(",")]
                        vals   = np.array(parse_series(y_raw))
                    explode = [explode_all] * len(vals)
                    colors  = color_cycle(color_map, len(vals))
                    autopct = None if pct_fmt == "None" else pct_fmt
                    wedges, texts, autotexts = ax.pie(
                        vals, labels=labels, explode=explode,
                        colors=colors, autopct=autopct,
                        startangle=start_angle, pctdistance=0.82,
                        wedgeprops={'linewidth': 0.8, 'edgecolor': 'white'}
                    ) if autopct else (ax.pie(
                        vals, labels=labels, explode=explode,
                        colors=colors, startangle=start_angle,
                        wedgeprops={'linewidth': 0.8, 'edgecolor': 'white'}
                    ) + ([],))
                    if autotexts:
                        for t in autotexts:
                            t.set_fontsize(8)
                    if donut:
                        centre = plt.Circle((0, 0), 0.55, color='white')
                        ax.add_patch(centre)
                    if fig_title:
                        ax.set_title(fig_title, fontsize=11, fontweight='bold', pad=8)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"pie_chart.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # MULTIPLE LINES 
    elif chart_type == "Multiple Lines":
        n_lines = st.number_input("Number of series", 2, 8, 3, 1)
        if df_csv is not None:
            xc = col_select("X column", df_csv, 0)
            y_cols = st.multiselect("Y columns", list(df_csv.columns), default=list(df_csv.columns)[1:n_lines+1])
        else:
            x_raw = st.text_input("X values (shared)", "1,2,3,4,5,6")
            series_inputs = []
            for i in range(n_lines):
                s = st.text_input(f"Series {i+1} values", f"{np.random.randint(1,9)},{np.random.randint(1,9)},{np.random.randint(1,9)},{np.random.randint(1,9)},{np.random.randint(1,9)},{np.random.randint(1,9)}", key=f"ml_{i}")
                lname = st.text_input(f"Series {i+1} label", f"Series {i+1}", key=f"ml_lbl_{i}")
                series_inputs.append((s, lname))
        ls  = st.selectbox("Line style", LINESTYLES)
        mk  = st.selectbox("Marker", MARKERS)
        lw  = st.slider("Line width", 0.5, 5.0, 1.5, 0.5)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    colors = color_cycle(color_map, n_lines)
                    if df_csv is not None:
                        x_vals = df_csv[xc].values
                        for j, yc in enumerate(y_cols):
                            ax.plot(x_vals, df_csv[yc].values,
                                    label=yc, color=colors[j],
                                    linestyle=ls if ls != "None" else "None",
                                    marker=mk if mk != "None" else None,
                                    linewidth=lw)
                    else:
                        x_vals = parse_series(x_raw)
                        for j, (s, lname) in enumerate(series_inputs):
                            ax.plot(x_vals, parse_series(s),
                                    label=lname, color=colors[j],
                                    linestyle=ls if ls != "None" else "None",
                                    marker=mk if mk != "None" else None,
                                    linewidth=lw)
                    apply_common(ax, x_label, y_label, fig_title or "Multiple Lines", show_grid, show_legend)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"multi_line.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

    # SUBPLOT GRID 
    elif chart_type == "Subplot Grid":
        n_rows = st.number_input("Rows", 1, 4, 2, 1)
        n_cols = st.number_input("Columns", 1, 4, 2, 1)
        share_x = st.checkbox("Share X axis", False)
        share_y = st.checkbox("Share Y axis", False)
        n_plots = int(n_rows * n_cols)
        st.markdown(f"**{n_plots} subplot(s) — configure each below:**")
        plot_cfgs = []
        for i in range(n_plots):
            with st.expander(f"Subplot {i+1}", expanded=(i == 0)):
                ptype = st.selectbox("Type", ["Line", "Bar", "Scatter", "Histogram"], key=f"sp_t_{i}")
                if df_csv is not None:
                    xc_s = col_select("X column", df_csv, 0)
                    yc_s = col_select("Y column", df_csv, 1)
                    plot_cfgs.append({"type": ptype, "xc": xc_s, "yc": yc_s,
                                      "label": f"Plot {i+1}", "color": "#333"})
                else:
                    xd = st.text_input("X", "1,2,3,4,5", key=f"sp_x_{i}")
                    yd = st.text_input("Y", f"{np.random.randint(1,5)},{np.random.randint(1,9)},{np.random.randint(2,8)},{np.random.randint(1,7)},{np.random.randint(3,9)}", key=f"sp_y_{i}")
                    lbl = st.text_input("Title", f"Plot {i+1}", key=f"sp_l_{i}")
                    col = st.color_picker("Color", f"#{['1a6f3c','1a4fa0','8a2c2c','8a6a1a','5a2c8a','2c5f8a'][i%6]}", key=f"sp_c_{i}")
                    plot_cfgs.append({"type": ptype, "x": xd, "y": yd, "label": lbl, "color": col})

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, axes = plt.subplots(int(n_rows), int(n_cols),
                                             figsize=(fig_w, fig_h),
                                             sharex=share_x, sharey=share_y,
                                             squeeze=False)
                    flat_axes = axes.flatten()
                    for i, cfg in enumerate(plot_cfgs):
                        ax = flat_axes[i]
                        if df_csv is not None:
                            x_v = df_csv[cfg["xc"]].values
                            y_v = df_csv[cfg["yc"]].values
                        else:
                            x_v = parse_series(cfg["x"])
                            y_v = parse_series(cfg["y"])
                        ptype = cfg["type"]
                        clr   = cfg["color"]
                        lbl   = cfg.get("label", f"Plot {i+1}")
                        if ptype == "Line":
                            ax.plot(x_v, y_v, color=clr, linewidth=1.5, label=lbl)
                        elif ptype == "Bar":
                            ax.bar(range(len(y_v)), y_v, color=clr, edgecolor='white', linewidth=0.6, label=lbl)
                        elif ptype == "Scatter":
                            ax.scatter(x_v, y_v, color=clr, s=40, alpha=0.8, label=lbl, edgecolors='white', linewidths=0.5)
                        elif ptype == "Histogram":
                            ax.hist(y_v, bins=10, color=clr, edgecolor='white', linewidth=0.6, label=lbl)
                        apply_common(ax, "", "", lbl, show_grid, show_legend)
                    # hide unused axes
                    for j in range(len(plot_cfgs), len(flat_axes)):
                        flat_axes[j].set_visible(False)
                    if fig_title:
                        fig.suptitle(fig_title, fontsize=12, fontweight='bold', y=1.01)
                    fig.tight_layout()
                    st.pyplot(fig)
                    data = fig_to_bytes(fig, dl_fmt, dpi)
                    st.download_button(f"Download .{dl_fmt}", data, f"subplots.{dl_fmt}", mime=f"image/{dl_fmt}")
                    plt.close(fig)

#  Footer 
st.markdown("<br><hr><p style='font-size:0.75rem;color:#aaa;text-align:center;'>Graphia — Matplotlib-powered</p>", unsafe_allow_html=True)
