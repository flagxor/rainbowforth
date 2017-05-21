import datetime
import json
import logging
import os
import random
import re

import glossary

import jinja2
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import search
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import deferred
from google.appengine.ext import ndb


CACHE_TIMEOUT = 120
SPAM_RE = re.compile('[A-Za-z0-9]{30}')
NUMBER_RE = re.compile('^[0-9eE.+-]+$')
SEARCH_INDEX = 'search'


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')))


def ToDatetime(s):
  # From a Date in JS do: new String(dt.getTime()).
  return datetime.datetime.utcfromtimestamp(float(s) / 1000.0)

  
def FromDatetime(dt):
  # To get a JS data do: new Date(s).
  epoch = datetime.datetime.utcfromtimestamp(0)
  return str((dt - epoch).total_seconds() * 1000.0)


def IsGoodWord(word):
  return glossary.IsHaikuWord(word) and word not in ('and', 'or', 'not', 'then')


def HaikuWordCount(text):
  text = text.replace('\n', ' ')
  text = text.replace('\r', ' ')
  text = text.replace('\t', ' ')
  return len([i for i in text.split(' ')
              if IsGoodWord(i) or NUMBER_RE.match(i)])


class Password(ndb.Model):
  secret = ndb.StringProperty()


def CheckPassword(secret):
  passwd = memcache.get('passwd')
  if passwd:
    return secret == passwd
  q = Password.query()
  items = q.fetch(limit=1)
  if len(items) == 0:
    p = Password()
    p.secret = ''
    p.put()
    return False
  if len(items) != 1:
    return False
  if items[0].secret == '':
    return False
  memcache.add('passwd', items[0].secret)
  return secret == items[0].secret


class Haiku(ndb.Model):
  when = ndb.DateTimeProperty(auto_now_add=True)
  title = ndb.StringProperty()
  author = ndb.StringProperty()
  code = ndb.TextProperty()
  score = ndb.IntegerProperty()
  rank = ndb.FloatProperty(default=0.0)
  last_modified = ndb.DateTimeProperty(auto_now=True)
  parent = ndb.StringProperty(default='')
  parent_recorded = ndb.BooleanProperty(default=False)

  def GetId(self):
    return self.key.urlsafe() 

  def ToDict(self):
    return {
        'id': self.GetId(),
        'when': self.when,
        'title': self.title,
        'author': self.author,
        'code': self.code,
        'score': self.score,
        'rank': self.rank,
        'code_formatted': glossary.FormatHtml(self.code),
        'code_formatted_print': glossary.FormatHtmlPrint(self.code),
        'parent': self.parent,
        'parent_recorded': self.parent_recorded,
    }

  def ToJSDict(self):
    return {
        'id': self.GetId(),
        'when': FromDatetime(self.when),
        'last_modified': FromDatetime(self.last_modified),
        'title': self.title,
        'author': self.author,
        'code': self.code,
        'score': self.score,
        'rank': self.rank,
        'parent': self.parent,
        'parent_recorded': self.parent_recorded,
    }

  def FromRequest(self, src):
    self.when = ToDatetime(src.get('when'))
    self.last_modified = ToDatetime(src.get('last_modified'))
    self.title = src.get('title')
    self.author = src.get('author')
    self.code = src.get('code')
    self.score = int(src.get('score'))
    self.rank = float(src.get('rank'))
    self.parent = src.get('parent')
    self.parent_recorded = bool(src.get('parent_recorded'))

  def ToDocument(self):
    return search.Document(
        doc_id = self.GetId(),
        fields = [
          search.DateField(name='when', value=self.when),
          search.DateField(name='last_modified', value=self.last_modified),
          search.TextField(name='title', value=self.title),
          search.TextField(name='author', value=self.author),
          search.TextField(name='code', value=self.code),
        ])


