"""
Scraper for XKCD webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.telegram import send_message
from rsr.config import botapi, adminchat, comics_channel

class XkcdScraper(BaseScraper):
    """
    Scraper for XKCD webcomic
    Uses direct JSON API provided by XKCD
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('xkcd', comics_channel)
        self.api_url = "http://xkcd.com/info.0.json"
        self.comic_name = "XKCD"  # Override default name
    
    def check_for_updates(self):
        """
        Check for and post new XKCD comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the XKCD API
        request = handleRequest(self.api_url)
        
        if request['timeout']:
            self.log_error("API request timed out")
            return numberposted
        
        try:
            # Parse the JSON response
            data = request['request'].json()
            
            # Check if response contains required fields
            if 'num' in data and 'img' in data and 'alt' in data:
                # Generate the permalink to the comic
                permalink = f"https://xkcd.com/{data['num']}/"
                
                # Check if we've already posted this comic
                if not self.is_already_posted(data['num']):
                    # Format title - use a default if not available
                    title = data.get('title', 'Untitled')
                    
                    # Format the comic caption with title, alt text as spoiler, and link
                    comic_caption = f"XKCD #{data['num']}: {title}\n\n"
                    comic_caption += f"Alt text: ||{data['alt']}||\n\n"
                    comic_caption += f"[Link]({permalink})"
                    
                    # Post the new comic
                    self.post_comic(data['img'], comic_caption)
                    
                    # Add to database
                    self.add_to_posted({
                        'comic_id': data['num'],
                        'title': title,
                        'alt_text': data['alt'],
                        'image_url': data['img'],
                        'url': permalink,
                        'date': datetime.now()
                    })
                    
                    numberposted += 1
                    
                    # Log success
                    self.log_success(numberposted)
            else:
                self.log_error("JSON data missing required fields")
                
        except Exception as e:
            self.log_error(f"Error parsing JSON - {str(e)}")
        
        return numberposted

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = XkcdScraper()
    scraper.check_for_updates() 