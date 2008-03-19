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

from inspect import getsource, getcomments

from grammar import read_grammar, Conflicts, Unique
import template
from text import split_it, write_block
from version import VERSION


class Automaton(object):

    """LR(1) parsing automatons"""

    def __init__(self, g, params={}):
        self.g = g
        self.overrides = params.get("overrides",{})
        self.tables_generated = False
        self.checked = False

    @staticmethod
    def _is_compatible(S, T):
        """Check whether S and T can be merged.

        This implements definition 1 (p. 254) from Pager, 1975."""
        core = S.keys()
        if set(T.keys()) != set(core):
            return False
        if len(core) == 1:
            return True
        for i in range(0, len(core)-1):
            I = core[i]
            for j in range(i+1, len(core)):
                J = core[j]
                if ((S[I]&T[J] or S[J]&T[I])
                    and not S[I]&S[J]
                    and not T[I]&T[J]):
                    return False
        return True

    def _closure(self, U):
        rules = self.g.rules
        todo = U.copy()
        res = {}
        while todo:
            prod,ctx = todo.popitem()
            res.setdefault(prod, set()).update(ctx)
            key,l,n = prod
            if n == l:
                continue
            rule = rules[key]
            for X in ctx:
                lookahead = self.g.first_tokens(list(rule[n+1:])+[X])
                for k,l in self.g.rule_from_head[rule[n]]:
                    res_ctx = res.setdefault((k,l,1), set())
                    for Z in lookahead:
                        if Z not in res_ctx:
                            todo.setdefault((k,l,1), set()).add(Z)
        return res

    def _generate_tables(self):
        """This implements the algorithm of Pager, 1975."""
        if self.tables_generated:
            return

        class StateIndex(object):

            def set_label(self, label):
                self.label = label

            def __int__(self):
                return self.label

            def __repr__(self):
                return str(self.label)

        rules = self.g.rules

        state_tab = {}
        self.initial_state = StateIndex()
        key, l = self.g.rule_from_head[self.g.start][0]
        state_tab[self.initial_state] = { (key,l,1): set([self.g.EOF]) }

        todo = set([self.initial_state])
        done = set()

        reduce_tab = {}
        shift_tab = {}

        while todo:
            state_no = todo.pop()
            state = state_tab[state_no]
            done.add(state_no)

            rtab = reduce_tab.setdefault(state_no,{})
            stab = shift_tab.setdefault(state_no,{})

            state = self._closure(state)
            shift = {}
            for prod,ctx in state.iteritems():
                key,l,n = prod
                r = rules[key]
                if n == l:
                    # reduce using rule 'key'
                    rtab[key] = ctx
                else:
                    # shift symbol r[n]
                    X = r[n]
                    p = (key,l,n+1)

                    X_neighbour = shift.setdefault(X, {})
                    neighbour_ctx = X_neighbour.setdefault(p, set())
                    neighbour_ctx.update(ctx)

            for X,S in shift.iteritems():
                for Tn, T in state_tab.iteritems():
                    if not self._is_compatible(S, T):
                        continue
                    # merge S into T
                    stab[X] = Tn
                    changed = False
                    for prod in S:
                        add = S[prod] - T[prod]
                        if add:
                            T[prod] |= add
                            changed = True
                    if changed and Tn in done:
                        # regenerate the neighbours of T as needed
                        done.remove(Tn)
                        del shift_tab[Tn]
                        del reduce_tab[Tn]
                        todo.add(Tn)
                    break
                else:
                    # create a new state for S
                    next_state = StateIndex()
                    stab[X] = next_state
                    state_tab[next_state] = S
                    todo.add(next_state)
                    if X == self.g.EOF:
                        self.halting_state = next_state

        # throw away unused states (might happen when regeneration of
        # states was needed).
        todo = set([self.initial_state])
        used_states = set()
        while todo:
            n = todo.pop()
            used_states.add(n)
            todo.update(set(shift_tab[n].values())-used_states)
        for s in set(state_tab.keys())-used_states:
            del state_tab[s]
            del reduce_tab[s]
            del shift_tab[s]

        keyfn = lambda x: (x == self.halting_state,min(state_tab[x]))
        states = sorted(used_states, key=keyfn)
        for k, s in enumerate(states):
            s.set_label(k)
        assert repr(self.initial_state) == "0"

        self.states = states
        self.state_tab = state_tab
        self.reduce_tab = reduce_tab
        self.shift_tab = shift_tab

        self.tables_generated = False

    def _get_actions(self, state, X):
        """Get the neighbours of a node in the automaton's state graph.

        The return value is a set of tuples, where the first element
        is 'R' for reduce actions and 'S' for shift actions.  In case of a
        reduce action, the second element of the tuple gives the
        grammar rule to use for the reduction.  In case of a shift
        action, the second element gives the new state of the
        automaton.
        """
        ritems = self.reduce_tab[state].iteritems()
        actions = [ ('R',key) for key,ctx in ritems if X in ctx ]
        stab = self.shift_tab[state]
        if X in stab:
            actions.append(('S',stab[X]))
        return actions

    def _get_all_actions(self, state):
        """Return a dict of all actions possible in a state.

        The keys of the dict are the input tokens valid in this state,
        the corresponding value is the same as returned by
        `_get_actions`.
        """
        res = {}
        for key,ctx in self.reduce_tab[state].iteritems():
            for X in ctx:
                res.setdefault(X, []).append(('R',key))
        for X,next in self.shift_tab[state].iteritems():
            res.setdefault(X, []).append(('S',next))
        return res

    def _check_overrides(self, state, X, action):
        rules = self.g.rules
        if action[0] == 'S':
            for k,l,n in self._closure(self.state_tab[state]):
                if n == l or rules[k][n] != X:
                    continue
                if n not in self.overrides.get(k, []):
                    return False
            return True
        else:
            n = len(rules[action[1]])
            return n in self.overrides.get(action[1], [])

    def check(self):
        """Check whether the grammar is LR(1).

        If conflicts are detected, an Error exception listing all
        detected conflicts is raised.
        """
        if self.checked:
            return
        self._generate_tables()

        conflicts = Conflicts()
        shortcuts = self.g.shortcuts()

        rtab = {}
        gtab = {}
        stab = {}

        path = {}
        path[self.initial_state] = ()
        todo = set([self.initial_state])
        while todo:
            state = todo.pop()

            for X,actions in self._get_all_actions(state).iteritems():
                word = path[state] + (X,)

                # try conflict overrides
                if len(actions) > 1:
                    repl = [ a for a in actions
                             if self._check_overrides(state, X, a) ]
                    if len(repl) == 1:
                        actions = repl

                for action in actions:
                    if action[0] == 'S':
                        next = action[1]
                        if next not in path:
                            path[next] = word
                            todo.add(next)

                if len(actions) > 1:
                    # conflict: more than one action possible
                    res = set()
                    for action in actions:
                        if action[0] == 'S':
                            for k,l,n in self._closure(self.state_tab[state]):
                                if n<l and self.g.rules[k][n] == X:
                                    res.add(('S',k,n))
                        else:
                            res.add(('R', action[1]))
                    res = tuple(sorted(res))
                    text = tuple(" ".join(repr(Y) for Y in shortcuts[Z])
                                 for Z in word)
                    conflicts.add(res, text)
                    continue

                # no conflicts
                action = actions[0]
                if action[0] == 'S':
                    if X in self.g.terminals:
                        stab[(int(state),X)] = action[1]
                    else:
                        gtab[(int(state),X)] = action[1]
                else:
                    rule = self.g.rules[action[1]]
                    rtab[(int(state),X)] = (rule[0],len(rule)-1)

        if conflicts:
            raise conflicts

        self.rtab = rtab
        self.gtab = gtab
        self.stab = stab

        self.checked = True

    def write_transition_table(self, fd, prefix="# "):
        self._generate_tables()

        def write(str):
            fd.write((prefix+str).rstrip()+'\n')
        write("transition table:")
        write("")
        tt1 = sorted(self.g.terminals)
        tt2 = sorted(self.g.nonterminals-set([self.g.start]))
        tt = tt1 + tt2
        ttt = [ repr(t) for t in tt ]

        table = []
        table.append(["state"]+ttt)

        for state in self.states:
            if state == self.halting_state:
                continue
            line = [ str(state) ]
            for X in tt:
                entries = []
                for a in self._get_actions(state, X):
                    if a[0] == 'S':     # shift
                        if a[1] == self.halting_state:
                            desc = "HLT"
                        elif X in self.g.terminals:
                            desc = "s%s"%a[1]
                        else:
                            desc = "g%s"%a[1]
                    else:               # reduce
                        desc = "r%d"%a[1]
                    if self._check_overrides(state, X, a):
                        desc += "!"
                    entries.append(desc)
                line.append(",".join(entries))
            table.append(line)

        widths = [ max(len(entry) for entry in col) for col in zip(*table) ]
        def fmt_line(l):
            cols = [ entry.center(w) for entry,w in zip(l[1:],widths[1:]) ]
            return l[0].rjust(widths[0]) + " | " + " ".join(cols)
        write(fmt_line(table[0]))
        write("-"*(sum(widths)+len(widths)+1))
        for line in table[1:]:
            write(fmt_line(line))

    def write_parser_states(self, fd, prefix="# "):
        self._generate_tables()

        def write(str):
            fd.write((prefix+str).rstrip()+'\n')
        write("parser states:")
        for state in self.states:
            U = self._closure(self.state_tab[state])
            write("")
            msg = ""
            if state == self.initial_state:
                msg += " (initial state)"
            if state == self.halting_state:
                msg += " (halting state)"
            write("state %s%s:"%(state,msg))

            keyfn = lambda x: (x[2]==1, self.g.rules[x[0]])
            for prod in sorted(U, key=keyfn):
                k,l,n = prod
                rule = self.g.rules[k]
                rr = map(str, rule)
                rulestr = rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])
                ctx = U[prod]
                ctxstr = "{"+",".join(str(x) for x in sorted(ctx))+"}"
                write("  "+rulestr+" "+ctxstr)

    def write_parser(self, fd, params={}):
        self.check()

        from time import strftime
        params.setdefault('date', strftime("%Y-%m-%d %H:%M:%S"))
        params['version'] = VERSION

        write_block(fd, 0, """#! /usr/bin/env python
# LR(1) parser, autogenerated on %(date)s
# generator: wisent %(version)s, http://seehuhn.de/pages/wisent
        """%params, first=True)
        if 'fname' in params:
            fd.write("# source: %(fname)s\n"%params)

        write_block(fd, 0, """
# All parts of this file which are not taken verbatim from the input grammar
# are covered by the following notice:
#""")
        fd.write(getcomments(template))

        fd.write('\n')
        fd.write('from itertools import chain\n')

        write_block(fd, 0, getsource(Unique))
        fd.write('\n')

        fd.write('class Parser(object):\n\n')

        fd.write('    """LR(1) parser class.\n')
        if params.get("parser_debugprint", False):
            write_block(fd, 4, """
            Instances of this class print additional debug messages and are
            not suitable for production use.
            """)
        fd.write('\n')
        self.g.write_terminals(fd, "    ")
        fd.write('\n')
        self.g.write_nonterminals(fd, "    ")
        fd.write('\n')
        self.g.write_productions(fd, "    ")
        fd.write('    """\n')

        if "parser_comment" in params:
            fd.write('\n')
            self.write_transition_table(fd)
            fd.write('\n')
            self.write_parser_states(fd)

        write_block(fd, 4, getsource(template.Parser.ParseErrors))

        fd.write('\n')
        tt = map(repr, sorted(self.g.terminals-set([self.g.EOF])))
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

        # halting state
        fd.write('\n')
        fd.write("    _halting_state = %s\n"%self.halting_state)

        # reduce actions
        fd.write('\n')
        rtab = self.rtab
        r_items = [ "%s: %s"%(repr(key),repr(rtab[key]))
                    for key in sorted(self.rtab) ]
        fd.write("    _reduce = {\n")
        for l in split_it(r_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        # goto table
        fd.write('\n')
        gtab = self.gtab
        g_items = [ "%s: %s"%(repr(key),repr(gtab[key]))
                    for key in sorted(self.gtab) ]
        fd.write("    _goto = {\n")
        for l in split_it(g_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        # shift table
        fd.write('\n')
        stab = self.stab
        s_items = [ "%s: %s"%(repr(key),repr(stab[key]))
                    for key in sorted(self.stab) ]
        fd.write("    _shift = {\n")
        for l in split_it(s_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        write_block(fd, 4, getsource(template.Parser.__init__), params)
        write_block(fd, 4, getsource(template.Parser.leaves), params)
        write_block(fd, 4, getsource(template.Parser._parse_tree), params)
        write_block(fd, 4, getsource(template.Parser._try_parse), params)
        write_block(fd, 4, getsource(template.Parser.parse_tree), params)
