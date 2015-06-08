#!/usr/bin/python

import json
import sys


items = json.loads(open(sys.argv[1]).read())


results = []


lookup = {}


for item in items:
  lookup[item['id']] = item
  item['old_rank'] = item['rank']
  item['rank'] = 0.0


for item in items:
  p = item['parent']
  while p in lookup:
    parent = lookup[p]
    parent['rank'] += 3.0
    p = parent['parent']


for item in items:
  item['rank'] += item['score']


for item in items:
  if item['rank'] != item['old_rank']:
    results.append({
      'id': item['id'],
      'rank': item['rank'],
    })


print json.dumps(results, sort_keys=True, indent=2, separators=(',', ': '))
