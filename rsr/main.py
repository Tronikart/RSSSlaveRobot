"""
Main entry point for the RSS Slave Bot

This script runs all the active scrapers in sequence
"""
from datetime import datetime

from rsr.scrapers import active_scrapers
from rsr.utils.telegram import send_message
from rsr.config import botapi, adminchat

def run_scraper(scraper_class):
    """
    Run a scraper with proper error handling
    
    Args:
        scraper_class: The scraper class to instantiate and run
        
    Returns:
        int: Number of comics posted
    """
    try:
        scraper = scraper_class()
        return scraper.check_for_updates()
    except Exception as e:
        scraper_name = getattr(scraper_class, "__name__", "Unknown scraper")
        error_msg = f"{scraper_name} error: {str(e)}"
        print(error_msg)
        send_message(botapi, adminchat, error_msg)
        return 0

def main():
    """Main function to run all scrapers"""
    # Log start time
    now = datetime.now()
    message = f"{now.strftime('%Y-%m-%d %H:%M:%S')} Checking for updates..."
    send_message(botapi, adminchat, f"*{message}*", "parse_mode=Markdown")
    
    # Run all active scrapers
    for scraper_class in active_scrapers:
        run_scraper(scraper_class)
    
    # Log completion
    send_message(botapi, adminchat, "*Done!*", "parse_mode=Markdown")

if __name__ == "__main__":
    main() 