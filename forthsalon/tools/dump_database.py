#!/usr/bin/python

import json
import urllib


items = []
cursor = ''

while True:
  data = json.loads(urllib.urlopen(
      'https://forthsalon.appspot.com/haiku-dump?cursor=' + cursor).read())
  items.extend(data['items'])
  if not data['more']:
    break
  cursor = data['cursor']


with open('dump.json', 'w') as fh:
  fh.write(json.dumps(items, encoding='utf8', sort_keys=True, indent=2, separators=(',', ': ')))
