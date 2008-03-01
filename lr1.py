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

from inspect import getsource

from grammar import Grammar, GrammarError, Unique
from template import LR1Parser as Parser
from text import split_it, write_block


class LR1(Grammar):

    """Represent LR(1) grammars and generate parsers."""

    class LR1Errors(Exception):

        def __init__(self):
            self.list = {}

        def __len__(self):
            return len(self.list)

        def __iter__(self):
            return self.list.iteritems()

        def add(self, data, text):
            if data not in self.list or len(self.list[data]) > len(text):
                self.list[data] = text


    def __init__(self, *args, **kwargs):
        Grammar.__init__(self, *args, **kwargs)
        self.init_graph()

    def closure(self, U):
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
                for k,l in self.rule_from_head[r[n]]:
                    for Z in lookahead:
                        item = (k,l,1,Z)
                        if item not in U:
                            new.add(item)
            current = new
            U |= new
        U = frozenset(U)
        try:
            return self.rstate[U]
        except KeyError:
            no = self.nstates
            self.state[no] = U
            self.rstate[U] = no
            self.nstates += 1
            return no

    def init_graph(self):
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
        self.closure([ (key,l,1,self.EOF) ])

    def neighbours(self, state):
        try:
            return self.edges[state]
        except:
            rules = self.rules
            U = self.state[state]
            red = set()
            shift = {}
            for key,l,n,next in U:
                r = rules[key]
                if n == l:
                    # reduce using rule 'key'
                    red.add((next,'R',key))
                else:
                    # shift using rule 'key'
                    X = r[n]
                    seed = shift.get(X,[])
                    seed.append((key,l,n+1,next))
                    shift[X] = seed

            res = set()
            for X,seed in shift.iteritems():
                nextstate = self.closure(seed)
                res.add((X,'S',nextstate))
                if X == self.EOF:
                    self.halting_state = nextstate
            res.update(red)
            self.edges[state] = res
            return res

    def check(self):
        """Check whether the grammar is LR(1).

        If conflicts are detected, an LR1Error exception is raised,
        listing all detected conflicts.
        """
        errors = self.LR1Errors()
        shortcuts = self.shortcuts()

        rtab = {}
        gtab = {}
        stab = {}

        path = {}
        path[0] = ()
        todo = set([0])
        while todo:
            state = todo.pop()
            word = path[state]
            actions = {}
            for m in self.neighbours(state):
                X = m[0]
                if m[1] == 'S':
                    # shift
                    next = m[2]
                    if X in self.terminal:
                        stab[(state,X)] = next
                    else:
                        gtab[(state,X)] = next
                else:
                    # reduce
                    r = self.rules[m[2]]
                    rtab[(state,X)] = (r[0],len(r)-1)

                if X not in actions:
                    actions[X] = []
                actions[X].append(m[1:])
            for X,mm in actions.iteritems():
                word += (X,)
                if len(mm) == 1:
                    # no conflicts
                    m = mm[0]
                    if m[0] == 'R' or m[1] in path:
                        continue
                    path[m[1]] = word
                    todo.add(m[1])
                else:
                    # more than one action possible
                    res = []
                    for m in mm:
                        if m[0] == 'S':
                            for k,l,n,_ in self.state[state]:
                                if n<l and self.rules[k][n] == X:
                                    if ('S',k,n) not in res:
                                        res.append(('S',k,n))
                        else:
                            res.append(('R', m[1]))
                    res = tuple(res)
                    text = tuple(" ".join(repr(Y) for Y in shortcuts[X])
                                 for X in word)
                    errors.add(res, text)

        self.rtab = rtab
        self.gtab = gtab
        self.stab = stab
        if errors:
            raise errors

    def generate_tables(self):
        if not hasattr(self, "rtab"):
            try:
                self.check()
            except self.LR1Errors:
                pass

    def _write_decorations(self, fd):
        self.generate_tables()

        fd.write('\n')
        fd.write("# parser states:\n")
        for n in range(0, self.nstates):
            U = self.state[n]
            fd.write("#\n")
            fd.write("# state %d:\n"%n)
            for k,l,n,lookahead in U:
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
        for I in range(0, self.nstates):
            line = {}
            for m in self.neighbours(I):
                X = m[0]
                line.setdefault(X, [])
                if m[1] == 'S':
                    if X in self.terminal:
                        line[X].append("s%d"%m[2])
                    else:
                        line[X].append("g%d"%m[2])
                else:
                    if m[2] == -1:
                        line[X].append("HLT")
                    else:
                        line[X].append("r%d"%m[2])
            rest = [ ]
            for t,l in zip(tt,widths):
                s = ",".join(line.get(t,[]))
                rest.append(s.center(l))
            fd.write("# %5d | %s\n"%(I," ".join(rest)))

    def _write_tables(self, fd):
        self.generate_tables()

        fd.write('\n')
        r_items = [ (i[0], repr(i[1]), repr(ri[0]), ri[1])
                    for i,ri in sorted(self.rtab.items()) ]
        r_items = [ "(%d,%s): (%s,%d)"%ri for ri in r_items ]
        fd.write("    _reduce = {\n")
        for l in split_it(r_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write('\n')
        g_items = [ "(%d,%s): %s"%(i[0],repr(i[1]),next)
                    for i,next in sorted(self.gtab.items()) ]
        fd.write("    _goto = {\n")
        for l in split_it(g_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        fd.write('\n')
        s_items = [ "(%d,%s): %s"%(i[0],repr(i[1]),next)
                    for i,next in sorted(self.stab.items()) ]
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
        tt = map(repr, sorted(self.terminal-set([self.EOF])))
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

        if "parser_comment" in params:
            self._write_decorations(fd)

        self._write_tables(fd)

        fd.write('\n')
        fd.write("    _halting_state = %d\n"%self.halting_state)

        write_block(fd, 4, getsource(Parser.__init__), params)
        write_block(fd, 4, getsource(Parser.leaves), params)
        write_block(fd, 4, getsource(Parser._parse_tree), params)
        write_block(fd, 4, getsource(Parser._try_parse), params)
        write_block(fd, 4, getsource(Parser.parse_tree), params)
