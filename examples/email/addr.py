#! /usr/bin/env python
# addr.py - illustrate the use of a Wisent-generated parser
# example code autogenerated on 2010-09-16 16:18:05
# generator: wisent 0.6.1, http://seehuhn.de/pages/wisent
# source: header.wi

from sys import stderr, argv

from scanner import tokenize
from parser import Parser

def print_tree(tree, terminals, indent=0):
    """Print a parse tree to stdout."""
    prefix = "    "*indent
    if tree[0] in terminals:
        print prefix + repr(tree)
    else:
        print prefix + unicode(tree[0])
        for x in tree[1:]:
            print_tree(x, terminals, indent+1)

def prepare(s):
    for tp, val in tokenize(s):
        if tp == "comment":
            pass
        elif tp == "special":
            yield (val, val)
        else:
            yield (tp, val)

p = Parser()
try:
    tree = p.parse(prepare(argv[1]))
except p.ParseErrors, e:
    for token,expected in e.errors:
        if token[0] == p.EOF:
            print >>stderr, "unexpected end of file"
            continue

        found = repr(token[0])
        if len(expected) == 1:
            msg = "missing %s (found %s)"%(repr(expected[0]), found)
        else:
            msg1 = "parse error before %s, "%found
            l = sorted([ repr(s) for s in expected ])
            msg2 = "expected one of "+", ".join(l)
            msg = msg1+msg2
        print >>stderr, msg
    raise SystemExit(1)

print_tree(tree, p.terminals)