class HaikuViewPage(webapp2.RequestHandler):
  def get(self):
    id = self.request.path.split('/')[2]
    haiku = memcache.get('haiku_' + id)
    if haiku is None:
      key = ndb.Key(*ndb.Key(urlsafe=id).flat())
      haiku = key.get().ToDict()
      memcache.add('haiku_' + id, haiku)

    parent_id = haiku.get('parent')
    parent = None
    if parent_id:
      parent = memcache.get('haiku_' + parent_id)
      if parent is None:
        key = ndb.Key(*ndb.Key(urlsafe=parent_id).flat())
        parent = key.get().ToDict()
        memcache.add('haiku_' + parent_id, parent)
    has_parent = parent is not None

    template = JINJA_ENVIRONMENT.get_template('haiku-view.html')
    haiku_size = self.request.get('size', 256)
    haiku_width = self.request.get('width', haiku_size)
    haiku_height = self.request.get('height', haiku_size)
    self.response.out.write(template.render({
        'haiku': haiku,
        'parent': parent,
        'has_parent': has_parent,
        'haiku_width': haiku_width,
        'haiku_height': haiku_height,
    }))


class HaikuSlideshowPage(webapp2.RequestHandler):
  def get(self):
    limit = int(self.request.get('limit', 40))

    order = self.request.get('order', '')
    if order != 'rank':
      order = 'age'
    cursorv = self.request.get('cursor', None)
    if order == 'rank':
      qorder = 'ORDER BY rank DESC'
      norder = 'rank'
    else:
      qorder = 'ORDER BY when DESC'
      norder = 'when'
    cursor = Cursor(urlsafe=cursorv)
    q = Haiku.gql(qorder)
    haikus, next_cursor, more = q.fetch_page(limit, start_cursor=cursor)
    haikus = [h.ToDict() for h in haikus]
    if next_cursor:
      next_cursor = next_cursor.urlsafe()

    template = JINJA_ENVIRONMENT.get_template('haiku-slideshow.html')
    haiku_size = self.request.get('size', 600)
    haiku_width = self.request.get('width', haiku_size)
    haiku_height = self.request.get('height', haiku_size)
    self.response.out.write(template.render({
        'haikus': haikus,
        'haiku_count': len(haikus),
        'haiku_width': haiku_width,
        'haiku_height': haiku_height,
        'order': order,
        'more': more,
        'cursor': next_cursor,
        'limit': limit,
    }))


class HaikuBarePage(webapp2.RequestHandler):
  def get(self):
    id = self.request.path.split('/')[2]
    haiku = memcache.get('haiku_' + id)
    if haiku is None:
      key = ndb.Key(*ndb.Key(urlsafe=id).flat())
      haiku = key.get().ToDict()
      memcache.add('haiku_' + id, haiku)
    template = JINJA_ENVIRONMENT.get_template('haiku-bare.html')
    haiku_size = self.request.get('size', 256)
    haiku_width = self.request.get('width', haiku_size)
    haiku_height = self.request.get('height', haiku_size)
    self.response.out.write(template.render({
        'haiku': haiku,
        'haiku_width': haiku_width,
        'haiku_height': haiku_height,
    }))


class HaikuPrintPage(webapp2.RequestHandler):
  def get(self):
    id = self.request.path.split('/')[2]
    haiku = memcache.get('haiku_' + id)
    if haiku is None:
      key = ndb.Key(*ndb.Key(urlsafe=id).flat())
      haiku = key.get().ToDict()
      memcache.add('haiku_' + id, haiku)
    template = JINJA_ENVIRONMENT.get_template('haiku-print.html')
    haiku_size = self.request.get('size', 600)
    haiku_width = self.request.get('width', haiku_size)
    haiku_height = self.request.get('height', haiku_size)
    self.response.out.write(template.render({
        'haiku': haiku,
        'haiku_width': haiku_width,
        'haiku_height': haiku_height,
    }))


class HaikuDumpPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-type'] = 'text/plain'
    cursorv = self.request.get('cursor', None)
    cursor = Cursor(urlsafe=cursorv)
    q = Haiku.query()
    haikus, next_cursor, more = q.fetch_page(40, start_cursor=cursor)
    if next_cursor:
      next_cursor = next_cursor.urlsafe()
    haikus = [h.ToJSDict() for h in haikus]
    self.response.out.write(json.dumps({
      'items': haikus,
      'cursor': next_cursor,
      'more': more,
      }, sort_keys=True, indent=2, separators=(',', ':')))


class HaikuAboutPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('haiku-about.html')
    self.response.out.write(template.render({
        'words': glossary.core_words,
    }))


class HaikuAnimatedPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('haiku-animated.html')
    self.response.out.write(template.render({
    }))


