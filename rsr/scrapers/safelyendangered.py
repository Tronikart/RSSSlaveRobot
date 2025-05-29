"""
Scraper for Safely Endangered webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class SafelyEndangeredScraper(BaseScraper):
    """
    Scraper for Safely Endangered webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('safelyendangered', comics_channel)
        self.comic_name = "Safely Endangered"
        self.url = "https://safelyendangered.com/blogs/comics"
    
    def check_for_updates(self):
        """
        Check for and post new Safely Endangered comics
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
            # The site appears to be a Shopify store with blogs
            # Comics are displayed in a grid with links and images
            
            # Find all articles or divs that contain comics
            comic_containers = soup.find_all('article') or soup.find_all('div', class_=re.compile('(blog|comic)-(post|item|grid|article)'))
            
            if not comic_containers:
                # Try alternative approaches to find comic elements
                comic_containers = soup.find_all('a', href=re.compile('/blogs/comics/'))
                
                if not comic_containers:
                    self.log_error("No comic containers found")
                    return numberposted
            
            # Process the first (latest) comic container
            if not comic_containers or len(comic_containers) == 0:
                self.log_error("No comic containers found")
                return numberposted
                
            latest_comic = comic_containers[0]
            
            # Find the title of the comic
            title_elem = latest_comic.find(['h1', 'h2', 'h3']) or latest_comic.find(class_=re.compile('title'))
            title = "Safely Endangered"
            if title_elem:
                title = title_elem.text.strip()
            else:
                # If no explicit title element, look for alt text or title attributes
                img_elem = latest_comic.find('img')
                if img_elem and 'alt' in img_elem.attrs:
                    title = img_elem['alt'].strip()
                elif img_elem and 'title' in img_elem.attrs:
                    title = img_elem['title'].strip()
            
            # Find the permalink to the comic
            permalink_elem = latest_comic.find('a', href=re.compile('/blogs/comics/'))
            if not permalink_elem or 'href' not in permalink_elem.attrs:
                self.log_error("Could not find permalink")
                return numberposted
                
            permalink = permalink_elem['href']
            if not permalink.startswith('http'):
                # Handle relative URLs
                permalink = f"https://safelyendangered.com{permalink}"
            
            # Extract comic ID from permalink
            post_id_match = re.search(r'/blogs/comics/([^/]+)$', permalink)
            if not post_id_match:
                self.log_error("Could not extract comic ID from permalink")
                return numberposted
                
            comic_id = post_id_match.group(1)
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
            
            # Find the comic image
            img_elem = latest_comic.find('img')
            image_url = None
            
            if img_elem and 'src' in img_elem.attrs:
                img_url = img_elem['src']
                
                # Check if it's a data URL or placeholder
                if img_url.startswith('data:') or 'placeholder' in img_url.lower():
                    # Try srcset instead
                    if 'srcset' in img_elem.attrs:
                        srcset = img_elem['srcset']
                        # Parse the srcset to get the highest resolution image
                        srcset_parts = srcset.split(',')
                        # Get the last part (usually highest resolution)
                        if srcset_parts:
                            last_part = srcset_parts[-1].strip()
                            img_url = last_part.split(' ')[0]
                
                # Clean up the URL
                if img_url.startswith('//'):
                    img_url = f"https:{img_url}"
                
                # Handle Shopify URLs with parameters
                if '?' in img_url:
                    base_url = img_url.split('?')[0]
                    # Check if the URL looks like a Shopify asset URL
                    if 'cdn.shopify.com' in base_url:
                        # Add parameters for high resolution
                        img_url = f"{base_url}?width=1500&height=1500&crop=center"
                
                image_url = img_url
            
            # If no direct image found, we might need to visit the permalink
            if not image_url and permalink:
                comic_page_request = handleRequest(permalink)
                
                if not comic_page_request['timeout']:
                    comic_page_soup = makesoup(comic_page_request['request'])
                    
                    # Look for the main comic image
                    main_img = comic_page_soup.find('img', class_=re.compile('featured|main|comic')) or comic_page_soup.find('img', alt=re.compile(title))
                    
                    if not main_img:
                        # Try to find images in the main content area
                        content_div = comic_page_soup.find('div', class_=re.compile('content|article|body'))
                        if content_div:
                            main_img = content_div.find('img')
                    
                    if main_img and 'src' in main_img.attrs:
                        img_url = main_img['src']
                        
                        # Clean up the URL
                        if img_url.startswith('//'):
                            img_url = f"https:{img_url}"
                        
                        # Handle Shopify URLs with parameters
                        if '?' in img_url:
                            base_url = img_url.split('?')[0]
                            # Check if the URL looks like a Shopify asset URL
                            if 'cdn.shopify.com' in base_url:
                                # Add parameters for high resolution
                                img_url = f"{base_url}?width=1500&height=1500&crop=center"
                        
                        image_url = img_url
            
            if not image_url:
                self.log_error("Found comic but couldn't find image URL")
                return numberposted
            
            # Post the comic
            caption = f"Safely Endangered: {title}"
            if permalink:
                caption += f"\n\n[Link]({permalink})"
                
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
    scraper = SafelyEndangeredScraper()
    scraper.check_for_updates() 