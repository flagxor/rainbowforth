#!/usr/bin/python

import getpass
import json
import sys
import urllib


passwd = getpass.getpass('password: ')

items = json.loads(open(sys.argv[1]).read())

for i in xrange(len(items)):
  print '%d of %d' % (i + 1, len(items))
  item = items[i]
  req = {'passwd': passwd}
  req.update(item)
  params = urllib.urlencode(req)
  urllib.urlopen("http://www.musi-cal.com/cgi-bin/query", params)
  f = urllib.urlopen(
      'https://forthsalon.appspot.com/haiku-adjust', params)
  f.read()
