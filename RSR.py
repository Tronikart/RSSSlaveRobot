 #  _____  _          _       _
 # |  __ \(_)        | |     (_)
 # | |  | |_ ___  ___| | __ _ _ _ __ ___   ___ _ __
 # | |  | | / __|/ __| |/ _` | | '_ ` _ \ / _ \ '__|
 # | |__| | \__ \ (__| | (_| | | | | | | |  __/ |
 # |_____/|_|___/\___|_|\__,_|_|_| |_| |_|\___|_|
 #
 # The sole purpose of this project being in my github is so
 # people interested in helping me fix something that broke
 # have a way to do so, it IS a mess, there are TONS of ways
 # to make the things that Im doing here, I just went ahead
 # with what I knew at the moment and the fastest, easiest
 # way to make it work, keep yourself from doing requests
 # that are only related to formatting or PEP8 or whatever,
 # this wasnt meant to leave my machine because of this,
 # it. is. a. mess. and one done lazily.
 #
 # The reason there are so many functions doing almost the
 # same thing is because every page had its particular details
 # I tried to fix this by migrating most of the fetching
 # to FB Graph API but they implemented some policies
 # for reviewing that I simply can't provide given the
 # nature of this code and it not being a FB app per se
 #
 # The code should be straightforward except when it isn't,
 # but the basic actions that go through every run are:
 #
 #     Request Page
 #         ↓
 #     Find last posted comic
 #         ↓
 #     Compare with DB
 #         ↓
 #     If new, include it in DB, post it
 #     If not new, do nothing
 #         ↓
 #     Continue
 #
 # This code is supposed to be running every 30 min with a cronjob

import json
import requests
import re

from pymongo import MongoClient
from datetime import datetime
from bs4 import BeautifulSoup

client = MongoClient()
db = client.comics_db

# Telegram bot api key
botapi = #Telegram Bot Key#
adminchat = #where the bot is going to spew info to#

reddit_user = #/u/your_user_name#

def send_message(botapi, chat, message, params = ""):
    if params:
        requests.get(f"https://api.telegram.org/bot{botapi}/sendMessage?chat_id={chat}&text={message}&{params}")
    else:
        requests.get(f"https://api.telegram.org/bot{botapi}/sendMessage?chat_id={chat}&text={message}")

def handleRequest(url):
    try:
        request = requests.get(url)
        return {"timeout" : False, "request" : request}
    except:
        return {"timeout" : True, "request": ""}

def handleRedditRequest(url):
    try:
        request = requests.get(url, headers = {'User-agent': f'{reddit_user}'})
        return {'timeout' : False, 'request' : request}
    except:
        return {"timeout" : True, 'request' : ""}

def makesoup(request):
    soup = BeautifulSoup(request.text, "html.parser")
    return soup

def makexmlsoup(request):
    soup = BeautifulSoup(request.text, "xml")
    return soup

def sendPhoto(chatid, url, caption=""):
    if caption:
        print (f"Posting{url} to {chatid} with {caption} as caption")
        if len(caption) > 200:
            url = f"https://api.telegram.org/bot{botapi}/sendPhoto?chat_id={chatid}&photo={url}"
            requests.get(url)
            send_message(botapi, chatid, caption)
        else:
            url = f"https://api.telegram.org/bot{botapi}/sendPhoto?chat_id={chatid}&photo={url}&caption={caption}&parse_mode=Markdown"
            requests.get(url)
    else:
        print (f"Posting {url} to {chatid}")
        url = f"https://api.telegram.org/bot{botapi}/sendPhoto?chat_id={chatid}&photo={url}"
        requests.get(url)

def sendAlbums(channel, array):
    url = f"https://api.telegram.org/bot{botapi}/sendMediagroup"
    chat_id = channel
    photo_urls = []
    video_urls = []
    for i in array:
        if "mp4" in i or "gif" in i:
            video_urls.append({'type': "video", "media" : i})
        else:
            photo_urls.append({'type': "photo", "media" : i})
    if len(array) > 10:
        number = len(array)
        start = 0
        stop = 10
        while number > 0:
            request = requests.get(url, 
                        {
                            "chat_id"   : chat_id,
                            "media"     : json.dumps(photo_urls[start:stop])
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
                            "chat_id"   : chat_id,
                            "media"     : json.dumps(photo_urls)
                        }
                    )
    return request



