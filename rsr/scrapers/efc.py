"""
Scraper for Extra Fabulous Comics webcomic
"""
from datetime import datetime

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class EfcScraper(BaseScraper):
    """
    Scraper for Extra Fabulous Comics webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('efc', comics_channel)
        self.comic_name = "Extra Fabulous Comics"
        self.url = "https://www.extrafabulouscomics.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Extra Fabulous Comics
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
            # This is a Wix site now with a different structure
            # First try to find the comic by title and number
            h2_tags = soup.find_all('h2')
            if not h2_tags or len(h2_tags) == 0:
                self.log_error("Failed to find comic title")
                return numberposted
            
            # Get the latest comic number/title
            comic_title = h2_tags[0].text.strip()
            comic_id = comic_title.replace(" ", "-").lower()
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                return numberposted
            
            # Look at all images on the main page
            all_imgs = soup.find_all('img')
            found_image = False
            img_url = None
            
            # First look for blurred thumbnails and convert them to high-quality versions
            for img in all_imgs:
                if 'src' in img.attrs and 'static.wixstatic.com' in img['src'] and 'media' in img['src']:
                    img_url_candidate = img['src']
                    
                    # Skip obvious UI elements
                    if any(x in img_url_candidate.lower() for x in ['logo', 'banner', 'icon', 'title']):
                        continue
                        
                    # Check if it's a blurred thumbnail (most likely the comic)
                    if 'blur' in img_url_candidate:
                        # Try to extract a clean URL by removing blur and resizing parameters
                        if 'fill' in img_url_candidate:
                            base_url = img_url_candidate.split('/fill/')[0]
                            file_name = img_url_candidate.split('/')[-1]
                            if '~' in file_name:
                                # Extract the base filename without manipulation parameters
                                parts = file_name.split('~')
                                if len(parts) >= 2:
                                    # Use simplified URL format 
                                    clean_url = f"{parts[0]}~{parts[1].split('/')[0]}".split('/')[-1]
                                    img_url = f"https://static.wixstatic.com/media/904535_{clean_url}"
                                    found_image = True
                                    break
            
            # If we couldn't find a blurred thumbnail, look for any high-res image
            if not found_image:
                for img in all_imgs:
                    if 'src' in img.attrs and 'static.wixstatic.com' in img['src'] and 'media' in img['src']:
                        img_url_candidate = img['src']
                        
                        # Simplify the URL to avoid complex paths
                        if '~mv2' in img_url_candidate:
                            parts = img_url_candidate.split('/')
                            for part in parts:
                                if '~mv2' in part:
                                    # Found the filename part
                                    clean_url = f"https://static.wixstatic.com/media/{part}"
                                    
                                    # Skip obvious UI elements
                                    if any(x in clean_url.lower() for x in ['logo', 'banner', 'icon', 'title']):
                                        continue
                                        
                                    # This is likely a high-quality comic image
                                    img_url = clean_url
                                    found_image = True
                                    break
                            
                            if found_image:
                                break
            
            if not img_url:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Create caption with title and link to website
            caption = f"Extra Fabulous Comics: {comic_title}\n\n[Link]({self.url})"
            
            # Post the comic
            self.post_comic(img_url, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_id,
                'title': comic_title,
                'image_url': img_url,
                'permalink': self.url,
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
    scraper = EfcScraper()
    scraper.check_for_updates() 