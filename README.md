# RSS Slave Bot

A Python bot that scrapes webcomics from their original websites and posts them to Telegram channels. The bot is designed with a modular architecture for easy maintenance and extension.

## Features

- Scrapes 17 different webcomics from their original websites
- Posts comics to Telegram channels with proper attribution
- Stores comic history in MongoDB to avoid duplicate posts
- Modular architecture makes adding new comics easy
- Supports multi-image comics (like The Oatmeal)
- Error handling and logging for reliability

## Architecture

The codebase follows a modular architecture:

- `run.py` - Main entry point script that runs the bot
- `rsr/` - Main package
  - `main.py` - Core logic to run all scrapers in sequence
  - `config.py` - Configuration settings (API keys, channel IDs, etc.)
  - `scrapers/` - Package containing all webcomic scrapers
    - `base.py` - Base scraper class that all others inherit from
    - Individual scraper modules (one per webcomic)
  - `utils/` - Utility functions
    - `db.py` - Database utilities
    - `http.py` - HTTP request handling
    - `parsers.py` - HTML/XML parsing utilities
    - `telegram.py` - Telegram API utilities

## Implemented Scrapers

| Status | Scraper Name | File | Description |
|--------|-------------|------|-------------|
| ✅ | XKCD | `xkcd.py` | Direct API-based scraper with title, alt text as spoiler, and link |
| ✅ | The Oatmeal | `oatmeal.py` | RSS-based scraper with multi-image support |
| ✅ | Perry Bible Fellowship | `pbf.py` | Gallery-based scraper for PBF |
| ✅ | War & Peas | `warandpeas.py` | WordPress-based scraper with lazy loading |
| ✅ | Sarah's Scribbles | `sarahsscribbles.py` | Tumblr-based scraper |
| ✅ | Cyanide & Happiness | `explosm.py` | Direct image extraction with permalink |
| ✅ | Extra Fabulous Comics | `efc.py` | Wix-based website scraper |
| ✅ | Loading Artist | `loadingartist.py` | Two-step scraper (find comic link then image) |
| ✅ | Optipess | `optipess.py` | Single-page scraper with title extraction |
| ✅ | Pie Comic | `piecomic.py` | Tumblr-based scraper with recency scoring |
| ✅ | Poorly Drawn Lines | `pdl.py` | WordPress-based comic image extractor |
| ✅ | Nerf Now | `nerfnow.py` | Archive-based scraper with permalink following |
| ✅ | TheOdd1sOut | `theodd1sout.py` | Shopify-based scraper with structured data parsing |
| ✅ | Skeleton Claw | `skeletonclaw.py` | Tumblr-based scraper with image filtering |
| ✅ | Something Positive | `somethingpositive.py` | WordPress-based site with multiple image source strategies |
| ✅ | Safely Endangered | `safelyendangered.py` | Shopify-based comic site with srcset handling |
| ✅ | False Knees | `falseknees.py` | Archive-based scraper with multiple image finding strategies |

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/RSSSlaveBot.git
   cd RSSSlaveBot
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration:
   ```
   python setup_config.py
   ```
   Then edit `rsr/config.py` with your personal settings:
   - Get a Telegram bot token from [@BotFather](https://t.me/BotFather)
   - Create a Telegram channel where comics will be posted
   - Set your admin chat ID for error notifications

4. Ensure MongoDB is running on localhost:27017

5. Run the verification script to check your installation:
   ```
   python verify_installation.py
   ```

6. Start the bot:
   ```
   python run.py
   ```

## Configuration

The bot requires several configuration values to work properly:

- `botapi`: Your Telegram bot API token (from [@BotFather](https://t.me/BotFather))
- `adminchat`: Chat ID for receiving admin notifications and error messages
- `comics_channel`: Channel ID where comics will be posted (e.g., `@your_channel_name`)
- `mongodb_db`: Name of your MongoDB database (default: `comics_db`)

These values should be set in `rsr/config.py`. For security reasons, this file is not included in the repository. Instead, use `setup_config.py` to create it from the template.

## Database Structure

The bot uses MongoDB to track posted comics. Each scraper has its own collection, and documents typically include:
- `url` or `comic_id`: Unique identifier for the comic
- `image_url`: URL of the comic image
- `permalink`: Link to the original comic page
- `title`: Comic title (when available)
- `date`: Timestamp when the comic was posted

## Database Migration

If you need to move the bot to a different machine, you can use the provided database migration tools.

### Exporting the Database

```bash
python export_db.py
```

This will export all collections to JSON files in a `db_export` directory.

### Importing the Database

```bash
python import_db.py [options]
```

Options:
- `--host`: MongoDB host (default: localhost)
- `--port`: MongoDB port (default: 27017)
- `--db`: Database name (default: rssbot)
- `--dir`: Directory containing exported files (default: db_export)
- `--merge`: Merge with existing collections instead of replacing
- `--dry-run`: Show what would be imported without importing

## How to Add a New Scraper

1. Create a new file in `rsr/scrapers/` for your scraper (e.g., `mynewcomic.py`)
2. Implement a class that inherits from `BaseScraper`
3. Implement the `check_for_updates()` method
4. Add your scraper to the `active_scrapers` list in `rsr/scrapers/__init__.py`

Example template:

```python
from datetime import datetime
from rsr.scrapers.base import BaseScraper
from rsr.utils.http import handleRequest
from rsr.utils.parsers import makesoup
from rsr.config import comics_channel

class MyNewComicScraper(BaseScraper):
    def __init__(self):
        # Initialize with database collection name and channel ID
        super().__init__('mynewcomic_collection_name', comics_channel)
        self.comic_name = "My New Comic"
        self.url = "https://mynewcomic.example.com/"
    
    def check_for_updates(self):
        """
        Check for and post new comics
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
            # Find the comic image URL
            # ...your scraping logic here...
            
            # Check if we've already seen this comic
            if self.is_already_posted(comic_id, 'url'):
                return numberposted
            
            # Create caption with link
            caption = f"My New Comic: {title}\n\n[Link]({permalink})"
            
            # Post the comic
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
            self.log_success(numberposted)
                
        except Exception as e:
            self.log_error(f"Error processing comic: {str(e)}")
        
        return numberposted
```

## Troubleshooting

### Database Issues

- **Duplicate Key Errors**: Run `verify_installation.py` to fix index issues.
- **Missing Comics**: Check the MongoDB collection for the specific scraper.
- **Connection Issues**: Verify MongoDB is running with `systemctl status mongod`.

### Scraper Issues

Common issues with scrapers:
- Website structure changes: Update the scraper's HTML parsing logic
- Rate limiting: Add delays or custom headers to `handleRequest`
- Image URL problems: Check if the site uses CDNs or dynamic image loading

## Publishing Your Own Fork

If you've made changes to this repository and want to publish your own fork, you need to be careful about sensitive information in the configuration files.

### Removing Sensitive Data

The repository includes scripts to safely remove sensitive information from Git history:

1. First, create the template configuration file:
   ```
   cp rsr/config.py rsr/config.template.py
   ```
   Then edit `rsr/config.template.py` to remove any personal API keys or tokens.

2. Run the appropriate cleanup script for your operating system:
   - Linux/Mac: `bash cleanup_history.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File cleanup_history.ps1`

3. After the script completes, verify that `rsr/config.py` is no longer in the Git history:
   ```
   git log --all --full-history -- rsr/config.py
   ```
   This command should show no results.

4. Finally, force push your changes to publish the cleaned repository:
   ```
   git push origin --force --all
   ```

### Note for New Users

When someone clones your published repository, they'll need to:
1. Run `python setup_config.py` to create their own `config.py` file
2. Edit the configuration with their own API keys and settings

## License

This project is for personal use only. 