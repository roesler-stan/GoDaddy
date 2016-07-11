import itertools
import re

def generate_list_domains(domains_input, extensions):
    """ Return list of domain names
    If extensions are input, find all domain-extension combinations.  Otherwise, just look for inputted domains

    Args:
        domains_input (list of str): Domain names with or without extensions
        extensions (list): may be empty
    """
    errors = set()
    extensions = ['.' + str(extension) for extension in extensions]
    domain_names = domains_input.split(',')
    clean_domain_names = []
    good_extensions = ['com', 'net', 'org', 'gov', 'edu', 'io']
    
    for domain_name in domain_names:
        periods = len(re.findall(re.compile('\.'), domain_name))
        if periods > 1:
            errors.add('Please do not include more than one extension per domain name.')
        elif periods == 1:
            extension = domain_name.split('.')[1]
            if extension not in good_extensions:
                errors.add('Please only include extensions from the list below.')
            else:
                clean_domain_names.append(domain_name)
        elif periods == 0:
            if not extensions:
                errors.add('Please include an extension in each domain name or choose one from the list below.')
            for extension in extensions:
                clean_domain_names.append(domain_name + extension)

    clean_domain_names = [clean_text(domain_name) for domain_name in clean_domain_names]
    # remove duplicate names
    clean_domain_names = list(set(clean_domain_names))
    errors = list(errors)
    
    return clean_domain_names, errors

def generate_keyword_domains(keywords_allcombos, keywords1, keywords2, keywords_unordered, extensions):
    """ Take keywords and return list of domain names
    Args:
        keywords_allcombos (str): keywords that should be given in all combinations
        keywords1 (str): keywords that should go first (if only one direction)
        keywords2 (str): keywords that should go second (if only one direction)
        keywords_unordered (boolean): whether both orders should be crated
        extensions (list of str): extensions, will not be empty
    """

    errors = []
    extensions = ['.' + str(extension) for extension in extensions]
    domain_names = []

    clean_keywords_allcombos, errors_allcombos = check_keywords(keywords_allcombos)
    if clean_keywords_allcombos:
        if len(clean_keywords_allcombos) == 1:
            for extension in extensions:
                domain_names.append(clean_keywords_allcombos[0] + extension)
        else:
            for combo in itertools.permutations(clean_keywords_allcombos, 2):
                for extension in extensions:
                    domain_names.append(''.join(combo) + extension)

    clean_keywords1, errors1 = check_keywords(keywords1)
    clean_keywords2, errors2 = check_keywords(keywords2)

    if clean_keywords1 and clean_keywords2:
        for extension in extensions:
            for keyword1 in clean_keywords1:
                for keyword2 in clean_keywords2:
                    domain_names.append(keyword1 + keyword2 + extension)
                    if str(keywords_unordered) == 'yes':
                        domain_names.append(keyword2 + keyword1 + extension)

    domain_names = [clean_text(domain_name) for domain_name in domain_names]
    # remove duplicate names
    domain_names = list(set(domain_names))

    errors += errors_allcombos + errors1 + errors2

    return domain_names, errors

def check_keywords(keywords_string):
    if keywords_string == '':
        return [], []

    errors = set()
    clean_keywords = []

    for keyword in keywords_string.split(','):
        periods = len(re.findall(re.compile('\.'), keyword))
        if periods != 0:
            errors.add('Please do not include extensions in your keywords.')
            clean_keyword = keyword.split('.')[0]
            clean_keywords.append(clean_keyword)
        else:
            clean_keywords.append(keyword)

    return clean_keywords, list(errors)

def clean_text(input_string):
    return re.sub('[^\w\.]|_', '', str(input_string).strip()).lower()
