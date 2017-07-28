
from bs4 import BeautifulSoup


def scrape_visas(country, wikipedia_content):
    """
    returns [(country, visa_status, notes),]
    """
    soup = BeautifulSoup(wikipedia_content)
    table = soup.find(lambda tag: tag.name == 'table' and tag.has_attr('class') and 'sortable' in tag['class'])
    print len(table)
    for flag in table.find(lambda tag: tag.name == 'a' and 'flagicon' in tag['class']):
        print flag



scrape_visas('Spain', open('testvisa.html', 'r').read())




