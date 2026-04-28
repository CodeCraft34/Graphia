import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.interpolate import interp1d
import numpy as np

# Page Config
st.set_page_config(page_title="Visualisor", layout="wide")
st.title("📊 Visualisor: Your Data, Your Vision")

# --- SIDEBAR NAVIGATION ---
st.sidebar.header("Navigation")
app_mode = st.sidebar.selectbox("Choose a Section", ["Data Input & Viz", "Analysis Tools"])

# --- SHARED DATA INITIALIZATION ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["X", "Y"])

# --- SECTION 1: DATA INPUT & VIZ ---
if app_mode == "Data Input & Viz":
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Load Data")
        upload_choice = st.radio("Source:", ["Upload CSV", "Manual Entry"])
        
        if upload_choice == "Upload CSV":
            uploaded_file = st.file_uploader("Upload your file", type=["csv"])
            if uploaded_file:
                st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.info("Edit the table below to add data:")
            st.session_state.df = st.data_editor(st.session_state.df, num_rows="dynamic")

    with col2:
        st.subheader("2. Configure Visualization")
        df = st.session_state.df
        
        if not df.empty and len(df.columns) >= 2:
            chart_type = st.selectbox("Chart Type", ["Line/Scatter", "Pie Chart", "Histogram"])
            title = st.text_input("Chart Title", "My Visualization")
            
            # Dynamic Columns based on data
            cols = df.columns.tolist()
            
            if chart_type == "Line/Scatter":
                x_axis = st.selectbox("X Axis", cols)
                y_axis = st.selectbox("Y Axis", cols)
                mode = st.toggle("Show as Points (Scatter)")
                animate = st.toggle("Animated Preview (requires sequential data)")
                
                if animate:
                    fig = px.scatter(df, x=x_axis, y=y_axis, animation_frame=x_axis, title=title)
                else:
                    fig = px.scatter(df, x=x_axis, y=y_axis, title=title) if mode else px.line(df, x=x_axis, y=y_axis, title=title)

            elif chart_type == "Pie Chart":
                names = st.selectbox("Labels Column", cols)
                values = st.selectbox("Values Column", cols)
                hole_size = st.slider("Donut Hole Size", 0.0, 0.9, 0.4)
                fig = px.pie(df, names=names, values=values, title=title, hole=hole_size)

            elif chart_type == "Histogram":
                x_hist = st.selectbox("Select Column", cols)
                bins = st.slider("Bins", 5, 100, 20)
                fig = px.histogram(df, x=x_hist, nbins=bins, title=title)

            # --- DISPLAY & DOWNLOAD ---
            st.plotly_chart(fig, use_container_width=True)
            
            # Export Logic
            img_format = st.selectbox("Download Format", ["png", "jpg", "svg", "pdf"])
            if st.button(f"Generate Downloadable {img_format.upper()}"):
                fig.write_image(f"viz.{img_format}")
                with open(f"viz.{img_format}", "rb") as f:
                    st.download_button("Click here to Download", f, file_name=f"visualization.{img_format}")
        else:
            st.warning("Please enter at least two columns of data to visualize.")

# --- SECTION 2: ANALYSIS TOOLS ---
elif app_mode == "Analysis Tools":
    st.subheader("🛠️ Data Analysis Toolkit")
    df = st.session_state.df
    
    if df.empty:
        st.error("No data found! Go to 'Data Input & Viz' first.")
    else:
        tab1, tab2 = st.tabs(["Statistics (Mean/Median)", "Linear Interpolation"])
        
        with tab1:
            target_col = st.selectbox("Select Numeric Column", df.select_dtypes(include=np.number).columns)
            if target_col:
                c1, c2, c3 = st.columns(3)
                c1.metric("Average (Mean)", round(df[target_col].mean(), 2))
                c2.metric("Median", round(df[target_col].median(), 2))
                c3.metric("Std Deviation", round(df[target_col].std(), 2))

        with tab2:
            st.write("Estimate missing values between points.")
            x_col = st.selectbox("X (Independent)", df.columns, key="interp_x")
            y_col = st.selectbox("Y (Dependent)", df.columns, key="interp_y")
            
            target_x = st.number_input(f"Enter {x_col} to find {y_col}:", value=0.0)
            
            if st.button("Interpolate"):
                try:
                    f = interp1d(df[x_col], df[y_col], kind='linear', fill_value="extrapolate")
                    result = f(target_x)
                    st.success(f"The interpolated value for {y_col} is: **{result:.4f}**")
                except Exception as e:
                    st.error(f"Error: {e}. Ensure X is sorted and contains only numbers.")