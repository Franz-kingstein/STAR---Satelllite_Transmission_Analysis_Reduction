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
    
    # Generate realistic star data based on Hipparcos catalog structure
    data = {
        'HIP': range(1, n_stars + 1),
        'RAhms': np.random.uniform(0, 24, n_stars),  # Right Ascension in hours
        'DEdms': np.random.uniform(-90, 90, n_stars),  # Declination in degrees
        'Vmag': np.random.normal(9, 2, n_stars),  # Visual magnitude
        'BV': np.random.normal(0.7, 0.4, n_stars),  # B-V color index
        'Dist': np.random.exponential(100, n_stars),  # Distance in parsecs
        'AbsMag': np.random.normal(4, 3, n_stars),  # Absolute magnitude
        'SpType': np.random.choice(['O', 'B', 'A', 'F', 'G', 'K', 'M'], n_stars)
    }
    
    return pd.DataFrame(data)

# Page configuration
st.set_page_config(
    page_title="STAR Analysis - Cloud Demo", 
    page_icon="⭐",
    layout="wide"
)

# Main title
st.title("STAR - Satellite Transmission Analysis Reduction")
st.subheader("Cloud Demo Version - Big Data Tools and Techniques Project")

# Load data
df = load_sample_data()

# Sidebar navigation
st.sidebar.title("Navigation")

page = st.sidebar.selectbox(
    "Choose a page:",
    ["Overview", "Star Explorer", "HR Diagram", "Space Facts"]
)

st.sidebar.success(f"✓ {len(df):,} stars loaded")

# Page content
if page == "Overview":
    st.header("Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Stars", f"{len(df):,}")
    
    with col2:
        avg_mag = df['Vmag'].mean()
        st.metric("Average Magnitude", f"{avg_mag:.2f}")
    
    with col3:
        max_dist = df['Dist'].max()
        st.metric("Max Distance", f"{max_dist:.1f} pc")
    
    with col4:
        unique_types = df['SpType'].nunique()
        st.metric("Spectral Types", unique_types)
    
    # Display sample data
    st.subheader("Sample Data")
    st.dataframe(df.head(10))
    
    # Distribution plots
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Magnitude Distribution")
        fig, ax = plt.subplots()
        ax.hist(df['Vmag'], bins=50, alpha=0.7, color='skyblue')
        ax.set_xlabel('Visual Magnitude')
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
    
    with col2:
        st.subheader("Spectral Type Distribution")
        type_counts = df['SpType'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%')
        st.pyplot(fig)

elif page == "Star Explorer":
    st.header("Interactive Star Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mag_range = st.slider("Visual Magnitude Range", 
                             float(df['Vmag'].min()), 
                             float(df['Vmag'].max()), 
                             (5.0, 10.0))
    
    with col2:
        selected_types = st.multiselect(
            "Spectral Types",
            df['SpType'].unique(),
            default=['G', 'K', 'M']
        )
    
    with col3:
        max_distance = st.slider("Maximum Distance (pc)", 
                                1, int(df['Dist'].max()), 200)
    
    # Filter data
    filtered_df = df[
        (df['Vmag'] >= mag_range[0]) & 
        (df['Vmag'] <= mag_range[1]) &
        (df['SpType'].isin(selected_types)) &
        (df['Dist'] <= max_distance)
    ]
    
    st.info(f"Showing {len(filtered_df):,} stars matching your criteria")
    
    # Interactive scatter plot using Plotly
    if len(filtered_df) > 0:
        fig = px.scatter(
            filtered_df, 
            x='RAhms', 
            y='DEdms',
            color='Vmag',
            size='Dist',
            hover_data=['HIP', 'SpType', 'BV'],
            title="Star Positions (Right Ascension vs Declination)"
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "HR Diagram":
    st.header("Hertzsprung-Russell Diagram")
    
    st.write("The HR diagram shows the relationship between stars' absolute magnitude and color index.")
    
    # Sample for better performance
    sample_df = df.sample(min(2000, len(df)))
    
    # Create HR diagram with Plotly
    fig = px.scatter(
        sample_df,
        x='BV',
        y='AbsMag',
        color='SpType',
        title="Hertzsprung-Russell Diagram",
        labels={
            'BV': 'B-V Color Index',
            'AbsMag': 'Absolute Magnitude'
        }
    )
    
    # Invert y-axis (brighter stars at top)
    fig.update_yaxes(autorange="reversed")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.subheader("Understanding the HR Diagram")
    st.write("""
    - **Main Sequence**: Most stars fall along a diagonal band
    - **Red Giants**: Upper right (cool but very bright)
    - **White Dwarfs**: Lower left (hot but dim)
    - **Color Index**: Blue stars (negative B-V) vs Red stars (positive B-V)
    """)

elif page == "Space Facts":
    st.header("Fascinating Space Facts")
    
    facts = [
        "The Hipparcos satellite measured star positions with unprecedented precision!",
        "Our Sun is a G-type main sequence star, just one of billions in our galaxy.",
        "The brightest stars have negative magnitudes!",
        "Our galaxy contains over 100 billion stars!",
        "Red giants can be 100 times larger than our Sun!",
        "The nearest star to Earth (besides the Sun) is Proxima Centauri at 4.24 light-years away.",
        "Some stars are so massive they will eventually become black holes.",
        "The color of a star tells us its temperature - blue stars are hottest, red stars are coolest."
    ]
    
    if st.button("Get Random Space Fact"):
        fact = random.choice(facts)
        st.success(fact)
    
    st.subheader("About This Project")
    st.write("""
    This is a demonstration of the STAR (Satellite Transmission Analysis Reduction) project 
    for the Big Data Tools and Techniques course. The project showcases:
    
    - **Data Processing**: Handling large astronomical datasets
    - **Visualization**: Interactive charts and plots
    - **Web Deployment**: Cloud-hosted Streamlit application
    - **Big Data Tools**: MongoDB, Python, Streamlit, Docker
    
    The full project includes a complete MongoDB database with 118,218 real stars 
    from the European Space Agency's Hipparcos catalog.
    """)
    
    st.subheader("Technologies Used")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Backend:**")
        st.write("- Python 3.x")
        st.write("- MongoDB")
        st.write("- Pandas/NumPy")
        
    with col2:
        st.write("**Frontend:**")
        st.write("- Streamlit")
        st.write("- Plotly")
        st.write("- Matplotlib")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**STAR Project** - Big Data Tools and Techniques")
st.sidebar.markdown("Cloud Demo Version")
