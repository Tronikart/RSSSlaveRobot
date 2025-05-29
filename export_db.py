#!/usr/bin/env python3
"""
Export MongoDB collections to JSON files for easy transfer to another system
"""
import os
import json
from datetime import datetime
from pymongo import MongoClient
from bson import json_util

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['comics_db']  # Use the correct database name from base.py

# Create export directory if it doesn't exist
export_dir = 'db_export'
if not os.path.exists(export_dir):
    os.makedirs(export_dir)

# Get all collection names from the scrapers module
collections = []
try:
    # Add the current directory to path if not already there
    import sys
    if '.' not in sys.path:
        sys.path.insert(0, '.')
        
    from rsr.scrapers import active_scrapers
    for scraper_class in active_scrapers:
        try:
            scraper_instance = scraper_class()
            # Get the collection name - note that BaseScraper doesn't directly expose 
            # the collection name as an attribute, we need to get it from the posted attribute
            collections.append(scraper_instance.posted.name)
        except Exception as e:
            print(f"Error initializing {scraper_class.__name__}: {str(e)}")
except ImportError as e:
    print(f"Warning: Could not import scrapers module: {str(e)}")
    # Fallback: list of known comic collections
    collections = [
        'xkcd', 'theoatmeal', 'pbf', 'warandpeas', 'sarahsscribbles',
        'explosm', 'efc', 'loadingartist', 'Optipess', 'piecomic',
        'poorlydrawnlines', 'NerfNow', 'theodd1sout', 'skeletonclaw',
        'somethingpositive', 'safelyendangered', 'falseknees'
    ]
    print(f"Using hardcoded collection list: {collections}")
except Exception as e:
    print(f"Error getting collections from scrapers: {str(e)}")
    # Fallback to listing all collections in the database
    collections = db.list_collection_names()
    print(f"Using all database collections: {collections}")

# Export each collection to a JSON file
exported_collections = []
for collection_name in collections:
    try:
        collection = db[collection_name]
        data = list(collection.find())
        
        if data:
            # Convert MongoDB data to JSON
            json_data = json_util.dumps(data, indent=2)
            
            # Save to file
            filename = os.path.join(export_dir, f"{collection_name}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            exported_collections.append({
                'name': collection_name,
                'count': len(data),
                'filename': filename
            })
            print(f"Exported {len(data)} records from '{collection_name}' to {filename}")
        else:
            print(f"Collection '{collection_name}' is empty, skipping export")
    except Exception as e:
        print(f"Error exporting collection '{collection_name}': {str(e)}")

# Create a manifest file with export info
manifest = {
    'export_date': datetime.now().isoformat(),
    'collections': exported_collections,
    'total_collections': len(exported_collections)
}

manifest_path = os.path.join(export_dir, 'manifest.json')
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)

print(f"\nExport complete. {len(exported_collections)} collections exported to {export_dir}/")
print(f"Manifest saved to {manifest_path}") 