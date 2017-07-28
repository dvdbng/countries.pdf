# -*- coding: utf-8 -*-
import urllib, re, json
from bs4 import BeautifulSoup

url = "http://wwwnc.cdc.gov/travel/destinations/traveler/none/%s"

tap_water_override = {
    "south africa": True,
    "panama": True,
}

def scrape_country(country, html=None):
    if html is None:
        html = urllib.urlopen(url % country).read()
    soup = BeautifulSoup(html)
    table = soup.find(id="dest-vm-a").find('table', attrs={'class': "disease"})

    vaccines = {}
    mode = None

    for row in table.findAll('tr'):
        if row.find('td', attrs={'class': 'group-head'}):
            mode = row.find('h4').text
            vaccines[mode] = []
        elif row.find('td', attrs={'class': 'traveler-disease'}):
            name = row.find('td', attrs={'class': 'traveler-disease'}).find('a').next
            vaccines[mode].append(name)
        else:
            print "Skipped row"

    tap_water = None

    if country.lower() in tap_water_override:
        tap_water = tap_water_override[country.lower()]
    else:
        nodrink = soup.find('h5', text="Don’t Drink")
        if nodrink:
            nodrinkTapWater = nodrink.findNextSibling('ul').find('li', text=re.compile('tap( or well)? water', re.IGNORECASE))
            if nodrinkTapWater:
                tap_water = False

    return vaccines, tap_water

#print scrape_country('Panama', open('testhealth_pa.html', 'r').read())

countries = {}
for country in open('countries.txt', 'r'):
    country = country.strip()
    try:
        res = scrape_country(country)
        print res
        countries[country] = res
    except Exception, ex:
        print ex

print countries

with open('vaccines.json', 'w') as f:
    f.write(json.dumps(countries))

