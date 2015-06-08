#!/usr/bin/python

import json
import sys

# convert with:
# dot -Tsvg <foo.grf >foo.svg

items = json.loads(open(sys.argv[1]).read())

used = set()

for item in items:
  if item['parent']:
    used.add(item['parent'])

print 'digraph "Forth Haiku" {'
print 'rankdir="RL";'
for item in items:
  try:
    if not item['parent'] and item['id'] not in used:
      continue
    if '"' in item['title'] or '"' in item['author']:
      continue
    print '%s [shape=box, style=filled, label="%s"];' % (
      item['id'].replace('-', '_'), item['title'] + ' - ' + item['author'])
    if item['parent']:
      print '%s -> %s' % (
          item['id'].replace('-', '_'), item['parent'].replace('-', '_'))
  except:
    pass
print '}'
