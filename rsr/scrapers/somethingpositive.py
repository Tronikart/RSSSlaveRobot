"""
Scraper for Something Positive webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class SomethingPositiveScraper(BaseScraper):
    """
    Scraper for Something Positive webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('somethingpositive', comics_channel)
        self.comic_name = "Something Positive"
        self.url = "https://somethingpositive.net/"
    
    def check_for_updates(self):
        """
        Check for and post new Something Positive comics
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
            # Look for all article elements - Something Positive site uses WordPress
            articles = soup.find_all('article')
            
            if not articles:
                self.log_error("No article elements found")
                return numberposted
            
            # Find Something Positive comics by looking for specific categories or tags
            latest_sp_post = None
            
            for article in articles:
                # Check if it's a Something Positive comic post based on various indicators
                # Look for "Something*Positive" in category links
                category_links = article.find_all('a', href=re.compile(r'category/something', re.IGNORECASE))
                
                # Also look for "Webcomic" category
                webcomic_links = article.find_all('a', href=re.compile(r'category/webcomic', re.IGNORECASE))
                
                # Look for specific text in the article
                sp_text = article.find(string=re.compile(r'Something\*Positive', re.IGNORECASE))
                
                # Look for title pattern that matches date format (e.g., "May 27, 2025")
                title_elem = article.find(['h1', 'h2', 'h3'])
                title_match = False
                if title_elem:
                    title_match = bool(re.match(r'(January|February|March|April|May|June|July|August|September|October|November|December) \d+, \d{4}', title_elem.text.strip()))
                
                # Check for post-thumbnail that contains a comic image
                thumbnail_link = article.find('a', class_='post-thumbnail')
                has_comic_thumbnail = False
                if thumbnail_link:
                    comic_img = thumbnail_link.find('img', alt=re.compile(r'Comic for', re.IGNORECASE))
                    has_comic_thumbnail = bool(comic_img)
                
                # If any of these indicators are found, this is likely a Something Positive comic post
                if category_links or webcomic_links or sp_text or (title_match and has_comic_thumbnail):
                    latest_sp_post = article
                    break
            
            if not latest_sp_post:
                self.log_error("No Something Positive comic posts found")
                return numberposted
            
            # Try to find the title/date (usually the heading)
            title_elem = latest_sp_post.find(['h1', 'h2', 'h3']) or latest_sp_post.find(class_=re.compile('title|heading'))
            title = "Something Positive"
            if title_elem:
                title = title_elem.text.strip()
            
            # Find permalink
            permalink_elem = latest_sp_post.find('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/')) or latest_sp_post.find('a', text=re.compile('permalink', re.IGNORECASE))
            permalink = None
            comic_id = None
            
            if not permalink_elem or 'href' not in permalink_elem.attrs:
                self.log_error("Could not find permalink")
                return numberposted
                
            permalink = permalink_elem['href']
            if not permalink.startswith('http'):
                # Handle relative URLs
                permalink = f"https://somethingpositive.net{permalink}"
            
            # Extract post ID from permalink
            post_id_match = re.search(r'/(\d{4}/\d{2}/\d{2}/[^/]+)/?$', permalink)
            if not post_id_match:
                self.log_error("Could not extract post ID from permalink")
                return numberposted
                
            comic_id = post_id_match.group(1)
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
            
            # Find the comic image - first check in post-thumbnail
            image_url = None
            
            # Look for the post-thumbnail element which typically contains the comic image
            thumbnail_link = latest_sp_post.find('a', class_='post-thumbnail')
            if thumbnail_link:
                comic_img = thumbnail_link.find('img')
                if comic_img and 'src' in comic_img.attrs:
                    img_url = comic_img['src']
                    if not img_url.startswith('http'):
                        # Handle relative URLs
                        img_url = f"https://somethingpositive.net{img_url}"
                    
                    image_url = img_url
            
            # If no image found in post-thumbnail, look for links with "Comic for" text
            if not image_url:
                comic_links = latest_sp_post.find_all('a', string=re.compile(r'Comic for', re.IGNORECASE))
                
                for link in comic_links:
                    if 'href' in link.attrs:
                        comic_page_url = link['href']
                        if not comic_page_url.startswith('http'):
                            # Handle relative URLs
                            comic_page_url = f"https://somethingpositive.net{comic_page_url}"
                        
                        # Visit the comic page to get the image
                        comic_request = handleRequest(comic_page_url)
                        if not comic_request['timeout']:
                            comic_soup = makesoup(comic_request['request'])
                            
                            # Find the comic image on the page
                            article_content = comic_soup.find('div', class_='entry-content')
                            if article_content:
                                content_imgs = article_content.find_all('img')
                                if content_imgs:
                                    for img in content_imgs:
                                        if 'src' in img.attrs:
                                            # Skip small UI elements
                                            if any(x in img['src'].lower() for x in ['avatar', 'icon', 'logo', 'button']):
                                                continue
                                            
                                            img_url = img['src']
                                            if not img_url.startswith('http'):
                                                # Handle relative URLs
                                                img_url = f"https://somethingpositive.net{img_url}"
                                            
                                            image_url = img_url
                                            break
            
            # If we still don't have an image, try looking at figures
            if not image_url:
                figures = latest_sp_post.find_all('figure') or latest_sp_post.find_all(class_='wp-block-image')
                for figure in figures:
                    img = figure.find('img')
                    if img and 'src' in img.attrs:
                        img_url = img['src']
                        if not img_url.startswith('http'):
                            # Handle relative URLs
                            img_url = f"https://somethingpositive.net{img_url}"
                        
                        image_url = img_url
                        break
            
            if not image_url:
                self.log_error("Found comic but couldn't find image URL")
                return numberposted
            
            # Post the comic
            caption = f"Something Positive: {title}"
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
    scraper = SomethingPositiveScraper()
    scraper.check_for_updates() 