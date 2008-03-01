#! /usr/bin/env python
#
# Copyright (C) 2008  Jochen Voss <voss@seehuhn.de>
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

from sys import argv, stderr
from grammar import Grammar
from wifile import read_rules
from sniplets import *

g = Grammar(read_rules(argv[1]))

tab = {}
for n in g.nonterminal:
    tab[n] = {}
    for t in g.terminal:
        tab[n][t] = set()
for key in g.rules:
    r = g.rules[key]
    for t in g.first_tokens(r[1:]):
        tab[r[0]][t].add(key)
    if not g.is_nullable(r[1:]):
        continue
    for t in g.follow_tokens(r[0]):
        tab[r[0]][t].add(key)

for n in tab:
    for t in tab[n]:
        if len(tab[n][t]) <= 1:
            continue
        print >>stderr, "not an LL(1) grammar"
        raise SystemExit(1)

alnum = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

names = {}
for k,n in enumerate(sorted(g.nonterminal)):
    s = str(n)
    if set(s) <= alnum:
        names[n] = "_parse_"+s
    else:
        names[n] = "_parse%s"%k

print "from itertools import chain"
print
emit_class_parseerror()
print
print "class Parser(object):"
print
print "    def __init__(self):"
print "        pass"
print
print "    def parse(self, input):"
print "        self.input = chain(input,[(%s,)])"%repr(g.terminator)
print "        self.valid = False"
print "        return self.%s()"%names[g.start]
print
print "    def _peek(self):"
print "        if not self.valid:"
print "            next = self.input.next()"
print "            self.t,self.val = next[0], next[1:]"
print "            self.valid = True"
print "        return self.t"
print
print "    def _eat(self, token):"
print "        t = self._peek()"
print "        if t != token:"
msg = '"unexpected %s (%s)"%(repr(t),repr(self.val))'
print "            raise ParseError(%s, self.val)"%msg
print "        self.valid = False"
print "        return (t,self.val)"
for n in sorted(g.nonterminal):
    print
    print "    def %s(self):"%names[n]
    print "        t = self._peek()"
    nt = tab[n]
    tokens = {}
    for t in nt:
        for r in nt[t]:
            if r in tokens:
                tokens[r].append(t)
            else:
                tokens[r] = [ t ]

    i = "if"
    for rule in tokens:
        r = g.rules[rule]
        tt = tokens[rule]
        if len(tt) > 1:
            xx = (i, ", ".join(map(repr, tt)))
            print "        %s t in [ %s ]:"%xx
        else:
            print "        %s t == %s:"%(i,repr(tt[0]))

        args = [ ]
        for t in r[1:]:
            if t in g.nonterminal:
                args.append("self.%s()"%names[t])
            else:
                args.append("self._eat(%s)"%(repr(t)))
        if rule is not None:
            xx = (repr(rule),repr(r[0])," ".join(map(repr, r[1:])))
        print "            args = [ %s ]"%", ".join(args)
        i = "elif"
    print "        else:"
    msg = '"unexpected %s"%repr(t)'
    print "            raise ParseError(%s, self.val)"%msg
    if n == g.start:
        print "        return args[0]"
    else:
        print "        return (%s,args)"%repr(n)
