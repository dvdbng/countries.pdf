# -*- coding: utf-8 -*-

# Visa, Have it
# Tap water Have it
# Currency Need.
# Language Need
# Vaccinations Have it
# Country embassy in origin country  Back log
# Origin country embassy in destination country  Back log


from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.platypus.flowables import Spacer
import json
from collections import defaultdict
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import sqlite3
import re

pdfmetrics.registerFont(TTFont('Ubuntu', 'Ubuntu-R.ttf'))
pdfmetrics.registerFont(TTFont('UbuntuB', 'Ubuntu-B.ttf'))
addMapping('Ubuntu', 0, 0, 'Ubuntu')
addMapping('Ubuntu', 1, 0, 'UbuntuB')

countries_by_region = defaultdict(list)
countries_by_name = {}
countries_by_code = {}

for x in json.loads(open('countries.json', 'r').read()):
    country = {
        'name': x['name']['common'],
        'code2': x['cca2'],
        'code3': x['cca3'],
        'callingCode': (x['callingCode'] + ['Unknown'])[0],
        'languages': ", ".join(x['languages'].values()),
        'currency': (x['currency'] + ['UNK'])[0], #code
        'capital': x['capital'],
        'demonym': x['demonym'],
        'vaccines': [],
    }
    if x['region'] == '':
        continue
    countries_by_region[x['region']].append(country)
    countries_by_name[country['name'].lower()] = country
    countries_by_code[country['code2'].lower()] = country

for country_name, vaccines in json.loads(open('vaccines.json', 'r').read()).items():
    vaccines = vaccines[0]
    country = countries_by_name.get(country_name.strip().lower(), None)
    if country is None:
        print "Unknown country %s" % country_name
        continue

    country['vaccines'] = map(lambda x: '<b>%s</b>' % x, filter(lambda x: x != 'Routine vaccines',  vaccines.get('All travelers', []))) + vaccines.get('Most travelers',  [])

def chunks(l, n):
    """ Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

conn = sqlite3.connect('Timatic.db')

def generate_pdf(oringin_country):
    x = 10
    y = 10
    styleSheet = getSampleStyleSheet()
    p = SimpleDocTemplate("countries-%s.pdf" % oringin_country, bottomup=0)
    style = styleSheet['BodyText']
    style.fontName='Ubuntu'

    elements = [Paragraph(u"""
        This is a list of %s countries along with visa information for %s citizens, vaccination information (vaccines in <b>bold</b> are <b>REQUIRED</b> to enter the country) capital city, calling code and official languages.
        <br/> Keep this PDF in your phone when travelling to know the essential information of every country.
        <br/> This project was put together in a day and is not verified to be correct, double check the information here.
    """ % (len(countries_by_name.keys()), countries_by_code[oringin_country]['demonym']), style)]

    for region, countries in countries_by_region.iteritems():
        elements.append(Paragraph('<font size="18">%s</font>' % region, style))
        elements.append(Spacer(0, 20))

        data = []
        for country in countries:
            if country['code2'].lower() == oringin_country:
                continue
            c = conn.cursor()
            c.execute("SELECT Desc FROM VisaReq WHERE National='%s' and Destination='%s'" % (oringin_country.upper(), country['code2'].upper()))
            visa_desc = c.fetchone()
            if visa_desc is None:
                visa_desc = ['Unknown']
            visa_desc = re.sub('^[A-Z]{2} to [A-Z]{2} (visa)?', '', visa_desc[0].strip()).strip().capitalize()

            text = """
            <font size="10"><b>%(name)s</b></font><br/>
            <font size="8" color="#555555">Capital</font><font size="8">: %(capital)s</font><br/>
            <font size="8" color="#555555">Calling code</font><font size="8">: +%(callingCode)s</font><br/>
            <font size="8" color="#555555">Languages</font><font size="8">: %(languages)s</font>
            """ % country

            text += '<br/><font size="8" color="#555555">Visa</font><font size="8">: %s</font>' % visa_desc

            if len(country['vaccines']) > 0:
                text += '<br/><font size="8" color="#555555">Vaccines</font><font size="8">: %s</font>' % ", ".join(country['vaccines'])

            cell = Paragraph(text, style)
            data.append(cell)

        t=Table(list(chunks(data, 3)), style=[
            ('GRID',(0,0),(-1,-1),0.5,colors.black),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ])
        elements.append(t)

    p.build(elements)

generate_pdf('es')

for code in countries_by_code.iterkeys():
    generate_pdf(code.lower())

