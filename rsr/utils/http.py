"""
HTTP request handling utilities
"""
import requests
from rsr.config import reddit_user, botapi, adminchat
from rsr.utils.telegram import send_message

def handleRequest(url):
    """
    Make an HTTP request with error handling
    
    Args:
        url (str): URL to request
        
    Returns:
        dict: Dictionary with 'timeout' flag and 'request' object
    """
    try:
        request = requests.get(url)
        return {"timeout": False, "request": request}
    except Exception as e:
        send_message(botapi, adminchat, f"Request error for {url}: {str(e)}")
        return {"timeout": True, "request": ""}

def handleRedditRequest(url):
    """
    Make an HTTP request to Reddit with proper user agent
    
    Args:
        url (str): Reddit URL to request
        
    Returns:
        dict: Dictionary with 'timeout' flag and 'request' object
    """
    try:
        request = requests.get(url, headers={'User-agent': f'{reddit_user}'})
        return {'timeout': False, 'request': request}
    except Exception as e:
        send_message(botapi, adminchat, f"Reddit request error for {url}: {str(e)}")
        return {"timeout": True, 'request': ""} 