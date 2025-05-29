"""
Scraper for TheOdd1sOut webcomic
"""
from datetime import datetime
import re
import json

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class TheOdd1sOutScraper(BaseScraper):
    """
    Scraper for TheOdd1sOut webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('theodd1sout', comics_channel)
        self.comic_name = "TheOdd1sOut"
        self.url = "https://www.theodd1sout.com/blogs/comics"
    
    def check_for_updates(self):
        """
        Check for and post new TheOdd1sOut comics
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
            # Find the main content area
            main_content = soup.find('main', id='MainContent')
            if not main_content:
                self.log_error("Could not find main content area")
                return numberposted
            
            # Find all comic entries in the main content
            comic_list = main_content.find_all(class_=re.compile('article|blog-post|comics?'))
            if not comic_list:
                # Try to find divs with specific patterns that might indicate comic entries
                comic_list = main_content.find_all('div', class_=re.compile('grid__item|blog-list'))
                if not comic_list:
                    self.log_error("Could not find comic entries in main content")
                    return numberposted
            
            # If we have comic entries, process the first (latest) one
            if not comic_list or len(comic_list) == 0:
                self.log_error("No comic entries found")
                return numberposted
                
            latest_comic = comic_list[0]
            
            # Find the title
            title_elem = latest_comic.find(['h2', 'h3', 'h4', 'h5']) or latest_comic.find(class_=re.compile('title|heading'))
            title = title_elem.text.strip() if title_elem else "TheOdd1sOut Comic"
            
            # Find link to the comic page
            link_elem = latest_comic.find('a')
            if not link_elem or 'href' not in link_elem.attrs:
                self.log_error("Could not find link to comic page")
                return numberposted
                
            comic_path = link_elem['href']
            
            # Make sure it's a full URL
            if not comic_path.startswith('http'):
                comic_path = f"https://www.theodd1sout.com{comic_path}"
            
            permalink = comic_path
            
            # Extract comic ID from the URL
            comic_id = comic_path.split("/")[-1]
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
            
            # Visit the comic page to get the image
            comic_request = handleRequest(comic_path)
            
            if comic_request['timeout']:
                self.log_error("Comic page request timed out")
                return numberposted
                
            comic_soup = makesoup(comic_request['request'])
            
            # Look for the comic image - Shopify often uses structured data
            structured_data = comic_soup.find('script', type='application/ld+json')
            image_url = None
            
            if structured_data:
                try:
                    data = json.loads(structured_data.string)
                    if 'image' in data:
                        if isinstance(data['image'], list) and len(data['image']) > 0:
                            image_url = data['image'][0]
                        else:
                            image_url = data['image']
                except (json.JSONDecodeError, AttributeError) as e:
                    self.log_error(f"Error parsing structured data: {str(e)}")
            
            # If we didn't find the image in structured data, look in the page
            if not image_url:
                # First look for the og:image meta tag (usually high quality)
                og_image = comic_soup.find("meta", property="og:image")
                if og_image and 'content' in og_image.attrs:
                    image_url = og_image['content']
            
            if not image_url:
                self.log_error("Found comic but couldn't find image URL")
                return numberposted
            
            # Post the comic
            caption = f"TheOdd1sOut: {title}\n\n[Link]({permalink})"
            self.post_comic(image_url, caption)
            
            # Add to database
            self.add_to_posted({
                'comic_id': comic_id,
                'title': title,
                'url': permalink,
                'image_url': image_url,
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
    scraper = TheOdd1sOutScraper()
    scraper.check_for_updates() 