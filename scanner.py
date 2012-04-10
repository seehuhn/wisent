# scanner.py - tokenize Wisent's input
#
# Copyright (C) 2008, 2009, 2012  Jochen Voss <voss@seehuhn.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

def isascii(s):
    return all(ord(c)<128 for c in s)

def conv(s):
    if isinstance(s, unicode) and isascii(s):
        return str(s)
    else:
        return s

def tokens(source):
    """Generator to read input and break it into tokens.

    'Source' must iterate over the lines of input (it could for
    example be a file-like object).  The generator then yields
    4-tuples consisting of a type string, a value, the line number
    (starting with 1) and the column number (starting with 1): if the
    type string is one of "token" or "string", the value is the
    corresponding input character sequence.  Otherwise both the type
    string and the value are the same, single input character.

    If the input ends in an unterminated string or comment, a
    SyntaxError exception is raised.
    """
    s = None
    state = None
    line = 1
    for l in source:
        l = l.expandtabs()
        if not l.endswith("\n"):
            l = l + '\n'
        for col, c in enumerate(l):
            if state == "skip":
                state = None
            elif state == "word":
                if c.isalnum() or c in "-_":
                    s += c
                else:
                    yield ("token", conv(s), line0, col0)
                    state = None
            elif state == "string":
                if c == '\\':
                    state = "quote"
                elif c == sep:
                    yield ("string", conv(s), line0, col0)
                    state = "skip"
                else:
                    s += c
            elif state == "quote":
                s += c
                state = "string"
            elif state == "comment" and c == '\n':
                state = "skip"

            if state is None:
                line0 = line
                col0 = col+1
                if c == "'":
                    state = "string"
                    sep = "'"
                    s = ""
                elif c == '"':
                    state = "string"
                    sep = '"'
                    s = ""
                elif c.isalnum() or c == "_":
                    state = "word"
                    s = c
                elif c == "#":
                    state = "comment"
                elif c.isspace():
                    state = "skip"
                else:
                    yield (conv(c), conv(c), line0, col0)
                    state = "skip"
        line += 1

    if state == "word":
        yield ("token", conv(s), line0, col0)
    elif state not in [ None, "skip", "comment" ]:
        if l[-1] == '\n':
            l = l[:-1]
        msg = "unterminated string"
        raise SyntaxError(msg, (source.name, line0, col0, l[-20:]))
