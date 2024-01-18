import datetime
import json
import logging
import os
import random
import re
import time

import glossary

import jinja2
from flask import Flask, request, redirect

from google.cloud import datastore


CACHE_TIMEOUT = 120
SPAM_RE = re.compile('[A-Za-z0-9]{30}')
NUMBER_RE = re.compile('^[0-9eE.+-]+$')


class Memcache:
  def __init__(self):
    self.data = {}

  def get(self, key, default=None):
    item = self.data.get(key)
    if item is None:
      return default
    if item[1] < time.time():
      del self.data[key]
      return default
    else:
      return item[0]

  def add(self, key, value, timeout=None):
    if not timeout:
      timeout = 15
    timeout = time.time() + timeout
    self.data[key] = [value, timeout]

  def clear(self, key):
    if key in self.data:
      del self.data[key]


memcache = Memcache()
client = datastore.Client()


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')))


app = Flask(__name__)


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


#class Password(ndb.Model):
#  secret = ndb.StringProperty()


def CheckPassword(secret):
  passwd = memcache.get('passwd')
  if passwd:
    return secret == passwd
  q = client.query(kind='Password')
  items = q.fetch(limit=1)
  if len(items) == 0:
    p = datastore.Entity(client.key('Password'))
    p['secret'] = ''
    client.put(p)
    return False
  if len(items) != 1:
    return False
  if items[0].secret == '':
    return False
  memcache.add('passwd', items[0]['secret'])
  return secret == items[0]['secret']


#class Haiku(ndb.Model):
#  when = ndb.DateTimeProperty(auto_now_add=True)
#  title = ndb.StringProperty()
#  author = ndb.StringProperty()
#  code = ndb.TextProperty()
#  score = ndb.IntegerProperty()
#  rank = ndb.FloatProperty(default=0.0)
#  last_modified = ndb.DateTimeProperty(auto_now=True)
#  parent = ndb.StringProperty(default='')
#  parent_recorded = ndb.BooleanProperty(default=False)


def Now():
  #return datetime.datetime.now(tz=datetime.timezone.utc)
  return datetime.datetime.utcnow()


def GetId(haiku):
  return str(haiku.key.to_legacy_urlsafe(), 'ascii')


def ToBaseDict(haiku):
  return {
      'id': GetId(haiku),
      'title': haiku.get('title', 'Untitled'),
      'author': haiku.get('author', 'Unknown'),
      'code': haiku.get('code', ''),
      'score': haiku.get('score', 0),
      'rank': haiku.get('rank', 0),
      'parent': haiku.get('parent'),
      'parent_recorded': bool(haiku.get('parent_recorded', False)),
  }


def ToDict(haiku):
  haiku = ToBaseDict(haiku)
  haiku.update({
      'when': haiku.get('when', Now()),
      'code_formatted': glossary.FormatHtml(haiku.get('code', '')),
      'code_formatted_print': glossary.FormatHtmlPrint(haiku.get('code', '')),
  })
  return haiku


def ToJSDict(haiku):
  haiku = ToBaseDict(haiku)
  haiku.update({
      'when': FromDatetime(haiku.get('when', Now())),
      'last_modified': FromDatetime(haiku.get('last_modified', Now())),
  })
  return haiku


def FromRequest(src):
  haiku = datastore.Entity(client.key('Haiku'))
  haiku['when'] = ToDatetime(src.get('when'))
  haiku['last_modified'] = ToDatetime(src.get('last_modified'))
  haiku['title'] = src.get('title')
  haiku['author'] = src.get('author')
  haiku['code'] = src.get('code')
  haiku['score'] = int(src.get('score'))
  haiku['rank'] = float(src.get('rank'))
  haiku['parent'] = src.get('parent')
  haiku['parent_recorded'] = bool(src.get('parent_recorded', False))


def GetHaiku(id):
  haiku = memcache.get('haiku_' + id)
  if haiku is None:
    key = datastore.Key.from_legacy_urlsafe(id)
    haiku = ToDict(client.get(key))
    memcache.add('haiku_' + id, haiku)
  return haiku


@app.route("/haiku-view/<path:id>", methods=["GET"])
def HaikuViewPage(id):
  haiku = GetHaiku(id)
  parent_id = haiku.get('parent')
  parent = None
  if parent_id:
    parent = GetHaiku(parent_id)
  has_parent = parent is not None

  template = JINJA_ENVIRONMENT.get_template('haiku-view.html')
  return template.render({
      'haiku': haiku,
      'parent': parent,
      'has_parent': has_parent,
  })


