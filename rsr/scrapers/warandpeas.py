"""
Scraper for War and Peas webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class WarAndPeasScraper(BaseScraper):
    """
    Scraper for War and Peas webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('warandpeas', comics_channel)
        self.comic_name = "War and Peas"
        self.url = "https://warandpeas.com/"
    
    def check_for_updates(self):
        """
        Check for and post new War and Peas comics
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
            # Find all article elements - they contain the comics
            articles = soup.find_all('article')
            
            if not articles or len(articles) == 0:
                self.log_error("Failed to find any articles")
                return numberposted
            
            # Process only the first (latest) article
            latest_article = articles[0]
            
            # Find the title element
            title_elem = latest_article.find(class_='entry-title')
            if not title_elem or not title_elem.a:
                self.log_error("Failed to find comic title or link")
                return numberposted
            
            comic_title = title_elem.text.strip()
            comic_url = title_elem.a.get('href')
            
            if not comic_url:
                self.log_error("Failed to extract comic URL")
                return numberposted
            
            # Extract the comic ID from the URL path
            url_parts = comic_url.strip('/').split('/')
            comic_id = url_parts[-1] if url_parts else None
            
            if not comic_id:
                self.log_error("Failed to extract comic ID from URL")
                return numberposted
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                return numberposted
            
            # Find the image in the entry content
            content_div = latest_article.find(class_='entry-content')
            comic_img = None
            
            if content_div:
                # Find all images
                images = content_div.find_all('img')
                
                # Look for data-lazy-src attribute first (site uses lazy loading)
                for img in images:
                    if 'data-lazy-src' in img.attrs:
                        img_url = img['data-lazy-src']
                        # Skip SVG placeholders
                        if not 'svg' in img_url:
                            comic_img = img_url
                            break
                
                # If no data-lazy-src found, try regular src
                if not comic_img:
                    for img in images:
                        if 'src' in img.attrs:
                            img_url = img['src']
                            # Skip SVG placeholders
                            if not 'svg' in img_url:
                                comic_img = img_url
                                break
            
            if not comic_img:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Clean up the URL (remove resize parameters for full resolution)
            if '?' in comic_img:
                comic_img = comic_img.split('?')[0]
            
            # Post the comic
            caption = f"War and Peas: {comic_title}\n\n[Link]({comic_url})"
            self.post_comic(comic_img, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_id,
                'title': comic_title,
                'image_url': comic_img,
                'permalink': comic_url,
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
    scraper = WarAndPeasScraper()
    scraper.check_for_updates() 