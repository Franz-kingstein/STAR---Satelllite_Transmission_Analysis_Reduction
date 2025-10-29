# Streamlit Cloud Deployment - STAR Analysis
# Cloud-optimized version of the STAR project

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import random

# For Streamlit Cloud, we'll include a sample dataset
@st.cache_data
def load_sample_data():
    """Load a sample of the Hipparcos data for cloud deployment"""
    # Generate sample star data for demonstration
    np.random.seed(42)  # For reproducible results
    
    # Generate sample star data
    n_stars = 10000  # Smaller dataset for cloud hosting
    
    data = {
        'HIP': range(1, n_stars + 1),
        'Vmag': np.random.normal(8, 3, n_stars),
        'Distance_pc': np.random.exponential(50, n_stars),
        'B-V': np.random.normal(0.6, 0.4, n_stars),
        'RA': np.random.uniform(0, 360, n_stars),
        'DE': np.random.uniform(-90, 90, n_stars),
        'SpType': np.random.choice(['O', 'B', 'A', 'F', 'G', 'K', 'M'], n_stars, p=[0.01, 0.05, 0.1, 0.15, 0.25, 0.3, 0.14])
    }
    
    return pd.DataFrame(data)

# Main app configuration
st.set_page_config(
    page_title="🌟 STAR Analysis - Cloud Demo", 
    page_icon="🌟",
    layout="wide"
)

st.title("🌟 STAR - Satellite Transmission Analysis Reduction")
st.markdown("### Hipparcos Star Catalog Analysis (Cloud Demo)")

# Load data
df = load_sample_data()

# Sidebar
st.sidebar.title("🚀 Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["📊 Overview", "🌟 Star Explorer", "📈 HR Diagram", "🌌 Space Facts"]
)

# Display connection info
st.sidebar.success(f"✅ {len(df):,} stars loaded")
st.sidebar.info("🌥️ Running on Cloud")

if page == "📊 Overview":
    st.header("📊 Dataset Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Stars", f"{len(df):,}")
    with col2:
        bright_stars = len(df[df['Vmag'] < 6])
        st.metric("Visible Stars", f"{bright_stars:,}")
    with col3:
        nearby_stars = len(df[df['Distance_pc'] < 50])
        st.metric("Nearby Stars", f"{nearby_stars:,}")
    with col4:
        avg_magnitude = df['Vmag'].mean()
        st.metric("Avg Magnitude", f"{avg_magnitude:.2f}")
    
    # Spectral type distribution
    st.subheader("🌈 Spectral Type Distribution")
    spectral_counts = df['SpType'].value_counts()
    
    fig_bar = px.bar(
        x=spectral_counts.index, 
        y=spectral_counts.values,
        title="Star Count by Spectral Type",
        labels={'x': 'Spectral Type', 'y': 'Count'},
        color=spectral_counts.values,
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "🌟 Star Explorer":
    st.header("🌟 Interactive Star Explorer")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        mag_range = st.slider("Visual Magnitude Range", 
                             float(df['Vmag'].min()), 
                             float(df['Vmag'].max()), 
                             (2.0, 10.0))
    with col2:
        distance_range = st.slider("Distance Range (parsecs)", 
                                  0, int(df['Distance_pc'].max()), 
                                  (0, 100))
    
    # Filter data
    filtered_df = df[
        (df['Vmag'] >= mag_range[0]) & 
        (df['Vmag'] <= mag_range[1]) &
        (df['Distance_pc'] >= distance_range[0]) & 
        (df['Distance_pc'] <= distance_range[1])
    ]
    
    st.success(f"Found {len(filtered_df):,} stars matching your criteria!")
    
    # 3D scatter plot
    if len(filtered_df) > 0:
        fig_3d = px.scatter_3d(
            filtered_df.sample(min(1000, len(filtered_df))), 
            x='RA', y='DE', z='Distance_pc',
            color='Vmag', 
            title='3D Star Map',
            labels={'RA': 'Right Ascension', 'DE': 'Declination', 'Distance_pc': 'Distance (pc)'}
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # Data table
        st.subheader("📋 Filtered Star Data")
        st.dataframe(filtered_df.head(100), use_container_width=True)

elif page == "📈 HR Diagram":
    st.header("📈 Hertzsprung-Russell Diagram")
    
    # Calculate absolute magnitude
    df_hr = df.copy()
    df_hr['Absolute_Magnitude'] = df_hr['Vmag'] - 5 * np.log10(df_hr['Distance_pc']) + 5
    
    # Clean data
    df_hr = df_hr.dropna(subset=['B-V', 'Absolute_Magnitude'])
    df_hr = df_hr[(df_hr['Absolute_Magnitude'] > -5) & (df_hr['Absolute_Magnitude'] < 15)]
    
    # Sample for performance
    sample_size = st.slider("Sample Size", 1000, len(df_hr), 5000)
    df_sample = df_hr.sample(min(sample_size, len(df_hr)))
    
    # HR Diagram
    fig_hr = px.scatter(
        df_sample, 
        x='B-V', 
        y='Absolute_Magnitude',
        color='SpType',
        title=f'Hertzsprung-Russell Diagram ({len(df_sample):,} stars)',
        labels={'B-V': 'B-V Color Index', 'Absolute_Magnitude': 'Absolute Magnitude'}
    )
    fig_hr.update_yaxis(autorange='reversed')  # Brighter stars at top
    st.plotly_chart(fig_hr, use_container_width=True)

elif page == "🌌 Space Facts":
    st.header("🌌 Fascinating Space Facts")
    
    space_facts = [
        "🌟 The Hipparcos satellite measured star positions with unprecedented precision!",
        "🔭 A parsec is approximately 3.26 light-years!",
        "⭐ The brightest stars have negative magnitudes!",
        "🌌 Our galaxy contains over 100 billion stars!",
        "💫 Red giants can be 100 times larger than our Sun!",
        "🌠 Blue stars burn hot but live only a few million years!",
    ]
    
    if st.button("🎲 Random Space Fact"):
        fact = random.choice(space_facts)
        st.info(fact)
    
    # Statistics
    st.subheader("📊 Dataset Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        brightest = df['Vmag'].min()
        st.metric("Brightest Star", f"{brightest:.2f} mag")
    
    with col2:
        farthest = df['Distance_pc'].max()
        st.metric("Farthest Star", f"{farthest:.1f} pc")
    
    with col3:
        spectral_types = df['SpType'].nunique()
        st.metric("Spectral Types", spectral_types)

# Footer
st.markdown("---")
st.markdown("*🌟 STAR Analysis - Deployed on Streamlit Community Cloud*")
st.markdown("*Data: ESA Hipparcos Mission • Built with Streamlit*")
