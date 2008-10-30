import os
import sys
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template


class Block(db.Model):
  author = db.UserProperty()
  index = db.IntegerProperty()
  data = db.BlobProperty()


class ReadBlock(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE author = :author and '
                        'index = :index '
                        'LIMIT 1',
                        author=user,
                        index=index)
      block = query.fetch(1)
      if block:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(block[0].data)
      else:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(' ' * 1024)
    else:
      self.redirect(users.create_login_url(self.request.uri))


class WriteBlock(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      data = self.request.str_POST['data']
      query = Block.gql('WHERE author = :author and '
                        'index = :index '
                        'LIMIT 1',
                        author=user,
                        index=index)
      block = query.fetch(1)
      if block:
        block[0].data = data
        block[0].put()
      else:
        b = Block()
        b.index = index
        b.author = user
        b.data = data
        b.put()
      self.response.headers['Content-Type'] = 'text/plain'
    else:
      self.redirect(users.create_login_url(self.request.uri))


class TestPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      path = os.path.join(os.path.dirname(__file__), 'html/blocktest.html')
      self.response.out.write(template.render(path, {}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      path = os.path.join(os.path.dirname(__file__), 'html/rainbowforth.html')
      self.response.out.write(template.render(path, {}))
    else:
      self.redirect(users.create_login_url(self.request.uri))



def main():
  application = webapp.WSGIApplication(
      [('/', MainPage),
       ('/test', TestPage),
       ('/read', ReadBlock),
       ('/write', WriteBlock)],
      debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
