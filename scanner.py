#! /usr/bin/env python

def tokens(source):
    """Generator to read input and break it into tokens.

    'Source' must iterate over the lines of input, it could, for
    example, be a file-like object.  The generator then yields
    4-tuples consisting of a type string, a value, the line number
    (starting with 1) and the column number (starting with 1): if the
    type string is one of "token" or "string", the value is the
    corresponding input character sequence.  Otherwise both the type
    string and the value are the same, single input character.  The
    third element of the tuple is the input line number.

    If the input ends in an unterminated string or comment, a
    SyntaxError exception is raised.
    """
    s = None
    state = None
    line = 1
    for l in source:
        for col, c in enumerate(l):
            if state == "skip":
                state = None
            elif state == "word":
                if c.isalnum() or c == "_":
                    s += c
                else:
                    yield ("token", s, line0, col0)
                    state = None
            elif state == "string":
                if c == '\\':
                    state = "quote"
                elif c == sep:
                    yield ("string", s, line0, col0)
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
                    yield (c, c, line0, col0)
                    state = "skip"
        line += 1

    if state == "word":
	yield ("token", s, line0, col0)
    elif state not in [ None, "skip", "comment" ]:
        if l[-1] == '\n':
            l = l[:-1]
        msg = "unterminated string"
	raise SyntaxError(msg, (source.name, line0, col0, l[-20:]))
