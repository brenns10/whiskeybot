# -*- coding: utf-8 -*-
"""
Check whether Redbreast Small Batch is available at some stores and email if so.

This script expects to be run periodically, probably as a cron job. It keeps a
state file containing each URL it searches, and the results that it has found.
If the results it finds don't match the state (e.g. the state file is not
present, a URL is not present in the file, or the number of results differ from
the value in the state file), it will send an email and update the state. In
this way, alerts will be sent when things change but not again.
"""
import re
import json
import os.path

import requests
from lxml import html
from notifyme import NotifyMeMailer


# Counts will be stored here
STATEFILE = '~/whiskey.json'
SUBJECT = 'WHISKEY ALERT!'
URLS = {
    'K&L - Redbreast Product Search': {
        'url': 'https://www.klwines.com/Products?searchText=redbreast',
        'type': 'xpath',
        'xpath': '//div[contains(@class, "tf-product-description")]',
    },
    'Blackwell - Redbreast Product Search': {
        'url': 'https://www.blackwellswines.com/search?q=Redbreast',
        'type': 'xpath',
        'xpath': '//div[@class="product_row"]',
    },
    'K&L - New Product Page': {
        'url': 'https://www.klwines.com/Products?&filters=sv2_NewProductFeedYN$eq$1$True$ProductFeed$!dflt-stock-all!206&limit=50&offset=0&orderBy=LotGeneratedFromPOYN%20asc,NewProductFeedDate%20desc&searchText=',
        'type': 'regex',
        'regex': r'(?i)redbreast',
    },
}


def xpath(name, response, config, expected):
    url = config['url']
    tree = html.fromstring(response.text)
    found = len(tree.xpath(config['xpath']))
    if found != expected:
        return f'{name}: found {found} xpath results, expected {expected} in {url}', found
    else:
        return None, None


def regex(name, response, config, expected):
    url = config['url']
    found = len(re.findall(config['regex'], response.text))
    if found != expected:
        return f'{name}: found {found} regex results, expected {expected} in {url}', found
    else:
        return None, None


def load_state():
    fullpath = os.path.expanduser(STATEFILE)
    if os.path.exists(fullpath):
        with open(fullpath) as f:
            return json.load(f)
    return {}


def save_state(state):
    fullpath = os.path.expanduser(STATEFILE)
    with open(fullpath, 'w') as f:
        json.dump(state, f)


def check(urls):
    mailer = NotifyMeMailer.create()
    messages = []
    state = load_state()
    for name, config in urls.items():
        print(f'Looking in {name}...')
        url = config['url']
        response = requests.get(url)
        expected = state.get(name)
        if config['type'] == 'xpath':
            message, expected = xpath(name, response, config, expected)
        elif config['type'] == 'regex':
            message, expected = regex(name, response, config, expected)

        if message:
            messages.append(message)
            state[name] = expected

    if messages:
        final_msg = f'{SUBJECT}\n\nWe found the following results:\n'
        final_msg += '\n'.join(messages)
        mailer.send(SUBJECT, final_msg)
        save_state(state)
    else:
        print('Nothing has changed :(')


if __name__ == '__main__':
    try:
        check(URLS)
    except Exception:
        mailer = NotifyMeMailer.create()
        mailer.send('WHISKEY ERROR', 'Your bot has crashed, pls fix')
        raise
