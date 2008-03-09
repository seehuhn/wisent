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
from template import LR0Parser as Parser
from text import split_it, write_block


class LR0(Grammar):

    """Represent LR(0) grammars and generate parsers."""

    class Errors(Exception):

        def __init__(self):
            self.list = {}

        def __len__(self):
            return len(self.list)

        def __iter__(self):
            return self.list.iteritems()

        def add(self, data, text):
            if data in self.list:
                if len("".join(text)) >= len("".join(self.list[data])):
                    return
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
            for key,l,n in current:
                if n == l:
                    continue
                r = rules[key]
                for k,l in self.rule_from_head[r[n]]:
                    item = (k,l,1)
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
        self.closure([ (key,l,1) ])

    def neighbours(self, state):
        """Get the neighbours of a node in the automaton's state graph.

        The return value is a set of tuples, where the first element
        is 'R' for reduce actions and 'S' for shift actions.  In case
        of a reduce action, the second element of the tuple is None
        and the third element gives the grammar rule to use for the
        reduction.  In case of a shift action, the second element is
        the lookahead symbol and the third element gives the new state
        of the automaton.
        """
        try:
            return self.edges[state]
        except:
            rules = self.rules
            res = set()

            shift = {}
            for key,l,n in self.state[state]:
                r = rules[key]
                if n == l:
                    # reduce using rule 'key'
                    res.add(('R',None,key))
                else:
                    # shift using rule 'key'
                    X = r[n]
                    shift.setdefault(X,[]).append((key,l,n+1))

            for readahead,seed in shift.iteritems():
                nextstate = self.closure(seed)
                res.add(('S',readahead,nextstate))
                if readahead == self.EOF:
                    self.halting_state = nextstate

            self.edges[state] = res
            return res

    def _check_overrides(self, state, action, overrides):
        if action[0] == 'S':
            for k,l,n in self.state[state]:
                if n == l or self.rules[k][n] != action[1]:
                    continue
                if n not in overrides.get(k, []):
                    return False
            return True
        else:
            k = action[2]
            n = len(self.rules[k])
            return n in overrides.get(k, [])

    def check(self, overrides={}):
        """Check whether the grammar is LR(0).

        If conflicts are detected, an Error exception listing all
        conflicts detected is raised.
        """
        errors = self.Errors()
        shortcuts = self.shortcuts()

        rtab = {}
        gtab = {}
        stab = {}

        path = {}
        path[0] = ()
        todo = set([0])
        while todo:
            state = todo.pop()

            actions = {}
            for action in self.neighbours(state):
                if action[0] == 'S':
                    actions.setdefault(action[1], []).append(action)
                else:
                    for X in self.terminals:
                        actions.setdefault(X, []).append(action)

            for readahead,aa in actions.iteritems():
                word = path[state] + (readahead,)

                # try conflict overrides
                if len(aa) > 1:
                    bb = []
                    for action in aa:
                        if self._check_overrides(state, action, overrides):
                            bb.append(action)
                    if len(bb) == 1:
                        aa = bb

                for action in aa:
                    if action[0] == 'S':
                        next = action[2]
                        if next not in path:
                            path[next] = word
                            todo.add(next)

                if len(aa) > 1:
                    # conflict: more than one action possible
                    res = set()
                    for action in aa:
                        if action[0] == 'S':
                            for k,l,n in self.state[state]:
                                if n<l and self.rules[k][n] == readahead:
                                    res.add(('S',k,n))
                        else:
                            res.add(('R', action[2]))
                    res = tuple(sorted(res))
                    text = tuple(" ".join(repr(Y) for Y in shortcuts[X])
                                 for X in word)
                    errors.add(res, text)
                    continue

                # no conflicts
                action = aa[0]
                if action[0] == 'S':
                    if readahead in self.terminals:
                        stab[(state,readahead)] = action[2]
                    else:
                        gtab[(state,readahead)] = action[2]
                else:
                    rule = self.rules[action[2]]
                    rtab[state] = (rule[0],len(rule)-1)

        if errors:
            raise errors

        self.rtab = rtab
        self.gtab = gtab
        self.stab = stab

    def _generate_tables(self, overrides):
        if not hasattr(self, "rtab"):
            self.check(overrides)

    def _write_decorations(self, fd, overrides):
        self._generate_tables(overrides)

        fd.write('\n')
        fd.write("# transition table:\n")
        fd.write("#\n")
        tt1 = sorted(self.terminals)
        tt2 = sorted(self.nonterminals-set([self.start]))
        tt = tt1 + tt2
        ttt = [ repr(t) for t in tt ]
        widths = [ len(t) for t in ttt ]
        fd.write("# state | "+" ".join(ttt)+'\n')
        fd.write("# %s\n"%("-"*(7+sum(widths)+len(tt))))
        for state in range(0, self.nstates):
            line = {}
            for m in self.neighbours(state):
                if m[0] == 'S':
                    readahead = m[1]
                    line.setdefault(readahead, [])
                    if readahead in self.terminals:
                        desc = "s%d"%m[2]
                    else:
                        desc = "g%d"%m[2]
                    if self._check_overrides(state, m, overrides):
                        desc += "!"
                    line[readahead].append(desc)
                else:
                    for readahead in self.terminals:
                        line.setdefault(readahead, [])
                        if m[2] == -1:
                            if readahead == self.EOF:
                                desc = "HLT"
                        else:
                            desc = "r%d"%m[2]
                        if self._check_overrides(state, m, overrides):
                            desc += "!"
                        line[readahead].append(desc)
            rest = [ ]
            for t,l in zip(tt,widths):
                s = ",".join(line.get(t,[]))
                rest.append(s.center(l))
            fd.write("# %5d | %s\n"%(state," ".join(rest)))

        fd.write('\n')
        fd.write("# parser states:\n")
        for state in range(0, self.nstates):
            U = self.state[state]
            fd.write("#\n")
            fd.write("# state %d:\n"%state)
            keyfn = lambda x: (x[2]==1, self.rules[x[0]])
            for k,l,n in sorted(U, key=keyfn):
                r = self.rules[k]
                head = repr(r[0])
                tail1 = " ".join(map(repr, r[1:n]))
                tail2 = " ".join(map(repr, r[n:l]))
                fd.write("#   %s -> %s.%s\n"%(head,tail1,tail2))

    def _write_tables(self, fd, overrides):
        self._generate_tables(overrides)

        fd.write('\n')
        r_items = [ (i, repr(ri[0]), ri[1])
                    for i,ri in sorted(self.rtab.items()) ]
        r_items = [ "%d: (%s,%d)"%ri for ri in r_items ]
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
        params.setdefault('type', 'LR(0)')
        overrides = params.setdefault('overrides', {})
        super(LR0, self).write_parser(fd, params)
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

        if "parser_comment" in params:
            self._write_decorations(fd, overrides)

        write_block(fd, 4, getsource(Parser.ParseErrors))

        fd.write('\n')
        tt = map(repr, sorted(self.terminals-set([self.EOF])))
        for l in split_it(tt, padding="    ", start1="terminals = [ ",
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

        self._write_tables(fd, overrides)

        fd.write('\n')
        fd.write("    _halting_state = %d\n"%self.halting_state)

        write_block(fd, 4, getsource(Parser.__init__), params)
        write_block(fd, 4, getsource(Parser.leaves), params)
        write_block(fd, 4, getsource(Parser._parse_tree), params)
        write_block(fd, 4, getsource(Parser._try_parse), params)
        write_block(fd, 4, getsource(Parser.parse_tree), params)
