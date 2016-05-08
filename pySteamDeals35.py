#!/usr/bin/env python3.5
import asyncio
import itertools
import models
from aiohttp import ClientSession
from bs4 import BeautifulSoup

BASE_URL = 'http://store.steampowered.com/search/results?cc=br&sort_by=_ASC&os=win&specials=1'
CURRENCY_SYMBOL = 'R$'
#CURRENCY_SYMBOL = '$'
#CURRENCY_SYMBOL = '€'


async def get_html(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            return await response.read()


async def get_links():
   html = await get_html(BASE_URL)

   soup = BeautifulSoup(html, "html.parser")

   last_page = soup.find_all('a', attrs={'onclick': 'SearchLinkClick( this ); return false;'})[2]
   last_page = int(last_page.text)

   links = list()
   for i in range(1, last_page+1):
       link = '{}&page={}'.format(BASE_URL, i)
       links.append(link)

   return links


async def list_titles(soup):
   titles = list()

   for link in soup.find_all('span', attrs={'class': 'title'}):
         game_title = link.text.strip()
         titles.append(game_title)

   return titles


async def list_links(soup):
   links = list()

   for link in soup.find_all('a', attrs={'class': 'search_result_row'}):
         game_link = link['href'].split('?')[0]
         links.append(game_link)

   return links


async def list_discounts(soup):
   discounts = list()

   for link in soup.find_all('div', attrs={'class': 'search_discount'}):
         game_discount = link.text.replace('-', '').replace('%', '').strip()
         try:
            game_discount = int(game_discount)
         except ValueError:
             game_discount = 0
         discounts.append(game_discount)

   return discounts


async def list_original_prices(soup):
   original_prices = list()

   for link in soup.find_all('strike'):
      if CURRENCY_SYMBOL in link.text:
         price = link.text.replace(CURRENCY_SYMBOL, '').replace(',', '.').strip()
         price = float(price)
         original_prices.append(price)

   return original_prices


async def list_discounted_prices(soup):
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


async def get_pages(url):
    html = await get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    tasks = [
        asyncio.ensure_future(list_titles(soup)),
        asyncio.ensure_future(list_links(soup)),
        asyncio.ensure_future(list_discounts(soup)),
        asyncio.ensure_future(list_original_prices(soup)),
        asyncio.ensure_future(list_discounted_prices(soup)),
    ]

    responses = await asyncio.gather(*tasks)
    return zip(*responses)


async def run(loop):
    tasks = list()

    for url in await get_links():
        task = asyncio.ensure_future(get_pages(url))
        tasks.append(task)

    responses = await asyncio.gather(*tasks)

    games = [{
        'title': i[0],
        'link': i[1],
        'discount': i[2],
        'original_price': i[3],
        'discounted_price': i[4],
    } for i in itertools.chain.from_iterable(responses)]

    with models.db.atomic():
        for chunk in range(0, len(games), 500): # sqlite limit
            models.Deals.insert_many(games[chunk:chunk+500]).execute()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(loop))
    loop.run_until_complete(future)
