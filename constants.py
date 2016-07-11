search_link = 'https://www.godaddy.com/'
WAIT_ATTEMPTS = 5

# Max time to wait for element to load
MAX_WAIT = 120

# Max number of threads per user
MAX_THREADS = 2

# If job doesn't return in 20 minutes, timout
ENQUEUE_TIMEOUT = 1200

base_url = 'https://www.godaddy.com/domains/searchresults.aspx?checkAvail=1&domainToCheck='

hdrs = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=1.8', 'Accept-Language':'en-us,en;q=0.5', \
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}

timeout_time = 10
min_pause = 0.1
max_pause = 4