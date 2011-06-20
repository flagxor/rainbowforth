import base64



return_stack_text = (
    'Forth uses two stacks, the data stack and the return stack. '
    'Most operations occur on the data stack. The return stack '
    'can be crucial when reaching below the top two data stack elements, '
    'or to put aside values. In traditional Forth, the return stack does, '
    'double duty, being used to track the return address of the current '
    'caller of a word. As such, it is important to balance what you push '
    'and pop to the return stack within each scope. The current '
    'Haiku Forth implement does not use the return stack for flow '
    'control, however, this behavior may change in future versions. '
)


floating_point_text = (
    'NOTE: In Haiku Forth (unlike Traditional Forth), all stack cells and '
    'variables are floating point numbers. '
)


boolean_text = (
    'Boolean values in Haiku Forth are returned as 1 (true) or 0 (false). '
    'This is in contrast to traditional Forth in which -1 is used for true. '
    'This choice to go 1 for true was made to facilitate using boolean value '
    'as multiplicative masks. For example: _x 0.5 _< _* .'
    'The Forth/C convention that anything non-zero is considered an alternate '
    'stand-in for true is carried over. '
)


core_words = [
  {
    'names': ['x'],
    'stack': '( -- x )',
    'summary': 'Put the current x-coordinate on the stack.',
    'description': [
        'Unique to Haiku Forth. Returns a floating point number from 0 to 1, '
        'where 0 meaning the current pixel is left-most, and 1 means '
        'right-most. '
        ,
        floating_point_text
    ],
  },
  {
    'names': ['y'],
    'stack': '( -- y )',
    'summary': 'Put the current y-coordinate on the stack.',
    'description': [
        'Unique to Haiku Forth. Returns a floating point number from 0 to 1, '
        'where 0 meaning the current pixel is bottom-most, and 1 means '
        'top-most. '
        ,
        floating_point_text
    ],
  },
  {
    'names': ['push', '>r'],
    'summary': 'Move one value from the data stack to the return stack.',
    'description': [
        return_stack_text
        ,
        'In tranditional Forth, this word is called _>r to visually '
        'illustrate how data flows to the return stack. The variant '
        '_push (from colorForth) is supported as this form is more '
        'conducive to cell phone entry. '
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _push _+ _pop _*', '9'],
        ['_2dup _push _push _* _pop _pop _/ _-', '(a*b) - (a/b)'],
    ],
  },
  {
    'names': ['pop', 'r>'],
    'summary': 'Move one value from the return stack to the data stack.',
    'description': [
        return_stack_text
        ,
        'In tranditional Forth, this word is called _r> to visually '
        'illustrate how data flows out of the return stack. The variant '
        '_pop (from colorForth) is supported as this form is more '
        'conducive to cell phone entry.'
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _push _+ _pop _*', '9'],
        ['_2dup _push _push _* _pop _pop _/ _-', '(a*b) - (a/b)'],
    ],
  },
  {
    'names': ['dup'],
    'stack' : '( n -- n n )',
    'summary': 'Duplicate the element on top of the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _dup', '1 2 3 3'],
        ['4 _dup _dup', '4 4 4'],
    ],
  },
  {
    'names': ['over'],
    'stack': '( a b -- a b a )',
    'summary': 'Duplicate the element under the top stack element.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _over', '1 2 3 2'],
    ],
  },
  {
    'names': ['2dup'],
    'stack': '( a b -- a b a b )',
    'summary': 'Duplicate the top two elements on the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _2dup', '1 2 3 2 3'],
    ],
  },
  {
    'names': ['drop'],
    'stack': '( n -- )',
    'summary': 'Drop the top element from the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _drop', '1 2'],
    ],
  },
  {
    'names': ['swap'],
    'stack': '( a b -- b a )',
    'summary': 'Swap the top two elements on the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 3 _swap', '1 3 2'],
    ],
  },
  {
    'names': ['='],
    'stack': '( a b -- f )',
    'summary': '1 if the top two stack elements are equal, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 _=', '0'],
        ['3 3 _=', '1'],
    ],
  },
  {
    'names': ['<>'],
    'stack': '( a b -- f )',
    'summary': '1 if the top two stack elements are not equal, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 _<>', '1'],
        ['3 3 _<>', '0'],
    ],
  },
  {
    'names': ['<'],
    'stack': '( a b -- f )',
    'summary': '1 if a is less than b, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 _<', '1'],
        ['3 3 _<', '0'],
    ],
  },
  {
    'names': ['>'],
    'stack': '( a b -- f )',
    'summary': '1 if a is greater than b, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['2 1 _>', '1'],
        ['3 3 _>', '0'],
    ],
  },
  {
    'names': ['<='],
    'stack': '( a b -- f )',
    'summary': '1 if a is less than or equal to b, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['2 1 _<=', '0'],
        ['3 3 _<=', '1'],
    ],
  },
  {
    'names': ['>='],
    'stack': '( a b -- f )',
    'summary': '1 if a is greater than or equal to b, else 0.',
    'description': [
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['1 2 _>=', '0'],
        ['3 3 _>=', '1'],
    ],
  },
  {
    'names': ['and'],
    'stack': '( f f -- f )',
    'summary': 'Find the logical "and" of the top two elements on the stack.',
    'description': [
        'NOTE: In contrast to traditional Forth, logical "and" is used '
        'instead of bitwise "and". This choice was made because in a Forth '
        'with a floating point data stack, logical operations are more useful '
        'in combining multiplicative masks, whereas bitwise operations are '
        'at best ambiguous. '
        , 
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['0 0 _and', '0'],
        ['0 1 _and', '0'],
        ['1 0 _and', '0'],
        ['1 1 _and', '1'],
    ],
  },
  {
    'names': ['or'],
    'stack': '( f f -- f )',
    'summary': 'Find the logical "or" of the top two elements on the stack.',
    'description': [
        'NOTE: In contrast to traditional Forth, logical "or" is used '
        'instead of bitwise "or". This choice was made because in a Forth '
        'with a floating point data stack, logical operations are more useful '
        'in combining multiplicative masks, whereas bitwise operations are '
        'at best ambiguous. '
        , 
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['0 0 _or', '0'],
        ['0 1 _or', '1'],
        ['1 0 _or', '1'],
        ['1 1 _or', '1'],
    ],
  },
  {
    'names': ['not'],
    'stack': '( f -- f )',
    'summary': 'Find the logical "not" of the top two elements on the stack.',
    'description': [
        'NOTE: In contrast to traditional Forth, logical "not" is used '
        'instead of bitwise INVERT. This choice was made because in a Forth '
        'with a floating point data stack, logical operations are more useful '
        'in combining multiplicative masks, whereas bitwise operations are '
        'at best ambiguous. '
        , 
        boolean_text
        ,
        floating_point_text
    ],
    'examples': [
        ['0 _not', '1'],
        ['1 _not', '0'],
    ],
  },
  {
    'names': ['min'],
    'stack': '( n n -- n )',
    'summary': 'Select the smaller of the top two stack elements.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['2 3 _min', '2'],
    ],
  },
  {
    'names': ['max'],
    'stack': '( n n -- n )',
    'summary': 'Select the larger of the top two stack elements.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['2 3 _max', '3'],
    ],
  },
  {
    'names': ['+'],
    'stack': '( n n -- n )',
    'summary': 'Add the top two numbers on the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1 2 _+', '3'],
    ],
  },
  {
    'names': ['-'],
    'stack': '( n n -- n )',
    'summary': 'Subtract the top element on the stack from the next element.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['7 4 _-', '3'],
    ],
  },
  {
    'names': ['*'],
    'stack': '( n n -- n )',
    'summary': 'Multiple the top two elements on the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['7 4 _*', '28'],
    ],
  },
  {
    'names': ['/'],
    'stack': '( n n -- n )',
    'summary': 'Divide the second element on the stack by the top element.',
    'description': [
        'NOTE: As the traditional Forth divide operation uses integers and '
        'rounds toward zero, this operation will return different results, '
        'even with integer inputs. '
        ,
        floating_point_text
    ],
    'examples': [
        ['8 4 _/', '2'],
        ['3 2 _/', '1.5'],
    ],
  },
  {
    'names': ['mod'],
    'stack': '( n n -- n )',
    'summary': 'Find a mod b.',
    'description': [
        'NOTE: As the traditional Forth mod operation uses integers and '
        'rounds toward zero, this operation will return different results, '
        'even with integer inputs. '
        ,
        floating_point_text
    ],
    'examples': [
        ['9 4 _mod', '1'],
    ],
  },
  {
    'names': ['pow', '**'],
    'stack': '( n n -- n )',
    'summary': 'Find a to the bth power.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word F**. '
        '** is used to emphasize the primary stack being floating point. '
        'Additionally the C derived word pow is supported. '
        ,
        floating_point_text
    ],
    'examples': [
        ['2 3 _pow', '8'],
        ['2 3 _**', '8'],
    ],
  },
  {
    'names': ['atan2'],
    'stack': '( a b -- n )',
    'summary': 'Find the arctangent of a/b.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FATAN2. '
        'atan2 is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['0 1 _atan2', '0'],
        ['1 0 _atan2', 'pi/2'],
    ],
  },
  {
    'names': ['negate'],
    'stack': '( n -- n )',
    'summary': 'Negate the element on top of the stack.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['2 _negate', '-2'],
        ['0 _negate', '0'],
        ['-4 _negate', '4'],
    ],
  },
  {
    'names': ['sin'],
    'stack': '( n -- n )',
    'summary': 'Compute the sine of the top element of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FSIN. '
        'sin is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['0 _sin', '0'],
        ['_pi 2 / _sin', '1'],
    ],
  },
  {
    'names': ['cos'],
    'stack': '( n -- n )',
    'summary': 'Compute the cosine of the top element of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FCOS. '
        'cos is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['0 _cos', '1'],
        ['_pi 2 / _cos', '0'],
    ],
  },
  {
    'names': ['tan'],
    'stack': '( n -- n )',
    'summary': 'Compute the tangent the top element of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FTAN. '
        'tan is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['0 _tan', '0'],
    ],
  },
  {
    'names': ['log'],
    'stack': '( n -- n )',
    'summary': 'Compute the log base e of the top element of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FLN. '
        'log is used to emphasize the primary stack being floating point, '
        'with a slight nod to the C function name. '
        ,
        floating_point_text
    ],
    'examples': [
        ['1 _log', '0'],
    ],
  },
  {
    'names': ['exp'],
    'stack': '( n -- n )',
    'summary': 'Compute e raised to the power on top of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FEXP. '
        'exp is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['0 _exp', '1'],
    ],
  },
  {
    'names': ['sqrt'],
    'stack': '( n -- n )',
    'summary': 'Compute the square root of the top element on the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FSQRT. '
        'sqrt is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['4 _sqrt', '2'],
    ],
  },
  {
    'names': ['floor'],
    'stack': '( n -- n )',
    'summary': 'Round the number on top of the stack downward.',
    'description': [
        floating_point_text
    ],
    'examples': [
        ['1.234 _floor', '1'],
    ],
  },
  {
    'names': ['ceil'],
    'stack': '( n -- n )',
    'summary': 'Round the number on top of the stack upward.',
    'description': [
        'Not in traditional Forth, included for completeness, borrowing the '
        'C function name. '
        ,
        floating_point_text
    ],
    'examples': [
        ['1.234 _ceil', '2'],
    ],
  },
  {
    'names': ['abs'],
    'stack': '( n -- n )',
    'summary': 'Compute the absolute value of the number on top of the stack.',
    'description': [
        'This word is roughly equivalent to the traditional Forth word FABS. '
        'abs is used to emphasize the primary stack being floating point. '
        ,
        floating_point_text
    ],
    'examples': [
        ['-123 _abs', '123'],
        ['-1.2 _abs', '1.2'],
    ],
  },
  {
    'names': ['pi'],
    'stack': '( -- n )',
    'summary': 'Push pi onto the stack.',
    'description': [
        'This word is Haiku Forth specific, included for completeness. '
        ,
        floating_point_text
    ],
    'examples': [
        ['pi', '3.1415926535897931'],
    ],
  },
  {
    'names': ['z+'],
    'stack': '( a b c d -- a+c b+d )',
    'summary': 'Complex addition.',
    'description': [
        'Haiku Forth specific word nominally to add two complex numbers on '
        'the stack. It could be used to add a two vector as well, as which '
        'part it real or imaginary does not matter for this operation. '
        ,
        floating_point_text
    ],
    'examples': [
        ['1 11 5 9 z+', '6 20'],
    ],
  },
  {
    'names': ['z*'],
    'stack': '( a b c d -- a*c-b*d a*d+b*c )',
    'summary': 'Complex multiplication.',
    'description': [
        'Haiku Forth specific word to multiple two complex numbers on the '
        'stack. Complex number are expected to be stored on the stack with '
        'the real part deeper in the stack (corresponding to real part first '
        'when pushing constants onto the stack. '
        ,
        floating_point_text
    ],
    'examples': [
        ['1 11 5 9 z*', '-94 64'],
        ['_2dup _z*', 'complex square'],
    ],
  },
  {
    'names': ['random'],
    'stack': '( -- n )',
    'summary': 'Return a pseudo-random number in the range [0, 1).',
    'description': [
        'This word is Haiku Forth specific.'
        ,
        floating_point_text
    ],
  },
  {
    'names': ['if', 'else', 'then'],
    'stack': '( f -- )',
    'summary': 'Describe a conditional branch.',
    'description': [
        'As in tradition Forth, one value is removed from the data stack. '
        'If that value is considered "true", the true-case is executed, '
        'execution then continues after "then". If not, the false-case if '
        'any is executed, execution then continues after "then". '
        ,
        'Much of the complexity surrounding interpreter state with flow '
        'control is glossed over, as these words are implemented using '
        'Javascript flow control words. '
        , 
        'if <true-case> else <false-case> then'
        ,
        'if <true-case> then'
        ,
        boolean_text,
    ],
    'examples': [
        [': foo 2dup < if drop else swap drop then ; 3 4 foo', '3 (min)'],
    ],
  },
  {
    'names': [':', ';'],
    'summary': 'Define a new word.',
    'description': [
        ': <word> <definition...> ; '
        ,
        'The complexity surrounding the interpreter state with word '
        'definition is glossed over in Haiku Forth. The current '
        'implementation works on top of Javascript function definition. '
    ],
    'examples': [
        [': square ( n -- n ) dup * ; 4 square', '16'],
    ],
  },
]


