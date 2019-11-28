# -*- coding: utf-8 -*-
"""
Check whether Redbreast Small Batch is available at some stores and email if so.
"""
import re

import requests
from lxml import html
from notifyme import NotifyMeMailer


SUBJECT = 'WHISKEY ALERT!'
URLS = {
    'K&L - Redbreast Product Search': {
        'url': 'https://www.klwines.com/Products?searchText=redbreast',
        'type': 'xpath',
        'xpath': '//div[contains(@class, "tf-product-description")]',
        'expected': 6,
    },
    'Blackwell - Redbreast Product Search': {
        'url': 'https://www.blackwellswines.com/search?q=Redbreast',
        'type': 'xpath',
        'xpath': '//div[@class="product_row"]',
        'expected': 5,
    },
    'K&L - New Product Page': {
        'url': 'https://www.klwines.com/Products?&filters=sv2_NewProductFeedYN$eq$1$True$ProductFeed$!dflt-stock-all!206&limit=50&offset=0&orderBy=LotGeneratedFromPOYN%20asc,NewProductFeedDate%20desc&searchText=',
        'type': 'regex',
        'regex': r'(?i)redbreast',
        'expected': 0,
    },
}


def xpath(name, response, config):
    url = config['url']
    tree = html.fromstring(response.text)
    found = len(tree.xpath(config['xpath']))
    num_expected = config['expected']
    if found != num_expected:
        yield f'{name}: found {found} xpath results, expected {num_expected} in {url}'


def regex(name, response, config):
    url = config['url']
    found = len(re.findall(config['regex'], response.text))
    num_expected = config['expected']
    if found != num_expected:
        yield f'{name}: found {found} regex results, expected {num_expected} in {url}'


def check(urls):
    mailer = NotifyMeMailer.create()
    messages = []
    for name, config in urls.items():
        print(f'Looking in {name}...')
        url = config['url']
        response = requests.get(url)
        if config['type'] == 'xpath':
            gen = xpath(name, response, config)
        elif config['type'] == 'regex':
            gen = regex(name, response, config)

        messages.extend(list(gen))

    if messages:
        final_msg = f'{SUBJECT}\n\nWe found the following results:\n'
        final_msg += '\n'.join(messages)
        mailer.send(SUBJECT, final_msg)
    else:
        print('Nothing found :(')


if __name__ == '__main__':
    try:
        check(URLS)
    except Exception:
        mailer = NotifyMeMailer.create()
        mailer.send('WHISKEY ERROR', 'Your bot has crashed, pls fix')
