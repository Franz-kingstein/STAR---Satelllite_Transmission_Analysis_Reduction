import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import random
import os
from datetime import datetime

st.set_page_config(
    page_title="🌟 STAR - Satellite Analysis", 
    page_icon="🌟",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🚀 Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["📊 Overview", "🌟 Star Explorer", "📈 HR Diagram", "🎯 Star Search", "🌌 Space Facts", "📡 Mission Info"]
)

st.title("🌟 STAR - Satellite Transmission Analysis Reduction")
st.markdown("*Hipparcos Star Catalog Data Analysis and Visualization Platform*")

# MongoDB connection with Docker support
@st.cache_resource
def get_collection():
    """Get MongoDB collection with Docker environment support"""
    try:
        # Get MongoDB URI from environment variable (Docker) or use default (local)
        uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/hippparcos_db')
        
        # Show connection info in sidebar
        with st.sidebar:
            connection_display = uri.split('@')[-1] if '@' in uri else uri
            st.info(f"🔗 Database: `{connection_display}`")
        
        # Connect with appropriate timeout
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.server_info()
        
        # Access database and collection
        db = client["hippparcos_db"]
        collection = db["stars"]
        
        # Verify collection has data
        total_docs = collection.count_documents({})
        if total_docs == 0:
            st.error("❌ No data found in database.")
            st.info("🔧 Data import may still be in progress. Please wait or refresh the page.")
            
            # Check if we're in Docker and show import status
            if os.path.exists('/.dockerenv'):
                st.info("🐳 Running in Docker - data import should complete automatically")
            else:
                st.info("💻 Running locally - run `python import_data.py` to import data")
            st.stop()
        
        # Success message in sidebar
        with st.sidebar:
            st.success(f"✅ Connected! {total_docs:,} stars loaded")
            
            # Show deployment info
            is_docker = os.path.exists('/.dockerenv')
            if is_docker:
                st.success("🐳 Running in Docker")
            else:
                st.info("💻 Running locally")
        
        return collection
        
    except ServerSelectionTimeoutError as e:
        st.error(f"❌ MongoDB connection timeout: {e}")
        show_connection_troubleshooting()
        st.stop()
        
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        show_connection_troubleshooting()
        st.stop()

def show_connection_troubleshooting():
    """Show troubleshooting information for connection issues"""
    with st.expander("🔧 Troubleshooting Connection Issues"):
        st.write("**Possible solutions:**")
        
        if os.path.exists('/.dockerenv'):
            st.write("🐳 **Docker Environment Detected:**")
            st.write("1. MongoDB container may still be starting up")
            st.write("2. Wait 30-60 seconds and refresh the page")
            st.write("3. Check Docker logs: `docker-compose logs mongodb`")
        else:
            st.write("💻 **Local Environment Detected:**")
            st.write("1. Start MongoDB: `docker-compose up -d mongodb`")
            st.write("2. Import data: `python import_data.py`")
            st.write("3. Check MongoDB is running: `docker ps`")
        
        st.write("**General checks:**")
        st.write("4. Verify network connectivity")
        st.write("5. Check MongoDB URI in environment variables")
        
        if st.button("🔄 Retry Connection"):
            st.cache_resource.clear()
            st.rerun()

# Get database connection
collection = get_collection()

# Space facts and interesting data
space_facts = [
    "🌟 The Hipparcos satellite measured the positions of over 100,000 stars with unprecedented precision!",
    "🔭 A parsec (pc) is approximately 3.26 light-years or 19.2 trillion miles!",
    "⭐ The brightest star in our catalog has a visual magnitude as low as -1.5!",
    "🌌 Stellar parallax was first successfully measured in 1838 by Friedrich Bessel!",
    "💫 Red giants can be up to 100 times larger than our Sun!",
    "🌠 The nearest star to Earth (besides the Sun) is Proxima Centauri at 4.24 light-years away!",
    "🔥 Blue stars burn so hot and bright that they only live for a few million years!",
    "❄️ Brown dwarfs are 'failed stars' that never got hot enough to start nuclear fusion!"
]

# Display a random space fact
if 'current_fact' not in st.session_state:
    st.session_state.current_fact = random.choice(space_facts)

if st.sidebar.button("🎲 New Space Fact"):
    st.session_state.current_fact = random.choice(space_facts)

st.sidebar.info(st.session_state.current_fact)

