import base64
import cgi
import os
import random
import re

import glossary

import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb


#JINJA_ENVIRONMENT = jinja2.Environment(
#    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
#    extensions=['jinja2.ext.autoescape'],
#    autoescape=True)
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


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


class Article(ndb.Model):
  when = ndb.DateTimeProperty(auto_now_add=True)
  title = ndb.StringProperty()
  summary = ndb.StringProperty()
  body = ndb.TextProperty()

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

  def ToDict(self):
    return {
        'id': self.key.urlsafe(),
        'when': self.when,
        'title': self.title,
        'author': self.author,
        'code': self.code,
        'score': self.score,
        'code_formatted': glossary.FormatHtml(self.code),
        'code_formatted_print': glossary.FormatHtmlPrint(self.code),
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
    haiku = ndb.Key(urlsafe=id).get()
    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 256),
    }))


class HaikuPrintPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    haiku = ndb.Key(urlsafe=id).get()
    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-print.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 600),
    }))


class HaikuSlideshowPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.gql('ORDER BY score DESC')
    haikus = q.fetch(int(self.request.get('limit', 1000)))
    haiku = haikus[random.randrange(len(haikus))]
    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-slideshow.html')
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
    haikus = q.fetch(int(self.request.get('limit', 1000)))
    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-slideshow2.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haikus': [h.ToDict() for h in haikus],
        'haiku_count': len(haikus),
        'haiku_size': self.request.get('size', 400),
        'speed': self.request.get('speed', 10),
    }))


class HaikuDumpPage(webapp2.RequestHandler):
  def get(self):
    q = Haiku.gql('ORDER BY score DESC')
    haikus = q.fetch(int(self.request.get('limit', 1000)))
    self.response.headers['Content-type'] = 'text/plain'
    for haiku in haikus:
      self.response.out.write('------------------------------------\n')
      self.response.out.write('Title: ' + haiku.title + '\n')
      self.response.out.write('Author: ' + haiku.author + '\n')
      self.response.out.write('Score: ' + str(haiku.score) + '\n')
      self.response.out.write('When: ' + str(haiku.when) + '\n')
      self.response.out.write('Code:\n' + haiku.code + '\n\n\n')


class HaikuAboutPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-about.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'words': glossary.core_words,
    }))


class HaikuAnimatedPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-animated.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
    }))


class HaikuSoundPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-sound.html')
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
    self.redirect('/')


class WordListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template(
        'templates/word-list.html')
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
    template = JINJA_ENVIRONMENT.get_template(
        'templates/word-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'entry': entry,
    }))


class ArticleViewPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    article = ndb.Key(urlsafe=id).get()
    template = JINJA_ENVIRONMENT.get_template(
        'templates/article-view.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'article': article.ToDict(),
    }))


class HaikuListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    if self.request.get('order', '') == 'score':
      q = Haiku.gql('ORDER BY score DESC')
    else:
      q = Haiku.gql('ORDER BY when DESC')
    haikus = q.fetch(1000)
    haikus = [h.ToDict() for h in haikus]

    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-list.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'haikus': haikus,
    }))


class ArticleListPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Article.gql('ORDER BY when DESC')
    articles = q.fetch(1000)
    articles = [a.ToDict() for a in articles]

    template = JINJA_ENVIRONMENT.get_template(
        'templates/article-list.html')
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
    template = JINJA_ENVIRONMENT.get_template(
        'templates/haiku-editor.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
        'code': code,
        'title': title,
        'haiku_size': self.request.get('size', 256),
    }))


class ArticleEditorPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    template = JINJA_ENVIRONMENT.get_template(
        'templates/article-editor.html')
    self.response.out.write(template.render({
        'login_status': LoginStatus(),
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

    article = Article()
    article.title = title
    article.summary = summary
    article.body = self.request.get('body', '') 
    article.put()
    self.redirect('/')


class BrowsersPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template(
        'templates/browsers.html')
    self.response.out.write(template.render({}))


class MainPage(webapp2.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.gql('ORDER BY score DESC')
    top_haikus = q.fetch(8)
    top_haikus = [h.ToDict() for h in top_haikus]
    q = Haiku.gql('ORDER BY when DESC')
    recent_haikus = q.fetch(8)
    recent_haikus = [h.ToDict() for h in recent_haikus]
    q = Article.gql('ORDER BY when DESC')
    recent_articles = q.fetch(5)
    recent_articles = [a.ToDict() for a in recent_articles]

    template = JINJA_ENVIRONMENT.get_template(
        'templates/main.html')
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
    ('/haiku-slideshow', HaikuSlideshowPage),
    ('/haiku-slideshow2', HaikuSlideshow2Page),
    ('/haiku-dump', HaikuDumpPage),
    ('/article-list', ArticleListPage),
    ('/article-view/.*', ArticleViewPage),
    ('/word-list', WordListPage),
    ('/word-view/.*', WordViewPage),
    ('/admin/article-editor', ArticleEditorPage),
    ('/admin/article-submit', ArticleSubmitPage),
], debug=False)