def QueryList():
  limit = int(request.args.get('limit', 40))
  order = request.args.get('order', '')
  if order != 'rank':
    order = 'age'
  cursorv = request.args.get('cursor', None)
  q = client.query(kind='Haiku')
  if order == 'rank':
    q.order = ['-rank']
  else:
    q.order = ['-when']
  qiter = q.fetch(start_cursor=cursorv, limit=limit)
  haikus = list(next(qiter.pages))
  next_cursor = qiter.next_page_token
  more = next_cursor is not None
  if next_cursor is not None:
    next_cursor = str(next_cursor, 'ascii')
  haikus = [ToDict(h) for h in haikus]
  return (haikus, next_cursor, more, order, limit)


@app.route("/haiku-slideshow", methods=["GET"])
def HaikuSlideshowPage():
  haikus, next_cursor, more, order, limit = QueryList()
  template = JINJA_ENVIRONMENT.get_template('haiku-slideshow.html')
  haiku_size = request.args.get('size', 600)
  haiku_width = request.args.get('width', haiku_size)
  haiku_height = request.args.get('height', haiku_size)
  return template.render({
      'haikus': haikus,
      'haiku_count': len(haikus),
      'haiku_width': haiku_width,
      'haiku_height': haiku_height,
      'order': order,
      'more': more,
      'cursor': next_cursor,
      'limit': limit,
  })


@app.route("/haiku-bare/<path:id>", methods=["GET"])
def HaikuBarePage(id):
  haiku = GetHaiku(id)
  template = JINJA_ENVIRONMENT.get_template('haiku-bare.html')
  audio_button = int(request.args.get('audio', 0))
  return template.render({
      'haiku': haiku,
      'audio_button': audio_button,
  })


@app.route("/haiku-print/<path:id>", methods=["GET"])
def HaikuPrintPage(id):
  haiku = GetHaiku(id)
  template = JINJA_ENVIRONMENT.get_template('haiku-print.html')
  return template.render({
      'haiku': haiku,
  })


@app.route("/haiku-dump", methods=["GET"])
def HaikuDumpPage():
  cursorv = request.args.get('cursor', None)
  cursor = Cursor(urlsafe=cursorv)
  q = Haiku.query()
  haikus, next_cursor, more = q.fetch_page(40, start_cursor=cursor)
  if next_cursor:
    next_cursor = next_cursor.urlsafe()
  haikus = [ToJSDict(h) for h in haikus]
  return (
      json.dumps({
        'items': haikus,
        'cursor': next_cursor,
        'more': more,
        }, sort_keys=True, indent=2, separators=(',', ':')),
      200, {'Content-type': 'text/plain'})


@app.route("/haiku-about", methods=["GET"])
def HaikuAboutPage():
  template = JINJA_ENVIRONMENT.get_template('haiku-about.html')
  return template.render({
      'words': glossary.core_words,
  })


@app.route("/haiku-animted", methods=["GET"])
def HaikuAnimatedPage():
  template = JINJA_ENVIRONMENT.get_template('haiku-animated.html')
  return template.render({})


@app.route("/haiku-camera", methods=["GET"])
def HaikuCameraPage():
  template = JINJA_ENVIRONMENT.get_template('haiku-camera.html')
  return template.render({})


@app.route("/haiku-interactive", methods=["GET"])
def HaikuInteractivePage():
  template = JINJA_ENVIRONMENT.get_template('haiku-interactive.html')
  return template.render({})


@app.route("/haiku-sound", methods=["GET"])
def HaikuSoundPage():
  template = JINJA_ENVIRONMENT.get_template('haiku-sound.html')
  return template.render({})


@app.route("/haiku-vote/<path:id>", methods=["POST"])
def HaikuVotePage(id):
  if request.args.get('good'):
    vote = 1
  elif request.args.get('bad'):
    vote = -1
  else:
    vote = 0
  if vote in [1, -1]:
    key = datastore.Key.from_legacy_urlsafe(id)
    haiku = client.get(key)
    haiku['score'] += vote
    haiku['rank'] += vote
    haiku['last_modified'] = Now()
    client.put(haiku)
  return redirect('/')


@app.route("/haiku-adjust", methods=["POST"])
def HaikuAdjustPage():
  passwd = request.args.get('passwd')
  if not CheckPassword(passwd):
    return
  id = request.args.get('id')
  key = datastore.Key.from_legacy_urlsafe(id)
  haiku = client.get(key)
  rank = request.args.get('rank', default_value=None)
  if rank is not None:
    haiku['rank'] = float(rank)
    haiku['last_modified'] = Now()
  parent = request.args.get('parent', default_value=None)
  if parent is not None:
    haiku['parent'] = parent
    haiku['last_modified'] = Now()
  client.put(haiku)


