#! /usr/bin/env python

from sys import argv, stderr
from grammar import Grammar
from wifile import read_rules
from text import layout_list
from sniplets import emit_class_parseerror, emit_rules

def LR1_closure(g, U):
    U = set(U)
    current = U
    while current:
        new = set()
        for key,l,n,next in current:
            if n == l: continue
            r = g.rules[key]
            X = r[n]
            if X in g.terminal: continue
            for k in g.rules:
                s = g.rules[k]
                if s[0] != X: continue
                for Y in g.first_tokens(list(r[n+1:])+[next]):
                    x = (k,len(s),1,Y)
                    if x not in U:
                        new.add(x)
        U |= new
        current = new
    return frozenset(U)

def LR1_goto(g, U, X):
    T = [ (key,l,n+1,next) for key,l,n,next in U if n<l and g.rules[key][n]==X ]
    return LR1_closure(g, T)

def LR1_tables(g):
    stateno = 0
    T = {}
    Tinv = {}
    E = {}

    for key in g.rules:
        if g.rules[key][0] == g.start:
            break
    state = LR1_closure(g, [ (key,len(g.rules[key]),1,g.terminator) ])
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
                J = LR1_goto(g, T[I], X)
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

g = Grammar(read_rules(argv[1]))
T, E = LR1_tables(g)

rtab = {}
for I in T:
    reductions = []
    for key,l,n,next in T[I]:
        if n<l:
            continue
        if (I,next) in rtab:
            print >>stderr, "not an LR(1) grammar (reduce-reduce conflict)"
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
            print >>stderr, "not an LR(1) grammar (shift-reduce conflict)"
            raise SystemExit(1)
        JJ = EI[X]
        if len(JJ)>1:
            # TODO: can this really occur?
            print >>stderr, "not an LR(1) grammar (shift-shift conflict)"
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
print "        self.state = self._stab[(self.state,t)]"
print "        self.valid = False"
print
print "    def parse(self, input):"
print "        self.input = chain(input,[(%s,)])"%repr(g.terminator)
print "        self.valid = False"
print "        self.state = 0"
print "        self.stack = []"
print "        while self.state != %s:"%final_state
print "            X = self._peek()"
print "            if (self.state,X) in self._rtab:"
print "                key,X,n = self._rtab[(self.state,X)]"
print "                oldstate = self.stack[-n][0]"
print "                self.stack[-n:] = [ (oldstate, X,[(Y,val) for s,Y,val in self.stack[-n:]]) ]"
print "                if X == %s:"%repr(g.start)
print "                    break"
print "                self.state = self._gtab[(oldstate,X)]"
print "            else:"
print "                self._shift()"
print "                "
print "        return (self.stack[0][1], self.stack[0][2])"
