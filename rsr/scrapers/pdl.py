"""
Scraper for Poorly Drawn Lines webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class PoorlyDrawnLinesScraper(BaseScraper):
    """
    Scraper for Poorly Drawn Lines webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('poorlydrawnlines', comics_channel)
        self.comic_name = "Poorly Drawn Lines"
        self.url = "https://poorlydrawnlines.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Poorly Drawn Lines comics
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
            
            # Find the actual comic image
            comic_img = None
            for img in img_tags:
                if 'src' in img.attrs:
                    img_url = img['src']
                    # Check if it's likely a comic image (contains wp-content and specific patterns)
                    # Avoid buttons and UI elements (arrows, logo, "unnamed-file" which is the random button)
                    if ('wp-content/uploads' in img_url and 
                        'logo' not in img_url.lower() and 
                        'arrow' not in img_url.lower() and
                        'unnamed-file' not in img_url):
                        comic_img = img_url
                        break
            
            if not comic_img:
                self.log_error("Failed to find comic image")
                return numberposted
                
            # Check if we've already seen this comic
            if self.is_already_posted(comic_img, 'url'):
                return numberposted
            
            # Find the title if available (usually in the article header)
            title_elem = soup.find('h1', class_='entry-title')
            title = title_elem.text.strip() if title_elem else "Poorly Drawn Lines"
            
            # Try to find the permalink to the specific comic
            permalink = self.url
            comic_link = soup.find('link', rel='canonical')
            if comic_link and 'href' in comic_link.attrs:
                permalink = comic_link['href']
            
            # Create caption with link
            caption = f"Poorly Drawn Lines: {title}\n\n[Link]({permalink})"
            
            # Post the comic
            self.post_comic(comic_img, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_img,
                'title': title,
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
    scraper = PoorlyDrawnLinesScraper()
    scraper.check_for_updates() 