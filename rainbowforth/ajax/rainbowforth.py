import re
import os
import sys
import io
import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import db


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=False)


class Block(db.Model):
  index = db.IntegerProperty()
  owner = db.UserProperty()
  data = db.BlobProperty()


class ReadBlock(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
      block = query.fetch(1)
      if block:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(block[0].data)
        if user.email() == block[0].owner.email():
          self.response.out.write('u')
        else:
          self.response.out.write('o')
      else:
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(' ' * 1024)
        self.response.out.write(' ')
    else:
      self.redirect(users.create_login_url(self.request.uri))


class WriteBlock(webapp2.RequestHandler):
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
        # Enforce ownership.
        if block[0].owner.email() != user.email(): return
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


class DeleteBlock(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      index = int(self.request.get('index'))
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
      block = query.fetch(1)
      if block:
        if user.email() == block[0].owner.email():
          block[0].delete()
      self.response.headers['Content-Type'] = 'text/plain'
    else:
      self.redirect(users.create_login_url(self.request.uri))


class View(webapp2.RequestHandler):
  def get(self):
    COLOR_MAP = {
      u'\xff': '#ff0000',
      u'\xfe': '#ffff00',
      u'\xfd': '#00ff00',
      u'\xfc': '#00ffff',
      u'\xfb': '#0000ff',
      u'\xfa': '#ff00ff',
      u' ': '#ffffff',
    }

    start = int(self.request.get('start'))
    end = int(self.request.get('end'))
    query = Block.gql('WHERE index >= :start and index <= :end',
                      start=start, end=end)

    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write('<html><body bgcolor="#ffffff">\n')

    blocks = query.fetch(1000)
    for b in blocks:
      self.response.out.write(
          '<table bgcolor="#000000"><tr><td><b><pre style="font-size:200%">\n')
      data = unicode(b.data, 'utf8')
      blk ='</font>'
      col = '#ffffff'
      for j in range(15, -1, -1):
        blk = '\n' + blk
        for i in range(63, -1, -1):
          ch = data[i + j * 64]
          if ch in COLOR_MAP:
            if col != COLOR_MAP.get(ch, None):
              blk = ' <font color="' + col + '">' + blk
              col = COLOR_MAP[ch]
            else:
              blk = ' ' + blk
          else:
            blk = ch + blk
      blk = '<font color="' + col + '">' + blk

      self.response.out.write(blk)
      self.response.out.write('</pre></b></td></tr></table>\n')
      self.response.out.write(
          '<b style="font-size:200%">' + str(b.index) + '</b><br><br>\n')

    self.response.out.write('</body></html>\n')


class Export(webapp2.RequestHandler):
  def get(self):
    COLOR_MAP = {
        u'\xff': ': %s ',
        u'\xfe': '[ %s ] ',
        u'\xfd': '%s ',
        u'\xfc': "' %s ",
        u'\xfb': '{ %s } ',
        u'\xfa': 'variable %s ',
        u' ': '( %s ) ',
    }

    start = int(self.request.get('start'))
    end = int(self.request.get('end'))
    query = Block.gql('WHERE index >= :start and index <= :end',
                      start=start, end=end)

    self.response.headers['Content-Type'] = 'text/plain'

    blocks = query.fetch(1000)
    for b in blocks:
      data = unicode(b.data, 'utf8')
      blk = ''
      col = ' '
      word = ''
      for j in range(15, -1, -1):
        blk = '\n' + blk
        for i in range(63, -1, -1):
          ch = data[i + j * 64]
          if ch in COLOR_MAP:
            if word:
              blk = (COLOR_MAP[col] % word) + blk
              word = ''
            col = ch
          else:
            word = ch + word
        if word:
          blk = (COLOR_MAP[col] % word) + blk
          word = ''

      blk = blk.replace(') ( ', '')
      blk = blk.replace('} { ', '')
      blk = blk.replace('] [ ', '')

      self.response.out.write('Block ' + str(b.index) + '\n')
      self.response.out.write('-' * 64 + '\n')
      self.response.out.write(blk)
      self.response.out.write('\n\n')


class Backup(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    if not users.is_current_user_admin():
      self.redirect('/')
      return

    start = int(self.request.get('start'))
    end = int(self.request.get('end'))
    query = Block.gql('WHERE index >= :start and index <= :end',
                      start=start, end=end)
    blocks = query.fetch(1000)

    self.response.headers['Content-Type'] = 'application/x-unknown'
    for b in blocks:
      self.response.out.write('%d %s %d\n' %
                              (b.index, str(b.owner.email()), len(b.data)))
      self.response.out.write(b.data)


class Restore(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return
    if not users.is_current_user_admin():
      self.redirect('/')
      return

    data = self.request.get('datafile')
    fh = io.StringIO(data)

    self.response.headers['Content-Type'] = 'text/plain'

    while True:
      # Get description line.
      line = fh.readline()
      if not line: break
      # Decide it
      index, owner, sz = line.split(' ')
      index = int(index)
      owner = users.User(owner)
      sz = int(sz)
      self.response.out.write(line)
      dt = fh.read(int(sz))
      # Get existing block if any.
      query = Block.gql('WHERE index = :index LIMIT 1', index=index)
      block = query.fetch(1)
      if block:
        b = block[0]
      else:
        b = Block()
      # Store data.
      b.index = index
      b.owner = owner
      b.data = dt
      b.put()

    fh.close()
    self.response.out.write('Done.')


class Reflect(webapp2.RequestHandler):
  def post(self):
    user = users.get_current_user()
    if user:
      data = self.request.str_POST['data']
      self.response.headers['Content-Type'] = 'application/x-unknown'
      self.response.out.write(data)
    else:
      self.redirect(users.create_login_url(self.request.uri))


class AdminPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      template = JINJA_ENVIRONMENT.get_template('html/admin.html')
      self.response.out.write(template.render({}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class BasicEditor(webapp2.RequestHandler):
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
      email = user.email()
      signout = users.create_logout_url(users.create_login_url('/'))
      template = JINJA_ENVIRONMENT.get_template('html/rainbowforth.html')
      self.response.out.write(template.render({'bootstrap': bootstrap,
                                               'email': email,
                                               'signout': signout}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      email = user.email()
      signout = users.create_logout_url(users.create_login_url('/'))
      bootstrap = '" : startup 0 raw-read push raw-load ; [ startup ] "'
      template = JINJA_ENVIRONMENT.get_template('html/rainbowforth.html')
      self.response.out.write(template.render({'bootstrap': bootstrap,
                                               'email': email,
                                               'signout': signout}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


app = webapp2.WSGIApplication(
    [
      ('/[0-9]*', MainPage),
      ('/basic_editor', BasicEditor),
      ('/read', ReadBlock),
      ('/write', WriteBlock),
      ('/delete', DeleteBlock),
      ('/reflect/.*', Reflect),
      ('/admin', AdminPage),
      ('/view', View),
      ('/export', Export),
      ('/backup', Backup),
      ('/restore', Restore),
      ])  #, debug=True)
