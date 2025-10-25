#! /usr/bin/env python3

import json
import requests


items = []
cursor = ''

while True:
  data = requests.get('https://forthsalon.appspot.com/haiku-dump?cursor=' + cursor).json()
  items.extend(data['items'])
  cursor = data['cursor']
  if cursor is None:
    break

with open('dump.json', 'w') as fh:
  fh.write(json.dumps(items, sort_keys=True, indent=2, separators=(',', ': ')))
