import datetime
import json
import os
import random

import glossary

import jinja2
import webapp2

from google.appengine.api import memcache
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
from google.appengine.api import users

CACHE_TIMEOUT = 120


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')))


def IsAgentOk(request):
  user_agent = request.headers.get('User-Agent', '').lower()
  return ('safari' in user_agent or
          'chrome' in user_agent or
          'chromium' in user_agent or
          'android' in user_agent or
          'firefox' in user_agent or
          'gecko' in user_agent or
          'iceweasel' in user_agent or
          'webkit' in user_agent)


def BrowserRedirect(handler):
  if not IsAgentOk(handler.request):
    handler.redirect('/browsers')
    return True
  return False


def ToDatetime(s):
  # From a Date in JS do: new String(dt.getTime()).
  return datetime.datetime.utcfromtimestamp(float(s) / 1000.0)

  
def FromDatetime(dt):
  # To get a JS data do: new Date(s).
  epoch = datetime.datetime.utcfromtimestamp(0)
  return str((dt - epoch).total_seconds() * 1000.0)


class Article(ndb.Model):
  when = ndb.DateTimeProperty(auto_now_add=True)
  title = ndb.StringProperty()
  summary = ndb.StringProperty()
  body = ndb.TextProperty()
  last_modified = ndb.DateTimeProperty(auto_now=True)

  def ToDict(self):
    return {
        'id': self.key.urlsafe(),
        'when': self.when,
        'title': self.title,
        'summary': self.summary,
        'body': self.body,
    }


class Haiku(ndb.Model):
  when = ndb.DateTimeProperty(auto_now_add=True)
  title = ndb.StringProperty()
  author = ndb.StringProperty()
  code = ndb.TextProperty()
  score = ndb.IntegerProperty()
  last_modified = ndb.DateTimeProperty(auto_now=True)

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
        'code_formatted': glossary.FormatHtml(self.code),
        'code_formatted_print': glossary.FormatHtmlPrint(self.code),
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
    }


def LoginStatus():
  user = users.get_current_user()
  if not user:
    return '<a href="' + users.create_login_url('/') + '">Sign in</a>'
  elif users.is_current_user_admin():
    return ('<a href="/admin/article-editor">Article Editor</a> '
            '<a href="' + users.create_logout_url('/') + '">Sign out</a>')
  else:
    return '<a href="' + users.create_logout_url('/') + '">Sign out</a>'


class HaikuViewPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    haiku = memcache.get('haiku_' + id)
    if haiku is None:
      haiku = ndb.Key(urlsafe=id).get().ToDict()
      memcache.add('haiku_' + id, haiku)
    template = JINJA_ENVIRONMENT.get_template('haiku-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haiku': haiku,
        'haiku_size': self.request.get('size', 256),
    }))


class HaikuPrintPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    haiku = memcache.get('haiku_' + id)
    if haiku is None:
      haiku = ndb.Key(urlsafe=id).get().ToDict()
      memcache.add('haiku_' + id, haiku)
    template = JINJA_ENVIRONMENT.get_template('haiku-print.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haiku': haiku,
        'haiku_size': self.request.get('size', 600),
    }))


class HaikuSlideshowPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.gql('ORDER BY score DESC')
    haikus = q.fetch(int(self.request.get('limit', 200)))
    haiku = haikus[random.randrange(len(haikus))]
    template = JINJA_ENVIRONMENT.get_template('haiku-slideshow.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 400),
        'speed': self.request.get('speed', 15),
    }))


class HaikuSlideshow2Page(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.gql('ORDER BY score DESC')
    haikus = memcache.get('slideshow2')
    if haikus is None:
      haikus = q.fetch(int(self.request.get('limit', 200)))
      haikus = [h.ToDict() for h in haikus]
      memcache.add('slideshow2', haikus, CACHE_TIMEOUT)
    template = JINJA_ENVIRONMENT.get_template('haiku-slideshow2.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haikus': haikus,
        'haiku_count': len(haikus),
        'haiku_size': self.request.get('size', 400),
        'speed': self.request.get('speed', 10),
    }))


class HaikuDumpPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-type'] = 'text/plain'
    start = ToDatetime(self.request.get('start', '0'))
    q = Haiku.gql('WHERE when >= :1 ORDER BY when', start)
    haikus = q.fetch(int(self.request.get('limit', 100)))
    content = []
    for haiku in haikus:
      content.append('------------------------------------\n')
      content.append('ID: ' + haiku.GetId() + '\n')
      content.append('Title: ' + haiku.title + '\n')
      content.append('Author: ' + haiku.author + '\n')
      content.append('Score: ' + str(haiku.score) + '\n')
      content.append('When: ' + str(haiku.when) + '\n')
      content.append('Code:\n' + haiku.code + '\n\n\n')
    content = ''.join(content)
    self.response.out.write(content)


class HaikuFetchPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-type'] = 'text/plain'
    item_id = self.request.get('id')
    if item_id:
      haikus = [ndb.Key(urlsafe=item_id).get().ToDict()]
    else:
      start = ToDatetime(self.request.get('start', '0'))
      q = Haiku.gql('where last_modified > :1 ORDER BY last_modified',
                    start)
      haikus = q.fetch(int(self.request.get('limit', 40)))
    content = []
    for haiku in haikus:
      content.append(haiku.ToJSDict())
    self.response.out.write(json.dumps(content))


class HaikuSweepPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-type'] = 'text/plain'
    q = Haiku.gql('ORDER BY last_modified')
    haikus = q.fetch(50)
    count = 0
    for haiku in haikus:
      if haiku.last_modified is None:
        count += 1
        if count > 50:
          break
        haiku.put()
    self.response.out.write(str(count))


class HaikuAboutPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template('haiku-about.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'words': glossary.core_words,
    }))


class HaikuAnimatedPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template('haiku-animated.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
    }))


class HaikuSoundPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template('haiku-sound.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
    }))


class HaikuVotePage(webapp2.RequestHandler):
  def post(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    if self.request.get('good'):
      vote = 1
    elif self.request.get('bad'):
      vote = -1
    else:
      vote = 0
    if vote in [1, -1]:
      haiku = ndb.Key(urlsafe=id).get()
      haiku.score += vote
      haiku.put()
           
    self.response.out.write(content)
    self.redirect('/')


class WordListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template('word-list.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'words': glossary.core_words,
    }))


class WordViewPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    name = self.request.path.split('/')[2]
    entry = glossary.LookupEntryById(name)
    assert entry
    template = JINJA_ENVIRONMENT.get_template('word-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'entry': entry,
    }))


class ArticleViewPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    article = ndb.Key(urlsafe=id).get()
    template = JINJA_ENVIRONMENT.get_template('article-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'article': article.ToDict(),
        'is_admin': users.is_current_user_admin(),
    }))


class HaikuListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    order = self.request.get('order', '')
    if order != 'score':
      order = 'age'
    cursorv = self.request.get('cursor', '')
    if order == 'score':
      qorder = 'ORDER BY score DESC'
      norder = 'score'
    else:
      qorder = 'ORDER BY when DESC'
      norder = 'when'
    cursor = Cursor(urlsafe=cursorv)
    q = Haiku.gql(qorder)
    haikus, next_cursor, more = q.fetch_page(40, start_cursor=cursor)
    haikus = [h.ToDict() for h in haikus]

    template = JINJA_ENVIRONMENT.get_template('haiku-list.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haikus': haikus,
        'order': order,
        'more': more,
        'cursor': next_cursor.urlsafe(),
    }))


class ArticleListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Article.gql('ORDER BY when DESC')
    articles = q.fetch(200)
    articles = [a.ToDict() for a in articles]

    template = JINJA_ENVIRONMENT.get_template('article-list.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'articles': articles,
    }))


class HaikuEditorPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.get('id')
    if id:
      haiku = ndb.Key(urlsafe=id).get()
      title = haiku.title + ' Redux'
      code = haiku.code
    else:
      title = ''
      code = ''
    template = JINJA_ENVIRONMENT.get_template('haiku-editor.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'code': code,
        'title': title,
        'haiku_size': self.request.get('size', 256),
    }))


class ArticleEditorPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template('article-editor.html')
    item_id = self.request.get('id', '')
    if item_id:
      article = ndb.Key(urlsafe=item_id).get()
      self.response.out.write(template.render({
          'login_status': LoginStatus(),
          'article': article.ToDict(),
      }))
    else:      
      self.response.out.write(template.render({
          'login_status': LoginStatus(),
          'article': {
              'id': '',
              'title': '',
              'summary': '',
              'body': '',
          },
      }))


class HaikuSubmitPage(webapp2.RequestHandler):
  def post(self):
    if BrowserRedirect(self): return

    title = self.request.get('title')
    if not title:
      title = 'Untitled'
    author = self.request.get('author')
    if not author:
      author = 'Anonymous'

    haiku = Haiku()
    haiku.title = title
    haiku.author = author
    haiku.code = self.request.get('code', '')
    haiku.score = 0
    haiku.put()
    self.redirect('/')


class ArticleSubmitPage(webapp2.RequestHandler):
  def post(self):
    if BrowserRedirect(self): return

    title = self.request.get('title')
    if not title:
      title = 'Untitled'
    summary = self.request.get('summary')
    if not summary:
      title = 'No summary.'

    item_id = self.request.get('id')
    if item_id:
      article = ndb.Key(urlsafe=item_id).get()
    else:
      article = Article()
    article.title = title
    article.summary = summary
    article.body = self.request.get('body', '') 
    article.put()
    self.redirect('/')


class BrowsersPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('browsers.html')
    self.response.out.write(template.render({}))


class MainPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    main_items = memcache.get('main_items')
    if main_items is None:
      q = Haiku.gql('ORDER BY score DESC')
      top_haikus = q.fetch(8)
      top_haikus = [h.ToDict() for h in top_haikus]
      q = Haiku.gql('ORDER BY when DESC')
      recent_haikus = q.fetch(8)
      recent_haikus = [h.ToDict() for h in recent_haikus]
      q = Article.gql('ORDER BY when DESC')
      recent_articles = q.fetch(5)
      recent_articles = [a.ToDict() for a in recent_articles]
      main_items = [top_haikus, recent_haikus, recent_articles]
      memcache.add('main_items', main_items, CACHE_TIMEOUT)
    else:
      top_haikus, recent_haikus, recent_articles = main_items

    template = JINJA_ENVIRONMENT.get_template('main.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'top_haikus': top_haikus,
        'recent_haikus': recent_haikus,
        'recent_articles': recent_articles,
    }))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/browsers', BrowsersPage),
    ('/haiku-editor', HaikuEditorPage),
    ('/haiku-submit', HaikuSubmitPage),
    ('/haiku-list', HaikuListPage),
    ('/haiku-view/.*', HaikuViewPage),
    ('/haiku-print/.*', HaikuPrintPage),
    ('/haiku-vote/.*', HaikuVotePage),
    ('/haiku-about', HaikuAboutPage),
    ('/haiku-animated', HaikuAnimatedPage),
    ('/haiku-sound', HaikuSoundPage),
    ('/haiku-slideshow', HaikuSlideshow2Page),
    ('/haiku-slideshow2', HaikuSlideshow2Page),
    ('/haiku-dump', HaikuDumpPage),
    ('/haiku-fetch', HaikuFetchPage),
#    ('/haiku-sweep', HaikuSweepPage),
    ('/article-list', ArticleListPage),
    ('/article-view/.*', ArticleViewPage),
    ('/word-list', WordListPage),
    ('/word-view/.*', WordViewPage),
    ('/admin/article-editor', ArticleEditorPage),
    ('/admin/article-submit', ArticleSubmitPage),
], debug=False)
