import datetime
import logging
import os
import random
import re
import sys
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


BLOCK_SIZE = 64 * 1024
BLOCK_COLS = 64
BLOCK_ROWS = int(BLOCK_SIZE / BLOCK_COLS)


class Block(db.Model):
  owner = db.UserProperty()
  index = db.IntegerProperty()
  data = db.BlobProperty()


class Quota(db.Model):
  who = db.UserProperty()
  limit = db.IntegerProperty()


class WebAlias(db.Model):
  name = db.StringProperty()
  who = db.UserProperty()
  index = db.IntegerProperty()


def GetQuota(user):
  key = '/quota/' + user.email()
  quota = memcache.get(key)
  if quota:
    return quota
  query = Quota.gql('WHERE who = :who LIMIT 1', who=user)
  e = query.fetch(1)
  if e:
    quota = e[0].limit
  else:
    quota = 4 # Default 4 block quota.
  memcache.set(key, quota)
  return quota


def ReadBlock(user, index):
  key = '/block/' + user.email() + '/index/%d' % index
  data = memcache.get(key)
  if data:
    return data
  query = Block.gql('WHERE owner = :owner and index = :index LIMIT 1',
                    owner=user, index=index)
  block = query.fetch(1)
  if block:
    data = block[0].data
  else:
    data = ''
  memcache.set(key, data)
  return data


def WriteBlock(user, index, data):
  if len(data) != BLOCK_SIZE: return False
  # Must be non-negative.
  if index < 0: return False
  # Limit range.
  limit = GetQuota(user)
  if index >= limit: return False
  # Update datastore.
  query = Block.gql('WHERE owner = :owner and index = :index LIMIT 1',
                    owner=user, index=index)
  block = query.fetch(1)
  if block:
    b = block[0]
  else:
    b = Block()
    b.owner = user
    b.index = index
  b.data = data
  b.put()
  # Update Cache
  key = '/block/' + user.email() + '/index/%d' % index
  memcache.set(key, data)
  return True


class ReadBlockHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      data = ReadBlock(user, index)
      self.response.out.write(data)


class WriteBlockHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      data = str(self.request.str_POST['data'])
      if WriteBlock(user, index, data):
        self.response.out.write('1\n')


def ChromeFrameMe(handler):
  agent = handler.request.headers.get('USER_AGENT', '')
  if agent.find('MSIE') >= 0 and agent.find('chromeframe') < 0:
    path = os.path.join(os.path.dirname(__file__),
                        'templates/chrome_frame.html')
    handler.response.out.write(template.render(path, {}))
    return True
  return False


class RunWordHandler(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    path = os.path.join(os.path.dirname(__file__),
                        'templates/run.html')
    self.response.out.write(template.render(path, {}))


def DecodeBlock(data):
  rows = []
  for i in range(BLOCK_ROWS):
    rows.append(data[i*BLOCK_COLS:(i+1)*BLOCK_COLS].rstrip())
  rows = rows[0:BLOCK_ROWS]
  return '\n'.join(rows)


def EncodeBlock(data):
  rows = data.split('\n')
  rows = rows[0:BLOCK_ROWS]
  rows = [(i[0:BLOCK_COLS] + ' ' * BLOCK_COLS)[0:BLOCK_COLS] for i in rows]
  while len(rows) < BLOCK_ROWS:
    rows.append(' ' * BLOCK_COLS)
  return ''.join(rows)


class EditorHandler(webapp.RequestHandler):
  def get(self):
    self.post()

  def post(self):
    # Make sure we're logged in.
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    url = users.create_logout_url(self.request.uri)
    greeting = '[%s] <a href="%s">Logout</a>' % (user.email(), url)

    # Get the current index.
    index = int(self.request.get('index', 0))

    # Save block if needed.
    if self.request.get('save'):
      data = self.request.get('data', '')
      data = str(data)
      data = EncodeBlock(str(self.request.get('data', '')))
      assert len(data) == BLOCK_SIZE
      WriteBlock(user, index, data)
    else:
      # Pick the new current index.
      if self.request.get('prev'):
        index -= 1
      elif self.request.get('next'):
        index += 1
      else:
        index = int(self.request.get('goindex', index))
      if index < 0:
        index = 0
      # Load it.
      data = ReadBlock(user, index)

    # Display output.
    path = os.path.join(os.path.dirname(__file__),
                        'templates/editor.html')
    self.response.out.write(template.render(path, {
      'greeting': greeting,
      'data': DecodeBlock(data),
      'index': index,
    }))


def main():
  application = webapp.WSGIApplication([
      ('/_readblock', ReadBlockHandler),
      ('/_writeblock', WriteBlockHandler),
      ('/_editor', EditorHandler),
      ('/.*', RunWordHandler),
  ], debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
