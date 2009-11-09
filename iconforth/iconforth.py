import datetime
import re
import os
import sys
import StringIO
import pngcanvas
import random
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class Word(db.Model):
  icon = db.BlobProperty()
  description = db.StringProperty(multiline=True)
  definition = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  accessed = db.DateTimeProperty(auto_now_add=True)
  indexed = db.DateTimeProperty(auto_now_add=True)
  author = db.StringProperty()
  version = db.IntegerProperty(default=1)
  intrinsic = db.IntegerProperty(default=0)
  words_used = db.StringListProperty()
  keywords = db.StringListProperty()
  score = db.FloatProperty(default=0.0)


colors = [
  [0xff, 0xff, 0xff, 0xff],
  [0x00, 0x00, 0x00, 0xff],
  [0xff, 0x00, 0x00, 0xff],
  [0xff, 0xcc, 0x00, 0xff],
  [0xff, 0xff, 0x00, 0xff],
  [0x00, 0xff, 0x00, 0xff],
  [0x00, 0xff, 0xff, 0xff],
  [0x00, 0x00, 0xff, 0xff],
  [0xff, 0x00, 0xff, 0xff],
];


# From http://github.com/DocSavage/bloog/blob/master/models/search.py
# Apache license.
STOP_WORDS = frozenset([
   'a', 'about', 'according', 'accordingly', 'affected', 'affecting', 'after',
   'again', 'against', 'all', 'almost', 'already', 'also', 'although',
   'always', 'am', 'among', 'an', 'and', 'any', 'anyone', 'apparently', 'are',
   'arise', 'as', 'aside', 'at', 'away', 'be', 'became', 'because', 'become',
   'becomes', 'been', 'before', 'being', 'between', 'both', 'briefly', 'but',
   'by', 'came', 'can', 'cannot', 'certain', 'certainly', 'could', 'did', 'do',
   'does', 'done', 'during', 'each', 'either', 'else', 'etc', 'ever', 'every',
   'following', 'for', 'found', 'from', 'further', 'gave', 'gets', 'give',
   'given', 'giving', 'gone', 'got', 'had', 'hardly', 'has', 'have', 'having',
   'here', 'how', 'however', 'i', 'if', 'in', 'into', 'is', 'it', 'itself',
   'just', 'keep', 'kept', 'knowledge', 'largely', 'like', 'made', 'mainly',
   'make', 'many', 'might', 'more', 'most', 'mostly', 'much', 'must', 'nearly',
   'necessarily', 'neither', 'next', 'no', 'none', 'nor', 'normally', 'not',
   'noted', 'now', 'obtain', 'obtained', 'of', 'often', 'on', 'only', 'or',
   'other', 'our', 'out', 'owing', 'particularly', 'past', 'perhaps', 'please',
   'poorly', 'possible', 'possibly', 'potentially', 'predominantly', 'present',
   'previously', 'primarily', 'probably', 'prompt', 'promptly', 'put',
   'quickly', 'quite', 'rather', 'readily', 'really', 'recently', 'regarding',
   'regardless', 'relatively', 'respectively', 'resulted', 'resulting',
   'results', 'said', 'same', 'seem', 'seen', 'several', 'shall', 'should',
   'show', 'showed', 'shown', 'shows', 'significantly', 'similar', 'similarly',
   'since', 'slightly', 'so', 'some', 'sometime', 'somewhat', 'soon',
   'specifically', 'state', 'states', 'strongly', 'substantially',
   'successfully', 'such', 'sufficiently', 'than', 'that', 'the', 'their',
   'theirs', 'them', 'then', 'there', 'therefore', 'these', 'they', 'this',
   'those', 'though', 'through', 'throughout', 'to', 'too', 'toward', 'under',
   'unless', 'until', 'up', 'upon', 'use', 'used', 'usefully', 'usefulness',
   'using', 'usually', 'various', 'very', 'was', 'we', 'were', 'what', 'when',
   'where', 'whether', 'which', 'while', 'who', 'whose', 'why', 'widely',
   'will', 'with', 'within', 'without', 'would', 'yet', 'you'])


def ValidKeyword(word):
  return len(word) >= 3 and word not in STOP_WORDS


def FindKeywords(str):
  ret = set()
  word = ''
  for ch in str:
    if ((ch >= 'A' and ch <= 'Z') or
        (ch >= 'a' and ch <= 'z') or
        (ch >= '0' and ch <= '9')):
      word += ch.lower()
    else:
      if ValidKeyword(word):
        ret.add(word)
      word = ''
  if ValidKeyword(word):
    ret.add(word)
  return list(ret)


