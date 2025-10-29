#!/bin/bash
echo "🌟 Starting STAR Cloud Application..."
echo "Using app_cloud.py (no database required)"
streamlit run app_cloud.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
