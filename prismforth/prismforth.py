import datetime
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


class Block(db.Model):
  owner = db.UserProperty()
  index = db.IntegerProperty()
  data = db.BlobProperty()


class Quota(db.Model):
  owner = db.UserProperty()
  limit = db.IntegerProperty()


class ReadBlock(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE owner = :owner andindex = :index LIMIT 1',
                        owner=user, index=index)
      block = query.fetch(1)
      if block:
        self.response.out.write(block[0].data)


class WriteBlock(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      if index < 0 or index >= limit: return  # Limit range.
      data = self.request.str_POST['data']
      if len(data) > 2048: return  # Seems to encode it wastefully.
      query = Block.gql('WHERE owner=:owner and index = :index LIMIT 1',
                        owner=user, index=index)
      block = query.fetch(1)
      if block:
        block[0].data = data
        block[0].put()
      else:
        b = Block()
        b.index = index
        b.owner = user
        b.data = data
        b.put()


def ChromeFrameMe(handler):
  agent = handler.request.headers.get('USER_AGENT', '')
  if agent.find('MSIE') >= 0 and agent.find('chromeframe') < 0:
    path = os.path.join(os.path.dirname(__file__),
                        'templates/chrome_frame.html')
    handler.response.out.write(template.render(path, {}))
    return True
  return False



class RunWord(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    path = os.path.join(os.path.dirname(__file__),
                        'templates/run.html')
    self.response.out.write(template.render(path, {}))


def main():
  application = webapp.WSGIApplication([
      ('/', RunWord),
      ('/readblock', ReadBlock),
      ('/writeblock', WriteBlock),
  ], debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
