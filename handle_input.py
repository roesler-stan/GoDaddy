import re
import pandas
import find_domains
import multiprocessing

results_dataframe = pandas.DataFrame(columns = ['domain', 'available', 'price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now', 'godaddy'])

def main(domain_names):
    # Call find_domains.py to scrape GoDaddy.  Split domain names into 6-name groups and spawn a thread for each
    domain_name_groups = [domain_names[x: x + 6] for x in xrange(0, len(domain_names), 6)]

    def log_result(results_dataframe_found):
        global results_dataframe
        results_dataframe = results_dataframe.append(results_dataframe_found, ignore_index = True)

    # Should I determine the number of processes?  Or use a queue?
    pool = multiprocessing.Pool()
    for domain_name_group in domain_name_groups:
        pool.apply_async(find_domains.main, args = (domain_name_group, ), callback = log_result)

    pool.close()
    pool.join()

    numeric_vars = ['price_year1', 'price_renewal', 'price_min_offer', 'price_buy_now']
    results_dataframe[numeric_vars] = pandas.to_numeric(results_dataframe[numeric_vars], errors = 'coerce').astype(float)
    results_dataframe = results_dataframe.sort_values('available', ascending = False)
    results_dataframe = results_dataframe.rename(columns = {'domain': 'Domain', 'available': 'Availability', 'price_year1': '1st Year Price',
        'price_renewal': 'Renewal Price', 'price_min_offer': 'Minimum Offer Price', 'price_buy_now': 'Buy it Now Price', 'godaddy': 'GoDaddy Link'})

    return results_dataframe