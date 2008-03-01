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
from text import layout_list
from sniplets import emit_class_parseerror, emit_rules

def LR0_closure(g, U):
    U = set(U)
    current = U
    while current:
        new = set()
        for key,l,n in current:
            if n == l: continue
            r = g.rules[key]
            X = r[n]
            if X in g.terminal: continue
            for k in g.rules:
                s = g.rules[k]
                if s[0] != X: continue
                x = (k,len(s),1)
                if x not in U:
                    new.add(x)
        U |= new
        current = new
    return frozenset(U)

def LR0_goto(g, U, X):
    T = [ (key,l,n+1) for key,l,n in U if n<l and g.rules[key][n]==X ]
    return LR0_closure(g, T)

def LR0_states(g):
    stateno = 0
    T = {}
    E = set()
    Tinv = {}

    for key in g.rules:
        if g.rules[key][0] == g.start:
            break
    state = LR0_closure(g, [ (key,len(g.rules[key]),1) ])
    T[stateno] = state
    Tinv[state] = stateno
    stateno += 1

    done = False
    while not done:
        done = True
        for I in T.keys():
            for key,l,n in T[I]:
                if n == l: continue
                r = g.rules[key]
                X = r[n]
                J = LR0_goto(g, T[I], X)
                if J not in Tinv:
                    T[stateno] = J
                    Tinv[J] = stateno
                    stateno += 1
                    done = False
                E.add((I,Tinv[J]))
    return  T, E

def LALR1_closure(self, U):
    rules = self.rules
    U = set(U)
    current = U
    while current:
        new = set()
        for key,l,n,X in current:
            if n == l:
                continue
            r = rules[key]
            lookahead = self.first_tokens(list(r[n+1:])+[X])
            if r[n] in self.terminal: continue
            for k in rules:
                s = rules[k]
                if s[0] != r[n]: continue
                for Z in lookahead:
                    zz = (k,len(s),1,Z)
                    if zz not in U:
                        new.add(zz)
        current = new
        U |= new
    return frozenset(U)

def LALR1_goto(g, U, X):
    T = [ (key,l,n+1,next) for key,l,n,next in U if n<l and g.rules[key][n]==X ]
    return LALR1_closure(g, T)

def LALR1_tables(g):
    stateno = 0
    T = {}
    Tinv = {}
    E = {}

    for key in g.rules:
        if g.rules[key][0] == g.start:
            break
    state = LALR1_closure(g, [ (key,len(g.rules[key]),1,g.terminator) ])
    T[stateno] = state
    Tinv[state] = stateno
    stateno += 1

    done = False
    while not done:
        done = True
        for I in T.keys():
            if I not in E: E[I] = {}
            for key,l,n,next in T[I]:
                if n == l: continue
                r = g.rules[key]
                X = r[n]
                J = LALR1_goto(g, T[I], X)
                if J not in Tinv:
                    T[stateno] = J
                    Tinv[J] = stateno
                    stateno += 1
                    done = False
                if X not in E[I]: E[I][X] = []
                if Tinv[J] not in E[I][X]:
                    E[I][X].append(Tinv[J])
                    done = False
    return  T, E

def LALR1_ifollow(g, T):
    ifollow = {}
    for S in T:
        for key,l,n in T[S]:
            if n > l-2:
                continue
            r = g.rules[key]
            X = r[n]
            if X not in g.nonterminal:
                continue
            if (X,S) not in ifollow:
                ifollow[(X,S)] = set()
            ifollow[(X,S)] |= g.first_tokens(r[n+1:])

            if n == 1 and r[0] == g.start:
                 ifollow[(r[0],S)] = set([g.terminator])
    return ifollow

g = Grammar(read_rules(argv[1]))
T,E = LR0_states(g)

ifollow = LALR1_ifollow(g, T)

keys = sorted(T.keys())
for i in keys:
    print "state %s:"%i
    for k,l,n in T[i]:
        r = g.rules[k]
        rr = map(repr, r)
        print "  "+rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])
    print "edges to "+" ".join(map(str,sorted(set([j for (k,j) in E if k == i]))))
    print [ (X,S,"{"+",".join(map(str,ifollow[(X,S)]))+"}") for X,S in ifollow if S==i ]
    print

raise SystemExit(1)

T, E = LALR1_tables(g)

rtab = {}
for I in T:
    reductions = []
    for key,l,n,next in T[I]:
        if n<l:
            continue
        if (I,next) in rtab:
            print >>stderr, "not an LALR(1) grammar (reduce-reduce conflict)"
            raise SystemExit(1)
        r = g.rules[key]
        rtab[(I,next)] = (key, r[0], n-1)

stab = {}
gtab = {}
for I in E:
    EI = E[I]
    if not EI:
        continue
    for X in EI:
        if (I,X) in rtab:
            print >>stderr, "not an LALR(1) grammar (shift-reduce conflict)"
            raise SystemExit(1)
        JJ = EI[X]
        if len(JJ)>1:
            # TODO: can this really occur?
            print >>stderr, "not an LALR(1) grammar (shift-shift conflict)"
            raise SystemExit(1)
        J = JJ[0]
        if X in g.terminal:
            stab[(I,X)] = J
            if X == g.terminator:
                final_state = J
        else:
            gtab[(I,X)] = J

print "from itertools import chain"
print
emit_class_parseerror()
print
print "class Parser(object):"
print
print "    _rtab = {"
for l in layout_list("        ", ["%s: %s"%(repr(i),repr(rtab[i])) for i in rtab], ""):
    print l
print "    }"
print
print "    _stab = {"
for l in layout_list("        ", ["(%d,%s): %s"%(i,repr(x),stab[(i,x)]) for i,x in stab], ""):
    print l
print "    }"
print
print "    _gtab = {"
for l in layout_list("        ", ["(%d,%s): %s"%(i,repr(x),gtab[(i,x)]) for i,x in gtab], ""):
    print l
print "    }"
print
print "    def __init__(self):"
print "        pass"
print
print "    def _peek(self):"
print "        if not self.valid:"
print "            next = self.input.next()"
print "            self.t,self.val = next[0], next[1:]"
print "            self.valid = True"
print "        return self.t"
print
print "    def _shift(self):"
print "        t = self._peek()"
print "        self.stack.append((self.state,t,self.val))"
print "        print 'shift '+repr(t)+' -> '+str(self._stab[(self.state,t)])"
print "        self.state = self._stab[(self.state,t)]"
print "        self.valid = False"
print
print "    def parse(self, input):"
print "        self.input = chain(input,[(%s,)])"%repr(g.terminator)
print "        self.valid = False"
print "        self.state = 0"
print "        self.stack = []"
print "        while self.state != %s:"%final_state
print "            print 'state %s:'%self.state,"
print "            X = self._peek()"
print "            if (self.state,X) in self._rtab:"
print "                key,X,n = self._rtab[(self.state,X)]"
print "                print 'reduce '+str(key)"
print "                print '  %s -> %s '%(repr(X),repr(self.stack[-n:]))"
print "                oldstate = self.stack[-n][0]"
print "                self.stack[-n:] = [ (oldstate, X,[(Y,val) for s,Y,val in self.stack[-n:]]) ]"
print "                if X == %s:"%repr(g.start)
print "                    break"
print "                self.state = self._gtab[(oldstate,X)]"
print "            else:"
print "                self._shift()"
print "                "
print "        return (self.stack[0][1], self.stack[0][2])"
