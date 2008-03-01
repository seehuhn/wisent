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

from scanner import tokens
from parser import Parser

def rules(tree):
    for rule in tree[2:]:
        target = rule[2][1:3]
        for l in rule[4:-1]:
            if l[1] != "list":
                continue
            yield tuple([target]+[x[1:3] for x in l[2:]])

def read_rules(fname, aux):
    p = Parser()
    fd = open(fname)
    try:
        res = p.parse_tree(tokens(fd))
    except SyntaxError, e:
        print >>stderr, "%s:%d:%d: %s"%(e.filename, e.lineno, e.offset, e.msg)
        raise SystemExit(1)
    fd.close()

    for l in rules(res):
        if l[0][0] == 'token' and l[0][1].startswith("_"):
            aux.add(l[0][1])
        todo = []
        ll = []
        attention = ""
        for token in reversed(l):
            if attention == "+":
                seq = token[1]+"+"
                if seq not in aux:
                    todo.append((seq, token[1]))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                attention = False
            elif attention == "*":
                seq = token[1]+"*"
                if seq not in aux:
                    todo.append((seq,))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                attention = False
            elif token[0] == '*':
                attention = "*"
            elif token[0] == '+':
                attention = "+"
            else:
                ll.append(token[1])
        yield tuple(reversed(ll))
        while todo:
            yield todo.pop(0)
