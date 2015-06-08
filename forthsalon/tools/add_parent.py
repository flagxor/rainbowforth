#!/usr/bin/python

import difflib
import json
import sys


def StringSimilarity(a, b):
  return difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio()


items = json.loads(open('dump.json').read())


mistakes = len(sys.argv) == 2 and sys.argv[1] == 'mistakes'


results = []


for i in xrange(len(items)):
  pick = None
  score = 0
  for j in xrange(len(items)):
    if i == j:
      continue
    if items[j]['when'] >= items[i]['when']:
      continue
    s = StringSimilarity(items[i]['title'] + '|' + items[i]['code'],
                         items[j]['title'] + '|' + items[j]['code'])
    if pick is None or s > score:
      pick = j
      score = s

  old_pick = items[i].get('parent', '')
  if score < 0.6:
    continue
  if old_pick == items[pick]['id']:
    continue
  if mistakes == (old_pick != ''):
    results.append({
      'id': items[i]['id'],
      'parent': items[pick]['id'],
    })

print json.dumps(results, sort_keys=True, indent=2, separators=(',', ': '))
