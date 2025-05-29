#!/usr/bin/env python3
"""
Verify that the RSSSlaveBot installation is correctly configured
- Checks MongoDB connection
- Verifies database collections are populated
- Tests import of scrapers
- Validates configuration
"""
import os
import sys
import importlib
from datetime import datetime

def check_mongodb_connection():
    """Check if MongoDB is accessible"""
    print("\n1. Checking MongoDB connection...")
    try:
        from pymongo import MongoClient
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        # Force a connection check
        info = client.server_info()
        print(f"✅ MongoDB connection successful")
        print(f"   - MongoDB version: {info.get('version', 'unknown')}")
        return client
    except ImportError:
        print("❌ PyMongo is not installed. Please install it with:")
        print("   pip install pymongo")
        return None
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("   Please ensure MongoDB is running on localhost:27017")
        return None

def check_database_collections(client):
    """Check if database collections exist and contain data"""
    print("\n2. Checking database collections...")
    if not client:
        print("⚠️ Skipping collection check (no MongoDB connection)")
        return
    
    try:
        db = client['comics_db']
        collections = db.list_collection_names()
        
        if not collections:
            print("⚠️ No collections found in 'comics_db' database")
            return
        
        print(f"✅ Found {len(collections)} collections:")
        for coll in collections:
            count = db[coll].count_documents({})
            print(f"   - {coll}: {count} documents")
    except Exception as e:
        print(f"❌ Error checking collections: {str(e)}")

def fix_duplicate_key_issues(client):
    """Fix common database issues by dropping problematic indexes"""
    print("\n3. Fixing potential database issues...")
    if not client:
        print("⚠️ Skipping database fixes (no MongoDB connection)")
        return
    
    try:
        db = client['comics_db']
        collections = db.list_collection_names()
        
        for coll_name in collections:
            collection = db[coll_name]
            
            # Get all indexes
            indexes = collection.index_information()
            print(f"   Checking indexes for {coll_name}...")
            
            # Look for the 'url' unique index which often causes problems
            for idx_name, idx_info in indexes.items():
                if idx_name != '_id_':  # Skip the default _id index
                    try:
                        key_fields = [field[0] for field in idx_info['key']]
                        if 'url' in key_fields and idx_info.get('unique', False):
                            print(f"   - Dropping problematic unique index on 'url' field in {coll_name}")
                            collection.drop_index(idx_name)
                            print(f"   ✅ Index dropped successfully")
                    except Exception as e:
                        print(f"   ❌ Error checking/dropping index {idx_name}: {str(e)}")
            
            # Create a better compound index on multiple fields
            try:
                print(f"   - Creating improved indexes for {coll_name}")
                # Create index on comic_id which is the most reliable identifier
                collection.create_index('comic_id', unique=True, sparse=True)
                # Create index on image_url which is also reliable
                collection.create_index('image_url', unique=True, sparse=True)
                print(f"   ✅ New indexes created successfully")
            except Exception as e:
                print(f"   ⚠️ Could not create new indexes: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error fixing database issues: {str(e)}")

def check_scraper_imports():
    """Test if the scrapers module can be imported"""
    print("\n4. Checking scraper imports...")
    try:
        # Add the current directory to path if not already there
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # Try to import the scrapers module
        import rsr.scrapers
        print(f"✅ Successfully imported scrapers module")
        
        # Check active scrapers
        try:
            from rsr.scrapers import active_scrapers
            print(f"✅ Found {len(active_scrapers)} active scrapers:")
            for scraper_class in active_scrapers:
                try:
                    scraper_instance = scraper_class()
                    # Get collection name from the posted attribute
                    collection_name = scraper_instance.posted.name
                    print(f"   - {scraper_instance.comic_name} ({collection_name})")
                except Exception as e:
                    print(f"   - {scraper_class.__name__}: ❌ Error initializing: {str(e)}")
        except Exception as e:
            print(f"❌ Error checking active scrapers: {str(e)}")
            
    except ImportError as e:
        print(f"❌ Error importing scrapers module: {str(e)}")
        print("   Make sure you're running this script from the root directory of the project")

def check_config():
    """Check if config file exists and is readable"""
    print("\n5. Checking configuration...")
    try:
        # Try to import config
        from rsr.config import comics_channel, botapi
        
        print("✅ Successfully imported configuration")
        print(f"   - Telegram channel: {comics_channel}")
        if botapi and botapi.startswith("0"):
            print("⚠️ Bot API token appears to be invalid")
        elif botapi:
            print("✅ Bot API token is set")
        else:
            print("❌ Bot API token is not set")
            
    except ImportError as e:
        print(f"❌ Error importing configuration: {str(e)}")
        config_path = os.path.join("rsr", "config.py")
        if not os.path.exists(config_path):
            print(f"   Config file not found at {config_path}")
        else:
            print(f"   Config file exists but cannot be imported")

def check_run_script():
    """Check if run.py exists and is executable"""
    print("\n6. Checking run script...")
    run_path = "run.py"
    if os.path.exists(run_path):
        print(f"✅ Found run script at {run_path}")
        if os.access(run_path, os.X_OK):
            print("✅ Run script is executable")
        else:
            print("⚠️ Run script is not executable. Consider running:")
            print("   chmod +x run.py")
    else:
        print(f"❌ Run script not found at {run_path}")

def main():
    """Main verification function"""
    print("=== RSS Slave Bot Installation Verification ===")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Run checks
    client = check_mongodb_connection()
    check_database_collections(client)
    fix_duplicate_key_issues(client)
    check_scraper_imports()
    check_config()
    check_run_script()
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main() 