import datetime
import os
import pickle
import pngcanvas
import random
import re
import sys
import zlib
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class Word(db.Model):
  description = db.BlobProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  last_used = db.DateTimeProperty(auto_now_add=True)
  author = db.UserProperty()
  remote_addr = db.StringProperty()
  user_agent = db.StringProperty()
  version = db.IntegerProperty(default=1)
  intrinsic = db.IntegerProperty(default=0)
  definition = db.StringListProperty()
  keywords = db.StringListProperty()
  score = db.FloatProperty(default=0.0)

class WordIcon(db.Model):
  icon = db.BlobProperty()

class WordSource(db.Model):
  source = db.BlobProperty()

class WordExecutable(db.Model):
  executable = db.BlobProperty()


colors = [
  [0xff, 0xff, 0xff, 0xff],
  [0xc0, 0xc0, 0xc0, 0xc0],
  [0x00, 0x00, 0x00, 0xff],
  [0xff, 0x00, 0x00, 0xff],
  [0xff, 0xc0, 0x00, 0xff],
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


def UpdateScore(key):
  # Fetch it.
  w = Word.get(key)
  if w:
    # Find users of this word.
    query = db.GqlQuery('SELECT __key__ FROM Word '
                        'WHERE definition=:1', key)
    use_count = query.count(1000)
    # Update score and last used.
    w.score = float(use_count)
    w.last_used = datetime.datetime.now()
    w.put()


def ChromeFrameMe(handler):
  agent = handler.request.headers.get('USER_AGENT', '')
  if agent.find('MSIE') >= 0 and agent.find('chromeframe') < 0:
    path = os.path.join(os.path.dirname(__file__),
                        'templates/chrome_frame.html')
    handler.response.out.write(template.render(path, {}))
    return True
  return False



class ReadWord(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    id = self.request.get('id', '')
    w = Word.get(id)
    if w:
      # Find users of this word.
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'WHERE definition=:1 '
                          'ORDER BY score DESC, last_used DESC', str(w.key()))
      words_used = query.fetch(1000)
      if not words_used:
        words_used = []
      # Decide if they can delete this.
      can_delete = (users.is_current_user_admin() or
                    users.get_current_user() == w.author)
      # Output info on word.
      path = os.path.join(os.path.dirname(__file__),
                          'templates/read.html')
      self.response.out.write(template.render(path, {
          'id': id,
          'description': w.description,
          'definition': w.definition,
          'created': str(w.created),
          'last_used': str(w.last_used),
          'words_used': words_used,
          'can_delete': can_delete,
      }))
    else:
      path = os.path.join(os.path.dirname(__file__),
                          'templates/read_notfound.html')
      self.response.out.write(template.render(path, {}))


class ListWord(webapp.RequestHandler):
  def get(self):
    # Get the source.
    lookup_id = self.request.get('id', '')
    query = db.GqlQuery('SELECT * FROM WordSource WHERE ANCESTOR is :1',
                        lookup_id)
    src = query.fetch(1)
    if src:
      source = DecodeSource(lookup_id, src[0].source)
    else:
      source = {}
    # Handle raw output more directly.
    if self.request.get('raw'):
      self.response.headers['Content-Type'] = 'text/plain'
      for w, d in source.iteritems():
        dfn = ' '.join((str(i) for i in d))
        self.response.out.write('%s %s\n' % (w, dfn))
      return
    # Display it in a sensible order.
    results = []
    pending_ids = [lookup_id]
    needed_ids = set([lookup_id])
    while pending_ids:
      # Pick one.
      id = pending_ids[0]
      pending_ids = pending_ids[1:]
      # Grab out its parts.
      intrinsic = source[id][0]
      definition = source[id][1:]
      # Collect each word.
      results.append({
          'id': id,
          'intrinsic': intrinsic,
          'definition': definition,
      })
      # Add new words needed.
      for w in definition:
        if w not in needed_ids:
          needed_ids.add(w)
          pending_ids.append(w)
    else:
      path = os.path.join(os.path.dirname(__file__),
                          'templates/list.html')
      self.response.out.write(template.render(path, {
          'results': results,
      }))


class RunWord(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    id = self.request.get('id', '')
    # Get the executable.
    query = db.GqlQuery('SELECT * FROM WordExecutable WHERE ANCESTOR is :1', id)
    exe = query.fetch(1)
    if exe:
      path = os.path.join(os.path.dirname(__file__),
                          'templates/run.html')
      self.response.out.write(template.render(path, {
          'id': id,
          'exe': exe[0].executable,
      }))
    else:
      path = os.path.join(os.path.dirname(__file__),
                          'templates/read_notfound.html')
      self.response.out.write(template.render(path, {}))


class Results(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    # Do a query.
    goal = self.request.get('q').lower()
    w = []
    if goal:
      # Show search results ordered by score then last_used.
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'WHERE keywords = :1 '
                          'ORDER BY score DESC, last_used DESC', goal)
      w1 = query.fetch(1000)
      if w1:
        w = w1
    else:
      w = []
      user = users.get_current_user()
      if user:
        # List up to the last 8 created by this remote_addr.
        query = db.GqlQuery('SELECT __key__ FROM Word '
                            'WHERE author = :1 '
                            'ORDER BY created DESC', user)
        w1 = query.fetch(8)
        if w1:
          w += w1
      else:
        # List up to the last 8 created by this remote_addr.
        query = db.GqlQuery('SELECT __key__ FROM Word '
                            'WHERE remote_addr = :1 '
                            'ORDER BY created DESC', self.request.remote_addr)
        w1 = query.fetch(8)
        if w1:
          w += w1
      # Then add in the more order by score then last_used.
      query = db.GqlQuery('SELECT __key__ FROM Word '
                          'ORDER BY score DESC, last_used DESC')
      w1 = query.fetch(1000)
      if w1:
        w += [i for i in w1 if i not in w]
    # Display results.
    path = os.path.join(os.path.dirname(__file__),
                        'templates/results.html')
    self.response.out.write(template.render(path, {
        'query': goal,
        'results': [str(i) for i in w],
    }))


class ReadIcon(webapp.RequestHandler):
  def get(self):
    self.response.headers['Cache-Control'] = 'public, max-age=86400'
    self.response.headers['Content-Type'] = 'image/png'
    c = pngcanvas.PNGCanvas(32, 32)
    id = self.request.get('id', '.png')[:-4]
    query = db.GqlQuery('SELECT * FROM WordIcon WHERE ANCESTOR is :1', id)
    w = query.fetch(1)
    if w:
      data = w[0].icon
      for y in range(0, 16):
        for x in range(0, 16):
          z = x + y * 16
          if z < len(data):
            c.color = colors[int(data[z])]
          c.rectangle(x*2, y*2, x*2+1, y*2+1)
    else:
      c.verticalGradient(0, 0, c.width-1, c.height-1,
                         [0xff,0,0,0xff],
                         [0x20,0,0xff,0x80])
    self.response.out.write(c.dump())


def EncodeSource(source):
  return zlib.compress(pickle.dumps(source))


def DecodeSource(key, data):
  source = pickle.loads(zlib.decompress(data))
  if source.get('this'):
    source[key] = source['this']
    del source['this']
  return source


def CompileSource(key, source):
  heap = []
  sym_table = {}
  pending = [key]
  # Process until nothing is pending.
  while pending:
    # Consider the last on on the stack.
    focus = pending[-1]
    # If we've handled it drop it and continue.
    if sym_table.get(focus):
      pending.pop()
      continue
    # Pull out intrinsic / definition.
    intrinsic = source[focus][0]
    defn = source[focus][1:]
    # Check if we've handled the children, or add them.
    ready = True
    for w in defn:
      if not sym_table.get(w):
        ready = False
        pending.append(w)
    # Repeat recursively if not everything has been handled.
    if not ready:
      continue
    # Take this one out.
    pending.pop()
    # Handle intrinsics specially.
    if not defn and intrinsic:
      sym_table[focus] = 'op(%d)' % intrinsic
      continue
    # Add a RET instruction.
    heap.append('RET')
    # Encode it (in anticipation of reverse).
    for w in reversed(defn):
      op = sym_table[w]
      if type(op) == str:
        heap.append(op)
      else:
        heap.append(str(len(heap) - op))
    # Add to symbol table.
    sym_table[focus] = len(heap)
  # Reverse things and convert to a string.
  heap.reverse()
  heap = ','.join(heap)
  return heap


def AddFullWord(description, definition, intrinsic,
                author, remote_addr, user_agent,
                keywords, icon, source, executable):
  # Add word to database.
  word = Word()
  word.description = description
  word.definition = definition
  word.intrinsic = intrinsic
  word.author = author
  word.remote_addr = remote_addr
  word.user_agent = user_agent
  word.keywords = keywords
  word.put()
  # Add icon to database.
  wicon = WordIcon(parent=word)
  wicon.icon = icon
  wicon.put()
  # Add source to database.
  wsource = WordSource(parent=word)
  wsource.source = source
  wsource.put()
  # Add executable to database.
  wexe = WordExecutable(parent=word)
  wexe.executable = executable
  wexe.put()


def DeleteFullWord(word, icon, source, exe):
  word.delete()
  icon.delete()
  source.delete()
  exe.delete()


class DeleteWord(webapp.RequestHandler):
  def post(self):
    # Get id.
    id = self.request.get('id', '')
    word = Word.get(id)
    # Decide if they can delete this.
    can_delete = (users.is_current_user_admin() or
                  users.get_current_user() == w.author)
    if not can_delete: return
    # Get other child entries.
    query = db.GqlQuery('SELECT * FROM WordIcon WHERE ANCESTOR is :1', id)
    icon = query.fetch(1)[0]
    query = db.GqlQuery('SELECT * FROM WordSource WHERE ANCESTOR is :1', id)
    source = query.fetch(1)[0]
    query = db.GqlQuery('SELECT * FROM WordExecutable WHERE ANCESTOR is :1', id)
    exe = query.fetch(1)[0]
    # Delete as transaction.
    db.run_in_transaction(DeleteFullWord, word, icon, source, exe)


class WriteWord(webapp.RequestHandler):
  def post(self):
    # Extract description + intrinsic.
    description = str(self.request.get('description'))
    m = re.match('^~~~intrinsic: ([0-9]+)~~~(.*)$', description)
    if m:
      intrinsic = int(m.group(1))
      description = m.group(2)
    else:
      intrinsic = 0
    # Pick out definition
    definition = str(self.request.get('definition'))
    if definition:
      definition = definition.split(' ')
    else:
      definition = []
    # Get user agent string.
    user_agent = self.request.headers.get('USER_AGENT', '')
    # Get out icon.
    icon = str(self.request.get('icon', ''))
    # Get source for each word that goes into this one.
    sources = {}
    for w in set(definition):
      query = db.GqlQuery('SELECT * FROM WordSource WHERE ANCESTOR is :1', w)
      src = query.fetch(1)
      if src:
        dsource = DecodeSource(w, src[0].source)
        sources.update(dsource)
    sources['this'] = [intrinsic] + definition
    my_source = EncodeSource(sources)
    # Compile it.
    my_executable = CompileSource('this', sources)
    # Transactionally add word and icon.
    db.run_in_transaction(AddFullWord,
                          description=description,
                          definition=definition,
                          intrinsic=intrinsic,
                          author=users.get_current_user(),
                          remote_addr=self.request.remote_addr,
                          user_agent=user_agent,
                          keywords=FindKeywords(description),
                          icon=icon,
                          source=my_source,
                          executable=my_executable)
    # Update score of each word used.
    for w in set(definition):
      UpdateScore(w)


class EditorPage(webapp.RequestHandler):
  def get(self):
    if ChromeFrameMe(self): return
    user = users.get_current_user()
    if user:
      greeting = ('Welcome, %s! (<a href="%s">sign out</a>)' %
                  (user.nickname(), users.create_logout_url('/editor')))
    else:
      greeting = ('<a href="%s">Sign in or register</a>.' %
                  users.create_login_url('/editor'))
    path = os.path.join(os.path.dirname(__file__), 'templates/editor.html')
    self.response.out.write(template.render(path, {
        'greeting': greeting,
    }))


def main():
  application = webapp.WSGIApplication([
      ('/delete', DeleteWord),
      ('/list', ListWord),
      ('/editor', EditorPage),
      ('/icon', ReadIcon),
      ('/read', ReadWord),
      ('/results', Results),
      ('/run', RunWord),
      ('/write', WriteWord),
  ], debug=True)
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