class ReadWord(webapp.RequestHandler):
  def get(self):
    id = self.request.path[6:]
    w = Word.get(id)
    if w:
      # Update access time.
      w.accessed = datetime.datetime.now()
      w.put()
      # Find users of this word.
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'WHERE words_used=:1 '
                          'ORDER BY score DESC, created DESC', str(w.key()))
      words_used = query.fetch(1000)
      if not words_used:
        words_used = []
      # Prepare definition.
      if w.definition == '':
        definition = []
      else:
        definition = w.definition.split(' ')
      # Output info on word.
      path = os.path.join(os.path.dirname(__file__), 'html/read.html')
      self.response.out.write(template.render(path, {
          'id': id,
          'description': w.description,
          'definition': definition,
          'created': str(w.created),
          'author': w.author,
          'words_used': words_used,
      }))
    else:
      path = os.path.join(os.path.dirname(__file__), 'html/read_notfound.html')
      self.response.out.write(template.render(path, {}))


class DumpWord(webapp.RequestHandler):
  def get(self):
    lookup_id = self.request.path[6:]
    results = []
    pending_ids = [lookup_id]
    needed_ids = set([lookup_id])
    emitted_ids = 0
    while pending_ids and emitted_ids < 100:
      # Pick one.
      id = pending_ids[0]
      pending_ids = pending_ids[1:]
      # Fetch it.
      w = Word.get(id)
      if w:
        # Update access time.
        w.accessed = datetime.datetime.now()
        w.put()
        # Convert definition to a list.
        if w.definition:
          definition = w.definition.split(' ')
        else:
          definition = []
        # Collect each word.
        results.append({
            'id': id,
            'intrinsic': w.intrinsic,
            'definition': definition,
            'description': w.description,
        })
        # Add new words needed.
        if w.definition:
          for cw in definition:
            if cw not in needed_ids:
              needed_ids.add(cw)
              pending_ids.append(cw)
      # Count how many we've emitted.
      emitted_ids += 1
    if self.request.get('raw'):
      self.response.headers['Content-Type'] = 'text/plain'
      for r in results:
        self.response.out.write('%s %d %s\n' % (
            r['id'], r['intrinsic'], ' '.join(r['definition'])))
    else:
      path = os.path.join(os.path.dirname(__file__), 'html/dump.html')
      self.response.out.write(template.render(path, {
          'results': results,
      }))


class RunWord(webapp.RequestHandler):
  def get(self):
    id = self.request.path[5:]
    path = os.path.join(os.path.dirname(__file__), 'html/run.html')
    self.response.out.write(template.render(path, {
        'id': id,
    }))


class Results(webapp.RequestHandler):
  def get(self):
    # Do a query.
    goal = self.request.get('q').lower()
    if goal:
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'WHERE keywords = :1 '
                          'ORDER BY score DESC, created DESC', goal)
    else:
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'ORDER BY score DESC, created DESC')
    w = query.fetch(1000)
    if not w:
      w = []
    # Display results.
    path = os.path.join(os.path.dirname(__file__), 'html/results.html')
    self.response.out.write(template.render(path, {
        'query': goal,
        'results': [str(i) for i in w],
    }))


class ReadIcon(webapp.RequestHandler):
  def get(self):
    self.response.headers['Cache-Control'] = 'public, max-age=86400'
    self.response.headers['Content-Type'] = 'image/png'
    c = pngcanvas.PNGCanvas(16, 16)
    id = self.request.path[6:-4]
    try:
      w = Word.get(id)
    except:
      w = None
    if w:
      data = w.icon
      for y in range(0, 16):
        for x in range(0, 16):
          z = x + y * 16
          if z < len(data):
            c.color = colors[int(data[z])]
          c.rectangle(x, y, x+1, y+1)
    else:
      c.verticalGradient(0, 0, c.width-1, c.height-1,
                        [0xff,0,0,0xff],
                        [0x20,0,0xff,0x80])
    self.response.out.write(c.dump())


class WriteWord(webapp.RequestHandler):
  def post(self):
    # Extract description + intrinsic.
    description = self.request.get('description')
    m = re.match('^~~~intrinsic: ([0-9]+)~~~(.*)$', description)
    if m:
      intrinsic = int(m.group(1))
      description = m.group(2)
    else:
      intrinsic = 0
    # Add word to the editor.
    w = Word()
    w.icon = str(self.request.get('icon'))
    w.description = description
    w.definition = self.request.get('definition')
    w.intrinsic = intrinsic
    w.author = self.request.remote_addr
    w.words_used = list(set(self.request.get('definition').split(' ')))
    w.keywords = FindKeywords(description)
    w.put()
    # Go back to the editor.
    self.redirect('/')


class MainPage(webapp.RequestHandler):
  def get(self):
    agent = self.request.headers.get('USER_AGENT', '')
    if agent.find('MSIE') >= 0 and agent.find('chromeframe') < 0:
      path = os.path.join(os.path.dirname(__file__), 'html/chrome_frame.html')
    else:
      path = os.path.join(os.path.dirname(__file__), 'html/editor.html')
    self.response.out.write(template.render(path, {}))


def main():
  application = webapp.WSGIApplication([
      ('/', MainPage),
      ('/read/.*', ReadWord),
      ('/dump/.*', DumpWord),
      ('/run/.*', RunWord),
      ('/icon/.*\\.png', ReadIcon),
      ('/write', WriteWord),
      ('/results', Results),
  ], debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
