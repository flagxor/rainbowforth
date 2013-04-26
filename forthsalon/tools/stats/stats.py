#!/usr/bin/python

import math
import re

THRESHOLD = 95

known = (
'x y t push pop dup over 2dup drop swap rot -rot = <> < > <= >= and or not '
'min max + - * / mod pow atan2 negate sin cos tan log exp sqrt floor ceil abs '
'pi z+ z* random : ; >r r>').split(' ')

print 'KNOWN: %d' % len(known)

haikus = []

inside = False
haiku = []
for line in open('haiku_snapshot.txt'):
  if line.startswith('Code:'):
    inside = True
    continue
  if line.startswith('--------'):
    haikus.append(haiku)
    haiku = []
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
          rword = '%.1f' % float(rword)
        else:
          rword = 'foo'
      haiku.append(rword)


def mean(items):
  return float(sum(items)) / float(len(items))


def midpoint(items, partition):
  items = sorted(items)
  count = len(items)
  mid = int(count * partition)
  return items[mid]


def median(items):
  items = sorted(items)
  count = len(items)
  if count % 2 == 0:
    return (items[count / 2] + items[count / 2 + 1]) / 2.0
  else:
    return items[count / 2]


def standard_deviation(items):
  m = mean(items)
  tally = 0
  for item in items:
    tally += pow(item - m, 2)
  return math.sqrt(tally / float(len(items)))


def stats(items):
  return 'range: %g:%g, mean: %g(%g), 50:%g 75:%g %d:%g' % (
      min(items),
      max(items),
      mean(items),
      standard_deviation(items),
      median(items),
      midpoint(items, 0.75),
      THRESHOLD,
      midpoint(items, THRESHOLD / 100.0),
      )

print 'Haiku Size> ' + stats([len(i) for i in haikus])


words = set()
for haiku in haikus:
  for word in haiku:
    words.add(word)
words = sorted(list(words))


active = 0
for word in words:
  uses = []
  for haiku in haikus:
    count = 0
    for w in haiku:
      if w == word:
        count += 1
    uses.append(count)
  use90 = midpoint(uses, THRESHOLD / 100.0)
  active += use90
  if use90 > 0:
    print '%s --- %s' % (word, stats(uses))


print 'ACTIVE: %d' % active
