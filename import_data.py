#!/usr/bin/env python3
"""
STAR - Satellite Transmission Analysis Reduction
Data Import Utility for Docker Environment

This script automatically imports the Hipparcos star catalog data
into MongoDB when the container starts.
"""

import pandas as pd
import numpy as np
from pymongo import MongoClient
import os
import time
import sys
from datetime import datetime

def log_message(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def wait_for_mongodb(uri, max_retries=30):
    """Wait for MongoDB to be ready with retries"""
    log_message("🔍 Checking MongoDB connection...")
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.server_info()
            log_message("✅ MongoDB is ready!")
            client.close()
            return True
        except Exception as e:
            log_message(f"⏳ Attempt {attempt + 1}/{max_retries}: MongoDB not ready yet... ({str(e)[:50]})")
            time.sleep(3)
    
    log_message("❌ MongoDB failed to start after maximum retries")
    return False

def create_database_indexes(collection):
    """Create optimized indexes for better query performance"""
    log_message("🔍 Creating database indexes...")
    
    indexes_to_create = [
        ("HIP", {"unique": True}),  # Unique index on HIP identifier
        ("Vmag", {}),               # Visual magnitude
        ("Distance_pc", {}),        # Distance in parsecs
        ("SpType", {}),             # Spectral type
        ("B-V", {}),                # Color index
        ([("RA", 1), ("DE", 1)], {"name": "sky_coordinates"}),  # Compound index for sky coordinates
        ([("Vmag", 1), ("Distance_pc", 1)], {"name": "brightness_distance"}),  # For HR diagrams
    ]
    
    created_count = 0
    for index_spec in indexes_to_create:
        try:
            if isinstance(index_spec[0], list):
                # Compound index
                collection.create_index(index_spec[0], **index_spec[1])
            else:
                # Single field index
                collection.create_index(index_spec[0], **index_spec[1])
            created_count += 1
        except Exception as e:
            log_message(f"⚠️  Warning: Could not create index {index_spec[0]}: {e}")
    
    log_message(f"✅ Created {created_count} database indexes!")

def clean_and_validate_data(df):
    """Clean and validate the star catalog data"""
    log_message("🧹 Cleaning and validating data...")
    
    original_count = len(df)
    
    # Convert numeric columns with proper error handling
    numeric_columns = ['HIP', 'Vmag', 'Distance_pc', 'B-V', 'RA', 'DE']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows where HIP (primary identifier) is missing
    df = df.dropna(subset=['HIP'])
    
    # Remove duplicate HIP entries (keep first occurrence)
    df = df.drop_duplicates(subset=['HIP'], keep='first')
    
    # Basic data validation
    if 'Vmag' in df.columns:
        # Remove unrealistic magnitude values
        df = df[(df['Vmag'] >= -3) & (df['Vmag'] <= 20)]
    
    if 'Distance_pc' in df.columns:
        # Remove negative distances
        df = df[(df['Distance_pc'] > 0) | df['Distance_pc'].isna()]
    
    cleaned_count = len(df)
    removed_count = original_count - cleaned_count
    
    log_message(f"📊 Data cleaning completed:")
    log_message(f"   Original records: {original_count:,}")
    log_message(f"   Cleaned records: {cleaned_count:,}")
    log_message(f"   Removed records: {removed_count:,}")
    
    return df

def import_star_data():
    """Main function to import Hipparcos star data into MongoDB"""
    
    log_message("🌟 STAR - Data Import Utility Starting...")
    log_message("=" * 60)
    
    # Get MongoDB URI from environment variable
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/hippparcos_db')
    log_message(f"📡 MongoDB URI: {uri}")
    
    # Wait for MongoDB to be ready
    if not wait_for_mongodb(uri):
        log_message("❌ Failed to connect to MongoDB. Exiting...")
        sys.exit(1)
    
    try:
        # Connect to MongoDB
        client = MongoClient(uri)
        db = client['hippparcos_db']
        collection = db['stars']
        
        # Check if data already exists
        existing_count = collection.count_documents({})
        if existing_count > 0:
            log_message(f"📊 Data already exists: {existing_count:,} documents")
            log_message("✅ Skipping import - database is ready!")
            
            # Still create indexes if they don't exist
            create_database_indexes(collection)
            return True
        
        # Find CSV file in possible locations
        csv_paths = [
            './hipparcos-voidmain.csv',     # Current directory
            '/app/hipparcos-voidmain.csv',  # App directory
            '/data/hipparcos-voidmain.csv', # Data volume mount
        ]
        
        csv_file = None
        for path in csv_paths:
            if os.path.exists(path):
                csv_file = path
                log_message(f"📥 Found CSV file: {csv_file}")
                break
        
        if not csv_file:
            log_message("❌ CSV file not found in any expected location:")
            for path in csv_paths:
                log_message(f"   - {path}")
            return False
        
        # Load and process CSV data
        log_message(f"📊 Loading data from: {csv_file}")
        
        try:
            df = pd.read_csv(csv_file)
            total_records = len(df)
            log_message(f"📈 Loaded {total_records:,} records from CSV")
            
            # Show column information
            log_message(f"📋 Columns found: {list(df.columns)}")
            
        except Exception as e:
            log_message(f"❌ Error reading CSV file: {e}")
            return False
        
        # Clean and validate data
        df = clean_and_validate_data(df)
        
        # Convert to records for MongoDB
        records = df.to_dict('records')
        valid_records = len(records)
        
        log_message(f"🔄 Importing {valid_records:,} records to MongoDB...")
        
        # Batch insert for better performance
        batch_size = 5000
        total_inserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                result = collection.insert_many(batch, ordered=False)
                total_inserted += len(result.inserted_ids)
                progress = min(i + batch_size, len(records))
                percentage = (progress / len(records)) * 100
                log_message(f"⚡ Batch {i//batch_size + 1}: Imported {len(result.inserted_ids):,} records ({percentage:.1f}% complete)")
            except Exception as e:
                log_message(f"⚠️  Warning: Batch insert error: {e}")
        
        log_message(f"✅ Data import completed! Total inserted: {total_inserted:,}")
        
        # Create indexes for better query performance
        create_database_indexes(collection)
        
        # Verify import and display statistics
        final_count = collection.count_documents({})
        log_message(f"🎉 Import verification: {final_count:,} documents in database")
        
        # Display sample statistics
        log_message("📈 Calculating database statistics...")
        
        try:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_stars": {"$sum": 1},
                    "avg_magnitude": {"$avg": "$Vmag"},
                    "min_magnitude": {"$min": "$Vmag"},
                    "max_magnitude": {"$max": "$Vmag"},
                    "max_distance": {"$max": "$Distance_pc"},
                    "avg_distance": {"$avg": "$Distance_pc"},
                    "spectral_types": {"$addToSet": "$SpType"}
                }}
            ]
            
            stats = list(collection.aggregate(pipeline))
            if stats:
                stat = stats[0]
                log_message("📊 Database Statistics:")
                log_message(f"   Total Stars: {stat.get('total_stars', 0):,}")
                log_message(f"   Magnitude Range: {stat.get('min_magnitude', 0):.2f} to {stat.get('max_magnitude', 0):.2f}")
                log_message(f"   Average Magnitude: {stat.get('avg_magnitude', 0):.2f}")
                log_message(f"   Max Distance: {stat.get('max_distance', 0):.1f} parsecs")
                log_message(f"   Average Distance: {stat.get('avg_distance', 0):.1f} parsecs")
                
                spectral_types = [t for t in stat.get('spectral_types', []) if t and str(t) != 'nan']
                log_message(f"   Unique Spectral Types: {len(spectral_types)}")
        
        except Exception as e:
            log_message(f"⚠️  Warning: Could not calculate statistics: {e}")
        
        return True
        
    except Exception as e:
        log_message(f"❌ Critical error during import: {e}")
        import traceback
        log_message(f"📋 Full error trace: {traceback.format_exc()}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Main execution function"""
    log_message("🌟 STAR - Satellite Transmission Analysis Reduction")
    log_message("🗄️  Automated Database Import Utility")
    log_message("=" * 60)
    
    success = import_star_data()
    
    if success:
        log_message("")
        log_message("🎉 Database setup completed successfully!")
        log_message("🚀 Ready for Streamlit application startup...")
        log_message("=" * 60)
        sys.exit(0)
    else:
        log_message("")
        log_message("❌ Database setup failed!")
        log_message("🔧 Please check the logs above for error details")
        log_message("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
