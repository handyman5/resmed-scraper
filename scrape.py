#!/usr/bin/env python

import datetime
import json
import re
import requests
import subprocess
import time
from bs4 import BeautifulSoup
from parsedatetime import Calendar

config = None
with open('config.json') as fh:
    config = json.loads(fh.read())

data = {
    '__VIEWSTATE': config['viewstate'],
    '__EVENTTARGET': 'ButtonSignIn',
    "__VIEWSTATEGENERATOR": "CA0B0334",
    '__VIEWSTATEENCRYPTED': '',
    'ctl00$ctl00$PageContent$MainPageContent$textBoxEmailAddress': config['email'],
    'ctl00$ctl00$PageContent$MainPageContent$textBoxPassword': config['password']
    }

cookies = {
    'LocalizationSettings': 'CurrentMyAirLocale=en-US',
    'resmed-myair-country': 'resmed-myair-country=2',
    'resmed-myair-instance': 'resmed-myair-instance=1'
}
url = 'https://myair.resmed.com/Default.aspx'




def get_page():
    result = requests.post(url, data=data, cookies=cookies)
    soup = BeautifulSoup(result.text, features="html.parser")
    return soup


def get_page2():
    s = subprocess.Popen(open('mycurl').read(), shell=True, stdout=subprocess.PIPE)
    soup = BeautifulSoup(s.stdout.read(), features="html.parser")
    return soup


if __name__ == '__main__':
    


    soup = get_page2()
    scripts = soup.find_all('script')
    scores_script = [x for x in scripts if 'myScores' in x.text][0].text
    matches = re.search('.+(\[.+?\]).+', scores_script).groups()[0]
    my_scores = json.loads(matches)

    scores = []
    parser = Calendar()
    for mys in my_scores:
        if not mys['DataReceived'] == 'has-data':
            continue
        date = datetime.datetime.fromtimestamp(
            time.mktime(
                parser.parse(
                    '{} {}'.format(mys['ChartDate'], datetime.datetime.now().year)
                )[0]
            )
        )
        date = date.replace(hour=0, minute=0, second=0)
        output = {
            'date': date.isoformat(),
            'events': float(mys['Events']),
            'events_score': float(mys['EventsScore']),
            'leak': float(mys['Leak']),
            'leak_score': float(mys['LeakScore']),
            'mask': float(mys['Mask']),
            'mask_score': float(mys['MaskScore']),
            'usage': mys['UsageDisplay'],
            'usage_hours': float(mys['Usage']) if mys['Usage'] else 0,
            'score': float(mys['Score'])
        }
        scores.append(output)

        data = [{
            'name': 'sleep',
            'date': date.strftime('%Y-%m-%d'),
            'value': output['usage_hours'] * 60
        }, {
            'name': 'sleep_awakenings',
            'date': date.strftime('%Y-%m-%d'),
            'value': (output['mask'] - 1) if output['mask'] > 0 else 0
        }]

        if 'exist_token' in config:
            exist_api = 'https://exist.io/api/1/'
            exist_headers = {
                'Authorization': 'Bearer {}'.format(config['exist_token'])
            }
            print "posting data"
            print data
            r = requests.post(
exist_api + 'attributes/update/', headers=exist_headers, json=data)
