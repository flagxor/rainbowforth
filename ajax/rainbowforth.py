import os
import sys
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class Block(db.Model):
  index = db.IntegerProperty()
  owner = db.UserProperty()
  data = db.BlobProperty()


class ReadBlock(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
      block = query.fetch(1)
      if block:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(block[0].data)
        if user == block[0].owner:
          self.response.out.write('u')
        else:
          self.response.out.write('o')
      else:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(' ' * 1024)
        self.response.out.write(' ')
    else:
      self.redirect(users.create_login_url(self.request.uri))


class WriteBlock(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      if index < 0 or index > 4096: return  # Limit range.
      data = self.request.str_POST['data']
      if len(data) > 2048: return  # Seems to encode it wastefully.
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
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
      self.response.headers['Content-Type'] = 'text/plain'
    else:
      self.redirect(users.create_login_url(self.request.uri))


class DeleteBlock(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
      block = query.fetch(1)
      if block:
        if user == block[0].owner:
          block[0].delete()
      self.response.headers['Content-Type'] = 'text/plain'
    else:
      self.redirect(users.create_login_url(self.request.uri))


class Reflect(webapp.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      data = self.request.str_POST['data']
      self.response.headers['Content-Type'] = 'application/x-unknown'
      self.response.out.write(data)
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


class BasicEditor(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      # Load bootstrap file, assumes no quotes.
      path = os.path.join(os.path.dirname(__file__), 'forth/basic_editor.fs')
      bootstrap = ''
      fh = open(path, 'r')
      for line in fh:
        nline = line
        nline = nline.replace('\r', ' ')
        nline = nline.replace('\n', ' ')
        bootstrap += '" ' + nline + '" +\n'
      bootstrap += '""'

      # Add bootstrap into template.
      path = os.path.join(os.path.dirname(__file__), 'html/rainbowforth.html')
      self.response.out.write(template.render(path, {'bootstrap': bootstrap}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      bootstrap = '" [ start-block raw-read push raw-load ] "'
      path = os.path.join(os.path.dirname(__file__), 'html/rainbowforth.html')
      self.response.out.write(template.render(path, {'bootstrap': bootstrap}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


def main():
  application = webapp.WSGIApplication(
      [
        ('/[0-9]*', MainPage),
        ('/basic_editor', BasicEditor),
        ('/read', ReadBlock),
        ('/write', WriteBlock),
        ('/delete', DeleteBlock),
        ('/reflect/.*', Reflect),
        ('/test', TestPage),
        ], debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
