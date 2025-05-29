"""
Scraper for The Oatmeal webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makexmlsoup, makesoup
from rsr.utils.telegram import send_message
from rsr.config import botapi, adminchat, comics_channel

class OatmealScraper(BaseScraper):
    """
    Scraper for The Oatmeal webcomic
    Uses RSS feed and direct scraping for multi-image comics
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('theoatmeal', comics_channel)
        self.rss_url = "https://theoatmeal.com/feed/rss"
        self.comic_name = "The Oatmeal"  # Override default name
    
    def check_for_updates(self):
        """
        Check for and post new Oatmeal comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the RSS feed
        request = handleRequest(self.rss_url)
        
        if request['timeout']:
            self.log_error("RSS feed request timed out")
            return numberposted
        
        # Parse the XML
        soup = makexmlsoup(request['request'])
        
        # Find all items in the RSS feed
        items = soup.find_all('item')
        
        if not items:
            self.log_error("No items found in RSS feed")
            return numberposted
        
        # Get the latest item (first one)
        latest_item = items[0]
        
        # Extract comic details
        comic_info = self._extract_comic_info(latest_item)
        
        # Skip if we couldn't find a comic ID
        if 'comic_id' not in comic_info:
            self.log_error("Could not extract comic ID from permalink")
            return numberposted
        
        # Check if we've already posted this comic
        if self.is_already_posted(comic_info['comic_id']):
            # Already posted this comic
            return numberposted
        
        # If we have a permalink, visit the comic page to get all images
        if 'permalink' in comic_info:
            # Get all image URLs from the comic page
            image_urls = self._get_comic_images(comic_info['permalink'])
            
            if not image_urls:
                self.log_error("No valid comic images found")
                return numberposted
            
            # Post the comic to Telegram
            try:
                # Prepare the caption
                title_text = f"The Oatmeal: {comic_info['title']}"
                if 'permalink' in comic_info:
                    title_text += f"\n\n[Link]({comic_info['permalink']})"
                
                # Post the comic (as album if multiple images)
                is_album = len(image_urls) > 1
                self.post_comic(image_urls, title_text, is_album=is_album)
                
                # Add to database
                self.add_to_posted({
                    'comic_id': comic_info['comic_id'],
                    'title': comic_info.get('title', 'The Oatmeal'),
                    'url': comic_info.get('permalink', ''),
                    'image_urls': image_urls,
                    'date': datetime.now()
                })
                
                numberposted += 1
                
                # Log success
                self.log_success(numberposted)
            except Exception as e:
                self.log_error(f"Error posting comic: {str(e)}")
        
        return numberposted
    
    def _extract_comic_info(self, item):
        """
        Extract comic details from RSS item
        
        Args:
            item: RSS item element
            
        Returns:
            dict: Comic information
        """
        comic_info = {}
        
        # Get title
        title_elem = item.find('title')
        if title_elem:
            comic_info['title'] = title_elem.text.strip()
        
        # Get link/permalink
        link_elem = item.find('link')
        if link_elem:
            comic_info['permalink'] = link_elem.text.strip()
            
            # Extract comic ID from permalink - try multiple patterns
            # Try first standard format: /comics/[comic_id]
            comic_id_match = re.search(r'/comics/([^/?&#]+)', comic_info['permalink'])
            if comic_id_match:
                comic_info['comic_id'] = comic_id_match.group(1)
            else:
                # Try format: /comic/[comic_id]
                comic_id_match = re.search(r'/comic/([^/?&#]+)', comic_info['permalink'])
                if comic_id_match:
                    comic_info['comic_id'] = comic_id_match.group(1)
                else:
                    # Try extracting just the final path component
                    parts = comic_info['permalink'].rstrip('/').split('/')
                    if len(parts) > 1:
                        comic_info['comic_id'] = parts[-1]
                    else:
                        # Last resort - use the entire URL as a hash
                        from hashlib import md5
                        comic_info['comic_id'] = md5(comic_info['permalink'].encode()).hexdigest()[:16]
        
        # Get publication date
        pubdate_elem = item.find('pubDate')
        if pubdate_elem:
            comic_info['date'] = pubdate_elem.text.strip()
            
        return comic_info
    
    def _get_comic_images(self, permalink):
        """
        Get all image URLs from the comic page
        
        Args:
            permalink (str): URL of the comic page
            
        Returns:
            list: List of image URLs
        """
        # Make sure we use the no_popup version for better parsing
        if '?' not in permalink:
            comic_url = permalink + "?no_popup=1"
        else:
            comic_url = permalink
            
        page_request = handleRequest(comic_url)
        
        if page_request['timeout']:
            self.log_error("Comic page request timed out")
            return []
        
        page_soup = makesoup(page_request['request'])
        
        # Find the comic content
        comic_content = page_soup.find('div', id='comic')
        
        if not comic_content:
            # Try other common container IDs
            comic_content = page_soup.find('div', class_='content') or page_soup.find('div', class_='comic')
        
        if not comic_content:
            self.log_error("Could not find comic content container")
            return []
        
        # Find all images in the comic content
        images = comic_content.find_all('img')
        
        if not images:
            self.log_error("No images found in comic content")
            return []
        
        # Extract all image URLs
        image_urls = []
        for img in images:
            if 'src' in img.attrs:
                img_url = img['src']
                
                # Make sure it's a full URL
                if not img_url.startswith('http'):
                    if img_url.startswith('/'):
                        img_url = f"https://theoatmeal.com{img_url}"
                    else:
                        img_url = f"https://theoatmeal.com/{img_url}"
                
                # Skip tiny images and icons
                is_small = False
                if 'width' in img.attrs and img['width'].isdigit() and int(img['width']) < 100:
                    is_small = True
                if 'height' in img.attrs and img['height'].isdigit() and int(img['height']) < 100:
                    is_small = True
                
                if not is_small and 'theoatmeal' in img_url and not any(x in img_url.lower() for x in ['avatar', 'icon', 'logo']):
                    image_urls.append(img_url)
                    
        return image_urls

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = OatmealScraper()
    scraper.check_for_updates() 