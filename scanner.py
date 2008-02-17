#! /usr/bin/env python

def tokens(source):
    """Generator to read input and break it into tokens.

    'Source' must iterate over the lines of input, it could, for
    example, be a file-like object.  The generator then yield 3-tuples
    consisting of a type string, a value and a line number: if the
    type string is one of _token_ or _string_, the value is the
    corresponding input character sequence.  Otherwise both the type
    string and the value are the same, single input character.  The
    third element in the tuple is the 0-based input line number.

    If the input ends in an unterminated string or comment, a
    ValueError exception is raised.
    """
    s = None
    state = None
    line = 0
    for l in source:
        for c in l:
            if state == "normal":
                state = None
            elif state == "word":
                if c.isalnum() or c == "_":
                    s += c
                else:
                    yield ("token", s, line)
                    state = None
            elif state == "string":
                if c == '\\':
                    state = "quote"
                elif c == sep:
                    yield ("string", s, line)
                    state = "normal"
                else:
                    s += c
            elif state == "quote":
                s += c
            elif state == "comment":
                if c == '\n':
                    state = "normal"

            if state is None:
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
                    state = "normal"
                else:
                    yield (c, c, line)
                    state = "normal"
        line += 1

    if state == "word":
	yield ("token", s, line)
    elif state != "normal":
	raise ValueError("incomplete input")