class HaikuInteractivePage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('haiku-interactive.html')
    self.response.out.write(template.render({
    }))


class HaikuSoundPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('haiku-sound.html')
    self.response.out.write(template.render({
    }))


class HaikuVotePage(webapp2.RequestHandler):
  def post(self):
    id = self.request.path.split('/')[2]
    if self.request.get('good'):
      vote = 1
    elif self.request.get('bad'):
      vote = -1
    else:
      vote = 0
    if vote in [1, -1]:
      key = ndb.Key(*ndb.Key(urlsafe=id).flat())
      haiku = key.get()
      haiku.score += vote
      haiku.rank += vote
      haiku.put()
    self.redirect('/')


class HaikuAdjustPage(webapp2.RequestHandler):
  def post(self):
    passwd = self.request.get('passwd')
    if not CheckPassword(passwd):
      return
    id = self.request.get('id')
    key = ndb.Key(*ndb.Key(urlsafe=id).flat())
    haiku = key.get()
    rank = self.request.get('rank', default_value=None)
    if rank is not None:
      haiku.rank = float(rank)
    parent = self.request.get('parent', default_value=None)
    if parent is not None:
      haiku.parent = parent
    haiku.put()


class HaikuUploadPage(webapp2.RequestHandler):
  def post(self):
    passwd = self.request.get('passwd')
    if not CheckPassword(passwd):
      return
    id = self.request.get('id')
    key = ndb.Key(*ndb.Key(urlsafe=id).flat())
    haiku = key.get()
    if haiku is None:
      haiku = Haiku(key=key)
    haiku.FromRequest(self.request)
    haiku.put()


class WordListPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('word-list.html')
    self.response.out.write(template.render({
        'words': glossary.core_words,
    }))


class WordViewPage(webapp2.RequestHandler):
  def get(self):
    name = self.request.path.split('/')[2]
    entry = glossary.LookupEntryById(name)
    assert entry
    template = JINJA_ENVIRONMENT.get_template('word-view.html')
    self.response.out.write(template.render({
        'entry': entry,
    }))


class HaikuSearchPage(webapp2.RequestHandler):
  def get(self):
    searchv = self.request.get('s', '')
    cursorv = self.request.get('cursor', None)
    options = search.QueryOptions(
        limit=40,
        cursor=search.Cursor(web_safe_string=cursorv),
        ids_only=True)
    query = search.Query(query_string=searchv, options=options)
    index = search.Index(name=SEARCH_INDEX)
    results = index.search(query)
  
    results_keys = [ndb.Key(*ndb.Key(urlsafe=i.doc_id).flat())
                    for i in results.results]
    haikus = ndb.get_multi(results_keys)
    haikus_list = [h.ToDict() for h in haikus]

    next_cursor = None
    if results.cursor:
      next_cursor = results.cursor.web_safe_string

    template = JINJA_ENVIRONMENT.get_template('haiku-search.html')
    self.response.out.write(template.render({
        'search': searchv,
        'haikus': haikus_list,
        'cursor': next_cursor,
    }))


class HaikuListPage(webapp2.RequestHandler):
  def get(self):
    order = self.request.get('order', '')
    if order != 'rank':
      order = 'age'
    cursorv = self.request.get('cursor', None)
    if order == 'rank':
      qorder = 'ORDER BY rank DESC'
      norder = 'rank'
    else:
      qorder = 'ORDER BY when DESC'
      norder = 'when'
    cursor = Cursor(urlsafe=cursorv)
    q = Haiku.gql(qorder)
    haikus, next_cursor, more = q.fetch_page(40, start_cursor=cursor)
    haikus = [h.ToDict() for h in haikus]

    if next_cursor:
      next_cursor = next_cursor.urlsafe()

    template = JINJA_ENVIRONMENT.get_template('haiku-list.html')
    self.response.out.write(template.render({
        'haikus': haikus,
        'order': order,
        'more': more,
        'cursor': next_cursor,
    }))


