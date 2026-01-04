# Streamlit Cloud with MongoDB Atlas
# Real data from MongoDB Atlas cloud database

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from pymongo import MongoClient
import os
from datetime import datetime

# MongoDB Atlas connection
@st.cache_resource
def init_mongodb():
    """Initialize MongoDB Atlas connection"""
    # Get connection string from Streamlit secrets or environment
    try:
        # Try Streamlit secrets first (for cloud deployment)
        atlas_uri = st.secrets["MONGODB_URI"]
    except:
        # Fallback to environment variable (for local testing)
        atlas_uri = os.getenv("MONGODB_URI")
    
    if not atlas_uri:
        st.error("❌ MongoDB Atlas connection string not configured!")
        st.info("Please add MONGODB_URI to your Streamlit secrets or environment variables")
        return None
    
    try:
        client = MongoClient(atlas_uri)
        # Test connection
        client.admin.command('ping')
        db = client["hippparcos_db"]
        return db
    except Exception as e:
        st.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
        return None

# Load data from Atlas
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_atlas_data():
    """Load star data from MongoDB Atlas"""
    db = init_mongodb()
    if not db:
        return None
    
    try:
        # Load data from Atlas
        collection = db["stars"]
        
        # Get total count
        total_count = collection.count_documents({})
        st.sidebar.info(f"📊 Connected to Atlas: {total_count:,} stars available")
        
        # Load a reasonable sample for web performance
        sample_size = min(50000, total_count)  # Max 50k for web performance
        
        # Get random sample
        pipeline = [{"$sample": {"size": sample_size}}]
        cursor = collection.aggregate(pipeline)
        
        # Convert to DataFrame
        data = list(cursor)
        if not data:
            st.error("❌ No data found in Atlas collection")
            return None
            
        df = pd.DataFrame(data)
        
        # Clean up MongoDB ObjectId
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading data from Atlas: {str(e)}")
        return None

# Fallback sample data (if Atlas connection fails)
@st.cache_data
def load_sample_data():
    """Fallback sample data if Atlas is unavailable"""
    np.random.seed(42)
    n_stars = 10000
    
    data = {
        'HIP': range(1, n_stars + 1),
        'RAhms': np.random.uniform(0, 24, n_stars),
        'DEdms': np.random.uniform(-90, 90, n_stars),
        'Vmag': np.random.normal(9, 2, n_stars),
        'BV': np.random.normal(0.7, 0.4, n_stars),
        'Dist': np.random.exponential(100, n_stars),
        'AbsMag': np.random.normal(4, 3, n_stars),
        'SpType': np.random.choice(['O', 'B', 'A', 'F', 'G', 'K', 'M'], n_stars)
    }
    
    return pd.DataFrame(data)

# Page configuration
st.set_page_config(
    page_title="STAR Analysis - Atlas Edition", 
    page_icon="⭐",
    layout="wide"
)

# Main title
st.title("🌟 STAR - Satellite Transmission Analysis Reduction")
st.subheader("MongoDB Atlas Edition - Real Hipparcos Data")

# Load data (try Atlas first, fallback to sample)
df = load_atlas_data()
if df is None:
    st.warning("⚠️ Using sample data - Atlas connection failed")
    df = load_sample_data()
    data_source = "Sample Data"
else:
    data_source = "MongoDB Atlas"

# Sidebar navigation
st.sidebar.title("🚀 Navigation")
st.sidebar.success(f"✅ {len(df):,} stars loaded from {data_source}")

page = st.sidebar.selectbox(
    "Choose a page:",
    ["📊 Overview", "🌟 Star Explorer", "📈 HR Diagram", "🌌 Space Facts"]
)

# Page content
if page == "📊 Overview":
    st.header("📊 Dataset Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Stars", f"{len(df):,}")
    
    with col2:
        avg_mag = df['Vmag'].mean()
        st.metric("Average Magnitude", f"{avg_mag:.2f}")
    
    with col3:
        if 'Dist' in df.columns:
            max_dist = df['Dist'].max()
            st.metric("Max Distance", f"{max_dist:.1f} pc")
        else:
            st.metric("Data Source", data_source)
    
    with col4:
        if 'SpType' in df.columns:
            unique_types = df['SpType'].nunique()
            st.metric("Spectral Types", unique_types)
        else:
            st.metric("Database", "MongoDB Atlas")
    
    # Display sample data
    st.subheader("Sample Data")
    st.dataframe(df.head(10))
    
    # Distribution plots
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Magnitude Distribution")
        if 'Vmag' in df.columns:
            fig = px.histogram(df, x='Vmag', nbins=50, title="Visual Magnitude Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Spectral Type Distribution")
        if 'SpType' in df.columns:
            type_counts = df['SpType'].value_counts()
            fig = px.pie(values=type_counts.values, names=type_counts.index, 
                        title="Stellar Classification")
            st.plotly_chart(fig, use_container_width=True)