# Precompute the words ids and entry map.
word_ids = {}
entry_map = {}
for entry in core_words:
  ids = []
  for name in entry['names']:
    id = base64.b16encode(name)
    word_ids[name] = id
    entry_map[id] = entry
    ids.append(id)
  entry['stack'] = entry.get('stack', '')
  entry['description'] = entry.get('description', [])
  entry['ids'] = ids
  entry['id'] = ids[0]
  entry['name'] = ' '.join(entry['names'])


def LookupWordId(word):
  return word_ids.get(word)


HTML_ENCODING = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&apos;',
  '\r': '',
  '\n': '<br>\n',
}


def FormatWord(word):
  id = LookupWordId(word)
  result = []
  if id:
    result.append('<a href="/word-view/' + id + '">')
  result.append(''.join(HTML_ENCODING.get(ch, ch) for ch in word))
  if id:
    result.append('</a>')
  return ''.join(result)


def FormatHtml(str):
  result = []
  word = ''
  for ch in str:
    if ch in '\r\n\t ':
      if word:
        result.append(FormatWord(word))
        word = ''
      result.append(HTML_ENCODING.get(ch, ch))
    else:
      word += ch
  if word:
    result.append(FormatWord(word))
  return ''.join(result)


def FormatHtmlPrint(str):
  return ''.join(HTML_ENCODING.get(ch, ch) for ch in str)


def LookupEntryById(id):
  return entry_map.get(id)
