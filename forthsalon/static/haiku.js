function core_words() {
  var dict = new Object();
  dict['x'] = ['dstack.push(xpos);']; 
  dict['y'] = ['dstack.push(ypos);']; 
  dict['t'] = ['dstack.push(time_val);']; 

  dict['push'] = ['rstack.push(dstack.pop());'];
  dict['pop'] = ['dstack.push(rstack.pop());'];
  dict['>r'] = dict['push'];
  dict['r>'] = dict['pop'];

  dict['dup'] = ['work1 = dstack.pop();',
                 'dstack.push(work1);',
                 'dstack.push(work1);'];
  dict['over'] = ['work1 = dstack.pop();',
                  'work2 = dstack.pop();',
                  'dstack.push(work2);',
                  'dstack.push(work1);',
                  'dstack.push(work2);'];

  dict['2dup'] = dict['over'].concat(dict['over']);
  dict['z+'] = ['work1 = dstack.pop();',
                'work2 = dstack.pop();',
                'work3 = dstack.pop();',
                'work4 = dstack.pop();',
                'dstack.push(work2 + work4);',
                'dstack.push(work1 + work3);'];
  dict['z*'] = ['work1 = dstack.pop();',
                'work2 = dstack.pop();',
                'work3 = dstack.pop();',
                'work4 = dstack.pop();',
                'dstack.push(work4 * work2 - work3 * work1);',
                'dstack.push(work4 * work1 + work3 * work2);'];

  dict['drop'] = ['work1 = dstack.pop();'];
  dict['swap'] = ['work1 = dstack.pop();',
                  'work2 = dstack.pop();',
                  'dstack.push(work1);',
                  'dstack.push(work2);'];

  dict['='] = ['dstack.push((dstack.pop() == dstack.pop())?1.0:0.0);'];
  dict['<>'] = ['dstack.push((dstack.pop() != dstack.pop())?1.0:0.0);'];
  dict['<'] = ['dstack.push((dstack.pop() > dstack.pop())?1.0:0.0);'];
  dict['>'] = ['dstack.push((dstack.pop() < dstack.pop())?1.0:0.0);'];
  dict['<='] = ['dstack.push((dstack.pop() >= dstack.pop())?1.0:0.0);'];
  dict['>='] = ['dstack.push((dstack.pop() <= dstack.pop())?1.0:0.0);'];

  dict['+'] = ['dstack.push(dstack.pop() + dstack.pop());'];
  dict['*'] = ['dstack.push(dstack.pop() * dstack.pop());'];
  dict['-'] = ['work1 = dstack.pop();',
               'dstack.push(dstack.pop() - work1);'];
  dict['/'] = ['work1 = dstack.pop();',
               'dstack.push(dstack.pop() / work1);'];
  dict['mod'] = ['work1 = dstack.pop();',
                 'work2 = dstack.pop();',
                 'work2 %= work1;',
                 'dstack.push(work2);'];
  dict['pow'] = ['work1 = dstack.pop();',
                 'dstack.push(Math.pow(dstack.pop(), work1));'];
  dict['**'] = dict['pow'];
  dict['atan2'] = ['work1 = dstack.pop();',
                   'dstack.push(Math.atan2(dstack.pop(), work1));'];

  dict['and'] = ['work1 = dstack.pop();',
                 'dstack.push((dstack.pop()!=0.0 && work1!=0.0)?1.0:0.0);'];
  dict['or'] = ['work1 = dstack.pop();',
                'dstack.push((dstack.pop()!=0.0 || work1!=0.0)?1.0:0.0);'];
  dict['not'] = ['dstack.push(dstack.pop()!=0.0?1.0:0.0);'];

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


BOGUS = ['var go = function(xpos, ypos) {',
         'return [1.0, 0.0, 0.7, 1.0]; }; go'];


function optimize(code) {
  if (code == BOGUS) return BOGUS;
  CAPPED_VALUE = 'dstack.pop()';

  // Use alternate pre/post-amble to optimize away dstack/rstack.
  code = code.slice(0, code.length - 1);
  code[0] = 'var go = function(xpos, ypos) { ' + 
            'var time_val=0.0; var work1, work2, work3, work4;';
  code.push(CAPPED_VALUE);
  code.push(CAPPED_VALUE);
  code.push(CAPPED_VALUE);
  code.push(CAPPED_VALUE);

  var tmp_index = 1;
  for (var i = 0; i < code.length - 1; i++) {
    var retry = false;
    var m = code[i].match(/^dstack\.push\((.*)\);$/);
    if (m) {
      for (var j = i + 1; j < code.length; j++) {
        if (code[j].search(/dstack\.pop\(\)/) >= 0) {
          var tmp = 'temp' + tmp_index;
          tmp_index++;
          var x = code[j].replace(/dstack\.pop\(\)/, tmp);
          code = code.slice(0, i).concat(
              'var ' + tmp + ' = ' + m[1] + ';').concat(code.slice(
              i + 1, j)).concat([x]).concat(code.slice(j + 1));
          i = -1;
          retry = true;
          break;
       }
        if (code[j].match(/^dstack\.push\((.*)\);$/)) break;
        if (code[j].match(/[{}]/)) break;
      }
      if (retry) continue;
    }

    var m = code[i].match(/^rstack\.push\((.*)\);$/);
    if (m) {
      for (var j = i + 1; j < code.length; j++) {
        if (code[j].search(/rstack\.pop\(\)/) >= 0) {
          var tmp = 'temp' + tmp_index;
          tmp_index++;
          var x = code[j].replace(/rstack\.pop\(\)/, tmp);
          code = code.slice(0, i).concat(
              'var ' + tmp + ' = ' + m[1] + ';').concat(code.slice(
              i + 1, j)).concat([x]).concat(code.slice(j + 1));
          i = -1;
          retry = true;
          break;
        }
        if (code[j].match(/^rstack\.push\((.*)\);$/)) break;
        if (code[j].match(/[{}]/)) break;
      }
      if (retry) continue;
    }
  }

  // Fill in missing stack items with defaults [0,0,0,1].
  var count = 0;
  while (count < 4 && code[code.length - 1] == CAPPED_VALUE) {
    code = code.slice(0, code.length - 1);
    count++;
  }
  count = 4 - count;
  var ret = code.slice(code.length - count, code.length).reverse();
  while (ret.length < 3) ret.push('0.0');
  if (ret.length < 4) ret.push('1.0');
  code = code.slice(0, code.length - count);
  code.push('return [' + ret.join(', ') + ']; }; go');

  // Dump code to console.
  console.log(code.join('\n') + '\n');

  // Require no extra stuff on the stacks.
  for (var i = 0; i < code.length; i++) {
    if (code[i].search(/stack/) >= 0) {
      return BOGUS;
    }
  }

  return code;
}


function compile(src) {
  var code = ['var go = function(xpos, ypos) { ' +
              'var time_val=0.0; var dstack=[]; var rstack=[];'];
  var dict = core_words();
  var pending_name = 'bogus';
  var code_stack = [];
  src = src.replace(/[ \r\n\t]+/g, ' ').trim();
  src = src.split(' ');
  for (var i = 0; i < src.length; i++) {
    var word = src[i];
    word = word.toLowerCase();
    if (word in dict) {
      code = code.concat(dict[word]);
    } else if (word == '(') {
      // Skip comments.
      while (i < src.length && src[i] != ')') {
        i++;
      }
    } else if (word == ':') {
      i++;
      pending_name = src[i];
      // Disallow nested words.
      if (code_stack.length != 0) return BOGUS;
      code_stack.push(code);
      code = [];
    } else if (word == ';') {
      // Disallow ; other than to end a word.
      if (code_stack.length != 1) return BOGUS;
      dict[pending_name] = code;
      code = code_stack.pop(); 
      pending_name = 'bogus';
    } else {
      var num = '' + parseFloat(word);
      if (num.match(/^[-]?[0-9]+$/)) {
        num += '.0';
      }
      code.push('dstack.push(' + num + ');');
    }
  }
  code.push('return dstack; }; go');
  // Limit number of steps.
  if (code.length > 2000) return BOGUS;
  code = optimize(code);
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
          var alpha = Math.min(Math.max(0.0, col[3]), 1.0);
          var alpha1 = 1.0 - alpha;
          var alpha2 = 0.9333333333333 * alpha1;
          col[0] = col[0] * alpha + alpha2;
          col[1] = col[1] * alpha + alpha2;
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
    }, 0);
  } else {
    setTimeout(next, 0);
  }
}

