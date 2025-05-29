"""
Configuration settings for the RSS Slave Bot

Copy this file to config.py and fill in your own values
"""

# Telegram bot API key - Get this from @BotFather
botapi = 'YOUR_BOT_API_TOKEN'

# Admin chat ID for notifications - Your personal chat ID for error messages
adminchat = 'YOUR_ADMIN_CHAT_ID'

# Default channel for comics - Channel where comics will be posted
comics_channel = '@YOUR_CHANNEL_NAME'

# Reddit user agent - Only needed if using Reddit-based scrapers
reddit_user = "YOUR_REDDIT_USERNAME"

# MongoDB configuration
mongodb_host = 'localhost'
mongodb_port = 27017
mongodb_db = 'comics_db' 