#! /usr/bin/env python

from grammar import Grammar

def emit_class_parseerror():
    print "class ParseError(Exception):"
    print
    print "    def __init__(self, msg, data=None):"
    print "        self.msg = msg"
    print "        self.data = data"
    print
    print "    def __str__(self):"
    print "        if self.data is not None:"
    print "            return 'parse error: %s, %s'%(self.msg,self.data)"
    print "        else:"
    print "            return 'parse error: %s'%self.msg"

def emit_rules(g):
    keys = sorted(g.rules.keys())
    print "    rules = {"
    for k in keys:
        print "        %s: %s,"%(repr(k), repr(g.rules[k]))
    print "    }"

