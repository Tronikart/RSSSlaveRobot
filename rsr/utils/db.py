"""
Database utilities for MongoDB
"""
from pymongo import MongoClient
from rsr.config import mongodb_host, mongodb_port, mongodb_db

def get_db_connection():
    """
    Get a connection to the MongoDB database
    
    Returns:
        pymongo.database.Database: MongoDB database instance
    """
    client = MongoClient(mongodb_host, mongodb_port)
    return client[mongodb_db]

def get_collection(collection_name):
    """
    Get a MongoDB collection
    
    Args:
        collection_name (str): Name of the collection
        
    Returns:
        pymongo.collection.Collection: MongoDB collection
    """
    db = get_db_connection()
    return db[collection_name]

def find_one(collection_name, query):
    """
    Find a single document in a collection
    
    Args:
        collection_name (str): Name of the collection
        query (dict): MongoDB query
        
    Returns:
        dict or None: The matching document or None
    """
    collection = get_collection(collection_name)
    return collection.find_one(query)

def insert_one(collection_name, document):
    """
    Insert a document into a collection
    
    Args:
        collection_name (str): Name of the collection
        document (dict): Document to insert
        
    Returns:
        pymongo.results.InsertOneResult: Result of the insert operation
    """
    collection = get_collection(collection_name)
    return collection.insert_one(document) 