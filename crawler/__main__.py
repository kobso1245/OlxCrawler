import requests
import re
from bs4 import BeautifulSoup as Soup
from collections import OrderedDict
import json
import os
from datetime import datetime
from functools import partial, reduce

from crawler import email_utils


OFFERS_FILE = 'output.json'
BASE_URL = 'https://www.olx.bg/ads/q-{search}/'


class Offer:
    def to_json(self):
        return self.__dict__

    def __init__(self, url, title, price):
        self.url = url
        self.title = title
        self.price = price

    def __eq__(self, other):
        # Make sure that the needed properties are here
        # We do not care if there are extra properties
        return all(map(lambda key: self[key] == other[key], self.__dict__.keys()))

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        """Defines the [] for the object
        That way the following can be done: a = Offer(1,2,3); a['url']
        """
        return self.__dict__[item]

    def __hash__(self):
        return hash(str(self))


def main(search_string):
    """Main function"""
    print("Retrieving information")
    live_offers = retrieve_offers(search_string)
    print("Offers retrieved")
    stored_offers = get_stored_offers()
    print("Old offers retrieved")
    new_offers, removed_offers = diff_offers(stored_offers[0]["offers"], live_offers)
    print("Diff made")
    if new_offers:
        print("New offers found")
        reducer((email_utils.generate_message, email_utils.send_message), new_offers)

    print("storing offers")
    store_offers(append_new_offers(stored_offers, live_offers))
    print("Offers stored")


def reducer(functions, init_value):
    """Helper function for function chaining"""
    return reduce(lambda res, func: func(res), functions, init_value)


def generate_new_offers_message(new_offers):
    message = email_utils.generate_message(new_offers)


def retrieve_offers(search_string):
    """Retrieve offers from web"""
    return reducer((retrieve_offers_html, parse_offers_html), search_string)


def store_offers(offers):
    """Store the offers into file"""
    reducer((serialize, store_in_db), offers)


def get_stored_offers():
    """Return stored offers from file"""
    return deserialize(read_from_db())


def parse_offers_html(html):
    """Parse the retrieved HTML to retrieve the needed information"""
    def parse_single_offer(html_offer):
        try:
            info_row = html_offer.table.tbody.tr
            return Offer(info_row.td.a['href'], info_row.td.a.img['alt'], info_row.find(class_='price').strong.string)
        except:
            pass

    raw_offers = Soup(html, 'html.parser').find('table', {'id': 'offers_table'}).find_all('td', class_=re.compile('offer$'))
    return reducer((partial(map, parse_single_offer), partial(filter, None.__ne__), list), raw_offers)


def retrieve_offers_html(search_string):
    """Retrieve the HTML for the given URL"""
    url = generate_request_url(search_string)
    return requests.get(url).text


def generate_request_url(search_string):
    """Generate the URL, used for searching"""
    return BASE_URL.format(search=search_string.replace(' ', '-'))


def read_from_db():
    """Read the offers, which are already stored in the DB"""
    try:
        with open(OFFERS_FILE, encoding='utf8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def store_in_db(offers):
    """Store offers into DB"""
    with open(OFFERS_FILE, 'w', encoding='utf8') as f:
        json.dump(offers, f, ensure_ascii=False, indent=4)


def serialize(file_content):
    """Serialize the output to json"""
    return list(map(lambda elem: {**elem, 'offers': [offer.to_json() for offer in elem["offers"]]}, file_content))


def deserialize(file_content):
    """Deserialize the content from json to Offer objects for easier parsing"""
    return list(map(lambda elem: {**elem, 'offers': [Offer(**off) for off in elem['offers']]}, file_content))


def append_new_offers(old_offers, new_offers):
    """Return a new list, containing the new and old offers"""
    return [{'offers': new_offers, 'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, *old_offers]


def diff_offers(old_offers, new_offers):
    """Return the new and removed offers"""
    old_offers_set, new_offers_set = map(set, [old_offers, new_offers])
    added_offers, removed_offers = new_offers_set - old_offers_set, old_offers_set - new_offers_set
    return added_offers, removed_offers


if __name__ == '__main__':
    main("ipad")
