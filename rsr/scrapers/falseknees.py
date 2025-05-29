"""
Scraper for False Knees webcomic
"""
from datetime import datetime
import re

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class FalseKneesScraper(BaseScraper):
    """
    Scraper for False Knees webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('falseknees', comics_channel)
        self.comic_name = "False Knees"
        self.url = "https://falseknees.com/archive.html"
    
    def check_for_updates(self):
        """
        Check for and post new False Knees comics
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
            # The archive page has links to individual comics
            # Each entry appears to be in the format "Month Day, Year - Title"
            comic_links = soup.find_all('a', href=re.compile(r'\d+\.html'))
            
            if not comic_links:
                self.log_error("No comic links found")
                return numberposted
            
            # Get the first (latest) comic link
            latest_link = comic_links[0]
            
            # Parse the link text to get date and title
            link_text = latest_link.text.strip()
            
            # Extract date and title - usually in format "Month Day, Year - Title"
            date_title_match = re.match(r'(.*?\d{4}) - (.*)', link_text)
            title = "False Knees"
            date_str = ""
            
            if date_title_match:
                date_str = date_title_match.group(1)
                title = date_title_match.group(2)
            else:
                # If the pattern doesn't match, use the whole text as title
                title = link_text
            
            # Get the permalink
            comic_href = latest_link['href']
            
            # Fix double slashes in URL if present
            if comic_href.startswith('/'):
                comic_href = comic_href[1:]
                
            if not comic_href.startswith('http'):
                # Handle relative URLs
                permalink = f"https://falseknees.com/{comic_href}"
            else:
                permalink = comic_href
            
            # Clean up any double slashes in the URL
            permalink = permalink.replace('//comics', '/comics')
            
            # Extract comic ID from the URL (typically a number)
            comic_id_match = re.search(r'(\d+)\.html', permalink)
            if not comic_id_match:
                self.log_error("Could not extract comic ID from permalink")
                return numberposted
                
            comic_id = comic_id_match.group(1)
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'comic_id'):
                return numberposted
            
            # Visit the comic page to get the image
            comic_request = handleRequest(permalink)
            
            if comic_request['timeout']:
                self.log_error("Comic page request timed out")
                return numberposted
                
            comic_soup = makesoup(comic_request['request'])
            
            # Try to find the comic image
            # First try direct path based on comic ID
            image_url = None
            
            # Try each possible path pattern
            possible_paths = [
                f"https://falseknees.com/comics/imgs/{comic_id}.webp",
                f"https://falseknees.com/comics/img/{comic_id}.webp",
                f"https://falseknees.com/imgs/{comic_id}.webp",
                f"https://falseknees.com/img/{comic_id}.webp",
                f"https://falseknees.com/comics/imgs/{comic_id}.png",
                f"https://falseknees.com/comics/img/{comic_id}.png",
                f"https://falseknees.com/imgs/{comic_id}.png",
                f"https://falseknees.com/img/{comic_id}.png",
                f"https://falseknees.com/comics/imgs/{comic_id}.jpg",
                f"https://falseknees.com/comics/img/{comic_id}.jpg",
                f"https://falseknees.com/imgs/{comic_id}.jpg",
                f"https://falseknees.com/img/{comic_id}.jpg"
            ]
            
            for path in possible_paths:
                img_request = handleRequest(path)
                if not img_request['timeout'] and img_request['request'].status_code == 200:
                    image_url = path
                    break
            
            # If direct path failed, look for og:image meta tag
            if not image_url:
                og_image = comic_soup.find('meta', property='og:image')
                if og_image and 'content' in og_image.attrs:
                    img_url = og_image['content']
                    if not img_url.startswith('http'):
                        if img_url.startswith('/'):
                            img_url = img_url[1:]
                        img_url = f"https://falseknees.com/{img_url}"
                    
                    image_url = img_url
            
            # If still not found, look for image tags in main content
            if not image_url:
                main_content = comic_soup.find('div', id='main') or comic_soup.find('div', class_='center')
                if main_content:
                    comic_img = main_content.find('img')
                    if comic_img and 'src' in comic_img.attrs:
                        img_url = comic_img['src']
                        if not img_url.startswith('http'):
                            # Handle relative URLs
                            if img_url.startswith('/'):
                                img_url = img_url[1:]
                            img_url = f"https://falseknees.com/{img_url}"
                        
                        image_url = img_url
            
            if not image_url:
                self.log_error("Found comic but couldn't find image URL")
                return numberposted
            
            # Post the comic
            caption = f"False Knees: {title}"
            if date_str:
                caption += f" ({date_str})"
            if permalink:
                caption += f"\n\n[Link]({permalink})"
            
            self.post_comic(image_url, caption)
            
            # Add to database
            self.add_to_posted({
                'comic_id': comic_id,
                'title': title,
                'date': date_str,
                'url': permalink,
                'image_url': image_url,
                'posted_date': datetime.now()
            })
            
            numberposted += 1
            
            # Log success
            self.log_success(numberposted)
                
        except Exception as e:
            self.log_error(f"Error processing comic: {str(e)}")
        
        return numberposted

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = FalseKneesScraper()
    scraper.check_for_updates() 