elif page == "🌟 Star Explorer":
    st.header("🌟 Interactive Star Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Vmag' in df.columns:
            mag_range = st.slider("Visual Magnitude Range", 
                                 float(df['Vmag'].min()), 
                                 float(df['Vmag'].max()), 
                                 (5.0, 10.0))
        else:
            mag_range = (5.0, 10.0)
    
    with col2:
        if 'SpType' in df.columns:
            selected_types = st.multiselect(
                "Spectral Types",
                df['SpType'].unique(),
                default=list(df['SpType'].unique())[:3]
            )
        else:
            selected_types = ['G', 'K', 'M']
    
    with col3:
        max_records = st.slider("Maximum Records to Display", 100, 5000, 1000)
    
    # Filter data
    filtered_df = df.copy()
    if 'Vmag' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['Vmag'] >= mag_range[0]) & 
            (filtered_df['Vmag'] <= mag_range[1])
        ]
    if 'SpType' in df.columns and selected_types:
        filtered_df = filtered_df[filtered_df['SpType'].isin(selected_types)]
    
    # Limit for performance
    filtered_df = filtered_df.head(max_records)
    
    st.info(f"Showing {len(filtered_df):,} stars matching your criteria")
    
    # Interactive scatter plot
    if len(filtered_df) > 0:
        # Use available columns for plotting
        x_col = 'RAhms' if 'RAhms' in filtered_df.columns else 'RA' if 'RA' in filtered_df.columns else filtered_df.columns[1]
        y_col = 'DEdms' if 'DEdms' in filtered_df.columns else 'DE' if 'DE' in filtered_df.columns else filtered_df.columns[2]
        color_col = 'Vmag' if 'Vmag' in filtered_df.columns else filtered_df.columns[3]
        
        fig = px.scatter(
            filtered_df.head(2000),  # Limit for performance
            x=x_col, 
            y=y_col,
            color=color_col,
            title="Star Positions (Sky Map)",
            hover_data=['HIP'] if 'HIP' in filtered_df.columns else None
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "📈 HR Diagram":
    st.header("📈 Hertzsprung-Russell Diagram")
    
    st.write("The HR diagram shows the relationship between stars' absolute magnitude and color index.")
    
    # Sample for better performance
    sample_df = df.sample(min(3000, len(df)))
    
    if 'BV' in sample_df.columns and 'AbsMag' in sample_df.columns:
        # Create HR diagram with real data
        fig = px.scatter(
            sample_df,
            x='BV',
            y='AbsMag',
            color='SpType' if 'SpType' in sample_df.columns else None,
            title="Hertzsprung-Russell Diagram - Real Hipparcos Data",
            labels={
                'BV': 'B-V Color Index',
                'AbsMag': 'Absolute Magnitude'
            }
        )
        
        # Invert y-axis (brighter stars at top)
        fig.update_yaxes(autorange="reversed")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("HR Diagram requires B-V color index and absolute magnitude data")
        st.info("This feature works best with the full Atlas dataset")

elif page == "🌌 Space Facts":
    st.header("🌌 Fascinating Space Facts")
    
    facts = [
        f"🌟 This app is connected to MongoDB Atlas with {len(df):,} real stars!",
        "🔭 The Hipparcos satellite measured star positions with unprecedented precision!",
        "☀️ Our Sun is a G-type main sequence star, just one of billions in our galaxy.",
        "⭐ The brightest stars have negative magnitudes!",
        "🌌 Our galaxy contains over 100 billion stars!",
        "🔴 Red giants can be 100 times larger than our Sun!",
        "🌟 The nearest star to Earth (besides the Sun) is Proxima Centauri at 4.24 light-years away.",
        "⚫ Some stars are so massive they will eventually become black holes.",
        "🌈 The color of a star tells us its temperature - blue stars are hottest, red stars are coolest."
    ]
    
    if st.button("Get Random Space Fact"):
        fact = np.random.choice(facts)
        st.success(fact)
    
    st.subheader("About This Project")
    st.write(f"""
    This STAR (Satellite Transmission Analysis Reduction) project showcases:
    
    - **Real Data**: Connected to MongoDB Atlas with {len(df):,} stars
    - **Data Source**: {data_source}
    - **Visualization**: Interactive charts and plots
    - **Cloud Deployment**: Streamlit Cloud with Atlas backend
    - **Big Data Tools**: MongoDB Atlas, Python, Streamlit
    
    The project demonstrates a complete big data pipeline from space agency data 
    to cloud-hosted interactive web application.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**STAR Project** - MongoDB Atlas Edition")
st.sidebar.markdown(f"Data Source: {data_source}")

# Show connection status
if data_source == "MongoDB Atlas":
    st.sidebar.success("☁️ Connected to MongoDB Atlas")
else:
    st.sidebar.warning("⚠️ Using fallback sample data")
