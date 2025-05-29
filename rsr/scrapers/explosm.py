"""
Scraper for Cyanide & Happiness webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class ExplosmScraper(BaseScraper):
    """
    Scraper for Cyanide & Happiness webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('explosm', comics_channel)
        self.comic_name = "Cyanide and Happiness"
        self.url = "https://explosm.net/"
    
    def check_for_updates(self):
        """
        Check for and post new Cyanide & Happiness comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the website
        request = handleRequest(self.url)
        
        if request['timeout']:
            self.log_error("Website request timed out")
            return numberposted
        
        soup = makesoup(request['request'])
        try:
            # Find all images
            img_tags = soup.find_all('img')
            
            # Find the comic image (typically in the staticexplosm.net domain with png extension)
            comic_img_src = None
            for img in img_tags:
                if 'src' in img.attrs and 'static.explosm.net' in img['src'] and img['src'].endswith('.png'):
                    comic_img_src = img['src']
                    break
            
            if not comic_img_src:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Extract comic ID from the image path
            comic_id_match = re.findall(r'comics/(\d+)', comic_img_src)
            if not comic_id_match:
                comic_id_match = re.findall(r'/(\d+)/', comic_img_src)
                
            comic_id = comic_id_match[0] if comic_id_match else comic_img_src
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                return numberposted
            
            # Generate permalink based on comic ID
            permalink = f"https://explosm.net/comics/{comic_id}"
            
            # Create caption with link
            caption = f"Cyanide and Happiness\n\n[Link]({permalink})"
            
            # Post the comic
            self.post_comic(comic_img_src, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_id,
                'image_url': comic_img_src,
                'permalink': permalink,
                'date': datetime.now()
            })
            
            numberposted += 1
            
            # Log success
            self.log_success(numberposted)
                
        except Exception as e:
            self.log_error(f"Error processing comic: {str(e)}")
        
        return numberposted

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = ExplosmScraper()
    scraper.check_for_updates() 