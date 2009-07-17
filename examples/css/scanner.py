#! /usr/bin/env python

import re

short = {
  'h': r'[0-9a-f]',
  'nonascii': r'[\200-\377]',
  'unicode': r'\\{h}{1,6}(\r\n|[ \t\r\n\f])?',
  'escape': r'{unicode}|\\[^\r\n\f0-9a-f]',
  'nmstart': r'[_a-z]|{nonascii}|{escape}',
  'nmchar': r'[_a-z0-9-]|{nonascii}|{escape}',
  'string1': r'"([^\n\r\f\\"]|\\{nl}|{escape})*"',
  'string2': r"'([^\n\r\f\\']|\\{nl}|{escape})*'",
  'invalid1': r'"([^\n\r\f\\"]|\\{nl}|{escape})*',
  'invalid2': r"'([^\n\r\f\\']|\\{nl}|{escape})*",
  'comment': r'/\*[^*]*\*+([^/*][^*]*\*+)*/',
  'ident': r'-?{nmstart}{nmchar}*',
  'name': r'{nmchar}+',
  'num': r'[0-9]+|[0-9]*\.[0-9]+',
  'string': r'{string1}|{string2}',
  'invalid': r'{invalid1}|{invalid2}',
  'url': r'([!#$%&*-~]|{nonascii}|{escape})*',
  's': r'[ \t\r\n\f]+',
  'w': r'{s}?',
  'nl': r'\n|\r\n|\r|\f',
  'A': r'a|\\0{0,4}(41|61)(\r\n|[ \t\r\n\f])?',
  'C': r'c|\\0{0,4}(43|63)(\r\n|[ \t\r\n\f])?',
  'D': r'd|\\0{0,4}(44|64)(\r\n|[ \t\r\n\f])?',
  'E': r'e|\\0{0,4}(45|65)(\r\n|[ \t\r\n\f])?',
  'G': r'g|\\0{0,4}(47|67)(\r\n|[ \t\r\n\f])?|\\g',
  'H': r'h|\\0{0,4}(48|68)(\r\n|[ \t\r\n\f])?|\\h',
  'I': r'i|\\0{0,4}(49|69)(\r\n|[ \t\r\n\f])?|\\i',
  'K': r'k|\\0{0,4}(4b|6b)(\r\n|[ \t\r\n\f])?|\\k',
  'L': r'l|\\0{0,4}(4c|6c)(\r\n|[ \t\r\n\f])?|\\l',
  'M': r'm|\\0{0,4}(4d|6d)(\r\n|[ \t\r\n\f])?|\\m',
  'N': r'n|\\0{0,4}(4e|6e)(\r\n|[ \t\r\n\f])?|\\n',
  'O': r'o|\\0{0,4}(4f|6f)(\r\n|[ \t\r\n\f])?|\\o',
  'P': r'p|\\0{0,4}(50|70)(\r\n|[ \t\r\n\f])?|\\p',
  'R': r'r|\\0{0,4}(52|72)(\r\n|[ \t\r\n\f])?|\\r',
  'S': r's|\\0{0,4}(53|73)(\r\n|[ \t\r\n\f])?|\\s',
  'T': r't|\\0{0,4}(54|74)(\r\n|[ \t\r\n\f])?|\\t',
  'U': r'u|\\0{0,4}(55|75)(\r\n|[ \t\r\n\f])?|\\u',
  'X': r'x|\\0{0,4}(58|78)(\r\n|[ \t\r\n\f])?|\\x',
  'Z': r'z|\\0{0,4}(5a|7a)(\r\n|[ \t\r\n\f])?|\\z',
}

patterns = [
  (r'{s}', 'S'),
  (r'/\*[^*]*\*+([^/*][^*]*\*+)*/', None),
  (r'<!--', 'CDO'),
  (r'-->', 'CDC'),
  (r'~=', 'INCLUDES'),
  (r'\|=', 'DASHMATCH'),
  (r'{w}\{', 'LBRACE'),
  (r'{w}\+', 'PLUS'),
  (r'{w}>', 'GREATER'),
  (r'{w},', 'COMMA'),
  (r'{string}', 'STRING'),
  (r'{invalid}', 'INVALID'),    # unclosed string
  (r'{ident}', 'IDENT'),
  (r'#{name}', 'HASH'),
  (r'@{I}{M}{P}{O}{R}{T}', 'IMPORT_SYM'),
  (r'@{P}{A}{G}{E}', 'PAGE_SYM'),
  (r'@{M}{E}{D}{I}{A}', 'MEDIA_SYM'),
  (r'@charset ', 'CHARSET_SYM'),
  (r'!({w}|{comment})*{I}{M}{P}{O}{R}{T}{A}{N}{T}', 'IMPORTANT_SYM'),
  (r'{num}{E}{M}', 'EMS'),
  (r'{num}{E}{X}', 'EXS'),
  (r'{num}{P}{X}', 'LENGTH'),
  (r'{num}{C}{M}', 'LENGTH'),
  (r'{num}{M}{M}', 'LENGTH'),
  (r'{num}{I}{N}', 'LENGTH'),
  (r'{num}{P}{T}', 'LENGTH'),
  (r'{num}{P}{C}', 'LENGTH'),
  (r'{num}{D}{E}{G}', 'ANGLE'),
  (r'{num}{R}{A}{D}', 'ANGLE'),
  (r'{num}{G}{R}{A}{D}', 'ANGLE'),
  (r'{num}{M}{S}', 'TIME'),
  (r'{num}{S}', 'TIME'),
  (r'{num}{H}{Z}', 'FREQ'),
  (r'{num}{K}{H}{Z}', 'FREQ'),
  (r'{num}{ident}', 'DIMENSION'),
  (r'{num}%', 'PERCENTAGE'),
  (r'{num}', 'NUMBER'),
  (r'{U}{R}{L}\({w}{string}{w}\)', 'URI'),
  (r'{U}{R}{L}\({w}{url}{w}\)', 'URI'),
  (r'{ident}\(', 'FUNCTION'),
]

cpatterns = []
for pat, val in patterns:
    done = False
    while not done:
        done = True
        def replfn(m):
            return "("+short[m.group(1)]+")"
        pat,n = re.subn(r'\{([a-zA-Z][a-zA-Z0-9]*)\}', replfn, pat)
        if n > 0:
            done = False
    try:
        pat = re.compile(pat, re.IGNORECASE)
    except:
        print pat
        raise
    cpatterns.append((pat, val))

def tokens(text):
    line = 1
    pos = 1
    while text:
        best_len = 0
        best_val = None
        for cpat, val in cpatterns:
            m = cpat.match(text)
            if m is not None and m.end() > best_len:
                best_len = m.end()
                best_val = val
        if best_len == 0:
            best_val = text[0]
            best_len = 1
        s, text = text[:best_len], text[best_len:]
        yield (best_val, s, line, pos)

        if '\n' in s:
            for c in s:
                if c == '\n':
                    line += 1
            pos = len(s)-s.rfind('\n')
        else:
            pos += len(s)
