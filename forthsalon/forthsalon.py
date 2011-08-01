import base64
import cgi
import os
import random
import re

import glossary

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


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


class Article(db.Model):
  when = db.DateTimeProperty(auto_now_add=True)
  title = db.StringProperty()
  summary = db.StringProperty()
  body = db.TextProperty()

  def ToDict(self):
    return {
        'id': self.key(),
        'when': self.when,
        'title': self.title,
        'summary': self.summary,
        'body': self.body,
    }


class Haiku(db.Model):
  when = db.DateTimeProperty(auto_now_add=True)
  title = db.StringProperty()
  author = db.StringProperty()
  code = db.TextProperty()
  score = db.IntegerProperty()

  def ToDict(self):
    return {
        'id': self.key(),
        'when': self.when,
        'title': self.title,
        'author': self.author,
        'code': self.code,
        'score': self.score,
        'code_formatted': glossary.FormatHtml(self.code),
        'code_formatted_print': glossary.FormatHtmlPrint(self.code),
    }


class HaikuSnapshot(db.Model):
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  image = db.BlobProperty()


def LoginStatus():
  user = users.get_current_user()
  if not user:
    return '<a href="' + users.create_login_url('/') + '">Sign in</a>'
  elif users.is_current_user_admin():
    return ('<a href="/admin/article-editor">Article Editor</a> '
            '<a href="' + users.create_logout_url('/') + '">Sign out</a>')
  else:
    return '<a href="' + users.create_logout_url('/') + '">Sign out</a>'


class HaikuViewPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    haiku = Haiku.get(db.Key(id))
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-view.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 256),
    }))


class HaikuPrintPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    haiku = Haiku.get(db.Key(id))
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-print.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 600),
    }))


class HaikuSlideshowPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    haikus = Haiku.all().fetch(1000)
    haiku = haikus[random.randrange(len(haikus))]
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-slideshow.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'haiku': haiku.ToDict(),
        'haiku_size': self.request.get('size', 400),
        'speed': self.request.get('speed', 15),
    }))


class HaikuSlideshow2Page(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.gql('ORDER BY score DESC')
    haikus = q.fetch(int(self.request.get('limit', 1000)))
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-slideshow2.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'haikus': [h.ToDict() for h in haikus],
        'haiku_count': len(haikus),
        'haiku_size': self.request.get('size', 400),
        'speed': self.request.get('speed', 10),
    }))


class HaikuDumpPage(webapp.RequestHandler):
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


class HaikuAboutPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-about.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'words': glossary.core_words,
    }))


class HaikuAnimatedPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-animated.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
    }))


class HaikuSoundPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-sound.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
    }))


class HaikuVotePage(webapp.RequestHandler):
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
      haiku = Haiku.get(db.Key(id))
      haiku.score += vote
      haiku.put()
    self.redirect('/')


class WordListPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'word-list.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'words': glossary.core_words,
    }))


class WordViewPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    name = self.request.path.split('/')[2]
    entry = glossary.LookupEntryById(name)
    assert entry
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'word-view.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'entry': entry,
    }))


class ArticleViewPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.path.split('/')[2]
    article = Article.get(db.Key(id))
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'article-view.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'article': article.ToDict(),
    }))


class HaikuListPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    if self.request.get('order', '') == 'score':
      q = Haiku.gql('ORDER BY score DESC')
    else:
      q = Haiku.gql('ORDER BY when DESC')
    haikus = q.fetch(1000)
    haikus = [h.ToDict() for h in haikus]

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-list.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'haikus': haikus,
    }))


class ArticleListPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Article.gql('ORDER BY when DESC')
    articles = q.fetch(1000)
    articles = [a.ToDict() for a in articles]

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'article-list.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'articles': articles,
    }))


class HaikuEditorPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    id = self.request.get('id')
    if id:
      haiku = Haiku.get(db.Key(id))
      title = haiku.title + ' Redux'
      code = haiku.code
    else:
      title = ''
      code = ''
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-editor.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'code': code,
        'title': title,
        'haiku_size': self.request.get('size', 256),
    }))


class ArticleEditorPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'article-editor.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
    }))


class HaikuSubmitPage(webapp.RequestHandler):
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


class HaikuUploadSnapshotPage(webapp.RequestHandler):
  data_pattern = re.compile('data:image/(png|jpeg);base64,(.*)$')

  def post(self):
    if BrowserRedirect(self): return

    id = self.reqest.get('id')
    width = self.request.get('width')
    height = self.request.get('height')
    
    image = self.request.get('image')
    image = self.data_pattern.match(image).group(2)
    if image is None and len(image) > 0:
      return
    image = db.Blob(base64.b64decode(image))

    snap = HaikuSnapshot.gql('WHERE ancestor=:1 and width=:2 and height=:3',
                             db.Key(id), width, height).get()
    if not snap:
      snap = HaikuSnapshot(parent=db.Key(id))

    snap.width = width
    snap.height = height
    snap.image = image
    snap.put()


class HaikuSweepPage(webapp.RequestHandler):
  def get(self):
    if BrowserRedirect(self): return

    q = Haiku.all()
    haikus = q.fetch(1000)
    haikus = [h.ToDict() for h in haikus]

    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'haiku-sweep.html')
    self.response.out.write(template.render(path, {
        'haikus': haikus,
    }))


class ArticleSubmitPage(webapp.RequestHandler):
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


class BrowsersPage(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__),
                        'templates', 'browsers.html')
    self.response.out.write(template.render(path, {}))


class MainPage(webapp.RequestHandler):
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

    path = os.path.join(os.path.dirname(__file__), 'templates', 'main.html')
    self.response.out.write(template.render(path, {
        'login_status': LoginStatus(),
        'top_haikus': top_haikus,
        'recent_haikus': recent_haikus,
        'recent_articles': recent_articles,
    }))


application = webapp.WSGIApplication([
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
    ('/admin/haiku-upload-snapshot', HaikuUploadSnapshotPage),
    ('/admin/haiku-sweep', HaikuSweepPage),
], debug=False)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
