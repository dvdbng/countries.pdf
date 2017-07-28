# -*- coding: utf-8 -*-

# Visa, Have it
# Tap water Have it
# Currency Need.
# Language Need
# Vaccinations Have it
# Country embassy in origin country  Back log
# Origin country embassy in destination country  Back log

import json
from collections import defaultdict
import sqlite3
import re

HEADER = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>%(title)s</title>
        <link rel="stylesheet" href="../assets/bootstrap.min.css" />
        <link rel="stylesheet" href="../assets/style.css" />
    </head>
    <body>
    <div class="container">
"""
FOOTER = """
<hr/>
<a href="index.html">Back to the index</a>
</div><!--JS-->
</body></html>"""

def dasherize(x):
    return re.sub('[^a-z]', '-', x.lower())


countries_by_name = {}
countries_by_code = {}
countries_by_region = defaultdict(list)
countries_by_subregion = defaultdict(list)

for x in json.loads(open('countries.json', 'r').read()):
    country = {
        'name': x['name']['common'],
        'official': x['name']['official'],
        'code2': x['cca2'],
        'code3': x['cca3'].lower(),
        'callingCode': (x['callingCode'] + ['Unknown'])[0],
        'languages': ", ".join(x['languages'].values()),
        'currency': (x['currency'] + ['UNK'])[0], #code
        'capital': x['capital'],
        'region': x['region'],
        'region_slug': dasherize(x['region']),
        'subregion': x['subregion'],
        'subregion_slug': dasherize(x['subregion']),
        'demonym': x['demonym'] or x['name']['common'],
        'borders': x['borders'],
        'area': x['area'],
        'landlocked': 'Yes' if x['landlocked'] else 'No',
        'vaccines_all': [],
        'vaccines_some': [],
    }
    if x['region'] == '':
        continue
    countries_by_name[country['name'].lower()] = country
    countries_by_code[country['code2'].lower()] = country
    countries_by_code[country['code3'].lower()] = country
    countries_by_region[country['region']].append(country)
    countries_by_subregion[country['subregion']].append(country)

for country_name, vaccines in json.loads(open('vaccines.json', 'r').read()).items():
    vaccines = vaccines[0]
    country = countries_by_name.get(country_name.strip().lower(), None)
    if country is None:
        print "Unknown country %s" % country_name
        continue

    country['vaccines_all'] = filter(lambda x: x != 'Routine vaccines',  vaccines.get('All travelers', []))
    country['vaccines_some'] = vaccines.get('Most travelers',  [])

print len(countries_by_name.items()), "countries"

conn = sqlite3.connect('Timatic.db')

def generate_simple_html(code2):
    country = countries_by_code[code2]
    body = HEADER + """
    <div class="thumbnail pull-right flag">
        <img src="../assets/flags/%(code3)s.svg" alt="Flag of %(name)s" />
        <div class="caption">
            <h3>Flag of %(name)s</h3>
        </div>
    </div>
    <h1>Information about %(name)s</h1>
    <p>%(name)s (Official name %(official)s) is a country in <a href="%(region_slug)s.html">%(region)s</a>, more specifically in <a href="%(subregion_slug)s.html">%(subregion)s</a>.</p>
    <table>
    """

    for label, key in (
        ('Calling Code', 'callingCode'),
        ('Official Languages', 'languages'),
        ('Currency', 'currency'),
        ('Capital', 'capital'),
        ('Demonym', 'demonym'),
        ('Landlocked', 'landlocked'),
        (u'Area (km²)', 'area'),
    ):
        body += "<tr><th>%s</th><td>%s</td></tr>" % (label, country[key])

    body += "</table>"
    body += "<h2>Bordering countries</h2><p>The following countries share a border with %(name)s:</p><ul>"

    for cborder in country['borders']:
        body += '<li><a href="%(code3)s.html">%(name)s</a></li>' % countries_by_code[cborder.lower()]

    body += "</ul>"

    body += """<div class="page-header"><h2>Thinking about travelling to %(name)s? <small>Here is what you need to know:</small></h2></div>
    <div class="alert alert-warning" role="alert"><strong>Warning:</strong> When travelling to other country you should always have the routine vaccines up to date.</div>"""
    if len(country['vaccines_all']) == 0 and len(country['vaccines_some']) == 0:
        body += "<p>%(name)s is a safe country health-wise, and no additional vaccines are required.</p>"
    else:
        if len(country['vaccines_all']):
            body += "<p>The following vaccines are <b>obligatory</b> when travelling into %(name)s: " + ", ".join(country['vaccines_all'])
            body += ".</p>"
        if len(country['vaccines_some']):
            body += "<p>The following vaccines are <b>recommended</b> when travelling into %(name)s: " + ", ".join(country['vaccines_some'])
            body += ".</p>"

    body += "<!--VISA-->"
    body += FOOTER

    ctx = {
        "title": "Information about %(name)s" % country
    }
    ctx.update(country)

    body = body % ctx
    return body

def write_simple_html(code2):
    code3 = countries_by_code[code2]['code3']
    with open('out/simple/%s.html' % code3, 'w') as f:
        f.write(generate_simple_html(code2).encode('utf-8'))

def write_js_html(code2):
    country = countries_by_code[code2]
    body = generate_simple_html(code2)

    body = body.replace('<table>', '<a href="#" id="showMore">Show details</a><table style="display: none;">')

    body = body.replace('<!--JS-->', """
    <script src="../assets/jquery.min.js" ></script>
    <script src="../assets/main.js" ></script>
    """)
    visa = """
    <div>Do I need visa to travel to %(name)s? Select your passport nationality to find out:
    <form class="form-inline">
    <input type="hidden" value="%(code2)s" id="country-code" />
    <select id="nat" class="form-control">
        <option value="">Select your nationality</option>
    """ % country
    countries = countries_by_name.values()
    countries.sort(key=lambda x: x['demonym'])
    for other in countries:
        if country['code2'] != other['code2']:
            visa += "<option value='%(code2)s'>%(demonym)s</option>" % other

    visa += """</select>
    <button class='btn btn-primary' id='check-btn'>Check visa status</button>
    </form>
    <div class="alert alert-info" id="visaresult" style="display:none;"></div>
    </div>"""

    body = body.replace('<!--VISA-->', visa)

    with open('out/interactive/%s.html' % country['code3'], 'w') as f:
        f.write(body.encode('utf-8'))

def generate_region_html(region):
    body = HEADER + "<h1>%(title)s</h1><ul>"

    for country in countries_by_region[region]:
        body += "<li><a href='%(code3)s.html'>%(name)s</a></li>" % country
    body += "</ul>" + FOOTER

    body = body % { "title": "Countries in %s" % region }
    with open('out/simple/%s.html' % dasherize(region), 'w') as f:
        f.write(body.encode('utf-8'))
    with open('out/interactive/%s.html' % dasherize(region), 'w') as f:
        f.write(body.encode('utf-8'))

def generate_subregion_html(region):
    body = HEADER + "<h1>%(title)s</h1><ul>"

    for country in countries_by_subregion[region]:
        body += "<li><a href='%(code3)s.html'>%(name)s</a></li>" % country
    body += "</ul>" + FOOTER

    body = body % { "title": "Countries in %s" % region }
    with open('out/simple/%s.html' % dasherize(region), 'w') as f:
        f.write(body.encode('utf-8'))
    with open('out/interactive/%s.html' % dasherize(region), 'w') as f:
        f.write(body.encode('utf-8'))

def generate_index_html():
    body = HEADER + "<h1>%(title)s</h1><h2>Regions</h2><ul>"

    for region in countries_by_region.keys():
        body += "<li><a href='%s.html'>%s</a></li>" % (dasherize(region), region)
    body += "</ul><h2>Subregions</h2><ul>"
    for region in countries_by_subregion.keys():
        body += "<li><a href='%s.html'>%s</a></li>" % (dasherize(region), region)
    body += "</ul>" + FOOTER

    body = body % { "title": "All countries in the world!" }
    with open('out/simple/index.html', 'w') as f:
        f.write(body.encode('utf-8'))
    with open('out/interactive/index.html', 'w') as f:
        f.write(body.encode('utf-8'))

def generate_json(nationality, country):
    c = conn.cursor()
    c.execute("SELECT Desc FROM VisaReq WHERE National='%s' and Destination='%s'" % (nationality.upper(), country.upper()))
    visa_desc = c.fetchone()
    if visa_desc is None:
        return
    visa_desc = re.sub('^[A-Z]{2} to [A-Z]{2} (visa)?', '', visa_desc[0].strip()).strip().capitalize()
    with open('out/data/%s-%s.json' % (nationality, country), 'w') as f:
        f.write(json.dumps({ "visa": visa_desc }))

#generate_simple_html('es')
#generate_simple_html('rw')
#generate_json('es', 'fr')

for region in countries_by_region.keys():
    generate_region_html(region)

for region in countries_by_subregion.keys():
    generate_subregion_html(region)

generate_index_html()

for country in countries_by_name.itervalues():
    code = country['code2'].lower()
    write_simple_html(code)
    write_js_html(code)
    #for othercountry in countries_by_name.itervalues():
    #    othercode = othercountry['code2'].lower()
    #    if code != othercode:
    #        generate_json(code, othercode)
