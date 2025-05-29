"""
Scraper for Perry Bible Fellowship webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class PbfScraper(BaseScraper):
    """
    Scraper for Perry Bible Fellowship webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('pbf', comics_channel)
        self.comic_name = "Perry Bible Fellowship"
        self.url = "https://pbfcomics.com/comics/"
    
    def check_for_updates(self):
        """
        Check for and post new PBF comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the archive page
        request = handleRequest(self.url)
        
        if request['timeout']:
            self.log_error("Archive page request timed out")
            return numberposted
        
        soup = makesoup(request['request'])
        try:
            # Get the comics on the archive page
            comics = soup.find_all('span', class_='thumbnail_gallery_item')
            
            if not comics or len(comics) == 0:
                self.log_error("Failed to find comics on archive page")
                return numberposted
            
            # Get the most recent comic (first in the list)
            latest_comic = comics[0]
            
            # Extract the comic details
            comic_link = None
            comic_title = None
            
            if latest_comic and latest_comic.a:
                comic_link = latest_comic.a.get('href')
                title_div = latest_comic.find('div', class_='thumbnail_post_title')
                if title_div:
                    comic_title = title_div.text.strip()
            
            if not comic_link or not comic_title:
                self.log_error("Failed to extract comic link or title")
                return numberposted
            
            # Extract the comic ID from the URL
            comic_id = comic_link.split('/')[-2] if comic_link.endswith('/') else comic_link.split('/')[-1]
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                return numberposted
            
            # Visit the permalink to get the actual image
            permalink_request = handleRequest(comic_link)
            
            if permalink_request['timeout']:
                self.log_error("Permalink request timed out")
                return numberposted
            
            permalink_soup = makesoup(permalink_request['request'])
            
            # Try multiple methods to find the image
            img_url = None
            
            # Method 1: Look for the og:image meta tag
            og_image = permalink_soup.find('meta', property='og:image')
            if og_image and 'content' in og_image.attrs:
                img_url = og_image['content']
            
            # Method 2: Look for images in the content area
            if not img_url:
                content_div = permalink_soup.find('div', class_='entry-content')
                if content_div:
                    comic_img = content_div.find('img')
                    if comic_img and 'src' in comic_img.attrs:
                        img_url = comic_img['src']
            
            if not img_url:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Post the comic
            caption = f"Perry Bible Fellowship: {comic_title}\n\n[Link]({comic_link})"
            self.post_comic(img_url, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_id,
                'title': comic_title,
                'image_url': img_url,
                'permalink': comic_link,
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
    scraper = PbfScraper()
    scraper.check_for_updates() 