# Main content based on selected page
if page == "📊 Overview":
    st.header("📊 Database Overview")
    
    # Enhanced metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        total = collection.count_documents({})
        st.metric("Total Stars", f"{total:,}")
    with c2:
        with_dist = collection.count_documents({'Distance_pc': {'$ne': None}})
        st.metric("Stars with Distance", f"{with_dist:,}")
    with c3:
        bright_stars = collection.count_documents({'Vmag': {'$lt': 6}})
        st.metric("Visible Stars (Vmag < 6)", f"{bright_stars:,}")
    with c4:
        nearby_stars = collection.count_documents({'Distance_pc': {'$lt': 50, '$ne': None}})
        st.metric("Nearby Stars (<50 pc)", f"{nearby_stars:,}")

    # Top spectral types
    st.subheader("🌈 Top 10 Spectral Types")
    pipeline = [
        {"$match": {"SpType": {"$ne": None}, "Vmag": {"$ne": None}}},
        {"$group": {"_id": "$SpType", "count": {"$sum": 1}, "avgVmag": {"$avg": "$Vmag"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    df = pd.DataFrame(list(collection.aggregate(pipeline))).rename(
        columns={"_id": "Spectral Type", "count": "Count", "avgVmag": "Avg Vmag"}
    )
    st.dataframe(df, use_container_width=True)
    
    # Distance distribution histogram
    st.subheader("📏 Distance Distribution")
    dist_pipeline = [
        {"$match": {"Distance_pc": {"$ne": None, "$lt": 200}}},
        {"$bucket": {
            "groupBy": "$Distance_pc",
            "boundaries": [0, 10, 25, 50, 100, 200],
            "default": "200+",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    dist_data = list(collection.aggregate(dist_pipeline))
    if dist_data:
        distances = [d['_id'] for d in dist_data]
        counts = [d['count'] for d in dist_data]
        
        fig_dist, ax_dist = plt.subplots(figsize=(10, 6))
        bars = ax_dist.bar(['0-10', '10-25', '25-50', '50-100', '100-200'], counts, 
                          color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        ax_dist.set_xlabel('Distance Range (parsecs)')
        ax_dist.set_ylabel('Number of Stars')
        ax_dist.set_title('Distribution of Stars by Distance')
        ax_dist.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax_dist.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}', ha='center', va='bottom')
        
        st.pyplot(fig_dist)

elif page == "🌟 Star Explorer":
    st.header("🌟 Interactive Star Explorer")
    
    # Star brightness filter
    col1, col2 = st.columns(2)
    with col1:
        mag_range = st.slider("Visual Magnitude Range", -2.0, 15.0, (-1.0, 6.0))
    with col2:
        distance_range = st.slider("Distance Range (parsecs)", 0, 200, (0, 100))
    
    # Additional filters
    col3, col4 = st.columns(2)
    with col3:
        spectral_filter = st.text_input("Spectral Type Filter (optional, e.g., 'G', 'M', 'K1'):")
    with col4:
        limit = st.selectbox("Number of results:", [100, 500, 1000, 2000])
    
    # Build query
    query = {
        "Vmag": {"$gte": mag_range[0], "$lte": mag_range[1], "$ne": None},
        "Distance_pc": {"$gte": distance_range[0], "$lte": distance_range[1], "$ne": None}
    }
    
    if spectral_filter:
        query["SpType"] = {"$regex": spectral_filter, "$options": "i"}
    
    stars = list(collection.find(query).limit(limit))
    
    if stars:
        st.success(f"Found {len(stars)} stars matching your criteria!")
        
        star_df = pd.DataFrame(stars)
        
        # Sky map visualization
        if 'RA' in star_df.columns and 'DE' in star_df.columns:
            st.subheader("🗺️ Sky Map")
            fig_sky, ax_sky = plt.subplots(figsize=(12, 8), subplot_kw=dict(projection='mollweide'))
            
            # Convert RA from degrees to radians and center on 0
            ra_rad = np.radians(star_df['RA'] - 180)
            de_rad = np.radians(star_df['DE'])
            
            scatter = ax_sky.scatter(ra_rad, de_rad, c=star_df['Vmag'], s=20, 
                                   cmap='viridis_r', alpha=0.7)
            ax_sky.set_xlabel('Right Ascension')
            ax_sky.set_ylabel('Declination')
            ax_sky.set_title('Sky Distribution of Selected Stars')
            ax_sky.grid(True, alpha=0.3)
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax_sky, shrink=0.8)
            cbar.set_label('Visual Magnitude')
            
            st.pyplot(fig_sky)
        
        # Brightness vs Distance scatter plot
        if 'Vmag' in star_df.columns and 'Distance_pc' in star_df.columns:
            st.subheader("💫 Brightness vs Distance")
            fig_bd, ax_bd = plt.subplots(figsize=(10, 6))
            
            scatter_bd = ax_bd.scatter(star_df['Distance_pc'], star_df['Vmag'], 
                                     alpha=0.6, s=30, c=star_df['Distance_pc'], cmap='plasma')
            ax_bd.set_xlabel('Distance (parsecs)')
            ax_bd.set_ylabel('Visual Magnitude (brighter ↑)')
            ax_bd.set_title('Star Brightness vs Distance')
            ax_bd.invert_yaxis()  # Brighter stars (lower magnitude) at top
            ax_bd.grid(True, alpha=0.3)
            
            plt.colorbar(scatter_bd, ax=ax_bd, label='Distance (pc)')
            st.pyplot(fig_bd)
        
        # Show sample stars table
        st.subheader("📋 Star Data Table")
        display_cols = ['HIP', 'Vmag', 'SpType', 'Distance_pc', 'B-V', 'RA', 'DE']
        available_cols = [col for col in display_cols if col in star_df.columns]
        st.dataframe(star_df[available_cols].head(50), use_container_width=True)
        
        # Download option
        csv = star_df[available_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download filtered data as CSV",
            data=csv,
            file_name=f"hipparcos_filtered_{len(stars)}_stars.csv",
            mime="text/csv"
        )
    else:
        st.warning("No stars found with the selected criteria. Try adjusting the filters!")

elif page == "📈 HR Diagram":
    st.header("📈 Hertzsprung–Russell Diagram")
    st.markdown("*The fundamental diagram relating stellar color to brightness*")
    
    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.slider("Sample size", 1000, 30000, 10000, 1000)
    with col2:
        color_by = st.selectbox("Color points by:", ["Density", "Spectral Type", "Distance"])

    cursor = collection.find(
        {"Distance_pc": {"$ne": None}, "Vmag": {"$ne": None}, "B-V": {"$ne": None}},
        {"Vmag": 1, "B-V": 1, "Distance_pc": 1, "SpType": 1, "_id": 0},
    ).limit(sample_size)

    hr_data = list(cursor)
    if hr_data:
        hr_df = pd.DataFrame(hr_data)
        
        # Calculate absolute magnitude
        hr_df['Absolute_Magnitude'] = hr_df['Vmag'] - 5 * np.log10(hr_df['Distance_pc']) + 5
        
        # Clean data
        hr_df = hr_df.dropna(subset=['B-V', 'Absolute_Magnitude'])
        
        fig_hr, ax_hr = plt.subplots(figsize=(12, 10))
        
        if color_by == "Spectral Type":
            # Color by spectral type
            spectral_colors = {'O': 'blue', 'B': 'lightblue', 'A': 'white', 'F': 'yellow', 
                             'G': 'orange', 'K': 'red', 'M': 'darkred'}
            colors = []
            for sptype in hr_df['SpType']:
                if pd.isna(sptype):
                    colors.append('gray')
                else:
                    first_char = str(sptype)[0] if len(str(sptype)) > 0 else 'U'
                    colors.append(spectral_colors.get(first_char, 'gray'))
            
            scatter = ax_hr.scatter(hr_df['B-V'], hr_df['Absolute_Magnitude'], 
                                  c=colors, s=20, alpha=0.6, edgecolors='none')
        elif color_by == "Distance":
            scatter = ax_hr.scatter(hr_df['B-V'], hr_df['Absolute_Magnitude'], 
                                  c=hr_df['Distance_pc'], s=20, alpha=0.6, 
                                  cmap='viridis', edgecolors='none')
            plt.colorbar(scatter, ax=ax_hr, label='Distance (pc)')
        else:
            # Density plot
            scatter = ax_hr.scatter(hr_df['B-V'], hr_df['Absolute_Magnitude'], 
                                  s=8, alpha=0.5, c='navy', edgecolors='none')
        
        ax_hr.invert_yaxis()
        ax_hr.set_xlabel("B-V Color Index (redder →)")
        ax_hr.set_ylabel("Absolute Magnitude (brighter ↑)")
        ax_hr.set_title(f"Hertzsprung-Russell Diagram ({len(hr_df):,} stars)")
        ax_hr.grid(True, ls="--", alpha=0.3)
        
        # Add main sequence guide line
        x_ms = np.linspace(-0.5, 2.0, 100)
        y_ms = 5 + 10 * x_ms  # Rough main sequence approximation
        ax_hr.plot(x_ms, y_ms, 'r--', alpha=0.7, linewidth=2, label='Main Sequence Guide')
        ax_hr.legend()
        
        st.pyplot(fig_hr)
        
        # Statistics
        st.subheader("📊 HR Diagram Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            bright_giants = len(hr_df[(hr_df['Absolute_Magnitude'] < 0) & (hr_df['B-V'] > 1.0)])
            st.metric("Bright Giants", bright_giants)
        with col2:
            main_sequence = len(hr_df[(hr_df['Absolute_Magnitude'] > 2) & (hr_df['Absolute_Magnitude'] < 15)])
            st.metric("Main Sequence Stars", main_sequence)
        with col3:
            white_dwarfs = len(hr_df[(hr_df['Absolute_Magnitude'] > 10) & (hr_df['B-V'] < 0.5)])
            st.metric("Possible White Dwarfs", white_dwarfs)

elif page == "🎯 Star Search":
    st.header("🎯 Individual Star Search")
    
    search_option = st.selectbox("Search by:", ["HIP Number", "Spectral Type", "Brightness Range", "Nearest Stars"])
    
    if search_option == "HIP Number":
        hip_number = st.number_input("Enter HIP number:", min_value=1, max_value=200000, value=1)
        if st.button("🔍 Search Star"):
            star = collection.find_one({"HIP": hip_number})
            if star:
                st.success(f"⭐ Found star HIP {hip_number}!")
                
                # Display star info in an attractive layout
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✨ Visual Magnitude", f"{star.get('Vmag', 'N/A')}")
                    st.metric("🌈 Spectral Type", f"{star.get('SpType', 'Unknown')}")
                with col2:
                    distance_pc = star.get('Distance_pc', 'Unknown')
                    st.metric("📏 Distance (pc)", f"{distance_pc}")
                    st.metric("🎨 B-V Color", f"{star.get('B-V', 'N/A')}")
                with col3:
                    if distance_pc != 'Unknown' and distance_pc:
                        ly_distance = round(distance_pc * 3.26, 1)
                        st.metric("🌌 Distance (light-years)", f"{ly_distance}")
                        
                        # Travel time calculations
                        st.subheader("🚀 Journey Times to This Star")
                        travel_times = {
                            "🚗 By car (60 mph)": f"{ly_distance * 6.7e6:.0e} years",
                            "✈️ By jet (500 mph)": f"{ly_distance * 8.0e5:.0e} years",
                            "🚀 Voyager 1": f"{ly_distance * 18000:.0f} years",
                            "⚡ At light speed": f"{ly_distance:.1f} years"
                        }
                        for method, time in travel_times.items():
                            st.write(f"{method}: **{time}**")
                
                # Show all available data
                st.subheader("📄 Complete Star Data")
                star_data = {k: v for k, v in star.items() if k != '_id'}
                st.json(star_data)
            else:
                st.error(f"❌ No star found with HIP number {hip_number}")
    
    elif search_option == "Nearest Stars":
        st.subheader("🌟 Find the Nearest Stars")
        max_distance = st.slider("Maximum distance (parsecs):", 1, 50, 25)
        
        nearest_stars = list(collection.find(
            {"Distance_pc": {"$lte": max_distance, "$ne": None}}
        ).sort("Distance_pc", 1).limit(20))
        
        if nearest_stars:
            st.success(f"Found {len(nearest_stars)} stars within {max_distance} parsecs!")
            
            # Create a dataframe for display
            nearest_df = pd.DataFrame(nearest_stars)
            if 'Distance_pc' in nearest_df.columns:
                nearest_df['Distance_ly'] = nearest_df['Distance_pc'] * 3.26
                display_cols = ['HIP', 'Vmag', 'SpType', 'Distance_pc', 'Distance_ly', 'B-V']
                available_cols = [col for col in display_cols if col in nearest_df.columns]
                
                # Format the dataframe for better display
                display_df = nearest_df[available_cols].copy()
                if 'Distance_pc' in display_df.columns:
                    display_df['Distance_pc'] = display_df['Distance_pc'].round(2)
                if 'Distance_ly' in display_df.columns:
                    display_df['Distance_ly'] = display_df['Distance_ly'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
                
                # Visualization of nearest stars
                if len(nearest_stars) > 5:
                    fig_nearest, ax_nearest = plt.subplots(figsize=(10, 6))
                    distances = [star['Distance_pc'] for star in nearest_stars if star.get('Distance_pc')]
                    magnitudes = [star.get('Vmag', 0) for star in nearest_stars if star.get('Vmag')]
                    
                    if distances and magnitudes:
                        scatter = ax_nearest.scatter(distances, magnitudes, s=100, alpha=0.7, c=distances, cmap='coolwarm')
                        ax_nearest.set_xlabel('Distance (parsecs)')
                        ax_nearest.set_ylabel('Visual Magnitude')
                        ax_nearest.set_title(f'Nearest {len(nearest_stars)} Stars')
                        ax_nearest.invert_yaxis()
                        ax_nearest.grid(True, alpha=0.3)
                        plt.colorbar(scatter, ax=ax_nearest, label='Distance (pc)')
                        st.pyplot(fig_nearest)

elif page == "🌌 Space Facts":
    st.header("🌌 Fascinating Space Facts & Data")
    
    st.markdown("""
    ### 🛰️ About the Hipparcos Mission
    
    The **Hipparcos** (High Precision Parallax Collecting Satellite) was a groundbreaking European Space Agency mission:
    
    - 🚀 **Launched**: August 8, 1989
    - 📡 **Mission Duration**: 4 years (1989-1993)  
    - 🎯 **Precision**: Measured star positions to 0.001 arcseconds!
    - 📊 **Stars Cataloged**: Over 100,000 stars
    - 🌟 **Legacy**: First space-based astrometry mission
    """)
    
    # Interactive statistics
    st.subheader("📊 Live Database Statistics")
    
    # Get interesting statistics
    total_stars = collection.count_documents({})
    giant_stars = collection.count_documents({"SpType": {"$regex": "III", "$options": "i"}})
    dwarf_stars = collection.count_documents({"SpType": {"$regex": "V", "$options": "i"}})
    very_bright = collection.count_documents({"Vmag": {"$lt": 3}})
    very_far = collection.count_documents({"Distance_pc": {"$gt": 100}})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔴 Giant Stars (Class III)", f"{giant_stars:,}")
        st.metric("⭐ Very Bright Stars (Vmag < 3)", f"{very_bright:,}")
    with col2:
        st.metric("🟡 Main Sequence (Class V)", f"{dwarf_stars:,}")
        st.metric("🌌 Distant Stars (>100 pc)", f"{very_far:,}")
    with col3:
        if total_stars > 0:
            giant_percent = round((giant_stars / total_stars) * 100, 1)
            bright_percent = round((very_bright / total_stars) * 100, 1)
            st.metric("% Giant Stars", f"{giant_percent}%")
            st.metric("% Very Bright Stars", f"{bright_percent}%")
    
    # Fun cosmic calculations
    st.subheader("🧮 Cosmic Journey Calculator")
    if st.button("🎲 Calculate Journey to Random Star"):
        random_star = collection.aggregate([
            {"$match": {"Distance_pc": {"$ne": None, "$gt": 1}}},
            {"$sample": {"size": 1}}
        ])
        star_data = list(random_star)
        
        if star_data:
            star = star_data[0]
            distance_pc = star['Distance_pc']
            distance_ly = distance_pc * 3.26
            
            st.markdown(f"""
            ### 🌟 Journey to HIP {star.get('HIP', 'Unknown')}
            **Star Details:**
            - 📏 Distance: {distance_pc:.1f} parsecs ({distance_ly:.1f} light-years)
            - ✨ Magnitude: {star.get('Vmag', 'Unknown')}
            - 🌈 Spectral Type: {star.get('SpType', 'Unknown')}
            
            **Travel Times:**
            - 🚗 By car (60 mph): **{distance_ly * 6.7e6:.0e} years**
            - ✈️ By commercial jet: **{distance_ly * 8.0e5:.0e} years**  
            - 🚀 By fastest spacecraft: **{distance_ly * 1.6e4:.0e} years**
            - ⚡ At light speed: **{distance_ly:.1f} years**
            """)
    
    # Stellar classification guide
    st.subheader("🌈 Stellar Classification Guide")
    st.markdown("""
    | Spectral Class | Color | Temperature (K) | Mass (Solar) | Examples |
    |----------------|-------|-----------------|--------------|----------|
    | O | Blue | 30,000+ | 15-90 | Alnitak, Mintaka |
    | B | Blue-white | 10,000-30,000 | 2.1-16 | Rigel, Spica |
    | A | White | 7,500-10,000 | 1.4-2.1 | Sirius, Vega |
    | F | Yellow-white | 6,000-7,500 | 1.04-1.4 | Canopus, Procyon |
    | G | Yellow | 5,200-6,000 | 0.8-1.04 | Sun, Alpha Centauri |
    | K | Orange | 3,700-5,200 | 0.45-0.8 | Arcturus, Aldebaran |
    | M | Red | 2,400-3,700 | 0.08-0.45 | Betelgeuse, Proxima Centauri |
    """)

elif page == "📡 Mission Info":
    st.header("📡 About This Application")
    
    st.markdown("""
    ### 🎯 Purpose
    This enhanced Streamlit application provides an interactive exploration of the **Hipparcos Star Catalog**, 
    one of the most important astronomical databases ever created. It combines scientific data visualization 
    with educational content about astronomy and space exploration.
    
    ### 🛠️ Technology Stack
    - **Database**: MongoDB for efficient storage and querying of star catalog data
    - **Backend**: Python with PyMongo for database operations and NumPy for calculations
    - **Frontend**: Streamlit for the interactive web interface
    - **Visualization**: Matplotlib for publication-quality plots and charts
    - **Data Processing**: Pandas for data manipulation and analysis
    - **Deployment**: Docker for containerized MongoDB instance
    
    ### 📊 Enhanced Features
    This version includes several new capabilities:
    
    #### 🌟 Interactive Navigation
    - Multi-page interface with sidebar navigation
    - Random space facts generator
    - Session state management for user experience
    
    #### 📈 Advanced Visualizations
    - Enhanced HR diagrams with spectral type coloring
    - Sky maps showing star positions
    - Distance distribution histograms
    - Brightness vs distance scatter plots
    
    #### 🔍 Smart Search & Filtering
    - Individual star lookup by HIP number
    - Nearest stars finder
    - Multi-parameter filtering (magnitude, distance, spectral type)
    - Real-time data exploration
    
    #### 🧮 Educational Content
    - Travel time calculations to stars
    - Stellar classification guide
    - Live database statistics
    - Space mission information
    """)
    
    # Show sample data structure
    sample_star = collection.find_one({})
    if sample_star:
        st.subheader("📋 Data Structure")
        st.write("Each star record contains the following fields:")
        
        fields_info = {
            "HIP": "Hipparcos catalog identifier number",
            "Vmag": "Visual magnitude (apparent brightness as seen from Earth)",
            "SpType": "Spectral classification (O,B,A,F,G,K,M with luminosity class)",
            "Distance_pc": "Distance in parsecs (1 pc ≈ 3.26 light-years)",
            "B-V": "Color index (blue minus visual magnitude)",
            "RA": "Right Ascension (celestial longitude coordinate)",
            "DE": "Declination (celestial latitude coordinate)",
        }
        
        available_fields = []
        for field, description in fields_info.items():
            if field in sample_star:
                available_fields.append(f"**{field}**: {description}")
        
        for field_desc in available_fields:
            st.markdown(f"- {field_desc}")
    
    # Usage statistics
    st.subheader("📈 Session Statistics")
    if 'page_visits' not in st.session_state:
        st.session_state.page_visits = {}
    
    current_page = page
    if current_page not in st.session_state.page_visits:
        st.session_state.page_visits[current_page] = 0
    st.session_state.page_visits[current_page] += 1
    
    st.write("**Pages visited this session:**")
    for visited_page, count in st.session_state.page_visits.items():
        st.write(f"- {visited_page}: {count} visits")
    
    # Performance info
    st.subheader("⚡ Performance Notes")
    st.markdown("""
    - **Caching**: Database connections are cached for optimal performance
    - **Sampling**: Large datasets are sampled to ensure responsive visualization
    - **Indexing**: MongoDB queries are optimized with appropriate indexes
    - **Memory**: Session state preserves user selections efficiently
    """)

# Footer
st.markdown("---")
st.markdown("*🌟 Built with Streamlit • Data from ESA Hipparcos Mission • Enhanced with astronomical insights*")
