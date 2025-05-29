"""
Scraper for Skeleton Claw webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class SkeletonClawScraper(BaseScraper):
    """
    Scraper for Skeleton Claw webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('skeletonclaw', comics_channel)
        self.comic_name = "Skeleton Claw"
        self.url = "https://www.skeletonclaw.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Skeleton Claw comics
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
            # The site is a Tumblr blog with posts in a certain format
            # Looking for posts with comic tags
            comic_posts = soup.find_all(lambda tag: tag.name == 'article' or 
                                      (tag.has_attr('class') and any('post' in c.lower() for c in tag['class'])))
            
            if not comic_posts:
                # Try alternate methods to find posts
                comic_posts = soup.find_all(class_=re.compile('post|entry|article'))
                
                if not comic_posts:
                    self.log_error("No comic posts found")
                    return numberposted
            
            # If we have comic entries, process the first (latest) one
            if not comic_posts or len(comic_posts) == 0:
                self.log_error("No comic posts found")
                return numberposted
                
            latest_post = comic_posts[0]
            
            # Try to find the date for the title
            date_elem = latest_post.find(class_=re.compile('date|time|when|posted'))
            title = "Skeleton Claw"
            if date_elem:
                title += f" - {date_elem.text.strip()}"
            
            # Find permalink if available
            permalink_elem = latest_post.find('a', class_=re.compile('permalink')) or latest_post.find('a', href=re.compile(r'/post/'))
            if not permalink_elem or 'href' not in permalink_elem.attrs:
                self.log_error("Could not find permalink")
                return numberposted
                
            permalink = permalink_elem['href']
            if not permalink.startswith('http'):
                # Handle relative URLs
                permalink = f"https://www.skeletonclaw.com{permalink}"
            
            # Extract post ID from permalink if available
            post_id_match = re.search(r'/post/(\d+)', permalink)
            if not post_id_match:
                self.log_error("Could not extract post ID from permalink")
                return numberposted
                
            comic_id = post_id_match.group(1)
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
            
            # Find the comic image
            images = latest_post.find_all('img')
            image_url = None
            
            if not images:
                self.log_error("No images found in post")
                return numberposted
                
            for img in images:
                if 'src' in img.attrs and img['src']:
                    img_url = img['src']
                    
                    # Skip icons and UI elements
                    if any(x in img_url.lower() for x in ['avatar', 'icon', 'logo', 'emoji']):
                        continue
                    
                    # Skip very small images
                    if 'width' in img.attrs and img['width'].isdigit() and int(img['width']) < 100:
                        continue
                    if 'height' in img.attrs and img['height'].isdigit() and int(img['height']) < 100:
                        continue
                    
                    # Get high-resolution version
                    if '_.jpg' in img_url or '_1280.jpg' in img_url:
                        # Already high resolution
                        image_url = img_url
                    else:
                        # Try to get high-resolution version by removing size suffix
                        high_res_url = re.sub(r'_\d+(\.\w+)$', r'\1', img_url)
                        image_url = high_res_url
                    
                    break
            
            # If we couldn't find any good images, just use the first one as a fallback
            if not image_url and images and 'src' in images[0].attrs:
                image_url = images[0]['src']
            
            if not image_url:
                self.log_error("Found comic but couldn't find image URL")
                return numberposted
            
            # Post the comic
            caption = f"Skeleton Claw\n\n[Link]({permalink})"
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
    scraper = SkeletonClawScraper()
    scraper.check_for_updates() 