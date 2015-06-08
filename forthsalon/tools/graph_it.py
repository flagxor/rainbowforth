#!/usr/bin/python

import json
import sys

# convert with:
# dot -Tsvg <foo.grf >foo.svg

items = json.loads(open(sys.argv[1]).read())

used = set()
lookup = {}

for item in items:
  lookup[item['id']] = item
  if item['parent']:
    used.add(item['parent'])

for item in items:
  rp = item
  while rp.get('parent'):
    rp = lookup[rp['parent']]
  item['root'] = rp

col = 0

print 'digraph "Forth Haiku" {'
print 'rankdir="RL";'
for item in items:
  try:
    if not item['parent'] and item['id'] not in used:
      continue
    if '"' in item['title'] or '"' in item['author']:
      continue
    if 'color' not in item['root']:
      col += 0.1
      if col >= 1.0:
        col = 0.0
      item['root']['color'] = col
    print '%s [shape=box, style=filled, label="%s", fillcolor="%s"];' % (
      item['id'].replace('-', '_'), item['title'] + ' - ' + item['author'],
      '%f+.3+.9' % item['root']['color'])
    if item['parent']:
      print '%s -> %s' % (
          item['id'].replace('-', '_'), item['parent'].replace('-', '_'))
  except:
    pass
print '}'
