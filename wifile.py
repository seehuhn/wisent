#! /usr/bin/env python

class ParseError(Exception):

    def __init__(self, msg, fname=None, line=None):
	self.msg = msg
	self.fname = fname
	self.line = line

    def __str__(self):
	res = ""
	if self.fname: res += self.fname+":"
	if self.line: res += str(self.line)+":"
	if res: res += " "
	return res+"parse error: "+self.msg

wordchar = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
whitespace = " \t\r\n"

def tokens(source, special=[], comment=[]):
    def read_and_count(fname):
	source["line"] = 1
	for c in open(fname).read():
	    yield c
	    if c == '\n': source["line"] += 1
    input = read_and_count(source["fname"])
    c = None
    s = None
    state = "normal"
    try:
	while True:
	    if state == "normal":
		c = input.next()
		state = "test"
	    elif state == "test":
		if c in special:
		    yield (1,c)
		    state = "normal"
		elif c == "'":
		    state = "string"
		    sep = "'"
		    s = ""
		elif c == '"':
		    state = "string"
		    sep = '"'
		    s = ""
		elif c in wordchar:
		    state = "word"
		    s = c
		elif c in comment:
		    state = "comment"
		elif c in whitespace:
		    state = "normal"
		else:
		    yield (0,c)
		    state = "normal"
	    elif state == "word":
		c = input.next()
		if c in wordchar:
		    s += c
		else:
		    yield (0,s)
		    state = "test"
	    elif state == "string":
		c = input.next()
		if c == '\\':
		    state = "quote"
		elif c == sep:
		    yield (0,s)
		    state = "normal"
		else:
		    s += c
	    elif state == "quote":
		c = input.next()
		s += c
	    elif state == "comment":
		c = input.next()
		if c == '\n': state = "normal"
    except StopIteration:
	pass
    if state == "word":
	yield (0,s)
	state = "normal"
    if state == "comment":
	raise ParseError("missing end of line",
			  source["fname"], source["line"])
    if state != "normal":
	raise ParseError("unterminated string",
			  source["fname"], source["line"])

def read_rules(fname):
    source = { 'fname': fname, 'line': None }
    input = tokens(source, ":;|", "#")
    state = "head"
    while True:
	try:
	    special,token = input.next()
	except StopIteration:
	    break
	if state == "head":
	    if special: raise  ParseError("missing production head",
					   source["fname"], source["line"])
            if token.lstrip(wordchar) != "":
                raise  ParseError("invalid nonterminal '%s'"%token,
				   source["fname"], source["line"])
	    head = token
	    state = "colon"
	elif state == "colon":
	    if token != ":" or not special:
		msg = "missing colon after production head '%s'"%head
		raise  ParseError(msg, source["fname"], source["line"])
	    body = []
	    state = "rule"
	elif state == "rule":
	    if special:
		if token == "|":
		    yield tuple([head]+body)
		    body = []
		elif token == ";":
		    yield tuple([head]+body)
		    state = "head"
	    else:
		body.append(token)
    if state != "head":
	raise ParseError("incomplete grammar file",
			  source["fname"], source["line"])