def getlastImageFacebook(url):
    request = requests.get(url)
    soup = makesoup(request)
    content = soup.find('div', id='pages_msite_body_contents')
    images = content.find_all('img')
    url = f"https://m.facebook.com{images[0].parent['href']}"
    return url

def getFullImage(url):
    request = requests.get(url)
    soup = makesoup(request)
    url = soup.findAll('a')[-1]['href']
    return url

def noAPIFBFetch(database, url, chat_id, page_name, page_url):
    url = f"https://m.facebook.com/{url}/photos/"
    numberposted = 0
    posted = db[database]
    lastImage = getlastImageFacebook(url)
    permalink = lastImage.replace('m.facebook', 'facebook')
    fullImage = getFullImage(lastImage).replace('?', '%3F').replace('&', '%26')
    lastFB = fullImage.split('.jpg')[0].split('/')[-1]
    if posted.find_one({'url':lastFB}):
        pass
    else:
        send_message(botapi, adminchat, f"Found new content for {page_name}")
        posted.insert_one({'url' : lastFB, 'date' : datetime.now()})
        sendPhoto(chat_id, fullImage, f"[{page_name}]({page_url})\n\n[permalink]({permalink})")


def eightbitfictioncheck():
    numberposted = 0
    posted = db['8bit']
    request = handleRequest("http://8bitfiction.com/rss")

    if not request['timeout']:
        xmlsoup = makexmlsoup(request['request'])
        photos = []
        for item in xmlsoup.channel.findAll("item"):
            if item.title.text == "Photo":
                photos.append(item.description.text)
                break

        if not posted.find_one({'url' : photos[0]}):
            numberposted += 1;
            sendPhoto("@eightbitfiction", BeautifulSoup(photos[0], "html.parser").img['src'].replace("500","1280"))
            posted.insert_one({'url' : photos[0], 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new pictures to 8bitfiction")
    else:
        send_message(botapi, adminchat, "8bitfiction Timed out")

def owlturd():
    posted = db['owlturd']
    request = handleRequest("http://owlturd.com/rss")
    numberposted = 0

    if not request['timeout']:
        xmlsoup = makexmlsoup(request['request'])
        items = xmlsoup.findAll('item')
        for item in items:
            if item.title.string == "Photo":
                imgs = item.description
                comicurl = item.link.string
                break
        soup = BeautifulSoup(imgs.string, 'html.parser')
        soup = soup.findAll('img')

        if not posted.find_one({'url' : comicurl}):
            numberposted += 1
            urls = []
            for img in soup:
                urls.append(img['src'])
                #sendPhoto('@assortedComics', img['src'])
            sendAlbums('@assortedComics', urls)
            send_message(botapi, "@assortedComics", f"[Owlturd]({comicurl})", "parse_mode=Markdown&disable_web_page_preview=True")
            posted.insert_one({'url' : comicurl, 'date' : datetime.now()})

            if numberposted:
                send_message(botapi, adminchat, f"posted {str(numberposted)} new Owlturd pictures to comics")
    else:
        send_message(botapi, adminchat, "Loading Artist Timed out")

def explosmcheck():
    numberposted = 0
    posted = db['explosm']
    request = handleRequest("http://feeds.feedburner.com/Explosm")

    if not request['timeout']:
        soup = makesoup(request['request'])
        lastch = re.findall(r'/+comics/(\d+)', soup.guid.text)

        if not posted.find_one({'url' : lastch[0]}):
            numberposted += 1
            url = f"http://explosm.net/comics/{str(lastch[0])}/"
            request = requests.get(url)
            soup = makesoup(request)
            comic = "http:" + soup.find('img', id="main-comic")['src']
            sendPhoto("@assortedComics", comic)
            posted.insert_one({'url' : lastch[0], 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new Cyande and Happiness pictures to comics")
    else:
        send_message(botapi, adminchat, "Cyanide and Happiness Timeout")

def efccheck():
    numberposted = 0
    posted = db['efc']
    request = handleRequest("http://extrafabulouscomics.com/feed/")

    if not request['timeout']:
        soup = makesoup(request['request'])
        comic = soup.channel.item.title.contents[0]
        lastefc = comic.replace("s", "")

        if not posted.find_one({'url' : lastefc}):
            numberposted += 1
            url = f"http://extrafabulouscomics.com/comic/{str(lastefc)}"
            request = requests.get(url)
            soup = makesoup(request)
            comic = soup.find('div', id='comic').img['src']
            sendPhoto("@assortedComics", comic, "http://extrafabulouscomics.com")
            posted.insert_one({'url' : lastefc, 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new EFC pictures to comics")
    else:
        send_message(botapi, adminchat, "EFC Timed out")

def lacheck():
    posted = db['la']
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    request = requests.get("http://www.loadingartist.com/latest", headers=headers)
    numberposted = 0

    if request.ok:
        soup = makesoup(request)
        comic = soup.findAll('div', class_='comic')
        comic = f"https://loadingartist.com{comic[1].img['src']}"
        title = soup.find('title').string
    
        if not posted.find_one({'url' : comic}):
            numberposted += 1
            sendPhoto("@assortedComics", comic, title)
            posted.insert_one({'url' : comic, 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new LoadingArtist pictures to comics")
    else:
        send_message(botapi, adminchat, "Loading Artist Timed out")

def NNCheck():
    numberposted = 0
    posted = db['NerfNow']
    request = handleRequest("http://www.nerfnow.com/archives")

    if not request['timeout']:
        soup = makesoup(request['request'])
        comic = soup.find('li').a['href']
        lastnn = re.findall(r'/+comic/(\d+)', comic)

        if not posted.find_one({'url' : lastnn[0]}):
            numberposted += 1
            url = "http://www.nerfnow.com/comic/" + str(lastnn[0])
            request = requests.get(url)
            soup = makesoup(request)
            comic = soup.find('div', id="comic").img['src'] 
            sendPhoto("@assortedComics", comic)
            posted.insert_one({'url' : lastnn[0], 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new Nerf Now pictures to comics")
    else:
        send_message(botapi, adminchat, "Nerf Now Timed out")

def opticheck():
    numberposted = 0
    posted = db['Optipess']
    request = handleRequest(f"http://www.optipess.com/archive/?archive_year={str(datetime.now().year)}")
    if not request['timeout']:
        soup = makesoup(request['request'])
        comics = soup.findAll('table', class_="month-table")
        comicurl = comics[0].findAll('td', class_="archive-title")
        comicurl = comicurl[0].a['href']
        request = requests.get(comicurl)
        soup = makesoup(request)
        comic = soup.find('div', class_='comicpane').img['src']
        title = soup.find('title').string

        if not posted.find_one({'url' : comic}):
            numberposted += 1
            sendPhoto("@assortedComics", comic, title)
            posted.insert_one({'url' : comic, 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new Optipess pictures to comics")
    else:
        send_message(botapi, adminchat, "Optipess Timed out")


def piecheck():
    numberposted = 0
    posted = db['piecomic']
    request = handleRequest("http://piecomic.tumblr.com")

    if not request['timeout']:
        soup = makesoup(request['request'])
        comics = soup.findAll('div', class_='photo post')
        comic = comics[0].a.img['src'].replace('500', '1280')

        if not posted.find_one({'url' : comic}):
            numberposted += 1
            sendPhoto("@assortedComics", comic)
            posted.insert_one({'url' : comic, 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new Piecomic pictures to comics")
    else:
        send_message(botapi, adminchat, "Piecomic Timed out")


def pdlcheck():
    numberposted = 0
    posted = db['poorlydrawnlines']
    request = handleRequest("http://poorlydrawnlines.com/archive/")

    if not request['timeout']:
        soup = makesoup(request['request'])
        comics = soup.find('div', class_="content page")
        comics = comics.findAll('li')
        comic = comics[0]
        url = comic.a['href']
        request = requests.get(url)
        soup = makesoup(request)
        comic = soup.find('div', class_='post')
        comic = comic.img['src']
        title = soup.find('title').string
        
        if not posted.find_one({'url' : comic}):
            numberposted += 1
            sendPhoto("@assortedComics", comic, title)
            posted.insert_one({'url' : comic, 'posted' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new PoorlyDrawnLines pictures to comics")
    else:
        send_message(botapi, adminchat, "Poorly Drawn Lines Timed out")

def xkcdcheck():
    numberposted = 0
    posted = db['xkcd']
    request = handleRequest("http://xkcd.com/info.0.json")

    if not request['timeout']:
        data = request['request'].json()

        if not posted.find_one({'url' : data['num']}):
            numberposted += 1;
            sendPhoto("@assortedComics", data['img'], data['alt'].encode('latin-1').decode('utf-8'))
            posted.insert_one({ 'url' : data['num'], 'date' : datetime.now()})

        if numberposted:
            send_message(botapi, adminchat, f"posted {str(numberposted)} new xkcd pictures to comics")
    else:
        send_message(botapi, adminchat, "XKCD Timed out")

def wcn():
    posted = db['webcomicname']
    request = handleRequest("http://webcomicname.tumblr.com/tagged/comics/rss")
    numberposted = 0

    if not request['timeout']:
        soup = makesoup(request['request'])
        comics = soup.findAll('div', class_='photo-wrapper')
        comicurl = comics[0].div.a.img['src']

        if not posted.find_one({'url' : comicurl}):
            numberposted += 1
            sendPhoto('@assortedComics', comicurl)
            posted.insert_one({ 'url' : comicurl, 'date' : datetime.now()})

            if numberposted:
                send_message(botapi, adminchat, f"posted {str(numberposted)} new webcomic name to comics")
    else:
        send_message(botapi, adminchat, "Webcomicname timed out")

now = datetime.now()
message = f"{str(now.year)}-{str(now.month).zfill(2)}-{str(now.day).zfill(2)} {str(now.hour).zfill(2)}:{str(now.minute).zfill(2)}:{str(now.second).zfill(2)} Checking for updates... "
token = getFBToken()

send_message(botapi, adminchat, f"*{message}*", "parse_mode=Markdown")

try:
    eightbitfictioncheck()
except:
    pass
try:
    efccheck()
except:
    pass
try:
    lacheck()
except:
    pass
try:
    #mrlovecheck()
    noAPIFBFetch("mrlove", "MrLovenstein", "@assortedComics", "Mr Lovenstein", "http://www.mrlovenstein.com")
except:
    pass
try:
    explosmcheck()
except:
    pass
try:
    #owlturd()
    noAPIFBFetch("owlturd", "shencomix", "@assortedComics", "Shen Comix", "https://shencomix.com")
except:
    pass
try:
    noAPIFBFetch("8bit", "eightdashbitfiction", "@eightbitfiction", "8-bitfiction", "http://8bitfiction.com/")
except:
    pass
try:
    opticheck()
except:
    pass
try:
    piecheck()
except:
    pass
try:
    pdlcheck()
    pass
except:
    pass
try:
    xkcdcheck()
except:
    pass
try:
    #wcn()
    noAPIFBFetch("webcomicname", "webcomicname", "@assortedComics", "Webcomic Name", "https://www.facebook.com/webcomicname/")
except Exception as e:
    send_message(botapi, adminchat, e)
    pass

try:
    noAPIFBFetch("strangeplanet", "nathanwpyle2", "@assortedComics", "Strange Planet", "https://www.facebook.com/nathanwpyle2/")
except:
    pass
try:
    noAPIFBFetch("SafelyEndangered", "safelyendangered", "@assortedComics", "Safely Endangered", "https://www.facebook.com/safelyendangered/")
except:
    pass
try:
    noAPIFBFetch("DeathBulge", "deathbulge", "@assortedComics", "Deathbulge", "https://www.facebook.com/deathbulge/")
except:
  pass
try:
    noAPIFBFetch('oatmeal', 'theoatmeal', '@assortedComics', "The Oatmeal", "http://theoatmeal.com")
except:
    pass
try:
    noAPIFBFetch("sarah", "DoodleTimeSarah", "@assortedComics", "Sarah's Scribbles", "http://www.gocomics.com/sarahs-scribble")
except:
    pass
try:
    noAPIFBFetch('goodbear', 'goodbearcomicswebsite', '@assortedComics', 'Good Bear Comics', 'https://goodbearcomics.com')
except:
    pass
try:
    noAPIFBFetch('falseknees', 'FalseKnees', '@assortedComics', 'False Knees', 'http://falseknees.com')
except:
    pass
try:
    noAPIFBFetch('skeletonclaw', 'skeletonclaw', '@assortedComics', 'Skeleton Claw', 'http://skeletonclaw.com/')
except:
    pass
try:
    noAPIFBFetch('jakelikesonions', 'jakelikesonions', '@assortedComics', 'Jake Likes Onions', 'https://www.facebook.com/jakelikesonions/')
except:
    pass
try:
    noAPIFBFetch('warandpeas', 'warnpeas', '@assortedComics', 'War & Peas', 'https://warandpeas.com')
except:
    pass

# noAPIFBFetch(database, url, chat_id, page_name, page_url):

send_message(botapi, adminchat, "*Done!*&parse_mode=Markdown")
