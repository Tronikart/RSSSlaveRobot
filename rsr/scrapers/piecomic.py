"""
Scraper for Pie Comic webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import botapi, adminchat, comics_channel

class PieComicScraper(BaseScraper):
    """
    Scraper for Pie Comic webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('piecomic', comics_channel)
        self.comic_name = "Pie Comic"
        self.url = "https://piecomic.tumblr.com"
    
    def check_for_updates(self):
        """
        Check for and post new Pie Comic comics
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
            # Look for post metadata with timestamps
            postmeta_divs = soup.find_all("div", class_="postmeta")
            
            if not postmeta_divs:
                self.log_error("No post metadata found")
                return numberposted
            
            # Find all posts with timestamps
            recent_posts = []
            for meta_div in postmeta_divs:
                links = meta_div.find_all("a")
                if links and len(links) > 0:
                    timestamp_link = links[0]
                    timestamp_text = timestamp_link.text.strip()
                    permalink = timestamp_link.get('href')
                    
                    # Find the parent post container
                    parent_post = meta_div.find_parent("div", class_="post") or meta_div.find_parent()
                    if parent_post:
                        # Assign a recency score (lower is more recent)
                        recency_score = 999  # Default high score (old)
                        
                        # Parse common Tumblr timestamp formats
                        if "minute ago" in timestamp_text or "minutes ago" in timestamp_text:
                            recency_score = 1
                        elif "hour ago" in timestamp_text or "hours ago" in timestamp_text:
                            recency_score = 2
                        elif "day ago" in timestamp_text or "days ago" in timestamp_text:
                            recency_score = 3
                        elif "week ago" in timestamp_text or "weeks ago" in timestamp_text:
                            recency_score = 4
                        elif "month ago" in timestamp_text or "months ago" in timestamp_text:
                            # If it says "X months ago", extract the number
                            month_match = re.search(r'(\d+) months ago', timestamp_text)
                            if month_match:
                                recency_score = 5 + int(month_match.group(1))
                            else:
                                recency_score = 5  # Just "month ago" (singular)
                        elif "year ago" in timestamp_text or "years ago" in timestamp_text:
                            # If it says "X years ago", extract the number
                            year_match = re.search(r'(\d+) years ago', timestamp_text)
                            if year_match:
                                recency_score = 100 + int(year_match.group(1))
                            else:
                                recency_score = 100  # Just "year ago" (singular)
                        
                        # Add to the list of posts
                        recent_posts.append({
                            "element": parent_post,
                            "timestamp": timestamp_text,
                            "permalink": permalink,
                            "recency_score": recency_score
                        })
            
            if not recent_posts:
                self.log_error("No posts with timestamps found")
                return numberposted
            
            # Sort posts by recency (lowest score first)
            recent_posts.sort(key=lambda post: post["recency_score"])
            
            # Get the most recent post
            latest_post = recent_posts[0]["element"]
            
            # Get the permalink and extract post ID
            permalink = recent_posts[0]["permalink"]
            post_id_match = re.search(r"/post/(\d+)", permalink)
            
            if not post_id_match:
                self.log_error("Could not extract post ID from permalink")
                return numberposted
                
            post_id = post_id_match.group(1)
            
            # Check if we've already seen this comic
            if self.is_already_posted(post_id, 'post_id'):
                return numberposted
            
            # Find the image in the post
            images = latest_post.find_all("img")
            image_url = None
            
            for img in images:
                if 'src' in img.attrs:
                    src = img['src']
                    
                    # Skip common UI elements
                    if any(x in src.lower() for x in ['avatar', 'icon', 'logo', 'emoji']):
                        continue
                    
                    # Skip very small images
                    is_small = False
                    if 'width' in img.attrs and img['width'].isdigit() and int(img['width']) < 100:
                        is_small = True
                    if 'height' in img.attrs and img['height'].isdigit() and int(img['height']) < 100:
                        is_small = True
                    
                    if not is_small:
                        # For Tumblr, replace _500 with _1280 for higher resolution
                        if "_500" in src:
                            high_res_url = src.replace("_500", "_1280")
                        else:
                            # General approach: remove size suffixes
                            high_res_url = re.sub(r'_\d+(\.\w+)$', r'\1', src)
                        
                        # If the URL has parameters, extract the base URL
                        if '?' in high_res_url:
                            high_res_url = high_res_url.split('?')[0]
                        
                        # Test if this URL works
                        test_request = handleRequest(high_res_url)
                        if not test_request['timeout'] and test_request['request'].status_code == 200:
                            image_url = high_res_url
                            break
                        else:
                            # If high-res doesn't work, try the original URL
                            test_request = handleRequest(src)
                            if not test_request['timeout'] and test_request['request'].status_code == 200:
                                image_url = src
                                break
                            else:
                                # Try different common sizes
                                for size in ["_1280", "_640", "_540", "_500", "_400", "_250"]:
                                    size_url = re.sub(r'_\d+(\.\w+)$', f'{size}\\1', src)
                                    test_request = handleRequest(size_url)
                                    if not test_request['timeout'] and test_request['request'].status_code == 200:
                                        image_url = size_url
                                        break
            
            # If no image found directly, try the permalink page
            if not image_url and permalink:
                permalink_request = handleRequest(permalink)
                
                if not permalink_request['timeout']:
                    permalink_soup = makesoup(permalink_request['request'])
                    
                    # Try to find images on the permalink page
                    permalink_images = permalink_soup.find_all("img")
                    
                    for img in permalink_images:
                        if 'src' in img.attrs:
                            src = img['src']
                            
                            # Skip common UI elements
                            if any(x in src.lower() for x in ['avatar', 'icon', 'logo', 'emoji']):
                                continue
                            
                            # Skip very small images
                            is_small = False
                            if 'width' in img.attrs and img['width'].isdigit() and int(img['width']) < 100:
                                is_small = True
                            if 'height' in img.attrs and img['height'].isdigit() and int(img['height']) < 100:
                                is_small = True
                            
                            if not is_small:
                                # For Tumblr, replace _500 with _1280 for higher resolution
                                if "_500" in src:
                                    high_res_url = src.replace("_500", "_1280")
                                else:
                                    # General approach: remove size suffixes
                                    high_res_url = re.sub(r'_\d+(\.\w+)$', r'\1', src)
                                
                                if '?' in high_res_url:
                                    high_res_url = high_res_url.split('?')[0]
                                
                                image_url = high_res_url
                                break
            
            if not image_url:
                self.log_error("Failed to find comic image")
                return numberposted
            
            # Get the title
            title_elem = latest_post.find(['h2', 'h3']) or latest_post.find(class_=re.compile("title"))
            title = title_elem.text.strip() if title_elem else "Pie Comic"
            
            # Post the comic
            caption = f"Pie Comic: {title}\n\n[Link]({permalink})"
            self.post_comic(image_url, caption)
            
            # Add to database
            self.add_to_posted({
                'post_id': post_id,
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
    scraper = PieComicScraper()
    scraper.check_for_updates() 