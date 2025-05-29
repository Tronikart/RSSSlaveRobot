"""
Scraper for Loading Artist webcomic
"""
from datetime import datetime
import requests

from rsr.scrapers.base import BaseScraper
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class LoadingArtistScraper(BaseScraper):
    """
    Scraper for Loading Artist webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('la', comics_channel)
        self.comic_name = "Loading Artist"
        self.url = "https://loadingartist.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Loading Artist comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the website with custom headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        request = requests.get(self.url, headers=headers)
        
        if not request.ok:
            self.log_error("Website request failed")
            return numberposted
        
        soup = makesoup(request)
        try:
            # Find all images
            img_tags = soup.find_all('img')
            comic_img = None
            comic_title = "Loading Artist"
            
            # Find all links that might lead to comics
            links = soup.find_all('a')
            comic_link = None
            
            # Find the latest comic link
            for link in links:
                if link.get('href') and '/comic/' in link.get('href'):
                    comic_link = link.get('href')
                    # If link has text content, use it as title
                    if link.text and link.text.strip():
                        comic_title = link.text.strip()
                    break
            
            # If we found a comic link, fetch the full comic page
            if comic_link:
                if not comic_link.startswith('http'):
                    comic_link = f"https://loadingartist.com{comic_link}"
                
                # Visit the comic page to get the full image
                comic_request = requests.get(comic_link, headers=headers)
                if comic_request.ok:
                    comic_soup = makesoup(comic_request)
                    
                    # Look for the comic image on the dedicated page
                    comic_imgs = comic_soup.find_all('img')
                    for img in comic_imgs:
                        if img.get('src') and '/full' in img.get('src'):
                            comic_img = img.get('src')
                            if not comic_img.startswith('http'):
                                comic_img = f"https://loadingartist.com{comic_img}"
                            break
                    
                    # If we couldn't find a 'full' image, look for any comic image
                    if not comic_img:
                        for img in comic_imgs:
                            if img.get('src') and '/comic/' in img.get('src') and not '/thumb' in img.get('src'):
                                comic_img = img.get('src')
                                if not comic_img.startswith('http'):
                                    comic_img = f"https://loadingartist.com{comic_img}"
                                break
            
            # If we still don't have an image, try the thumbnail approach
            if not comic_img:
                for img in img_tags:
                    if 'src' in img.attrs and '/comic/' in img['src'] and 'thumb' in img['src']:
                        # Found the comic thumbnail - convert to full image URL
                        comic_url = img['src'].replace('thumb', 'full').replace('thumb_wide', 'full')
                        # Make sure it's a full URL
                        if not comic_url.startswith('http'):
                            comic_url = f"https://loadingartist.com{comic_url}"
                        comic_img = comic_url
                        break
            
            if not comic_img:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_img, 'url'):
                return numberposted
            
            # Create the permalink if we have one
            permalink = comic_link if comic_link else self.url
            
            # Create caption with link
            caption = f"Loading Artist: {comic_title}\n\n[Link]({permalink})"
            
            # Post the comic
            self.post_comic(comic_img, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_img,
                'title': comic_title,
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
    scraper = LoadingArtistScraper()
    scraper.check_for_updates() 