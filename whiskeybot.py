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
    'https://www.klwines.com/Products?searchText=redbreast': {
        'type': 'xpath',
        'xpath': '//div[contains(@class, "result-desc")]',
        'expected': 6,
    },
    'https://www.blackwellswines.com/search?q=Redbreast': {
        'type': 'xpath',
        'xpath': '//div[@class="product_row"]',
        'expected': 6,
    }
}


def xpath(url, response, config):
    tree = html.fromstring(response.text)
    found = len(tree.xpath(config['xpath']))
    num_expected = config['expected']
    if found != num_expected:
        yield f'Found {found} xpath results, expected {num_expected} in {url}'


def check(urls):
    mailer = NotifyMeMailer.create()
    messages = []
    for url, config in urls.items():
        print(f'Looking in {url}...')
        response = requests.get(url)
        if config['type'] == 'xpath':
            gen = xpath(url, response, config)

        messages.extend(list(gen))

    if messages:
        final_msg = f'{SUBJECT}\n\nWe found the following results:\n'
        final_msg += '\n'.join(messages)
        mailer.send(SUBJECT, final_msg)
    else:
        print('Nothing found :(')


if __name__ == '__main__':
    check(URLS)
