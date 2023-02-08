from datetime import date, timedelta

TOKEN = ""
CHANNEL = "@"

UPDATE_INTERVAL_S = 3600
AUTO_EXIT = True

# Post date limit, prevent the bot to post too old images from instagram, will not affect updating of already posted images
POST_DATE_LIMIT = None  # date.today() - timedelta(days=60)

# instagram account names
INSTAGRAM_ACCOUNTS = ['instagram']

# maximal number of images that should be fetched from each instagram account, set to None for no limit
FETCHING_LIMIT = None

# requests timeout
TIMEOUT = 5
# header for sending requests to Instagram
HEADER = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "de,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
    "Cookie": "csrftoken=enter your cookie here", # enter your cookie from your web browser here
    "Host": "www.instagram.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0"
}
