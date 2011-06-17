function core_words() {
  var dict = new Object();
  dict['x'] = ['dstack.push(x);']; 
  dict['y'] = ['dstack.push(y);']; 

  dict['push'] = ['rstack.push(dstack.pop());'];
  dict['pop'] = ['dstack.push(rstack.pop());'];
  dict['>r'] = dict['push'];
  dict['r>'] = dict['pop'];

  dict['@'] = ['dstack.push(mem[dstack.pop()]);'];
  dict['!'] = ['var w1 = dstack.pop(); mem[w1] = dstack.pop();'];

  dict['dup'] = ['var w1 = dstack.pop(); ' +
                 'dstack.push(w1); dstack.push(w1);'];
  dict['over'] = ['var w1 = dstack.pop(); ' +
                  'var w2 = dstack.pop(); ' +
                  'dstack.push(w2); dstack.push(w1); dstack.push(w2);'];

  dict['2dup'] = dict['over'] + dict['over'];
  dict['z+'] = ['var w1 = dstack.pop(); var w2 = dstack.pop(); ' +
                'var w3 = dstack.pop(); var w4 = dstack.pop(); ' +
                'dstack.push(w2 + w4); dstack.push(w1 + w3);'];
  dict['z*'] = ['var w1 = dstack.pop(); var w2 = dstack.pop(); ' +
                'var w3 = dstack.pop(); var w4 = dstack.pop(); ' +
                'dstack.push(w4 * w2 - w3 * w1); ' +
                'dstack.push(w4 * w1 + w3 * w2);'];

  dict['drop'] = ['dstack.pop();'];
  dict['swap'] = ['var w1 = dstack.pop(); var w2 = dstack.pop(); ' +
                  'dstack.push(w1); dstack.push(w2);'];

  dict['='] = ['dstack.push((dstack.pop() == dstack.pop())?1:0);'];
  dict['<>'] = ['dstack.push((dstack.pop() != dstack.pop())?1:0);'];
  dict['<'] = ['dstack.push((dstack.pop() > dstack.pop())?1:0);'];
  dict['>'] = ['dstack.push((dstack.pop() < dstack.pop())?1:0);'];
  dict['<='] = ['dstack.push((dstack.pop() >= dstack.pop())?1:0);'];
  dict['>='] = ['dstack.push((dstack.pop() <= dstack.pop())?1:0);'];

  dict['+'] = ['dstack.push(dstack.pop() + dstack.pop());'];
  dict['*'] = ['dstack.push(dstack.pop() * dstack.pop());'];
  dict['-'] = ['var w1 = dstack.pop(); ' +
               'dstack.push(dstack.pop() - w1);'];
  dict['/'] = ['var w1 = dstack.pop(); ' +
               'dstack.push(dstack.pop() / w1);'];
  dict['mod'] = ['var w1 = dstack.pop(); ' +
                 'dstack.push(dstack.pop() % w1);'];
  dict['pow'] = ['var w1 = dstack.pop(); ' +
                 'dstack.push(Math.pow(dstack.pop(), w1));'];
  dict['**'] = dict['pow'];
  dict['atan2'] = ['var w1 = dstack.pop(); ' +
                   'dstack.push(Math.atan2(dstack.pop(), w1));'];

  dict['and'] = ['var w1 = dstack.pop(); ' +
                 'dstack.push((dstack.pop() && w1)?1:0);'];
  dict['or'] = ['var w1 = dstack.pop(); ' +
                'dstack.push((dstack.pop() || w1)?1:0);'];
  dict['not'] = ['dstack.push(!dstack.pop()?1:0);'];

  dict['min'] = ['dstack.push(Math.min(dstack.pop(), dstack.pop()));'];
  dict['max'] = ['dstack.push(Math.max(dstack.pop(), dstack.pop()));'];

  dict['negate'] = ['dstack.push(-dstack.pop());'];
  dict['sin'] = ['dstack.push(Math.sin(dstack.pop()));'];
  dict['cos'] = ['dstack.push(Math.cos(dstack.pop()));'];
  dict['tan'] = ['dstack.push(Math.tan(dstack.pop()));'];
  dict['log'] = ['dstack.push(Math.log(dstack.pop()));'];
  dict['exp'] = ['dstack.push(Math.exp(dstack.pop()));'];
  dict['sqrt'] = ['dstack.push(Math.sqrt(dstack.pop()));'];
  dict['floor'] = ['dstack.push(Math.floor(dstack.pop()));'];
  dict['ceil'] = ['dstack.push(Math.ceil(dstack.pop()));'];
  dict['abs'] = ['dstack.push(Math.abs(dstack.pop()));'];

  dict['pi'] = ['dstack.push(Math.PI);'];

  dict['random'] = ['dstack.push(Math.random());'];

  dict['if'] = ['if(dstack.pop()) {'];
  dict['else'] = ['} else {'];
  dict['then'] = ['}'];

  dict['here'] = ['dstack.push(here);'];
  dict['allot'] = ['here += dstack.pop();'];

  return dict;
}

