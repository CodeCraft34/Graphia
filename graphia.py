import streamlit as st
import matplotlib
matplotlib.use('Agg') #non-interactive environments like Streamlit Cloud
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import numpy as np
import pandas as pd
import io

st.set_page_config(page_title="Graphia \n- Create your Graphs and chart", layout="wide", initial_sidebar_state="expanded")

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
    .desc-box { background:#f0f4f8; border-left:3px solid #2c5f8a; padding:0.55rem 0.9rem;
        border-radius:4px; font-size:0.83rem; color:#333; margin-bottom:0.8rem; }
    .stButton > button { background:#111; color:#fff; border:none;
        border-radius:4px; padding:0.45rem 1.2rem; font-size:0.85rem; font-weight:600; }
    .stButton > button:hover { background:#333; }
    .stDownloadButton > button { background:#1a6f3c; color:#fff; border:none;
        border-radius:4px; padding:0.45rem 1.2rem; font-size:0.85rem; font-weight:600; }
    .stDownloadButton > button:hover { background:#145530; }
</style>
""", unsafe_allow_html=True)

MARKERS    = ["None","o","s","^","D","x","+","*","v","p","h"]
LINESTYLES = ["solid","dashed","dotted","dashdot","None"]
COLORMAPS  = ["tab10","Set1","Set2","Dark2","Paired","Accent"]

CHART_DESC = {
    "Line":           "Connects data points with a continuous line. Best for trends or changes over a sequence. X axis supports both numbers and letters (e.g. A, B, C or Jan, Feb, Mar).",
    "Scatter":        "Plots individual points with no connecting line. Reveals correlations, clusters, and outliers between two variables.",
    "Bar":            "Rectangular bars proportional to values. Best for comparing quantities across categories.",
    "Histogram":      "Groups values into bins and counts occurrences. Shows the distribution and spread of a dataset.",
    "Pie":            "Circular chart divided into slices. Each slice represents a proportion of the total.",
    "Multiple Lines": "Multiple line series on one chart. Compare trends of several variables side by side. X axis supports letters.",
    "Subplot Grid":   "Several independent charts arranged in a grid inside one figure — ideal for dashboards.",
    "Heatmap":        "Displays a data matrix using color intensity to represent values. Useful for correlation matrices and 2D data patterns.",
    "Area / Fill":    "A line chart where the area below is filled. Good for showing volume or cumulative quantities over time.",
    "Box Plot":       "Shows data distribution via median, quartiles, and outliers. Useful for statistical summaries and comparing groups.",
    "Treemap":        "Nested rectangles sized by value. Shows part-to-whole relationships with hierarchical data.",
    "Radar Chart":    "Spider/web chart with multiple axes from the centre. Compares multivariate data across categories.",
    "Stacked Area":   "Multiple filled areas stacked on top of each other. Shows how each part contributes to the total over time.",
    "Pictogram":      "Uses repeated symbols to represent quantities. Each symbol stands for a fixed number of units.",
    "Sankey Diagram": "Flow diagram showing quantities moving between nodes. Arrow widths are proportional to flow amounts.",
}

def parse_series(text):
    try: return [float(v.strip()) for v in text.split(",") if v.strip()]
    except: return []

def parse_labels(text):
    return [v.strip() for v in text.split(",") if v.strip()]

def apply_common(ax, xlabel, ylabel, title, grid, legend):
    if title:  ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5, linewidth=0.7) if grid else ax.grid(False)
    if legend:
        try: ax.legend(fontsize=8, framealpha=0.9)
        except: pass
    ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_linewidth(0.7); spine.set_color('#aaa')

def fig_to_bytes(fig, fmt, dpi):
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
    buf.seek(0); return buf.read()

def color_cycle(cmap_name, n):
    cmap = plt.get_cmap(cmap_name)
    return [cmap(i / max(n-1, 1)) for i in range(n)]

def dl_button(fig, fmt, dpi, fname):
    data = fig_to_bytes(fig, fmt, dpi)
    st.download_button(f"Download .{fmt}", data, f"{fname}.{fmt}", mime=f"image/{fmt}")

def desc(chart):
    st.markdown(f'<div class="desc-box">{CHART_DESC.get(chart,"")}</div>', unsafe_allow_html=True)

def col_select(label, df, default_idx=0):
    cols = list(df.columns)
    return st.selectbox(label, cols, index=min(default_idx, len(cols)-1))

def smart_xaxis(ax, x_raw, y_len):
    """Set x-axis to support both numeric and label inputs."""
    x_parts = parse_labels(x_raw)
    try:
        x_num = [float(v) for v in x_parts]
        return x_num, False
    except ValueError:
        ax.set_xticks(range(y_len))
        ax.set_xticklabels(x_parts[:y_len], fontsize=8)
        return list(range(y_len)), True

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Graphia \n - Graph Maker")
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Data Source**")
    data_source = st.radio("", ["Manual Entry","Upload CSV"], label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    df_csv = None
    if data_source == "Upload CSV":
        uploaded = st.file_uploader("CSV File", type=["csv"])
        if uploaded:
            df_csv = pd.read_csv(uploaded)
            st.success(f"{df_csv.shape[0]} rows, {df_csv.shape[1]} cols")
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Chart Type**")
    chart_type = st.selectbox("", [
        "Line","Scatter","Bar","Histogram","Pie",
        "Multiple Lines","Subplot Grid",
        "Heatmap","Area / Fill","Box Plot",
        "Treemap","Radar Chart","Stacked Area",
        "Pictogram","Sankey Diagram"
    ], label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Style**")
    color_map = st.selectbox("Color palette", COLORMAPS)
    mpl_style = st.selectbox("Theme", ["default","seaborn-v0_8-whitegrid","ggplot","bmh","fivethirtyeight","dark_background"])
    fig_w = st.slider("Figure width",  4, 16, 9)
    fig_h = st.slider("Figure height", 3, 12, 5)
    dpi   = st.selectbox("DPI", [100,150,200,300], index=1)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Labels & Decorations**")
    fig_title   = st.text_input("Figure title", "")
    x_label     = st.text_input("X-axis label", "X")
    y_label     = st.text_input("Y-axis label", "Y")
    show_grid   = st.checkbox("Grid", value=True)
    show_legend = st.checkbox("Legend", value=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Export**")
    dl_fmt = st.selectbox("Format", ["png","pdf","svg","jpeg"])

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown(f"## {chart_type}")
desc(chart_type)

cfg_col, preview_col = st.columns([1, 2], gap="large")

with cfg_col:
    st.markdown("### Configuration")

    # ── LINE ─────────────────────────────────────────────────────────────────
    if chart_type == "Line":
        if df_csv is not None:
            xc = col_select("X column", df_csv, 0)
            yc = col_select("Y column", df_csv, 1)
        else:
            x_raw = st.text_input("X values (numbers or letters)", "A,B,C,D,E")
            y_raw = st.text_input("Y values", "10,20,15,25,18")
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
                        ax.plot(range(len(y_vals)), y_vals, label=lbl,
                                linestyle=ls if ls!="None" else "None",
                                marker=mk if mk!="None" else None, linewidth=lw, color=color)
                        ax.set_xticks(range(len(x_vals)))
                        ax.set_xticklabels([str(v) for v in x_vals], rotation=45, ha='right', fontsize=8)
                    else:
                        y_vals  = parse_series(y_raw)
                        x_final, is_label = smart_xaxis(ax, x_raw, len(y_vals))
                        ax.plot(x_final, y_vals, label=lbl,
                                linestyle=ls if ls!="None" else "None",
                                marker=mk if mk!="None" else None, linewidth=lw, color=color)
                    apply_common(ax, x_label, y_label, fig_title or "Line Chart", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "line_chart"); plt.close(fig)

    # ── SCATTER ──────────────────────────────────────────────────────────────
    elif chart_type == "Scatter":
        if df_csv is not None:
            xc     = col_select("X column", df_csv, 0)
            yc     = col_select("Y column", df_csv, 1)
            size_c = st.selectbox("Size column (optional)", ["None"]+list(df_csv.columns))
        else:
            x_raw = st.text_input("X values", "10,20,30,40,50")
            y_raw = st.text_input("Y values", "5,15,25,35,45")
        lbl   = st.text_input("Series label", "Points")
        mk    = st.selectbox("Marker", [m for m in MARKERS if m!="None"])
        pt_sz = st.slider("Point size", 10, 400, 80)
        alpha = st.slider("Opacity", 0.1, 1.0, 0.8, 0.05)
        color = st.color_picker("Color", "#1a4fa0")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        x_vals = df_csv[xc].values; y_vals = df_csv[yc].values
                        sz = df_csv[size_c].values if size_c!="None" else pt_sz
                    else:
                        x_vals = parse_series(x_raw); y_vals = parse_series(y_raw); sz = pt_sz
                    ax.scatter(x_vals, y_vals, label=lbl, marker=mk,
                               s=sz, alpha=alpha, color=color, edgecolors='white', linewidths=0.5)
                    apply_common(ax, x_label, y_label, fig_title or "Scatter Plot", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "scatter"); plt.close(fig)

    # ── BAR ──────────────────────────────────────────────────────────────────
    elif chart_type == "Bar":
        if df_csv is not None:
            xc = col_select("Category column", df_csv, 0)
            yc = col_select("Value column",    df_csv, 1)
        else:
            x_raw = st.text_input("Categories", "Q1,Q2,Q3,Q4")
            y_raw = st.text_input("Values",     "42,58,75,63")
        orientation = st.radio("Orientation", ["Vertical","Horizontal"])
        bar_w = st.slider("Bar width", 0.2, 1.0, 0.6, 0.05)
        edge  = st.checkbox("Edge color", value=True)
        color = st.color_picker("Color", "#2c5f8a")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        cats = df_csv[xc].astype(str).tolist(); vals = df_csv[yc].values
                    else:
                        cats = parse_labels(x_raw); vals = parse_series(y_raw)
                    ec = '#222' if edge else 'none'
                    if orientation=="Vertical":
                        ax.bar(cats, vals, width=bar_w, color=color, edgecolor=ec, linewidth=0.7)
                    else:
                        ax.barh(cats, vals, height=bar_w, color=color, edgecolor=ec, linewidth=0.7)
                    apply_common(ax, x_label, y_label, fig_title or "Bar Chart", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "bar_chart"); plt.close(fig)

    # ── HISTOGRAM ────────────────────────────────────────────────────────────
    elif chart_type == "Histogram":
        if df_csv is not None:
            yc = col_select("Data column", df_csv, 0)
        else:
            y_raw = st.text_input("Data values", "5,8,12,10,14,14,18,20,20,22,22,22,25,28,30")
        bins  = st.slider("Number of bins", 5, 100, 15)
        kde   = st.checkbox("Density (normalize)", value=False)
        edge  = st.checkbox("Edge color", value=True)
        color = st.color_picker("Bar color", "#8a2c2c")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    vals = df_csv[yc].dropna().values if df_csv is not None else np.array(parse_series(y_raw))
                    ax.hist(vals, bins=bins, density=kde, color=color,
                            edgecolor='#111' if edge else 'none', linewidth=0.6, label="Distribution")
                    apply_common(ax, x_label, y_label, fig_title or "Histogram", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "histogram"); plt.close(fig)

    # ── PIE ──────────────────────────────────────────────────────────────────
    elif chart_type == "Pie":
        if df_csv is not None:
            label_c = col_select("Labels column", df_csv, 0)
            val_c   = col_select("Values column", df_csv, 1)
        else:
            x_raw = st.text_input("Labels", "Alpha,Beta,Gamma,Delta,Epsilon")
            y_raw = st.text_input("Values", "30,20,25,15,10")
        donut       = st.checkbox("Donut style", value=False)
        pct_fmt     = st.selectbox("Percentage format", ["%.1f%%","%.0f%%","None"])
        explode_all = st.slider("Explode slices", 0.0, 0.2, 0.0, 0.01)
        start_angle = st.slider("Start angle", 0, 360, 90)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        labels = df_csv[label_c].astype(str).tolist(); vals = df_csv[val_c].values
                    else:
                        labels = parse_labels(x_raw); vals = np.array(parse_series(y_raw))
                    explode = [explode_all]*len(vals)
                    colors  = color_cycle(color_map, len(vals))
                    autopct = None if pct_fmt=="None" else pct_fmt
                    if autopct:
                        wedges,texts,autotexts = ax.pie(vals, labels=labels, explode=explode,
                            colors=colors, autopct=autopct, startangle=start_angle,
                            pctdistance=0.82, wedgeprops={'linewidth':0.8,'edgecolor':'white'})
                        for t in autotexts: t.set_fontsize(8)
                    else:
                        ax.pie(vals, labels=labels, explode=explode, colors=colors,
                               startangle=start_angle, wedgeprops={'linewidth':0.8,'edgecolor':'white'})
                    if donut: ax.add_patch(plt.Circle((0,0),0.55,color='white'))
                    if fig_title: ax.set_title(fig_title, fontsize=11, fontweight='bold', pad=8)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "pie_chart"); plt.close(fig)

    # ── MULTIPLE LINES ───────────────────────────────────────────────────────
    elif chart_type == "Multiple Lines":
        n_lines = st.number_input("Number of series", 2, 8, 3, 1)
        if df_csv is not None:
            xc     = col_select("X column", df_csv, 0)
            y_cols = st.multiselect("Y columns", list(df_csv.columns),
                                    default=list(df_csv.columns)[1:int(n_lines)+1])
        else:
            x_raw = st.text_input("X values (numbers or letters)", "Jan,Feb,Mar,Apr,May,Jun")
            series_inputs = []
            for i in range(int(n_lines)):
                s    = st.text_input(f"Series {i+1} values", "2,4,3,5,4,6", key=f"ml_{i}")
                lname= st.text_input(f"Series {i+1} label",  f"Series {i+1}", key=f"ml_lbl_{i}")
                series_inputs.append((s, lname))
        ls = st.selectbox("Line style", LINESTYLES)
        mk = st.selectbox("Marker", MARKERS)
        lw = st.slider("Line width", 0.5, 5.0, 1.5, 0.5)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    colors  = color_cycle(color_map, int(n_lines))
                    if df_csv is not None:
                        x_raw_vals = df_csv[xc].values
                        for j, yc in enumerate(y_cols):
                            ax.plot(range(len(x_raw_vals)), df_csv[yc].values,
                                    label=yc, color=colors[j],
                                    linestyle=ls if ls!="None" else "None",
                                    marker=mk if mk!="None" else None, linewidth=lw)
                        ax.set_xticks(range(len(x_raw_vals)))
                        ax.set_xticklabels([str(v) for v in x_raw_vals], rotation=45, ha='right', fontsize=8)
                    else:
                        first_y = parse_series(series_inputs[0][0]) if series_inputs else [0]
                        x_final, is_label = smart_xaxis(ax, x_raw, len(first_y))
                        for j, (s, lname) in enumerate(series_inputs):
                            ax.plot(x_final, parse_series(s), label=lname, color=colors[j],
                                    linestyle=ls if ls!="None" else "None",
                                    marker=mk if mk!="None" else None, linewidth=lw)
                    apply_common(ax, x_label, y_label, fig_title or "Multiple Lines", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "multi_line"); plt.close(fig)

    # ── SUBPLOT GRID ─────────────────────────────────────────────────────────
    elif chart_type == "Subplot Grid":
        n_rows  = st.number_input("Rows", 1, 4, 2, 1)
        n_cols  = st.number_input("Columns", 1, 4, 2, 1)
        share_x = st.checkbox("Share X axis", False)
        share_y = st.checkbox("Share Y axis", False)
        n_plots = int(n_rows * n_cols)
        st.markdown(f"**{n_plots} subplot(s)**")
        plot_cfgs = []
        for i in range(n_plots):
            with st.expander(f"Subplot {i+1}", expanded=(i==0)):
                ptype = st.selectbox("Type",["Line","Bar","Scatter","Histogram"],key=f"sp_t_{i}")
                if df_csv is not None:
                    xc_s = col_select("X column", df_csv, 0)
                    yc_s = col_select("Y column", df_csv, 1)
                    plot_cfgs.append({"type":ptype,"xc":xc_s,"yc":yc_s,"label":f"Plot {i+1}","color":"#333"})
                else:
                    xd  = st.text_input("X","1,2,3,4,5",key=f"sp_x_{i}")
                    yd  = st.text_input("Y","3,6,2,8,5",key=f"sp_y_{i}")
                    lbl = st.text_input("Title",f"Plot {i+1}",key=f"sp_l_{i}")
                    col = st.color_picker("Color",f"#{['1a6f3c','1a4fa0','8a2c2c','8a6a1a','5a2c8a','2c5f8a'][i%6]}",key=f"sp_c_{i}")
                    plot_cfgs.append({"type":ptype,"x":xd,"y":yd,"label":lbl,"color":col})

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, axes = plt.subplots(int(n_rows),int(n_cols),figsize=(fig_w,fig_h),
                                             sharex=share_x,sharey=share_y,squeeze=False)
                    flat = axes.flatten()
                    for i, cfg in enumerate(plot_cfgs):
                        ax = flat[i]
                        if df_csv is not None:
                            x_v = df_csv[cfg["xc"]].values; y_v = df_csv[cfg["yc"]].values
                        else:
                            x_v = parse_series(cfg["x"]); y_v = parse_series(cfg["y"])
                        clr = cfg["color"]; lbl = cfg.get("label",f"Plot {i+1}")
                        if cfg["type"]=="Line":        ax.plot(x_v,y_v,color=clr,linewidth=1.5,label=lbl)
                        elif cfg["type"]=="Bar":       ax.bar(range(len(y_v)),y_v,color=clr,edgecolor='white',linewidth=0.6,label=lbl)
                        elif cfg["type"]=="Scatter":   ax.scatter(x_v,y_v,color=clr,s=40,alpha=0.8,label=lbl,edgecolors='white',linewidths=0.5)
                        elif cfg["type"]=="Histogram": ax.hist(y_v,bins=10,color=clr,edgecolor='white',linewidth=0.6,label=lbl)
                        apply_common(ax,"","",lbl,show_grid,show_legend)
                    for j in range(len(plot_cfgs),len(flat)): flat[j].set_visible(False)
                    if fig_title: fig.suptitle(fig_title,fontsize=12,fontweight='bold',y=1.01)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "subplots"); plt.close(fig)

    # ── HEATMAP ──────────────────────────────────────────────────────────────
    elif chart_type == "Heatmap":
        if df_csv is not None:
            st.info("Using numeric columns from CSV as the matrix.")
            annot = st.checkbox("Show values", value=True)
            hcmap = st.selectbox("Color map",["Reds","Blues","YlOrRd","RdBu","viridis","coolwarm","hot"])
        else:
            row1     = st.text_input("Row 1 values", "1,2,3")
            row2     = st.text_input("Row 2 values", "4,5,6")
            row3     = st.text_input("Row 3 values", "7,8,9")
            r_labels = st.text_input("Row labels",    "Row A,Row B,Row C")
            c_labels = st.text_input("Column labels", "Col 1,Col 2,Col 3")
            annot    = st.checkbox("Show values", value=True)
            hcmap    = st.selectbox("Color map",["Reds","Blues","YlOrRd","RdBu","viridis","coolwarm","hot"])

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        num_df = df_csv.select_dtypes(include=np.number)
                        matrix = num_df.values; rl = list(num_df.index); cl = list(num_df.columns)
                    else:
                        matrix = np.array([parse_series(row1),parse_series(row2),parse_series(row3)])
                        rl = parse_labels(r_labels); cl = parse_labels(c_labels)
                    im = ax.imshow(matrix, cmap=hcmap, aspect='auto')
                    plt.colorbar(im, ax=ax, shrink=0.8)
                    ax.set_xticks(range(len(cl))); ax.set_xticklabels(cl, fontsize=8)
                    ax.set_yticks(range(len(rl))); ax.set_yticklabels(rl, fontsize=8)
                    if annot:
                        vmax = matrix.max()
                        for r in range(matrix.shape[0]):
                            for c in range(matrix.shape[1]):
                                ax.text(c, r, f"{matrix[r,c]:.1f}", ha='center', va='center',
                                        fontsize=9, color='white' if matrix[r,c]>vmax*0.6 else 'black')
                    apply_common(ax, x_label, y_label, fig_title or "Heatmap", False, False)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "heatmap"); plt.close(fig)

    # ── AREA / FILL ───────────────────────────────────────────────────────────
    elif chart_type == "Area / Fill":
        if df_csv is not None:
            xc = col_select("X column", df_csv, 0)
            yc = col_select("Y column", df_csv, 1)
        else:
            x_raw = st.text_input("X values (numbers or letters)", "1,2,3,4,5")
            y_raw = st.text_input("Y values", "3,5,2,8,7")
        alpha = st.slider("Fill opacity", 0.1, 1.0, 0.35, 0.05)
        color = st.color_picker("Color", "#2c8aad")
        lbl   = st.text_input("Series label", "Area")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        x_vals = df_csv[xc].values; y_vals = df_csv[yc].values
                        ax.plot(range(len(y_vals)), y_vals, color=color, linewidth=1.5, label=lbl)
                        ax.fill_between(range(len(y_vals)), y_vals, alpha=alpha, color=color)
                        ax.set_xticks(range(len(x_vals)))
                        ax.set_xticklabels([str(v) for v in x_vals], rotation=45, ha='right', fontsize=8)
                    else:
                        y_vals  = parse_series(y_raw)
                        x_final, is_label = smart_xaxis(ax, x_raw, len(y_vals))
                        ax.plot(x_final, y_vals, color=color, linewidth=1.5, label=lbl)
                        ax.fill_between(x_final, y_vals, alpha=alpha, color=color)
                    apply_common(ax, x_label, y_label, fig_title or "Area Chart", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "area_chart"); plt.close(fig)

    # ── BOX PLOT ──────────────────────────────────────────────────────────────
    elif chart_type == "Box Plot":
        if df_csv is not None:
            num_cols = list(df_csv.select_dtypes(include=np.number).columns)
            y_cols   = st.multiselect("Select columns", num_cols, default=num_cols[:3])
        else:
            n_groups = st.number_input("Number of groups", 1, 6, 3, 1)
            groups=[]; labels_bp=[]
            for i in range(int(n_groups)):
                d = st.text_input(f"Group {i+1} values","10,15,14,20,22,18,25,28,30,12",key=f"bp_{i}")
                l = st.text_input(f"Group {i+1} label", f"Group {i+1}", key=f"bpl_{i}")
                groups.append(d); labels_bp.append(l)
        notch = st.checkbox("Notch style", value=False)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        data_bp = [df_csv[c].dropna().values for c in y_cols]; lbl_bp = y_cols
                    else:
                        data_bp = [parse_series(g) for g in groups]; lbl_bp = labels_bp
                    bp = ax.boxplot(data_bp, labels=lbl_bp, notch=notch, patch_artist=True)
                    for patch, c in zip(bp['boxes'], color_cycle(color_map, len(data_bp))):
                        patch.set_facecolor(c); patch.set_alpha(0.7)
                    for median in bp['medians']:
                        median.set_color('#e67e22'); median.set_linewidth(2)
                    apply_common(ax, x_label, y_label, fig_title or "Box Plot", show_grid, False)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "boxplot"); plt.close(fig)

    # ── TREEMAP ───────────────────────────────────────────────────────────────
    elif chart_type == "Treemap":
        if df_csv is not None:
            label_c = col_select("Labels column", df_csv, 0)
            val_c   = col_select("Values column", df_csv, 1)
        else:
            x_raw = st.text_input("Labels", "A,B,C,D")
            y_raw = st.text_input("Values", "40,30,20,10")

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    if df_csv is not None:
                        labels = df_csv[label_c].astype(str).tolist()
                        vals   = df_csv[val_c].values.astype(float)
                    else:
                        labels = parse_labels(x_raw); vals = np.array(parse_series(y_raw))
                    total = vals.sum()
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis('off')
                    sorted_idx  = np.argsort(vals)[::-1]
                    proportions = vals[sorted_idx] / total
                    lbl_sorted  = [labels[i] for i in sorted_idx]
                    clr_sorted  = color_cycle(color_map, len(vals))
                    x, y, w, h  = 0.0, 0.0, 1.0, 1.0
                    remaining   = list(zip(proportions, lbl_sorted, clr_sorted))
                    for i, (p, lbl, clr) in enumerate(remaining):
                        rest = sum(r[0] for r in remaining[i:])
                        if w >= h:
                            bw = (p / rest) * w if rest > 0 else 0; bh = h
                            rect = mpatches.FancyBboxPatch((x,y),bw,bh,
                                boxstyle="round,pad=0.005",facecolor=clr,edgecolor='white',linewidth=1.5)
                            ax.add_patch(rect)
                            fs = max(7, min(12, int(bw*50)))
                            ax.text(x+bw/2,y+bh/2,f"{lbl}\n{p*100:.1f}%",
                                    ha='center',va='center',fontsize=fs,fontweight='bold',color='white')
                            x += bw; w -= bw
                        else:
                            bw = w; bh = (p / rest) * h if rest > 0 else 0
                            rect = mpatches.FancyBboxPatch((x,y),bw,bh,
                                boxstyle="round,pad=0.005",facecolor=clr,edgecolor='white',linewidth=1.5)
                            ax.add_patch(rect)
                            fs = max(7, min(12, int(bh*50)))
                            ax.text(x+bw/2,y+bh/2,f"{lbl}\n{p*100:.1f}%",
                                    ha='center',va='center',fontsize=fs,fontweight='bold',color='white')
                            y += bh; h -= bh
                    if fig_title: ax.set_title(fig_title,fontsize=11,fontweight='bold',pad=8)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "treemap"); plt.close(fig)

    # ── RADAR CHART ───────────────────────────────────────────────────────────
    elif chart_type == "Radar Chart":
        if df_csv is not None:
            cat_c    = col_select("Category column (axes)", df_csv, 0)
            val_cols = st.multiselect("Value columns (one per series)", list(df_csv.columns),
                                      default=list(df_csv.columns)[1:3])
        else:
            axes_raw = st.text_input("Axes labels", "Speed,Strength,Stamina,Agility,Intelligence")
            n_series = st.number_input("Number of series", 1, 4, 1, 1)
            series_r = []
            for i in range(int(n_series)):
                v = st.text_input(f"Series {i+1} values","7,6,8,5,9",key=f"rad_{i}")
                l = st.text_input(f"Series {i+1} label", f"Entity {i+1}",key=f"radl_{i}")
                series_r.append((v, l))
        fill_alpha = st.slider("Fill opacity", 0.0, 0.6, 0.2, 0.05)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    if df_csv is not None:
                        axes_labels = df_csv[cat_c].astype(str).tolist()
                        all_series  = [(df_csv[c].values.tolist(), c) for c in val_cols]
                    else:
                        axes_labels = parse_labels(axes_raw)
                        all_series  = [(parse_series(v), l) for v, l in series_r]
                    N      = len(axes_labels)
                    angles = [n / float(N) * 2 * np.pi for n in range(N)] + [0]
                    fig, ax = plt.subplots(figsize=(fig_w,fig_h), subplot_kw=dict(polar=True))
                    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
                    ax.set_xticks(angles[:-1]); ax.set_xticklabels(axes_labels, fontsize=8)
                    for (vals_r, lbl_r), clr in zip(all_series, color_cycle(color_map,len(all_series))):
                        v = list(vals_r) + [vals_r[0]]
                        ax.plot(angles, v, color=clr, linewidth=2, label=lbl_r)
                        ax.fill(angles, v, color=clr, alpha=fill_alpha)
                    if show_legend: ax.legend(loc='upper right',bbox_to_anchor=(1.3,1.1),fontsize=8)
                    if fig_title:   ax.set_title(fig_title,fontsize=11,fontweight='bold',pad=20)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "radar_chart"); plt.close(fig)

    # ── STACKED AREA ─────────────────────────────────────────────────────────
    elif chart_type == "Stacked Area":
        if df_csv is not None:
            xc     = col_select("X column", df_csv, 0)
            y_cols = st.multiselect("Y columns (stacked)", list(df_csv.columns),
                                    default=list(df_csv.columns)[1:4])
        else:
            x_raw = st.text_input("X values (numbers or letters)","2018,2019,2020,2021,2022")
            n_s   = st.number_input("Number of series", 2, 6, 3, 1)
            sa_series = []
            for i in range(int(n_s)):
                v = st.text_input(f"Series {i+1} values","2,3,4,3,2",key=f"sa_{i}")
                l = st.text_input(f"Series {i+1} label", f"Series {chr(65+i)}",key=f"sal_{i}")
                sa_series.append((v, l))
        alpha_sa = st.slider("Layer opacity", 0.3, 1.0, 0.8, 0.05)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    if df_csv is not None:
                        x_raw_vals = df_csv[xc].values
                        ys = [df_csv[c].values for c in y_cols]; lbls = y_cols
                    else:
                        x_parts = parse_labels(x_raw)
                        try:    x_raw_vals = [float(v) for v in x_parts]
                        except: x_raw_vals = list(range(len(x_parts)))
                        ys   = [parse_series(v) for v, _ in sa_series]
                        lbls = [l for _, l in sa_series]
                    ax.stackplot(x_raw_vals, ys, labels=lbls,
                                 colors=color_cycle(color_map,len(ys)), alpha=alpha_sa)
                    if df_csv is None:
                        try: float(x_parts[0])
                        except:
                            ax.set_xticks(range(len(x_parts))); ax.set_xticklabels(x_parts,fontsize=8)
                    apply_common(ax, x_label, y_label, fig_title or "Stacked Area", show_grid, show_legend)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "stacked_area"); plt.close(fig)

    # ── PICTOGRAM ─────────────────────────────────────────────────────────────
    elif chart_type == "Pictogram":
        if df_csv is not None:
            label_c = col_select("Labels column", df_csv, 0)
            val_c   = col_select("Values column", df_csv, 1)
        else:
            x_raw = st.text_input("Categories", "Apples,Bananas,Cherries")
            y_raw = st.text_input("Values",     "5,3,7")
        symbol     = st.selectbox("Symbol", ["●","■","★","▲","♦","◆"])
        per_symbol = st.number_input("Each symbol represents", 1, 100, 1, 1)
        sym_size   = st.slider("Symbol size", 8, 28, 14)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    if df_csv is not None:
                        cats = df_csv[label_c].astype(str).tolist()
                        vals = df_csv[val_c].values.astype(float)
                    else:
                        cats = parse_labels(x_raw); vals = np.array(parse_series(y_raw))
                    colors_pic = color_cycle(color_map, len(cats))
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    ax.axis('off')
                    row_h = 1.0 / (len(cats)+1)
                    for i, (cat, val, clr) in enumerate(zip(cats, vals, colors_pic)):
                        n_sym = int(round(float(val) / float(per_symbol)))
                        y_pos = 1 - (i+1)*row_h
                        ax.text(0.02, y_pos, f"{cat}:", fontsize=sym_size-2, va='center',
                                ha='left', fontweight='bold', transform=ax.transAxes, color='#222')
                        ax.text(0.22, y_pos, (symbol+" ")*n_sym, fontsize=sym_size, va='center',
                                ha='left', transform=ax.transAxes, color=clr)
                    if fig_title: ax.set_title(fig_title, fontsize=11, fontweight='bold', pad=8)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "pictogram"); plt.close(fig)

    # ── SANKEY DIAGRAM ────────────────────────────────────────────────────────
    elif chart_type == "Sankey Diagram":
        st.info("Each row: Source, Target, Value")
        flows_raw = st.text_area("Flows (Source, Target, Value)",
            "Revenue, Operations, 500\nRevenue, Marketing, 300\nRevenue, R&D, 200\nOperations, Staff, 350\nOperations, Infra, 150")
        alpha_sk = st.slider("Flow opacity", 0.2, 0.9, 0.5, 0.05)

        if st.button("Generate"):
            with preview_col:
                with plt.style.context(mpl_style):
                    flows = []
                    for line in flows_raw.strip().split("\n"):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts)==3:
                            try: flows.append((parts[0], parts[1], float(parts[2])))
                            except: pass

                    sources  = [f[0] for f in flows]
                    targets  = [f[1] for f in flows]
                    all_nodes = list(dict.fromkeys(sources+targets))
                    left_n  = [n for n in all_nodes if n in sources and n not in targets]
                    right_n = [n for n in all_nodes if n in targets]
                    mid_n   = [n for n in all_nodes if n in sources and n in targets and n not in left_n]

                    level = {}
                    for n in left_n:  level[n] = 0
                    for n in mid_n:   level[n] = 1
                    for n in right_n: level[n] = 2

                    lvl_groups = {}
                    for nd in all_nodes:
                        lvl_groups.setdefault(level.get(nd,0),[]).append(nd)

                    y_pos = {}
                    for lvl, grp in lvl_groups.items():
                        for i, nd in enumerate(grp):
                            y_pos[nd] = (i+0.5)/max(len(grp),1)

                    x_map = {0:0.1, 1:0.5, 2:0.85}
                    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
                    ax.axis('off'); ax.set_xlim(0,1); ax.set_ylim(0,1)

                    max_val = max(f[2] for f in flows) if flows else 1
                    clrs    = color_cycle(color_map, len(flows))

                    for (src, tgt, val), clr in zip(flows, clrs):
                        x0 = x_map.get(level.get(src,0), 0.1)
                        x1 = x_map.get(level.get(tgt,2), 0.85)
                        y0 = y_pos.get(src, 0.5)
                        y1 = y_pos.get(tgt, 0.5)
                        lw = max(2, (val/max_val)*18)
                        verts = [(x0,y0),(x0+0.3*(x1-x0),y0),(x0+0.7*(x1-x0),y1),(x1,y1)]
                        codes = [mpath.Path.MOVETO,mpath.Path.CURVE4,mpath.Path.CURVE4,mpath.Path.CURVE4]
                        patch = mpatches.FancyArrowPatch(path=mpath.Path(verts,codes),
                                    arrowstyle="-", linewidth=lw, color=clr, alpha=alpha_sk)
                        ax.add_patch(patch)
                        ax.text((x0+x1)/2,(y0+y1)/2,f"{val:.0f}",fontsize=7,
                                ha='center',va='center',color='#333')

                    for nd in all_nodes:
                        x = x_map.get(level.get(nd,0),0.5); y = y_pos.get(nd,0.5)
                        ax.text(x, y, nd, fontsize=9, ha='center', va='center',
                                bbox=dict(boxstyle='round,pad=0.3',facecolor='white',
                                          edgecolor='#aaa',linewidth=0.8))

                    if fig_title: ax.set_title(fig_title,fontsize=11,fontweight='bold',pad=8)
                    fig.tight_layout(); st.pyplot(fig)
                    dl_button(fig, dl_fmt, dpi, "sankey"); plt.close(fig)

st.markdown("<br><hr><p style='font-size:0.75rem;color:#aaa;text-align:center;'>Graphia — Matplotlib-powered</p>",
            unsafe_allow_html=True)
