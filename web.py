import json
import requests
import urllib
import os
from flask import Flask, request, render_template, redirect

here = os.path.dirname(__file__)
os.chdir(here)

app = Flask(__name__)

app.debug = True

countries = {}

for country in json.loads(open('countries.json', 'r').read()):
    countries[country['cca2']] = country['demonym'] or country['name']['common']
countries_sorted = countries.items()
countries_sorted.sort(key=lambda x: x[1])

elasticmail_auth = {
    "api_key" : "XXXX",
    "username": "XXXX",
}

email_text = """Hi %s citizen!

Attached is your countries.pdf document with personalized visa information!

Regards,
David
"""

attachment_ids = {} # {country_id: id}

def elasticmail_query(endpoint, args, method="POST", data=None):
    headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
    args.update(elasticmail_auth)

    url = "https://api.elasticemail.com" + endpoint + "?" + urllib.urlencode(args)
    res = requests.request(method, url, data=data or "")
    print res.text
    return res.text

def send_countries(email, country):
    elasticmail_query('/lists/create-contact', {'email': email, 'country': country, 'listname': 'Countries.pdf'})

    if country not in attachment_ids:
        resp = elasticmail_query('/attachments/upload', {"file":'countries.pdf'}, "PUT", open('countries/countries-%s.pdf' % country.lower(), 'r'))
        attachment_ids[country] = resp

    attachment_id = attachment_ids[country]
    elasticmail_query('/mailer/send', {
        "to": email,
        "body_text": email_text % countries[country.upper()],
        "subject": "countries.pdf",
        "from": "hi@browserprotect.me",
        "attachments": attachment_id
    })

@app.route("/")
def hello():
    return render_template("index.html", countries=countries_sorted)

@app.route("/subscribe", methods=['POST'])
def subscribe():
    email = request.form['email']
    country = request.form['nationality'].upper()

    if country not in countries:
        print "Invalid country"
        raise Exception('Invalid country')

    send_countries(email, country);
    return redirect('/thanks')

@app.route("/thanks")
def thanks():
    return "We have sent you a personalized countries.pdf to the e-mail address you provided."

if __name__ == '__main__':
    app.run()

