#! /usr/bin/env python

from sys import argv, stderr
from grammar import Grammar
from wifile import read_rules
from text import layout_list
from sniplets import emit_class_parseerror, emit_rules

class LR1(Grammar):

    def __init__(self, *args, **kwargs):
        Grammar.__init__(self, *args, **kwargs)

        self.starts = {}
        for X in self.symbols:
            self.starts[X] = []
        for k,s in self.rules.items():
            self.starts[s[0]].append((k,len(s)))

        self._cache = {}

        self.generate_tables()
        self.check()

    def closure(self, U):
        rules = self.rules
        U = set(U)
        current = U
        while current:
            new = set()
            for key,l,n,Y in current:
                if n == l: continue
                r = rules[key]
                lookahead = self.first_tokens(list(r[n+1:])+[Y])
                for k,l in self.starts[r[n]]:
                    for Y in lookahead:
                        x = (k,l,1,Y)
                        if x not in U:
                            new.add(x)
            current = new
            U |= new
        return frozenset(U)

    def goto(self, U, X):
        if (U,X) in self._cache:
            return self._cache[(U,X)]
        rules = self.rules
        T = [ (key,l,n+1,Y) for key,l,n,Y in U if n<l and rules[key][n]==X ]
        res = self.closure(T)
        self._cache[(U,X)] = res
        return res

    def generate_tables(self):
        stateno = 0
        T = {}
        Tinv = {}
        E = {}

        for key in self.rules:
            if self.rules[key][0] == self.start:
                break
        state = self.closure([ (key,len(self.rules[key]),1,self.terminator) ])
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
                    r = self.rules[key]
                    X = r[n]
                    J = self.goto(T[I], X)
                    if J not in Tinv:
                        T[stateno] = J
                        Tinv[J] = stateno
                        stateno += 1
                        done = False
                    if X not in E[I]: E[I][X] = []
                    if Tinv[J] not in E[I][X]:
                        E[I][X].append(Tinv[J])
                        done = False
        self.T = T
        self.E = E

    def check(self):
        T = self.T
        E = self.E

        self.rtab = {}
        for I in T:
            reductions = []
            for key,l,n,next in T[I]:
                if n<l:
                    continue
                if (I,next) in self.rtab:
                    print >>stderr, "not an LR(1) grammar (reduce-reduce conflict)"
                    raise SystemExit(1)
                r = self.rules[key]
                self.rtab[(I,next)] = (key, r[0], n-1)

        self.stab = {}
        self.gtab = {}
        for I in E:
            EI = E[I]
            if not EI:
                continue
            for X in EI:
                if (I,X) in self.rtab:
                    print >>stderr, "not an LR(1) grammar (shift-reduce conflict)"
                    raise SystemExit(1)
                JJ = EI[X]
                if len(JJ)>1:
                    # TODO: can this really occur?
                    print >>stderr, "not an LR(1) grammar (shift-shift conflict)"
                    raise SystemExit(1)
                J = JJ[0]
                if X in self.terminal:
                    self.stab[(I,X)] = J
                    if X == self.terminator:
                        self.final_state = J
                else:
                    self.gtab[(I,X)] = J

g = LR1(read_rules(argv[1]))

print "from itertools import chain"
print
emit_class_parseerror()
print
print "class Parser(object):"
print
print "    _rtab = {"
for l in layout_list("        ", ["%s: %s"%(repr(i),repr(g.rtab[i])) for i in g.rtab], ""):
    print l
print "    }"
print
print "    _stab = {"
for l in layout_list("        ", ["(%d,%s): %s"%(i,repr(x),g.stab[(i,x)]) for i,x in g.stab], ""):
    print l
print "    }"
print
print "    _gtab = {"
for l in layout_list("        ", ["(%d,%s): %s"%(i,repr(x),g.gtab[(i,x)]) for i,x in g.gtab], ""):
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
print "        while self.state != %s:"%g.final_state
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
