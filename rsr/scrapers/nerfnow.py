"""
Scraper for Nerf Now webcomic
"""
from datetime import datetime
import re
import requests

from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class NerfNowScraper(BaseScraper):
    """
    Scraper for Nerf Now webcomic
    """
    
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('NerfNow', comics_channel)
        self.comic_name = "Nerf Now"
        self.url = "http://www.nerfnow.com/archives"
    
    def check_for_updates(self):
        """
        Check for and post new Nerf Now comics
        Returns number of new comics posted
        """
        numberposted = 0
        
        # Request the archive page
        print(f"Requesting URL: {self.url}")
        request = handleRequest(self.url)
        
        if request['timeout']:
            self.log_error("Website request timed out")
            print("Website request timed out")
            return numberposted
        
        soup = makesoup(request['request'])
        try:
            # Find all li tags that contain comic links
            li_tags = soup.find_all('li')
            print(f"Found {len(li_tags)} li tags")
            
            if not li_tags or len(li_tags) == 0:
                self.log_error("No li tags found")
                print("No li tags found")
                return numberposted
                
            # Print the first 5 li tags to see what they contain
            for i, li in enumerate(li_tags[:5]):
                print(f"Li tag {i}: {li}")
                if li.a and 'href' in li.a.attrs:
                    print(f"  Link: {li.a['href']}")
                
            if not li_tags[0] or not li_tags[0].a or 'href' not in li_tags[0].a.attrs:
                self.log_error("Failed to parse archive page")
                print("Failed to parse archive page - first li tag doesn't have a link")
                return numberposted
                
            # Get the latest comic URL
            comic_url = li_tags[0].a['href']
            print(f"Latest comic URL: {comic_url}")
            
            comic_id_match = re.findall(r'/+comic/(\d+)', comic_url)
            
            if not comic_id_match:
                self.log_error("Failed to extract comic ID from URL")
                print(f"Failed to extract comic ID from URL: {comic_url}")
                return numberposted
                
            comic_id = comic_id_match[0]
            print(f"Extracted comic ID: {comic_id}")
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                print(f"Comic ID {comic_id} already posted")
                return numberposted
            
            # Visit the comic page to get the image
            permalink = f"http://www.nerfnow.com/comic/{comic_id}"
            print(f"Requesting permalink: {permalink}")
            comic_request = requests.get(permalink)
            comic_soup = makesoup(comic_request)
            
            # Find the comic image
            comic_div = comic_soup.find('div', id="comic")
            if not comic_div:
                print("Could not find div with id='comic'")
                if comic_soup.find('div', id="comix"):
                    print("Found div with id='comix' instead")
                    comic_div = comic_soup.find('div', id="comix")
            
            if not comic_div or not comic_div.img or 'src' not in comic_div.img.attrs:
                self.log_error("Failed to find comic image")
                print("Failed to find comic image")
                # Print some of the HTML to debug
                print(f"Page HTML excerpt: {str(comic_soup)[:500]}...")
                return numberposted
                
            image_url = comic_div.img['src']
            print(f"Found image URL: {image_url}")
            
            # Make sure the image URL is absolute
            if not image_url.startswith('http'):
                image_url = f"http://www.nerfnow.com{image_url}"
                print(f"Converted to absolute URL: {image_url}")
            
            # Find a title if available
            title_elem = comic_soup.find(['h1', 'h2', 'h3'], class_='title') or comic_soup.find('title')
            title = title_elem.text.strip() if title_elem else "Nerf Now"
            print(f"Comic title: {title}")
            
            # Post the comic
            print(f"Posting comic with caption: Nerf Now: {title}\n\n[Link]({permalink})")
            caption = f"Nerf Now: {title}\n\n[Link]({permalink})"
            self.post_comic(image_url, caption)
            
            # Add to database
            self.add_to_posted({
                'url': comic_id,
                'title': title,
                'image_url': image_url,
                'permalink': permalink,
                'date': datetime.now()
            })
            
            numberposted += 1
            
            # Log success
            self.log_success(numberposted)
                
        except Exception as e:
            self.log_error(f"Error processing comic: {str(e)}")
            print(f"Error processing comic: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return numberposted

# Testing code - will only run if this file is executed directly
if __name__ == "__main__":
    scraper = NerfNowScraper()
    print(f"Running Nerf Now scraper test...")
    result = scraper.check_for_updates()
    print(f"Result: {result} new comics posted") 