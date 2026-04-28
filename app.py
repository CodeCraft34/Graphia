import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

st.set_page_config(
    page_title="Streamlit Template",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Streamlit Template")
st.write(
    "A starter template wired up with Streamlit, pandas, plotly, scipy, and kaleido."
)

with st.sidebar:
    st.header("Controls")
    n_points = st.slider("Number of points", min_value=50, max_value=1000, value=200, step=50)
    noise = st.slider("Noise level", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
    seed = st.number_input("Random seed", min_value=0, value=42, step=1)

rng = np.random.default_rng(int(seed))
x = np.linspace(0, 10, n_points)
y = 2.0 * x + 1.0 + rng.normal(0, noise, size=n_points)
df = pd.DataFrame({"x": x, "y": y})

slope, intercept, r_value, p_value, std_err = stats.linregress(df["x"], df["y"])
df["fit"] = intercept + slope * df["x"]

tab_chart, tab_data, tab_export = st.tabs(["Chart", "Data", "Export"])

with tab_chart:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Slope", f"{slope:.3f}")
    col2.metric("Intercept", f"{intercept:.3f}")
    col3.metric("R²", f"{r_value**2:.3f}")
    col4.metric("p-value", f"{p_value:.2e}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["x"], y=df["y"], mode="markers", name="Data"))
    fig.add_trace(go.Scatter(x=df["x"], y=df["fit"], mode="lines", name="Linear fit"))
    fig.update_layout(
        title="Linear regression",
        xaxis_title="x",
        yaxis_title="y",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    hist = px.histogram(df, x="y", nbins=30, title="Distribution of y")
    st.plotly_chart(hist, use_container_width=True)

with tab_data:
    st.subheader("Sample data")
    st.dataframe(df, use_container_width=True)
    st.subheader("Summary statistics")
    st.dataframe(df.describe(), use_container_width=True)

with tab_export:
    st.subheader("Download CSV")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download data.csv",
        data=csv,
        file_name="data.csv",
        mime="text/csv",
    )

    st.subheader("Download chart as PNG")
    st.caption("Static image export is powered by kaleido.")
    if st.button("Generate PNG"):
        png_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        st.download_button(
            label="Download chart.png",
            data=png_bytes,
            file_name="chart.png",
            mime="image/png",
        )
