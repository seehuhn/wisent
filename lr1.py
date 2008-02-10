#! /usr/bin/env python

from sys import argv, stderr
from grammar import Grammar
from wifile import read_rules
from text import list_lines, write_block
from sniplets import emit_class_parseerror, emit_rules

from wifile import ParseError

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

    def write_decorations(self, fd, grammar=True, parser=False):
        if grammar:
            fd.write("# terminal symbols:\n")
            tt = map(repr, sorted(self.terminal-set([self.terminator])))
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
            tt = map(repr, sorted(self.nonterminal-set([self.start])))
            line = "#   "+tt[0]
            for t in tt[1:]:
                test = line+" "+t
                if len(test)>=80:
                    fd.write(line+"\n")
                    line = "#   "+t
                else:
                    line = test
            fd.write(line+"\n\n")

            fd.write("# production rules:\n")
            keys = sorted(self.rules.keys())
            for key in keys:
                r = self.rules[key]
                if r[0] == self.start:
                    continue
                head = repr(r[0])
                tail = " ".join(map(repr, r[1:]))
                fd.write("#   %s -> %s\n"%(head, tail))
            fd.write("\n")

        if parser:
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
                    fd.write("#   %s -> %s.%s [%s]\n"%(head,tail1,tail2,readahead))
            fd.write("\n")

            fd.write("# transition table:\n")
            fd.write("#\n")
            tt1 = sorted(self.terminal)
            tt2 = sorted(self.nonterminal-set([self.start]))
            tt = tt1 + tt2
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

        self.terminator.push("EOF")
        fd.write("    EOF = object()\n")
        self.start.push("_start")
        fd.write("    _start = object()\n")

        fd.write("\n")
        r_items = [ (i[0], repr(i[1]), repr(ri[1]), ri[2])
                    for i,ri in self.rtab.iteritems() ]
        r_items = [ "(%d,%s): (%s,%d)"%ri for ri in r_items ]
        fd.write("    _reduce = {\n")
        for l in list_lines("        ", r_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write("\n")
        s_items = [ "(%d,%s): %s"%(i,repr(x),self.stab[(i,x)]) for i,x in self.stab ]
        fd.write("    _shift = {\n")
        for l in list_lines("        ", s_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write("\n")
        g_items = [ "(%d,%s): %s"%(i,repr(x),self.gtab[(i,x)]) for i,x in self.gtab ]
        fd.write("    _goto = {\n")
        for l in list_lines("        ", g_items, ""):
            fd.write(l+'\n')
        fd.write("    }\n")

        self.terminator.pop()
        self.start.pop()

    def write_parser(self, fd):
        self.terminator.push("self.EOF")
        self.start.push("self._start")

        fd.write("\n")
        write_block(fd, 4, """
        def parse_tree(self, input):
            state = 0
            stack = []
            read_next = True
            while state != %(final_state)s:
                if read_next:
                    try:
                        readahead = input.next()
                    except StopIteration:
                        readahead = (%(terminator)s,)
                    read_next = False
                token = readahead[0]
                if (state,token) in self._reduce:
                    X,n = self._reduce[(state,token)]
                    if n == 0:
                        tree = (False,X)
                    else:
                        state = stack[-n][0]
                        tree = (False,X)+tuple(s[1] for s in stack[-n:])
                        del stack[-n:]
                    stack.append((state,tree))
                    if X == %(start)s:
                        break
                    state = self._goto[(state,X)]
                elif (state,token) in self._shift:
                    stack.append((state,(True,)+readahead))
                    read_next = True
                    state = self._shift[(state,token)]
                else:
                    expect = [ t for s,t in self._reduce.keys()+self._shift.keys()
                               if s == state ]
                    raise self.ParseError(readahead, expect,
                                          [ s[1] for s in stack ])

            return stack[0][1]
        """%{'terminator': repr(self.terminator),
             'final_state': self.final_state,
             'start': repr(self.start) })

        self.terminator.pop()
        self.start.pop()
