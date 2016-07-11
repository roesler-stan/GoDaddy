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

@profile
def main():
    domain_names = ['exertbuy.com']
    # domain_names = ['exertbuy.com', 'buy4me.com', 'buyerhelp.com', 'exertbuy.io', 'buy4me.io', 'buyerhelp.io']
    group_size = 4
    domain_name_groups = [domain_names[x: x + group_size] for x in xrange(0, len(domain_names), group_size)]

    # To iterate through each subsequently
    for domain_name_group in domain_name_groups:
        results_dataframe_found = find_dataset(domain_name_group)
        print results_dataframe_found

def find_dataset(domain_names):
    """ Take user input and find data for this domain """
    driver = webdriver.PhantomJS(service_args=["--webdriver-loglevel=NONE"])
    driver.get(search_link)

    for i, domain_name in enumerate(domain_names):
        if i == 0:
            form_name = "domain-name-input"
        else:
            form_name = "domain_search_input"

        soup, godaddy_link, driver = find_soup(domain_name, driver, form_name)

    driver.quit()

    return 'results'

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

if __name__ == '__main__':
    main()