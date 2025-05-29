"""
Scraper for Sarah's Scribbles webcomic
"""
from datetime import datetime
import re
import time
import hashlib

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class SarahsScribblesScraper(BaseScraper):
    """
    Scraper for Sarah's Scribbles webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('sarahsscribbles', comics_channel)
        self.comic_name = "Sarah's Scribbles"
        self.url = "https://sarahcandersen.com/"
    
    def check_for_updates(self):
        """
        Check for and post new Sarah's Scribbles comics
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
            # Tumblr structure: typically posts are in articles
            posts = soup.find_all("article") or soup.find_all(class_=re.compile("post|entry|tumblr-post"))
            
            if not posts or len(posts) == 0:
                self.log_error("No posts found")
                return numberposted
            
            # Get the latest post
            latest_post = posts[0]
            
            # Extract date/timestamp if available
            timestamp = latest_post.find(class_=re.compile("date|time|timestamp"))
            date_str = timestamp.text.strip() if timestamp else "Unknown date"
            
            # Find images in the post
            images = latest_post.find_all("img")
            image_url = None
            
            # Process images to find the comic
            if images:
                for img in images:
                    if 'src' in img.attrs and img['src']:
                        img_url = img['src']
                        
                        # Fix truncated URLs
                        if img_url.endswith('...'):
                            for attr in ['data-highres', 'data-orig-src', 'data-src']:
                                if attr in img.attrs and img[attr]:
                                    img_url = img[attr]
                                    break
                        
                        # Check if it's a Tumblr media URL
                        if 'media.tumblr.com' in img_url:
                            # Get the highest resolution version
                            img_url = re.sub(r'_\d+(\.\w+)$', r'\1', img_url)
                        
                        # Use high-res version if available
                        if 'data-highres' in img.attrs and img['data-highres']:
                            img_url = img['data-highres']
                        
                        # Filter out small icons
                        if not (img.get('width') and int(img.get('width', '500')) < 100):
                            image_url = img_url
                            break
            
            if not image_url:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Generate a unique comic ID
            # Try to find permalink for ID
            permalink = None
            comic_id = None
            
            permalink_elem = latest_post.find('a', class_=re.compile("permalink")) or latest_post.find('a', attrs={'rel': 'permalink'})
            if permalink_elem and 'href' in permalink_elem.attrs:
                permalink = permalink_elem['href']
                # Don't use the homepage URL as permalink
                if permalink == self.url or permalink == "/":
                    permalink = None
                else:
                    # Extract ID from permalink URL
                    id_match = re.search(r'/post/(\d+)', permalink)
                    if id_match:
                        comic_id = id_match.group(1)
            
            # If we couldn't extract a proper comic ID, generate one from the image URL
            if not comic_id and image_url:
                comic_id = hashlib.md5(image_url.encode()).hexdigest()[:16]
            
            # If we still don't have an ID, use timestamp as last resort
            if not comic_id:
                comic_id = f"ss_{int(time.time())}"
            
            # Find post title if available
            title_elem = latest_post.find(['h1', 'h2', 'h3']) or latest_post.find(class_=re.compile("title|heading"))
            title = title_elem.text.strip() if title_elem else "Sarah's Scribbles"
            
            # Get post content/description
            content_elem = latest_post.find(class_=re.compile("content|caption|text"))
            description = content_elem.get_text(strip=True) if content_elem else ""
            
            # Check by image URL first since it's the most reliable identifier
            existing_by_image = self.posted.find_one({'image_url': image_url})
            if existing_by_image:
                return numberposted
            
            # Check if we've already seen this comic by comic_id
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
                
            # Generate caption
            caption = f"Sarah's Scribbles: {title}\n"
            if description:
                caption += f"{description}\n"
            if permalink and permalink != self.url:
                caption += f"Source: {permalink}"
            else:
                caption += f"Source: Sarah's Scribbles"
            
            # Post the comic
            self.post_comic(image_url, caption)
            
            # Add to database - explicitly avoid storing the homepage URL
            doc = {
                'comic_id': comic_id,
                'title': title,
                'date': date_str,
                'image_url': image_url,
                'posted_date': datetime.now()
            }
            
            # Only add permalink if it's not the homepage
            if permalink and permalink != self.url and permalink != "/":
                doc['url'] = permalink
                
            self.add_to_posted(doc)
            
            numberposted += 1
            
            # Log success
            self.log_success(numberposted)
                
        except Exception as e:
            self.log_error(f"Error processing comic: {str(e)}")
        
        return numberposted

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = SarahsScribblesScraper()
    scraper.check_for_updates() 