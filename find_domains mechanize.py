"""
Use mechanize - doesn't fool GoDaddy.com
"""

from bs4 import BeautifulSoup
import re
import pandas
import time
import mechanize
import cookielib
from constants import *

def main(domain_names):
    control_name = "domainToCheck"
    results_dataframe = pandas.DataFrame(columns = ['domain', 'available', 'price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now', 'godaddy'])
    br = newChromeEmulatingBrowser()
    br.open(search_link)

    for domain_name in domain_names:
        form = list(br.forms())[1]
        control = form.find_control(control_name)
        control.value = domain_name

        for control in form.controls:
            if control.type == 'submitbutton':
                submit_control = control

        request = form.click()
        response = br.open(request)
        html = str(response.read())
        soup = BeautifulSoup(html, "html.parser")
        data_row = find_data(soup)

        godaddy_link = br.geturl()
        data_row['domain'] = domain_name
        data_row['godaddy'] = '<a href="' + godaddy_link + '" style="color: white; text-decoration: none;">click here</a>'
        results_dataframe = results_dataframe.append(data_row, ignore_index = True)

        br.back()

    br.close()
    
    return results_dataframe

def find_data(soup):
    data_row = {}

    # If the domain is taken
    if soup.find('p', {'class': 'unavailableCopy container font-base ng-binding'}) or not soup.find('h3', {'class': 'font-primary-black headline ng-binding'}):
        data_row['available'] = 'No'
    else:
        data_row['available'] = 'Yes'

        pricing_container = soup.find('div', {'class': 'pricingContainer'})
        if pricing_container:
            pricing_container_found = pricing_container.find('span', {'class': 'ng-binding'})
            if pricing_container_found:
                data_row['price_year1'] = clean_price(pricing_container_found.text)

            renewal_price_tag = pricing_container.find('span', {'class': 'pricing pricing-renewal'})
            if renewal_price_tag:                
                data_row['price_renewal'] = clean_price(renewal_price_tag.text)

        # If not a simple one-year price, look for striked out price - but only if it's not a minimum or buy now offer, not "selected just for you"
        elif not pricing_container and not soup.find(text = 'Minimum Offer amount') and not soup.find(text = 'Buy Now price'):
            pricing_sibling = soup.find('span', {'class': 'priceStrike'})
            if pricing_sibling:
                price_tag = pricing_sibling.find_next_sibling('span')
                if price_tag:
                    data_row['price_year1'] = clean_price(price_tag.text)

            renewal_price_tag = soup.find('div', {'class': 'comPromoPricing'})
            if renewal_price_tag:
                renewal_prices_list = renewal_price_tag.text.split('Additional years')
                if len(renewal_prices_list) == 2:
                    renewal_price = renewal_prices_list[1]
                    data_row['price_renewal'] = clean_price(renewal_price)

        elif soup.find(text = 'Buy Now price'):
            pricing_container = soup.find('span', {'class': 'pricing'})
            if pricing_container:
                pricing_container_found = pricing_container.find('span', {'class': 'price ng-binding'})
                if pricing_container_found:
                    data_row['price_buy_now'] = clean_price(pricing_container_found.text)

        elif soup.find(text = 'Minimum Offer amount'):
            pricing_tag = soup.find('span', {'class': 'pricing'})
            if pricing_tag:
                price_minimum_tag = pricing_tag.find('span', {'class': 'price ng-binding'})
                if price_minimum_tag:
                    data_row['price_min_offer'] = clean_price(price_minimum_tag.text)

    return data_row

def clean_price(price_string):
    return str(re.sub('[^\d\.]*', '', price_string.split('/')[0]))

def newChromeEmulatingBrowser():
    # Browser
    br = mechanize.Browser()
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    #br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time = 1)

    # Headers chosen by me from Mugshots.com scraping
    br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=1.8'), ('Accept-Language', 'en-us,en;q=0.5'),
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36')]

    # Headers actually sent by Google Chrome - makes br.open time out
    # br.addheaders = [("Host", "www.godaddy.com:443"), ("Accept", "image/webp,image/*,*/*;q=0.8"), ("Accept-Encoding", "gzip, deflate, sdch"),
    # ("Accept-Language", "en-US,en;q=0.8,de;q=0.6,he;q=0.4"), ("Referer", "https//:www.godaddy.com/"),
    # ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"),
    # ("Cache-Control", "no-cache, no-store, must-revalidate"), ("Connection", "keep-alive"), ("Connection", "Transfer-Encoding"),
    # ("Content-Encoding", "gzip"), ("Content-Type", "text/html; charset=utf-8"),
    # ("Expires", "-1"), ("Pragma", "no-cache"), ("Server", "Microsoft-IIS/7.5"), ("Transfer-Encoding", "chunked"), ("Vary", "Accept-Encoding"),
    # ("X-ARC", "6"), ("X-ARC", "4"), ("X-AspNet-Version", "4.0.30319"), ("X-AspNetMvc-Version", "5.1"), ("X-Powered-By", "ASP.NET)")]

    # Browser it will claim to be. This affects the results. An old browser encourages pages to return nice HTML
    # instead of a bunch of JavaScript-generated bullcrap. Mechanize doesn't run Javascript.
    # br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # http://stockrt.github.com/p/emulating-a-browser-in-python-with-mechanize/
    # br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11')]

    return br

if __name__ == '__main__':
    main()