#! /usr/bin/env python

from sys import argv, stderr
from grammar import Grammar
from wifile import read_rules
from text import list_lines, write_block
from sniplets import emit_class_parseerror, emit_rules

class LR1(Grammar):

    """Represent LR(1) grammars and generate parsers."""

    def __init__(self, *args, **kwargs):
        Grammar.__init__(self, *args, **kwargs)

        self.starts = {}
        for X in self.symbols:
            self.starts[X] = []
        for k, s in self.rules.iteritems():
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
        """ Given a state U and a symbol X, return the new parser state."""
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

        key, l = self.starts[self.start][0]
        state = self.closure([ (key,l,1,self.terminator) ])
        T[stateno] = state
        Tinv[state] = stateno
        stateno += 1

        done = False
        while not done:
            done = True
            states = T.keys()
            for I in states:
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
                    msg = "not an LR(1) grammar (reduce-reduce conflict)"
                    print >>stderr, msg
                    raise SystemExit(1)
                r = self.rules[key]
                self.rtab[(I,next)] = (key, r[0], n-1)

        self.stab = {}
        self.gtab = {}
        for I, EI in E.iteritems():
            if not EI:
                continue
            for X in EI:
                if (I,X) in self.rtab:
                    msg = "not an LR(1) grammar (shift-reduce conflict)"
                    print >>stderr, msg
                    raise SystemExit(1)
                JJ = EI[X]
                if len(JJ)>1:
                    # TODO: can this really occur?
                    msg = "not an LR(1) grammar (shift-shift conflict)"
                    print >>stderr, msg
                    raise SystemExit(1)
                J = JJ[0]
                if X in self.terminal:
                    self.stab[(I,X)] = J
                    if X == self.terminator:
                        self.final_state = J
                else:
                    self.gtab[(I,X)] = J

    def write_decorations(self, fd):
        fd.write("# terminal symbols:\n")
        tt = map(repr, sorted(self.terminal))
        line = "#   "+tt[0]
        for t in tt[1:]:
            test = line+" "+t
            if len(test)>=80:
                fd.write(line+"\n")
                line = "#   "+t
            else:
                line = test
        fd.write(line+"\n\n")

        fd.write("# non-terminal symbols:\n")
        tt = map(repr, sorted(self.nonterminal))
        line = "#   "+tt[0]
        for t in tt[1:]:
            test = line+" "+t
            if len(test)>=80:
                fd.write(line+"\n")
                line = "#   "+t
            else:
                line = test
        fd.write(line+"\n\n")

        fd.write("# grammar rules:\n")
        keys = sorted(self.rules.keys())
        for key in keys:
            r = self.rules[key]
            head = repr(r[0])
            tail = " ".join(map(repr, r[1:]))
            fd.write("#   %s -> %s\n"%(head,tail))
        fd.write("\n")

        fd.write("# parser states:\n")
        keys = sorted(self.T.keys())
        for k in keys:
            fd.write("#\n")
            fd.write("# state %d:\n"%k)
            for k,l,n,readahead in self.T[k]:
                r = self.rules[k]
                head = repr(r[0])
                tail1 = " ".join(map(repr, r[1:n]))
                tail2 = " ".join(map(repr, r[n:l]))
                readahead = repr(readahead)
                fd.write("#   %s -> %s.%s | %s\n"%(head,tail1,tail2,readahead))
        fd.write("\n")

        fd.write("# transition table:\n")
        fd.write("#\n")
        tt = sorted(self.terminal)+sorted(self.nonterminal)
        ttt = [ repr(t) for t in tt ]
        widths = [ len(t) for t in ttt ]
        fd.write("# state | "+" ".join(ttt)+"\n")
        fd.write("# %s\n"%("-"*(7+sum(widths)+len(tt))))
        keys = sorted(self.T.keys())
        for I in keys:
            rest = [ ]
            for t,l in zip(tt,widths):
                if t in self.E[I]:
                    next = ",".join(["%d"%x for x in self.E[I][t]])
                    rest.append(next.center(l))
                else:
                    rest.append(" "*l)
            fd.write("# %5d | %s\n"%(I," ".join(rest)))
        fd.write("\n")

    def write_tables(self, fd):
        fd.write("\n")
        r_items = [ tuple(map(repr,i+self.rtab[i])) for i in self.rtab ]
        r_items = [ "(%s,%s): (%s,%s,%s)"%ri for ri in r_items ]
        fd.write("    _rtab = {\n")
        for l in list_lines("        ", r_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write("\n")
        s_items = [ "(%d,%s): %s"%(i,repr(x),self.stab[(i,x)]) for i,x in self.stab ]
        fd.write("    _stab = {\n")
        for l in list_lines("        ", s_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write("\n")
        g_items = [ "(%d,%s): %s"%(i,repr(x),self.gtab[(i,x)]) for i,x in self.gtab ]
        fd.write("    _gtab = {\n")
        for l in list_lines("        ", g_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

    def write_methods(self, fd):
        fd.write("\n")
        write_block(fd, 4, """
        def parse(self, input):
            self.input = chain(input,[(%(terminator)s,)])
            self.valid = False
            state = 0
            stack = []
            while state != %(final_state)s:
                X = self._peek()
                if (state,X) in self._rtab:
                    key,X,n = self._rtab[(state,X)]
                    oldstate = stack[-n][0]
                    stack[-n:] = [ (oldstate, X,[(Y,val) for s,Y,val in stack[-n:]]) ]
                    if X == %(start)s:
                        break
                    state = self._gtab[(oldstate,X)]
                elif (state,X) in self._stab:
                    stack.append((state,X,self.val))
                    state = self._stab[(state,X)]
                    self.valid = False
                else:
                    raise ParseError("unexpected token '%%s'"%%X, self.val)

            return (stack[0][1], stack[0][2])
        """%{'terminator': repr(self.terminator),
             'final_state': self.final_state,
             'start': repr(self.start) })
