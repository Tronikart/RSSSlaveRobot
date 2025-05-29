"""
Scraper for Optipess webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class OptipessScraper(BaseScraper):
    """
    Scraper for Optipess webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('Optipess', comics_channel)
        self.comic_name = "Optipess"
        self.url = "https://www.optipess.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Optipess comics
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
            # Find the first/top image which is likely to be the latest comic
            img_tags = soup.find_all('img')
            
            if not img_tags or len(img_tags) == 0:
                self.log_error("Failed to find any images")
                return numberposted
                
            # First image is usually the latest comic
            latest_img = img_tags[0]
            
            if 'src' not in latest_img.attrs:
                self.log_error("Image tag has no src attribute")
                return numberposted
                
            comic_url = latest_img['src']
            
            # Verify this is likely a comic (contains year/month in URL)
            if not ('/20' in comic_url and '.png' in comic_url):
                self.log_error("Found image but it doesn't appear to be a comic")
                return numberposted
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_url, 'url'):
                return numberposted
            
            # Get the title if available
            title_h1 = soup.find('h1')
            title_text = title_h1.text.strip() if title_h1 else "Optipess"
            
            # Try to find the permalink to the specific comic
            permalink = self.url
            comic_link = soup.find('link', rel='canonical')
            if comic_link and 'href' in comic_link.attrs:
                permalink = comic_link['href']
            
            # Create caption with link
            caption = f"Optipess: {title_text}\n\n[Link]({permalink})"
            
            # Post the comic
            self.post_comic(comic_url, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_url,
                'title': title_text,
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
    scraper = OptipessScraper()
    scraper.check_for_updates() 