function code_tags(src) {
  var tags = [];
  var char_count = src.length;
  src = src.replace(/[ \r\t]+/, ' ');
  src = src.replace(/[ ]+\n/, '\n');
  src = src.replace(/\n[ ]+/, '\n');
  src = src.replace(/[\n]+/, '\n');
  src = src.replace(/[\n]$/, '');
  // Measure each line.
  var lines = src.split('\n');
  var line_counts = [];
  for (var i = 0; i < lines.length; i++) {
    line_counts.push(lines[i].trim().split(' ').length);
  }
  // Pull out each word.
  var words = src.replace(/[ \n]+/g, ' ').trim().split(' ');
  // Decide style.
  if (lines.length == 3 &&
      lines[0].trim().split(' ').length == 5 &&
      lines[1].trim().split(' ').length == 7 &&
      lines[2].trim().split(' ').length == 5) {
    // Haiku has 7-5-7 words.
    tags.push('style:haiku');
  } else if (src.length <= 140) {
    // Short is <= 140 characters.
    tags.push('style:short');
  } else {
    // Anything else is long.
    tags.push('style:long');
  }
  // Detect animation.
  for (var i = 0; i < words.length; i++) {
    if (words[i].toLowerCase() == 't') {
      tags.push('animated');
      break;
    }
  }
  // Show counts.
  tags.push('characters:' + char_count);
  tags.push('words:' + words.length);
  tags.push('lines:' + line_counts.join(','));
  return tags;
}

if (typeof String.prototype.trim != 'function') {
  String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/, ''); 
  }
}


function compile(src) {
  var code = ['var go = function(x, y) {',
              ' var dstack=[]; var rstack=[]; var mem=[];',
              ' var here = 1024;'];
  var dict = core_words();
  var var_index = 0;
  var pending_name = 'bogus';
  var code_stack = [];
  src = src.replace(/[ \r\n\t]+/g, ' ').trim();
  src = src.split(' ');
  for (var i = 0; i < src.length; i++) {
    var word = src[i];
    word = word.toLowerCase();
    if (word == 'variable') {
      i++;
      dict[src[i]] = ['dstack.push(' + var_index + ');'];
      var_index++;
    } else if (word == '(') {
      // Skip comments.
      while (i < src.length && src[i] != ')') {
        i++;
      }
    } else if (word == ':') {
      i++;
      pending_name = src[i];
      // Disallow nested words.
      if (code_stack.length != 0) return 0;
      code_stack.push(code);
      code = [];
    } else if (word == ';') {
      // Disallow ; other than to end a word.
      if (code_stack.length != 1) return 0;
      dict[pending_name] = code;
      code = code_stack.pop(); 
      pending_name = 'bogus';
    } else if (word in dict) {
      code = code.concat(dict[word]);
    } else {
      code.push('dstack.push(' + parseFloat(word) + ');');
    }
  }
  code.push('return dstack; }; go');
  code = eval(code.join(' '));
  return code;
}

function render_rows(image, ctx, img, y, w, h, next) {
  start = new Date().getTime();
  try {
    // Decide if we're on android or a normal browser.
    if (navigator.userAgent.toLowerCase().search('android') < 0) {
      while (y < h) {
        var pos = w * (h - 1 - y) * 4;
        for (var x = 0; x < w; x++) {
          var col = image(x / w, y / h);
          if (col[3] == null) col[3] = 1;
          img.data[pos++] = Math.floor(col[0] * 255);
          img.data[pos++] = Math.floor(col[1] * 255);
          img.data[pos++] = Math.floor(col[2] * 255);
          img.data[pos++] = Math.floor(col[3] * 255);
        }
        y++;
        if (new Date().getTime() - start > 250) break;
      }
    } else {
      // Work around what seems to be an android canvas bug?
      while (y < h) {
        var pos = w * (h - 1 - y) * 4;
        for (var x = 0; x < w; x++) {
          var col = image(x / w, y / h);
          if (col[3] == null) col[3] = 1;
          if (isNaN(col[3])) col[3] = 0;
          var alpha = col[3];
          var alpha1 = 1 - col[3];
          col[0] = col[0] * alpha + alpha1;
          col[1] = col[1] * alpha + alpha1;
          col[2] = col[2] * alpha + alpha1;
          col[3] = 1;
          img.data[pos++] = Math.floor(col[0] * 255);
          img.data[pos++] = Math.floor(col[1] * 255);
          img.data[pos++] = Math.floor(col[2] * 255);
          img.data[pos++] = Math.floor(col[3] * 255);
        }
        y++;
        if (new Date().getTime() - start > 250) break;
      }
    }
  } catch(e) {
    // Ignore errors.
  }
  ctx.putImageData(img, 0, 0);
  if (y < h) {
    setTimeout(function() {
      render_rows(image, ctx, img, y, w, h, next);
    }, 1);
  } else {
    setTimeout(next, 1);
  }
}

function render(cv, image, next) {
  var ctx = cv.getContext('2d');
  var w = cv.width;
  var h = cv.height;
  var img = ctx.createImageData(w, h);

  render_rows(image, ctx, img, 0, w, h, function() {
    setTimeout(next, 1);
  });
}

function find_tag(parent, tag) {
  for (var i = 0; i < parent.childNodes.length; i++) {
    var child = parent.childNodes[i];
    if (child.tagName == tag.toUpperCase()) return child;
  }
  return null;
}

function update_haikus_one(work, next) {
  if (work.length == 0) {
    next();
    return;
  }
  var cv = work[0][0];
  var img = work[0][1];
  work = work.slice(1);
  render(cv, img, function() { update_haikus_one(work, next); });
}

function update_haikus(next) {
  var haikus = document.getElementsByName('haiku');
  var work = [];
  for (var i = 0; i < haikus.length; i++) {
    var haiku = haikus[i];
    var code_tag = find_tag(haiku, 'textarea');
    var code = code_tag.value;
    var canvas = find_tag(haiku, 'canvas');
    if (canvas == null) {
      canvas = document.createElement('canvas');
      haiku.appendChild(canvas);
    }
    canvas.setAttribute('width', haiku.getAttribute('width'));
    canvas.setAttribute('height', haiku.getAttribute('height'));
    try {
      work.push([canvas, compile(code)]);
    } catch(e) {
      // Ignore errors.
    }
  }
  update_haikus_one(work, next);
}