@app.route("/haiku-upload", methods=["POST"])
def HaikuUploadPage():
  passwd = request.args.get('passwd')
  if not CheckPassword(passwd):
    return
  id = request.args.get('id')
  key = datastore.Key.from_legacy_urlsafe(id)
  haiku = client.get(key)
  if haiku is None:
    haiku = datastore.Entity(client.key('Haiku'))
  haiku.FromRequest(request)
  client.put(haiku)


@app.route("/word-list", methods=["GET"])
def WordListPage():
  template = JINJA_ENVIRONMENT.get_template('word-list.html')
  return template.render({
      'words': glossary.core_words,
  })


@app.route("/word-view/<path:name>", methods=["GET"])
def WordViewPage(name):
  name = request.path.split('/')[2]
  entry = glossary.LookupEntryById(name)
  assert entry
  template = JINJA_ENVIRONMENT.get_template('word-view.html')
  return template.render({
      'entry': entry,
  })


def QuerySearch(field):
  searchv = request.args.get('s', '')
  cursorv = request.args.get('cursor', None)
  q = client.query(kind='Haiku')
  q.add_filter(field, '>=', searchv)
  q.add_filter(field, '<', searchv + '\uffff')
  qiter = q.fetch(start_cursor=cursorv, limit=100)
  haikus = list(next(qiter.pages))
  next_cursor = qiter.next_page_token
  more = next_cursor is not None
  if next_cursor is not None:
    next_cursor = str(next_cursor, 'ascii')
  return haikus, next_cursor, more


@app.route("/haiku-search", methods=["GET"])
def HaikuSearchPage():
  searchv = request.args.get('s', '')
  haikus_author, next_author, _ = QuerySearch('author')
  haikus_title, next_title, _ = QuerySearch('title')

  haikus = haikus_title + haikus_author
  haikus = [ToDict(h) for h in haikus]
  next_cursor = next_author
  if next_cursor is None:
    next_cursor = next_title

  template = JINJA_ENVIRONMENT.get_template('haiku-search.html')
  return template.render({
      'search': searchv,
      'haikus': haikus,
      'cursor': next_cursor,
  })


@app.route("/haiku-list", methods=["GET"])
def HaikuListPage():
  haikus, next_cursor, more, order, _ = QueryList()
  template = JINJA_ENVIRONMENT.get_template('haiku-list.html')
  return template.render({
      'haikus': haikus,
      'order': order,
      'more': more,
      'cursor': next_cursor,
  })


@app.route("/haiku-editor", methods=["GET"])
def HaikuEditorPage():
  id = request.args.get('id')
  if id:
    haiku = GetHaiku(id)
    title = haiku['title'] + ' Redux'
    code = haiku['code']
  else:
    title = ''
    code = ''
  template = JINJA_ENVIRONMENT.get_template('haiku-editor.html')
  return template.render({
      'code': code,
      'title': title,
      'parent': id,
  })


@app.route("/haiku-submit", methods=["POST"])
def HaikuSubmitPage():
  title = request.args.get('title')
  if not title:
    title = 'Untitled'
  author = request.args.get('author')
  if not author:
    author = 'Anonymous'
  parent = request.args.get('parent', '')
  code = request.args.get('code', '')
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
    logging.info(
        'Rejected [%s] by [%s] as spam. Code: %s' % (title, author, code))
    return redirect('/')

  p = datastore.Entity(client.key('Haiku'))
  haiku['title'] = title
  haiku['author'] = author
  haiku['code'] = code
  haiku['score'] = 0
  haiku['rank'] = 0.0
  haiku['parent'] = parent
  haiku['parent_recorded'] = True
  haiku['when'] = Now()
  haiku['last_modified'] = Now()
  client.put(haiku)
  memcache.clear('main_items')
  return redirect('/')


@app.route("/", methods=["GET"])
def MainPage():
  main_items = memcache.get('main_items')
  if main_items is None:
    q = client.query(kind='Haiku')
    q.order = ['-rank']
    top_haikus = q.fetch(8)
    top_haikus = [ToDict(h) for h in top_haikus]
    q = client.query(kind='Haiku')
    q.order = ['-when']
    recent_haikus = q.fetch(8)
    recent_haikus = [ToDict(h) for h in recent_haikus]
    main_items = [top_haikus, recent_haikus]
    memcache.add('main_items', main_items, CACHE_TIMEOUT)
  else:
    top_haikus, recent_haikus = main_items

  template = JINJA_ENVIRONMENT.get_template('main.html')
  return template.render({
      'top_haikus': top_haikus,
      'recent_haikus': recent_haikus,
  })