function setup3d(cv, fshader_code) {
  gl = cv.getContext('experimental-webgl');
  if (!gl) throw 'no gl context';

  var fshader = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fshader, fshader_code);
  gl.compileShader(fshader);
  if (!gl.getShaderParameter(fshader, gl.COMPILE_STATUS)) throw 'bad fshader';
 
  var vshader = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vshader, [
      'attribute vec2 ppos;',
      'varying highp vec2 tpos;',
      'void main(void) {',
      'gl_Position = vec4(ppos.x, ppos.y, 0.0, 1.0);',
      'tpos.x = (ppos.x + 1.0) / 2.0;',
      'tpos.y = (ppos.y + 1.0) / 2.0;',
      '}'].join('\n'));
  gl.compileShader(vshader);
  if (!gl.getShaderParameter(vshader, gl.COMPILE_STATUS)) throw 'bad vshader';

  var program = gl.createProgram();
  gl.attachShader(program, fshader);
  gl.attachShader(program, vshader);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw 'bad link';

  gl.validateProgram(program);
  if (!gl.getProgramParameter(program, gl.VALIDATE_STATUS)) {
    throw 'bad program';
  }
  gl.useProgram(program);

  var vattrib = gl.getAttribLocation(program, 'ppos');
  if(vattrib == -1) throw 'ppos cannot get address';
  gl.enableVertexAttribArray(vattrib);

  var vbuffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbuffer);
  var vertices = new Float32Array([-1.0,-1.0, 1.0,-1.0, 1.0,1.0,
                                   -1.0,-1.0, 1.0,1.0, -1.0,1.0]);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
  gl.vertexAttribPointer(vattrib, 2, gl.FLOAT, false, 0, 0);

  cv.program3d = program;
}

