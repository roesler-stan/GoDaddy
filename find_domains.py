from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import pandas
from constants import *
import multiprocessing

def main(domain_names):
    results_dataframe = pandas.DataFrame(columns = ['domain', 'available', 'price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now', 'godaddy'])
    if not domain_names:
        return results_dataframe

    # Split domain names into groups and spawn a thread for each (larger groups if more domain names are requested)
    # if len(domain_names) < 12:
    #     group_size = 4
    # else:
    #     group_size = len(domain_names) / MAX_THREADS

    # domain_name_groups = [domain_names[x: x + group_size] for x in xrange(0, len(domain_names), group_size)]

    # # Has at most MAX_THREADS processes, at min domain_names length / 4 (max 3)
    # pool = multiprocessing.Pool(processes = len(domain_name_groups))
    # results_dataframes_found = pool.map(find_dataset, domain_name_groups)

    # for results_dataframe_found in results_dataframes_found:
    #     results_dataframe = results_dataframe.append(results_dataframe_found, ignore_index = True)

    # To iterate through each name subsequently
    results_dataframe_found = find_dataset(domain_names)
    results_dataframe = results_dataframe.append(results_dataframe_found, ignore_index = True)    

    numeric_vars = ['price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now']
    results_dataframe[numeric_vars] = pandas.to_numeric(results_dataframe[numeric_vars], errors = 'coerce').astype(float)
    results_dataframe = results_dataframe.sort_values('available', ascending = False)
    results_dataframe = results_dataframe.rename(columns = {'domain': 'Domain', 'available': 'Availability', 'price_year1': '1st Year Price',
        'price_renewal': 'Renewal Price', 'price_min_offer': 'Minimum Offer Price', 'price_buy_now': 'Buy it Now Price', 'godaddy': 'GoDaddy Link'})

    results_html = results_to_html(results_dataframe)

    return results_html

def find_dataset(domain_names):
    """ Take user input and find data for this domain """
    results_dataframe = pandas.DataFrame(columns = ['domain', 'available', 'price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now', 'godaddy'])

    driver = webdriver.PhantomJS(service_args=["--webdriver-loglevel=NONE"])
    driver.get(search_link)

    for i, domain_name in enumerate(domain_names):
        if i == 0:
            form_name = "domain-name-input"
        else:
            form_name = "domain_search_input"

        soup, godaddy_link, driver = find_soup(domain_name, driver, form_name)
        data_row = find_data(soup)
        data_row['domain'] = domain_name
        data_row['godaddy'] = '<a href="' + godaddy_link + '" style="color: white; text-decoration: none;">click here</a>'
        results_dataframe = results_dataframe.append(data_row, ignore_index = True)

    driver.quit()

    return results_dataframe

def find_soup(domain_name, driver, form_name):
    # element_to_be_clickable, presence_of_element_located
    WebDriverWait(driver, MAX_WAIT).until(EC.element_to_be_clickable((By.ID, form_name)))
    domain_form = driver.find_element_by_id(form_name)
    WebDriverWait(driver, MAX_WAIT).until(EC.element_to_be_clickable((By.ID, form_name)))
    domain_form.clear()

    type_new = ActionChains(driver).click(domain_form).send_keys(domain_name)
    type_new.perform()
   
    driver.implicitly_wait(0.1)
    wait_attempts = 0
    while domain_form.get_attribute('value') != domain_name:
        driver.implicitly_wait(5)
        wait_attempts += 1
        if wait_attempts > WAIT_ATTEMPTS:
            break

    submit_new = ActionChains(driver).click(domain_form).send_keys(Keys.ENTER)
    submit_new.perform()

    WebDriverWait(driver, MAX_WAIT).until(EC.element_to_be_clickable((By.ID, "domain_search_input")))

    source = driver.page_source
    soup = BeautifulSoup(source, "html.parser")

    godaddy_link = 'https://www.godaddy.com/domains/searchresults.aspx?checkAvail=1&domainToCheck=' + domain_name

    # Can't do the following b/c the browser url doesn't change when editing form within page: godaddy_link = driver.current_url

    return soup, godaddy_link, driver

def find_data(soup):
    """ Parse HTML to find domain name's data, return as dict """
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

def results_to_html(results_dataframe):
    # Allow pandas dataframe strings to be long
    pandas.set_option('display.max_colwidth', -1)

    def format_table(result):
        if result < 1000:
            return '$%.2f' % result
        elif result >= 1000:
            return '$' + '{0:,d}'.format(int(result))
        else:
            return '-'

    results_html = results_dataframe.to_html(index = False, float_format = format_table, na_rep = '-', escape = False)
    results_html = str(results_html).replace('table border', 'table id="results" border')
    results_html = results_html.replace('1st', '1<sup>st</sup>')

    return results_html

if __name__ == '__main__':
    main()