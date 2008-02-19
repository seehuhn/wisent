#! /usr/bin/env python

from inspect import getsource

from grammar import Grammar, GrammarError, Unique
from template import LR1Parser as Parser
from text import split_it, write_block


class LR1(Grammar):

    """Represent LR(1) grammars and generate parsers."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("check", True)
        Grammar.__init__(self, *args, **kwargs)

        self.init_graph()

        self._gotocache = {}

        if kwargs["check"]:
            self.generate_graph()
            self.check()

    def closure(self, U):
        rules = self.rules
        U = set(U)
        current = U
        while current:
            new = set()
            for key,l,n,Y in current:
                if n == l:
                    continue
                r = rules[key]
                lookahead = self.first_tokens(list(r[n+1:])+[Y])
                for k,l in self.rule_from_head[r[n]]:
                    for Y in lookahead:
                        x = (k,l,1,Y)
                        if x not in U:
                            new.add(x)
            current = new
            U |= new
        return frozenset(U)

    def closure2(self, U):
        U = self.closure(U)
        try:
            return self.rstate[U]
        except KeyError:
            no = self.nstates
            self.state[no] = U
            self.rstate[U] = no
            self.nstates += 1
            return no

    def goto(self, U, X):
        """Given a state U and a symbol X, return the next parser state."""
        if (U,X) in self._gotocache:
            return self._gotocache[(U,X)]
        rules = self.rules
        T = [ (key,l,n+1,Y) for key,l,n,Y in U if n<l and rules[key][n]==X ]
        res = self.closure(T)
        self._gotocache[(U,X)] = res
        return res

    def init_graph(self):
        """Set up the on-demand graph computation framework."""
        self.nstates = 0
        self.state = {}
        self.rstate = {}
        self.edges = {}

        self.rule_from_head = {}
        for X in self.symbols:
            self.rule_from_head[X] = []
        for k, s in self.rules.iteritems():
            self.rule_from_head[s[0]].append((k,len(s)))

        key, l = self.rule_from_head[self.start][0]
        self.closure2([ (key,l,1,self.terminator) ])

    def neighbours(self, state):
        try:
            return self.edges[state]
        except:
            rules = self.rules
            U = self.state[state]
            red = []
            shift = {}
            for key,l,n,next in U:
                r = rules[key]
                if n == l:
                    red.append((next,r[0],n-1,key))
                else:
                    X = r[n]
                    seed = shift.get(X,[])
                    seed.append((key,l,n+1,next))
                    shift[X] = seed

            res = set()
            for X,seed in shift.iteritems():
                res.add(("shift",X,self.closure2(seed)))
            for R in red:
                res.add(("reduce",)+R)
            self.edges[state] = res
            return res

    def generate_graph(self):
        stateno = 0
        T = {}
        Tinv = {}
        E = {}

        key, l = self.rule_from_head[self.start][0]
        state = self.closure([ (key,l,1,self.terminator) ])
        T[stateno] = state
        Tinv[state] = stateno
        stateno += 1

        done = False
        while not done:
            done = True
            states = T.keys()
            for I in states:
                if I not in E:
                    E[I] = {}
                for key,l,n,next in T[I]:
                    if n == l:
                        continue
                    r = self.rules[key]
                    X = r[n]
                    J = self.goto(T[I], X)
                    if J not in Tinv:
                        T[stateno] = J
                        Tinv[J] = stateno
                        stateno += 1
                        done = False

                    if X not in E[I]:
                        E[I][X] = []
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
                    raise GrammarError(msg)
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
                    raise GrammarError(msg)
                JJ = EI[X]
                if len(JJ)>1:
                    # TODO: can this really occur?
                    msg = "not an LR(1) grammar (shift-shift conflict)"
                    raise GrammarError(msg)
                J = JJ[0]
                if X in self.terminal:
                    self.stab[(I,X)] = J
                    if X == self.terminator:
                        self.halting_state = J
                else:
                    self.gtab[(I,X)] = J

    def _write_decorations(self, fd):
        fd.write('\n')

        fd.write("# parser states:\n")
        keys = sorted(self.T.keys())
        for k in keys:
            fd.write("#\n")
            fd.write("# state %d:\n"%k)
            for k,l,n,lookahead in self.T[k]:
                r = self.rules[k]
                head = repr(r[0])
                tail1 = " ".join(map(repr, r[1:n]))
                tail2 = " ".join(map(repr, r[n:l]))
                lookahead = repr(lookahead)
                fd.write("#   %s -> %s.%s [%s]\n"%(head,tail1,tail2,lookahead))
        fd.write('\n')

        fd.write("# transition table:\n")
        fd.write("#\n")
        tt1 = sorted(self.terminal)
        tt2 = sorted(self.nonterminal-set([self.start]))
        tt = tt1 + tt2
        ttt = [ repr(t) for t in tt ]
        widths = [ len(t) for t in ttt ]
        fd.write("# state | "+" ".join(ttt)+'\n')
        fd.write("# %s\n"%("-"*(7+sum(widths)+len(tt))))
        keys = sorted(self.T.keys())
        for I in keys:
            rest = [ ]
            for t,l in zip(tt,widths):
                if t in self.E[I]:
                    if t in self.terminal:
                        next = ",".join(["s%d"%x for x in self.E[I][t]])
                    else:
                        next = ",".join(["g%d"%x for x in self.E[I][t]])
                    rest.append(next.center(l))
                else:
                    rest.append(" "*l)
            fd.write("# %5d | %s\n"%(I," ".join(rest)))

    def _write_tables(self, fd):
        fd.write('\n')
        r_items = [ (i[0], repr(i[1]), repr(ri[1]), ri[2])
                    for i,ri in sorted(self.rtab.items()) ]
        r_items = [ "(%d,%s): (%s,%d)"%ri for ri in r_items ]
        fd.write("    _reduce = {\n")
        for l in split_it(r_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write('\n')
        g_items = [ "(%d,%s): %s"%(i,repr(x),self.gtab[(i,x)])
                    for i,x in sorted(self.gtab) ]
        fd.write("    _goto = {\n")
        for l in split_it(g_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write('\n')
        s_items = [ "(%d,%s): %s"%(i,repr(x),self.stab[(i,x)])
                    for i,x in sorted(self.stab) ]
        fd.write("    _shift = {\n")
        for l in split_it(s_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

    def write_parser(self, fd, params={}):
        fd.write('\n')
        fd.write('from itertools import chain\n')

        write_block(fd, 0, getsource(Unique))
        fd.write('\n')

        fd.write('class Parser(object):\n\n')

        fd.write('    """%(type)s parser class.\n\n'%params)
        self.write_terminals(fd, "    ")
        fd.write('\n')
        self.write_nonterminals(fd, "    ")
        fd.write('\n')
        self.write_productions(fd, "    ")
        fd.write('    """\n')

        write_block(fd, 4, getsource(Parser.ParseErrors))

        fd.write('\n')
        tt = map(repr, sorted(self.terminal-set([self.terminator])))
        for l in split_it(tt, padding="    ", start1="terminal = [ ",
                          end2=" ]"):
            fd.write(l+'\n')
        fd.write("    EOF = Unique('EOF')\n")
        fd.write("    S = Unique('S')\n")
        transparent = params.get("transparent_tokens", False)
        if transparent:
            tt = map(repr, transparent)
            for l in split_it(tt, padding="    ", start1="_transparent = [ ",
                              end2=" ]"):
                fd.write(l+'\n')
        fd.write("    _halting_state = %d\n"%self.halting_state)

        if "parser_comment" in params:
            self._write_decorations(fd)

        self._write_tables(fd)

        write_block(fd, 4, getsource(Parser.__init__), params)
        write_block(fd, 4, getsource(Parser.leaves), params)
        write_block(fd, 4, getsource(Parser._parse_tree), params)
        write_block(fd, 4, getsource(Parser._try_parse), params)
        write_block(fd, 4, getsource(Parser.parse_tree), params)
