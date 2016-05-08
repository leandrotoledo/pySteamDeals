import requests
from bs4 import BeautifulSoup
from termcolor import colored

BASE_URL = 'http://store.steampowered.com/search/results?sort_by=_ASC&os=win&specials=1'
CURRENCY_SYMBOL = '€'


def get_html(url):
   html = requests.get(url, headers={'User_Agent':'Mozilla/5.0'})
   return html.text


def list_titles(url):
   soup = BeautifulSoup(get_html(url), "html.parser")

   titles = list()
   for link in soup.find_all('span', attrs={'class': 'title'}):
         game_title = link.text.strip()
         titles.append(game_title)

   return titles


def list_discounts(url):
   soup = BeautifulSoup(get_html(url), "html.parser")

   discounts = list()
   for link in soup.find_all('div', attrs={'class': 'search_discount'}):
         game_discount = link.text.replace('-', '').replace('%', '').strip()
         game_discount = int(game_discount)
         discounts.append(game_discount)

   return discounts


def list_original_prices(url):
   soup = BeautifulSoup(get_html(url), "html.parser")

   original_prices = list()
   for link in soup.find_all('strike'):
      if CURRENCY_SYMBOL in link.text:
         price = link.text.replace(CURRENCY_SYMBOL, '').replace(',', '.').strip()
         price = float(price)
         original_prices.append(price)

   return original_prices


def list_discounted_prices(url):
   soup = BeautifulSoup(get_html(url), "html.parser")

   discounted_prices = list()
   for link in soup.find_all('div', attrs={'class': 'discounted'}):
      if CURRENCY_SYMBOL in link.text:
         price = link.text.replace(CURRENCY_SYMBOL, '').replace(',', '.').split(' ')[-1].strip()

         try:
            price = float(price)
         except ValueError:
            if 'Free' in price:
                price = 0

         discounted_prices.append(price)

   return discounted_prices


def get_links():
   soup = BeautifulSoup(get_html(BASE_URL), "html.parser")

   last_page = soup.find_all('a', attrs={'onclick': 'SearchLinkClick( this ); return false;'})[2]
   last_page = int(last_page.text)

   links = list()
   for i in range(1, last_page+1):
       link = '{}&page={}'.format(BASE_URL, i)
       links.append(link)

   return links


for url in get_links():
    games = zip(list_titles(url), list_discounts(url), list_original_prices(url), list_discounted_prices(url))

    for title, discount, o_price, n_price in games:
        if discount < 50:
            print(title, colored(discount, 'blue') + ' from ' + str(o_price) + ' to ' + str(n_price))
        elif discount > 50 and discount < 75:
            print(title, colored(discount, 'yellow') + ' from ' + str(o_price) + ' to ' + str(n_price))
        elif discount > 75:
            print(title, colored(discount, 'green') + ' from ' + str(o_price) + ' to ' + str(n_price))
