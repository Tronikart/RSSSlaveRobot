#!/usr/bin/env python3
"""
Import MongoDB collections from JSON files exported by export_db.py
"""
import os
import json
import argparse
from datetime import datetime
from pymongo import MongoClient
from bson import json_util

def main():
    parser = argparse.ArgumentParser(description='Import MongoDB collections from exported JSON files')
    parser.add_argument('--host', default='localhost', help='MongoDB host (default: localhost)')
    parser.add_argument('--port', type=int, default=27017, help='MongoDB port (default: 27017)')
    parser.add_argument('--db', default='comics_db', help='Database name (default: comics_db)')
    parser.add_argument('--dir', default='db_export', help='Directory containing exported JSON files (default: db_export)')
    parser.add_argument('--merge', action='store_true', help='Merge with existing collections instead of replacing')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without actually importing')
    args = parser.parse_args()

    # Connect to MongoDB
    client = MongoClient(args.host, args.port)
    db = client[args.db]

    # Verify export directory exists
    if not os.path.exists(args.dir):
        print(f"Error: Export directory '{args.dir}' not found.")
        return 1

    # Load manifest if it exists
    manifest_path = os.path.join(args.dir, 'manifest.json')
    manifest = None
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        print(f"Found manifest file. Export date: {manifest['export_date']}")
        print(f"Collections in manifest: {manifest['total_collections']}")
    else:
        print("No manifest file found. Will import all JSON files in the directory.")

    # Get list of collections to import
    json_files = [f for f in os.listdir(args.dir) if f.endswith('.json') and f != 'manifest.json']
    
    if not json_files:
        print(f"No JSON files found in '{args.dir}'.")
        return 1

    print(f"Found {len(json_files)} JSON files to import.")
    imported_collections = []
    
    # Import each JSON file
    for json_file in json_files:
        collection_name = os.path.splitext(json_file)[0]
        file_path = os.path.join(args.dir, json_file)
        
        try:
            # Read JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
            
            # Parse JSON to MongoDB format
            data = json_util.loads(json_data)
            
            if not data:
                print(f"File '{json_file}' contains no data, skipping.")
                continue
                
            # Get target collection
            collection = db[collection_name]
            
            # Count records
            record_count = len(data)
            
            if args.dry_run:
                print(f"[DRY RUN] Would import {record_count} records into '{collection_name}'")
                continue
                
            # Import the data
            if not args.merge:
                # Replace existing collection
                collection.drop()
                print(f"Dropped existing collection '{collection_name}'")
            
            # Insert the data
            if record_count > 0:
                # Create a unique index on typical fields used to identify comics
                try:
                    # Try common field names used in the scrapers
                    for field in ['url', 'comic_id', 'post_id']:
                        if any(field in record for record in data):
                            collection.create_index(field, unique=True, background=True)
                            print(f"Created unique index on '{field}' for collection '{collection_name}'")
                            break
                except Exception as e:
                    print(f"Warning: Could not create index for '{collection_name}': {str(e)}")
                
                # Insert the data
                if args.merge:
                    # For merging, we need to insert one by one with upsert
                    imported_count = 0
                    for record in data:
                        # Create a filter based on typical unique identifiers
                        filter_dict = {}
                        for field in ['url', 'comic_id', 'post_id', 'image_url']:
                            if field in record:
                                filter_dict[field] = record[field]
                                break
                        
                        if filter_dict:
                            result = collection.replace_one(filter_dict, record, upsert=True)
                            if result.upserted_id or result.modified_count > 0:
                                imported_count += 1
                        else:
                            # No unique field found, just insert
                            collection.insert_one(record)
                            imported_count += 1
                    
                    print(f"Merged {imported_count} records into collection '{collection_name}'")
                else:
                    # For replacing, we can bulk insert
                    result = collection.insert_many(data)
                    print(f"Imported {len(result.inserted_ids)} records into collection '{collection_name}'")
            
            imported_collections.append({
                'name': collection_name,
                'count': record_count,
                'filename': json_file
            })
            
        except Exception as e:
            print(f"Error importing '{json_file}': {str(e)}")
    
    # Create an import summary
    if not args.dry_run:
        summary = {
            'import_date': datetime.now().isoformat(),
            'collections': imported_collections,
            'total_collections': len(imported_collections),
            'source_manifest': manifest,
            'import_options': {
                'merge': args.merge,
                'host': args.host,
                'port': args.port,
                'db_name': args.db
            }
        }
        
        summary_path = os.path.join(args.dir, 'import_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nImport complete. {len(imported_collections)} collections imported.")
        print(f"Summary saved to {summary_path}")
    else:
        print("\nDry run completed. No changes were made to the database.")
    
    return 0

if __name__ == "__main__":
    exit(main()) 