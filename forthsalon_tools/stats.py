#!/usr/bin/python

import re

known = (
'x y t push pop dup over 2dup drop swap rot -rot = <> < > <= >= and or not '
'min max + - * / mod pow atan2 negate sin cos tan log exp sqrt floor ceil abs '
'pi z+ z* random : ; >r r>').split(' ')

print 'KNOWN: %d' % len(known)

words = {}

inside = False
for line in open('haiku_snapshot.txt'):
  if line.startswith('Code:'):
    inside = True
    continue
  if line.startswith('--------'):
    inside = False
    continue
  if inside:
    line = line.replace('\r', ' ')
    line = line.replace('\n', ' ')
    line = re.sub('[ ]+', ' ', line)
    line = re.sub('[ ]$', '', line)
    line = re.sub('^[ ]', '', line)
    parts = line.split(' ')
    for word in parts:
      if not word:
        continue
      rword = word.lower()
      if rword not in known:
        if re.match('^[-]?[0-9\.]+$', rword):
          #rword = '%.1f' % float(rword)
          rword = 'number'
        else:
          rword = 'foo'
      if rword not in words:
        words[rword] = 0
      words[rword] += 1

groups = []
for word in words.keys():
  groups.append((words[word], word))
groups = sorted(groups)
for pair in groups:
  print pair[0], pair[1]
