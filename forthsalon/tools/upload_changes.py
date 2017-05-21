#!/usr/bin/python

import getpass
import json
import sys
import urllib


passwd = getpass.getpass('password: ')

items = json.loads(open(sys.argv[1]).read())

def encoded_dict(in_dict):
  out_dict = {}
  for k, v in in_dict.iteritems():
    if isinstance(v, unicode):
      v = v.encode('utf8')
    elif isinstance(v, str):
      # Must be encoded in UTF-8
      v.decode('utf8')
    out_dict[k] = v
  return out_dict

for i in xrange(len(items)):
  print '%d of %d' % (i + 1, len(items))
  item = items[i]
  req = {'passwd': passwd}
  req.update(encoded_dict(item))
  params = urllib.urlencode(req)
  f = urllib.urlopen(
      'http://localhost:8080/haiku-upload', params)
      #'https://forthsalon.appspot.com/haiku-adjust', params)
  f.read()
