"""
Telegram API utilities
"""
import os
import json
import requests
from rsr.config import botapi

def send_message(botapi, chat, message, params=""):
    """
    Send a text message to a Telegram chat
    
    Args:
        botapi (str): Telegram Bot API key
        chat (str): Chat ID to send the message to
        message (str): Message text
        params (str): Additional URL parameters
        
    Returns:
        Response from Telegram API
    """
    if params:
        return requests.get(f"https://api.telegram.org/bot{botapi}/sendMessage?chat_id={chat}&text={message}&{params}")
    else:
        return requests.get(f"https://api.telegram.org/bot{botapi}/sendMessage?chat_id={chat}&text={message}")

def sendPhoto(chatid, url, caption=""):
    """
    Send a photo to a Telegram chat
    
    Args:
        chatid (str): Chat ID to send the photo to
        url (str): URL of the image
        caption (str): Caption for the image
        
    Returns:
        Response from Telegram API or None on failure
    """
    print(f"Posting {url} to {chatid}")
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.extrafabulouscomics.com/'
        }
        
        # Download the image
        img_response = requests.get(url, headers=headers)
        
        if img_response.status_code == 200:
            # Save file temporarily
            with open('temp_comic.jpg', 'wb') as f:
                f.write(img_response.content)
            
            # Send the photo using multipart/form-data
            files = {'photo': open('temp_comic.jpg', 'rb')}
            params = {'chat_id': chatid}
            
            if caption:
                if len(caption) > 200:
                    # Send photo first
                    response = requests.post(f"https://api.telegram.org/bot{botapi}/sendPhoto", files=files, data={'chat_id': chatid})
                    # Then send caption as separate message
                    send_message(botapi, chatid, caption)
                else:
                    params['caption'] = caption
                    params['parse_mode'] = 'Markdown'
                    response = requests.post(f"https://api.telegram.org/bot{botapi}/sendPhoto", files=files, data=params)
            else:
                response = requests.post(f"https://api.telegram.org/bot{botapi}/sendPhoto", files=files, data=params)
            
            # Clean up
            try:
                files['photo'].close()
                if os.path.exists('temp_comic.jpg'):
                    os.remove('temp_comic.jpg')
            except Exception as cleanup_error:
                print(f"Error cleaning up temp file: {str(cleanup_error)}")
                
            return response
        else:
            error_msg = f"Failed to download image (status {img_response.status_code}): {url}"
            print(error_msg)
            from rsr.config import adminchat
            send_message(botapi, adminchat, error_msg)
            return None
    except Exception as e:
        error_msg = f"Error sending photo: {str(e)}"
        print(error_msg)
        from rsr.config import adminchat
        send_message(botapi, adminchat, error_msg)
        return None

def sendAlbums(channel, array, caption=None):
    """
    Send a media group (album) to a Telegram chat
    
    Args:
        channel (str): Chat ID to send the album to
        array (list): List of media URLs
        caption (str, optional): Caption for the album
        
    Returns:
        Response from Telegram API
    """
    url = f"https://api.telegram.org/bot{botapi}/sendMediagroup"
    chat_id = channel
    photo_urls = []
    video_urls = []
    
    for i, media_url in enumerate(array):
        if "mp4" in media_url or "gif" in media_url:
            media_item = {'type': "video", "media": media_url}
            # Add caption to first item if provided
            if i == 0 and caption:
                media_item['caption'] = caption
                media_item['parse_mode'] = 'Markdown'
            video_urls.append(media_item)
        else:
            media_item = {'type': "photo", "media": media_url}
            # Add caption to first item if provided
            if i == 0 and caption:
                media_item['caption'] = caption
                media_item['parse_mode'] = 'Markdown'
            photo_urls.append(media_item)
    
    if len(array) > 10:
        number = len(array)
        start = 0
        stop = 10
        while number > 0:
            request = requests.get(url, 
                        {
                            "chat_id": chat_id,
                            "media": json.dumps(photo_urls[start:stop])
                        }
                    )
            start = stop
            stop += 10
            number -= 10
    else:
        print("\n\n--------------------------------")
        print(array)
        print("\n\n--------------------------------")
        request = requests.get(url, 
                        {
                            "chat_id": chat_id,
                            "media": json.dumps(photo_urls)
                        }
                    )
    return request 