class HaikuEditorPage(webapp2.RequestHandler):
  def get(self):
    id = self.request.get('id')
    if id:
      key = ndb.Key(*ndb.Key(urlsafe=id).flat())
      haiku = key.get()
      title = haiku.title + ' Redux'
      code = haiku.code
    else:
      title = ''
      code = ''
    template = JINJA_ENVIRONMENT.get_template('haiku-editor.html')
    haiku_size = self.request.get('size', 256)
    haiku_width = self.request.get('width', haiku_size)
    haiku_height = self.request.get('height', haiku_size)
    self.response.out.write(template.render({
        'code': code,
        'title': title,
        'haiku_width': haiku_width,
        'haiku_height': haiku_height,
        'parent': id,
    }))


class HaikuSubmitPage(webapp2.RequestHandler):
  def post(self):
    title = self.request.get('title')
    if not title:
      title = 'Untitled'
    author = self.request.get('author')
    if not author:
      author = 'Anonymous'
    parent = self.request.get('parent', '')
    code = self.request.get('code', '')
    if ('href=' in code or
        'http://' in code or
        'https://' in code or
        code == '' or
        SPAM_RE.search(code) or
        SPAM_RE.search(title) or
        len(title) > 40 or
        SPAM_RE.search(author) or
        len(author) > 30 or
        HaikuWordCount(code) < 3):
      self.redirect('/')
      logging.info(
          'Rejected [%s] by [%s] as spam. Code: %s' % (title, author, code))
      return

    haiku = Haiku()
    haiku.title = title
    haiku.author = author
    haiku.code = code
    haiku.score = 0
    haiku.rank = 0.0
    haiku.parent = parent
    haiku.parent_recorded = True
    haiku.put()
    index = search.Index(name=SEARCH_INDEX)
    index.put(haiku.ToDocument())
    memcache.delete('main_items')
    self.redirect('/')


def ReindexHaikus(cursor=None, num_updated=0):
  query = Haiku.query()
  to_index = []
  items, next_cursor, more = query.fetch_page(50, start_cursor=cursor)
  for p in items:
    to_index.append(p.ToDocument())
  if to_index:
    num_updated += len(to_index)
    index = search.Index(name=SEARCH_INDEX)
    index.put(to_index)
    logging.debug('Indexed %d for total of %d', len(to_index), num_updated)
    deferred.defer(
        ReindexHaikus, cursor=next_cursor, num_updated=num_updated)
  else:
    logging.debug('Indexing complete')


class HaikuReindexPage(webapp2.RequestHandler):
  def get(self):
    deferred.defer(ReindexHaikus)
    logging.debug('Starting reindexing')


class MainPage(webapp2.RequestHandler):
  def get(self):
    main_items = memcache.get('main_items')
    if main_items is None:
      q = Haiku.gql('ORDER BY rank DESC')
      top_haikus = q.fetch(8)
      top_haikus = [h.ToDict() for h in top_haikus]
      q = Haiku.gql('ORDER BY when DESC')
      recent_haikus = q.fetch(8)
      recent_haikus = [h.ToDict() for h in recent_haikus]
      main_items = [top_haikus, recent_haikus]
      memcache.add('main_items', main_items, CACHE_TIMEOUT)
    else:
      top_haikus, recent_haikus = main_items

    template = JINJA_ENVIRONMENT.get_template('main.html')
    self.response.out.write(template.render({
        'top_haikus': top_haikus,
        'recent_haikus': recent_haikus,
    }))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/haiku-editor', HaikuEditorPage),
    ('/haiku-submit', HaikuSubmitPage),
    ('/haiku-list', HaikuListPage),
    ('/haiku-view/.*', HaikuViewPage),
    ('/haiku-bare/.*', HaikuBarePage),
    ('/haiku-print/.*', HaikuPrintPage),
    ('/haiku-vote/.*', HaikuVotePage),
    ('/haiku-adjust', HaikuAdjustPage),
    ('/haiku-upload', HaikuUploadPage),
    ('/haiku-about', HaikuAboutPage),
    ('/haiku-animated', HaikuAnimatedPage),
    ('/haiku-interactive', HaikuInteractivePage),
    ('/haiku-search', HaikuSearchPage),
    ('/haiku-sound', HaikuSoundPage),
    ('/haiku-slideshow', HaikuSlideshowPage),
    ('/haiku-dump', HaikuDumpPage),
    # Enable to allow reindexing.
    # ('/haiku-reindex', HaikuReindexPage),
    ('/word-list', WordListPage),
    ('/word-view/.*', WordViewPage),
], debug=False)
