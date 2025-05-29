"""
Base scraper class that serves as a foundation for all webcomic scrapers
"""
from datetime import datetime

from pymongo import MongoClient
from rsr.utils.telegram import sendPhoto, sendAlbums, send_message
from rsr.config import botapi, adminchat

class BaseScraper:
    """
    Base class for all webcomic scrapers
    
    Provides common functionality used by all scrapers:
    - Database interaction (checking if a comic exists, adding new entries)
    - Standard methods for posting to Telegram
    - Common utility methods
    
    Each specific scraper should inherit from this class and implement 
    the `check_for_updates` method.
    """
    
    def __init__(self, db_collection, channel_id):
        """
        Initialize the scraper with database collection and channel ID
        
        Args:
            db_collection (str): MongoDB collection name for this comic
            channel_id (str): Telegram channel ID to post comics to
        """
        client = MongoClient()
        db = client.comics_db
        
        self.posted = db[db_collection]
        self.channel_id = channel_id
        self.comic_name = db_collection.capitalize()  # Default name based on collection
        
    def check_for_updates(self):
        """
        Main method to check for and post updates
        
        Must be implemented by each specific scraper.
        Returns the number of new comics posted.
        """
        raise NotImplementedError("Subclasses must implement check_for_updates")
        
    def is_already_posted(self, identifier, id_field='comic_id'):
        """
        Check if a comic already exists in the database
        
        Args:
            identifier: The unique identifier for the comic
            id_field (str): The field name to check in the database
            
        Returns:
            bool: True if already posted, False otherwise
        """
        return bool(self.posted.find_one({id_field: identifier}))
        
    def add_to_posted(self, comic_data):
        """
        Add a comic to the database
        
        Args:
            comic_data (dict): Data to store in the database
        
        Returns:
            pymongo.results.InsertOneResult: The result of the insert operation
        """
        # Ensure it has a timestamp
        if 'date' not in comic_data:
            comic_data['date'] = datetime.now()
            
        return self.posted.insert_one(comic_data)
        
    def post_comic(self, image_url, caption="", is_album=False):
        """
        Post a comic to Telegram
        
        Args:
            image_url (str or list): URL of the image or list of URLs for albums
            caption (str): Caption to include with the image
            is_album (bool): Whether this is a multi-image comic (album)
            
        Returns:
            The result from the Telegram API
        """
        try:
            if is_album:
                # For multi-image comics
                return sendAlbums(self.channel_id, image_url, caption)
            else:
                # For single-image comics
                return sendPhoto(self.channel_id, image_url, caption)
        except Exception as e:
            send_message(botapi, adminchat, f"{self.comic_name} error posting comic: {str(e)}")
            return None
            
    def log_success(self, count):
        """
        Log successful posting to admin chat
        
        Args:
            count (int): Number of comics posted
        """
        if count > 0:
            send_message(botapi, adminchat, f"Posted {count} new {self.comic_name} comic(s) to {self.channel_id}")
            
    def log_error(self, message):
        """
        Log an error to admin chat
        
        Args:
            message (str): Error message
        """
        send_message(botapi, adminchat, f"{self.comic_name}: {message}") 