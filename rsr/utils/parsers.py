"""
HTML and XML parsing utilities
"""
from bs4 import BeautifulSoup
from rsr.config import botapi, adminchat
from rsr.utils.telegram import send_message

def makesoup(request):
    """
    Create a BeautifulSoup object from an HTTP request
    
    Args:
        request: HTTP request object with text attribute
        
    Returns:
        BeautifulSoup: Parsed HTML
    """
    try:
        if request and request.text:
            soup = BeautifulSoup(request.text, "html.parser")
            return soup
        else:
            send_message(botapi, adminchat, "Error: empty response in makesoup")
            return BeautifulSoup("", "html.parser")
    except Exception as e:
        send_message(botapi, adminchat, f"Error in makesoup: {str(e)}")
        return BeautifulSoup("", "html.parser")

def makexmlsoup(request):
    """
    Create a BeautifulSoup object for XML from an HTTP request
    
    Args:
        request: HTTP request object with text attribute
        
    Returns:
        BeautifulSoup: Parsed XML
    """
    try:
        if request and request.text:
            from bs4 import XMLParsedAsHTMLWarning
            import warnings
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            
            try:
                # Use lxml explicitly for XML parsing
                soup = BeautifulSoup(request.text, features="xml")
            except Exception as parser_error:
                send_message(botapi, adminchat, f"XML parser error, falling back to html.parser: {str(parser_error)}")
                # Fallback to html.parser
                soup = BeautifulSoup(request.text, "html.parser")
            return soup
        else:
            send_message(botapi, adminchat, "Error: empty response in makexmlsoup")
            return BeautifulSoup("", "html.parser")
    except Exception as e:
        send_message(botapi, adminchat, f"Error in makexmlsoup: {str(e)}")
        return BeautifulSoup("", "html.parser") 