function draw3d(cv) {
  gl = cv.getContext('experimental-webgl');
  if (!gl) throw 'no gl context';

  var time_val_loc = gl.getUniformLocation(cv.program3d, 'time_val');
  var dt = new Date();
  var tm = dt.getHours();
  tm = tm * 60 + dt.getMinutes();
  tm = tm * 60 + dt.getSeconds();
  tm = tm + dt.getMilliseconds() / 1000.0;
  gl.uniform1f(time_val_loc, tm);
 
  gl.clearColor(0.0, 0.0, 0.0, 0.0);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
}

function make_fragment_shader(code) {
  if (code.join(' ').search('random') >= 0) {
    throw 'random not supported';
  }
  code = code.slice(1);
//  if (code.join(' ').search('time_val') < 0) {
//    throw 'only use for time_val';
//  }
  code = ['precision highp float;',
          'varying vec2 tpos;',
          'uniform float time_val;',
          'void main(void) {',
          'float work1, work2, work3, work4;',
  ].concat(code);
  for (var i = 0; i < code.length; i++) {
    code[i] = code[i].replace(/var /, 'float ');
    code[i] = code[i].replace(/xpos/g, 'tpos.x');
    code[i] = code[i].replace(/ypos/g, 'tpos.y');
    code[i] = code[i].replace(/Math\./g, '');
    code[i] = code[i].replace(/atan2/g, 'atan');
    code[i] = code[i].replace('work2 %= work1;', 'work2 = mod(work2, work1);');
    code[i] = code[i].replace(/PI/g, '3.1415926535897931');
    code[i] = code[i].replace(/NaN/g, '0.0');
  }
  code[code.length-1] = code[code.length-1].replace(
      ']; }; go', '); ' +
      'gl_FragColor.a = min(max(0.0, gl_FragColor.a), 1.0); ' +
      'gl_FragColor.r *= gl_FragColor.a; ' +
      'gl_FragColor.g *= gl_FragColor.a; ' + 
      'gl_FragColor.b *= gl_FragColor.a; }');
  code[code.length-1] = code[code.length-1].replace(
      'return [', 'gl_FragColor = vec4(');
  code = code.join('\n');
  console.log(code);
  return code;
}

function render(cv, code, next) {
  if (cv.code == code) {
    if (cv.program3d != null) draw3d(cv);
    setTimeout(next, 0);
    return;
  }
  cv.code = code;
  var compiled_code = compile(code);
  try {
    var fshader = make_fragment_shader(compiled_code);
    setup3d(cv, fshader);
    draw3d(cv);
    setTimeout(next, 0);
    return;
  } catch(e) {
    // Fall back on software.
  }

  try {
    var image = eval(compiled_code.join(' '));
    var ctx = cv.getContext('2d');
    var w = cv.width;
    var h = cv.height;
    var img = ctx.createImageData(w, h);
  } catch(e) {
    // Go on to the next one.
    setTimeout(next, 0);
    return;
  }

  render_rows(image, ctx, img, 0, w, h, function() {
    setTimeout(next, 0);
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
    setTimeout(next, 0);
    return;
  }
  var cv = work[0][0];
  var code = work[0][1];
  work = work.slice(1);
  render(cv, code, function() {
    update_haikus_one(work, next);
  });
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
      work.push([canvas, code]);
    } catch(e) {
      // Ignore errors.
    }
  }
  update_haikus_one(work, next);
}
