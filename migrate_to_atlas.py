#!/usr/bin/env python3
"""
MongoDB Atlas Migration Script
Migrates local MongoDB data to Atlas cloud database
"""

import os
import sys
from pymongo import MongoClient
import json
from datetime import datetime

def migrate_to_atlas():
    print("🌟 STAR Data Migration to MongoDB Atlas")
    print("=" * 50)
    
    # Atlas connection string with properly encoded password
    # Note: # symbol needs to be URL encoded as %23
    atlas_uri = "mongodb+srv://franzkingstein:Joes1234@cluster0.vftpx.mongodb.net/hippparcos_db?retryWrites=true&w=majority"
    print("✅ Using configured Atlas connection string")
    
    if not atlas_uri:
        print("❌ Atlas URI is required!")
        return False
    
    try:
        # Connect to local MongoDB
        print("🔍 Connecting to local MongoDB...")
        local_client = MongoClient("mongodb://localhost:27017/")
        local_db = local_client["hippparcos_db"]
        local_collection = local_db["stars"]
        
        # Get document count
        local_count = local_collection.count_documents({})
        print(f"📊 Found {local_count:,} stars in local database")
        
        # Connect to Atlas
        print("☁️  Connecting to MongoDB Atlas...")
        atlas_client = MongoClient(atlas_uri)
        atlas_db = atlas_client["hippparcos_db"]
        atlas_collection = atlas_db["stars"]
        
        # Test connection
        atlas_client.admin.command('ping')
        print("✅ Successfully connected to Atlas!")
        
        # Check if data already exists
        atlas_count = atlas_collection.count_documents({})
        if atlas_count > 0:
            print(f"⚠️  Atlas already has {atlas_count:,} documents")
            overwrite = input("🤔 Overwrite existing data? (y/N): ").strip().lower()
            if overwrite == 'y':
                print("🗑️  Clearing existing Atlas data...")
                atlas_collection.delete_many({})
            else:
                print("❌ Migration cancelled")
                return False
        
        # Migrate data in batches
        batch_size = 1000
        migrated = 0
        
        print(f"🚀 Starting migration in batches of {batch_size:,}...")
        
        cursor = local_collection.find().batch_size(batch_size)
        batch = []
        
        for document in cursor:
            batch.append(document)
            
            if len(batch) >= batch_size:
                # Insert batch
                atlas_collection.insert_many(batch)
                migrated += len(batch)
                print(f"✅ Migrated {migrated:,}/{local_count:,} documents ({migrated/local_count*100:.1f}%)")
                batch = []
        
        # Insert remaining documents
        if batch:
            atlas_collection.insert_many(batch)
            migrated += len(batch)
        
        print(f"🎉 Migration complete! {migrated:,} stars migrated to Atlas")
        
        # Verify migration
        final_count = atlas_collection.count_documents({})
        print(f"✅ Verification: Atlas now has {final_count:,} documents")
        
        # Create index for performance
        print("🔧 Creating indexes for better performance...")
        atlas_collection.create_index([("HIP", 1)])
        atlas_collection.create_index([("Vmag", 1)])
        atlas_collection.create_index([("SpType", 1)])
        print("✅ Indexes created!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    finally:
        # Close connections
        try:
            local_client.close()
            atlas_client.close()
        except:
            pass

if __name__ == "__main__":
    success = migrate_to_atlas()
    if success:
        print("\n🌟 Next steps:")
        print("1. Update your Streamlit app to use Atlas connection string")
        print("2. Deploy to Streamlit Cloud with real data!")
        print("3. Share your live app with the world! 🚀")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
