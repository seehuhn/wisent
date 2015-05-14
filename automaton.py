# automaton.py - the Automaton class
#
# Copyright (C) 2008, 2012  Jochen Voss <voss@seehuhn.de>
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

    """LR(1) parsing automatons."""

    def __init__(self, g, params={}):
        """Construct a parser automaton from the grammar `g`.

        If `params["overrides"]` exists, it can be used to override
        LR(1) conflicts in the grammar.  The value should be a
        dictionary with production rule indices as keys and lists of
        overrides as values.
        """
        self.g = g
        self.overrides = params.get("overrides", {})

        self.replace_nonterminals = params.get("replace_nonterminals", False)
        nonterminals = sorted(self.g.nonterminals-set([self.g.start]))
        if self.replace_nonterminals:
            self.nt_tab = dict((X,k) for k,X in enumerate(nonterminals))
        else:
            self.nt_tab = dict((X,X) for X in nonterminals)
        self.nt_tab[self.g.start] = self.g.start

        self.tables_generated = False
        self.checked = False

    @staticmethod
    def _is_compatible(S, T):
        """Check whether S and T can be merged.

        This implements definition 1 (p. 254) from Pager, 1977."""
        core = list(S.keys())
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
        first_tokens = self.g.first_tokens
        rule_from_head = self.g.rule_from_head

        todo = U.copy()
        res = {}
        for prod in todo:
            res[prod] = todo[prod].copy()
        while todo:
            prod,ctx = todo.popitem()
            key,l,n = prod
            if n == l:
                continue
            rule = rules[key]
            tail = list(rule[n+1:])
            new_rules = [ ((k,l,1),res.setdefault((k,l,1), set()))
                          for k,l in rule_from_head[rule[n]] ]
            for X in ctx:
                lookahead = first_tokens(tail+[X])
                for prod,res_ctx in new_rules:
                    new = lookahead - res_ctx
                    if new:
                        todo_ctx = todo.setdefault(prod, set())
                        todo_ctx |= new
                        res_ctx |= new
        return res

    def _generate_tables(self):
        """This implements the algorithm of Pager, 1977."""
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

        maybe_compatible = {}
        for X in self.g.symbols:
            maybe_compatible[X] = set()

        todo = set([self.initial_state])
        done = set()

        reduce_tab = {}
        shift_tab = {}

        while todo:
            state_no = todo.pop()
            done.add(state_no)

            rtab = reduce_tab.setdefault(state_no,{})
            stab = shift_tab.setdefault(state_no,{})

            state = self._closure(state_tab[state_no])
            shift = {}
            for prod,ctx in state.items():
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

            for X,S in shift.items():
                for Tn in maybe_compatible[X]:
                    T = state_tab[Tn]
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
                    maybe_compatible[X].add(next_state)
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

        self.closure_tab = {}
        for state in states:
            self.closure_tab[state] = self._closure(self.state_tab[state])

        self.tables_generated = True

    def _get_actions(self, state, X):
        """Get the neighbours of a node in the automaton's state graph.

        The return value is a set of tuples, where the first element
        is 'R' for reduce actions and 'S' for shift actions.  In case of a
        reduce action, the second element of the tuple gives the
        grammar rule to use for the reduction.  In case of a shift
        action, the second element gives the new state of the
        automaton.
        """
        ritems = self.reduce_tab[state].items()
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
        for key,ctx in self.reduce_tab[state].items():
            for X in ctx:
                res.setdefault(X, []).append(('R',key))
        for X,next in self.shift_tab[state].items():
            res.setdefault(X, []).append(('S',next))
        return res

    def _check_overrides(self, state, X, action):
        rules = self.g.rules
        if action[0] == 'S':
            for k,l,n in self.closure_tab[state]:
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
        shortcuts = None
        nt_tab = self.nt_tab

        rtab = {}
        gtab = {}
        stab = {}

        path = {}
        path[self.initial_state] = ()
        todo = set([self.initial_state])
        while todo:
            state = todo.pop()

            for X,actions in self._get_all_actions(state).items():
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
                            for k,l,n in self.closure_tab[state]:
                                if n<l and self.g.rules[k][n] == X:
                                    res.add(('S',k,n))
                        else:
                            res.add(('R', action[1]))
                    res = tuple(sorted(res))
                    if shortcuts is None:
                        shortcuts = self.g.shortcuts()
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
                        gtab[(int(state),nt_tab[X])] = action[1]
                elif state != self.halting_state:
                    rule = self.g.rules[action[1]]
                    if X in nt_tab:
                        X = nt_tab[X]
                    rtab[(int(state),X)] = (nt_tab[rule[0]],len(rule)-1)

        if conflicts:
            raise conflicts

        self.rtab = rtab
        self.gtab = gtab
        self.stab = stab

        self.checked = True

    def write_transition_table(self, fd, prefix="# "):
        """Emit a textual description of the automaton's transition table.

        The human-readable table is written to the file-like object
        `fd`, each line of the output is prefixed with the string
        `prefix`.

        The output of this function will be only useful to persons
        with a good understanding of LR(1) parsing.
        """
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
        """Emit a textual description of the automaton's state.

        The human-readable description of states (as "dotted"
        productions with context sets) is written to the file-like
        object `fd`, each line of the output is prefixed with the
        string `prefix`.

        The output of this function will be only useful to persons
        with a good understanding of LR(1) parsing.
        """
        self._generate_tables()

        def write(str):
            fd.write((prefix+str).rstrip()+'\n')
        write("parser states:")
        for state in self.states:
            U = self.closure_tab[state]
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
                rr = list(map(str, rule))
                rulestr = rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])
                ctx = U[prod]
                ctxstr = "{"+",".join(str(x) for x in sorted(ctx))+"}"
                write("  "+rulestr+" "+ctxstr)

    def write_parser(self, fd, params={}):
        """Emit Python code implementing the parser.

        A complete, stand-alone Python source file implementing the
        parser is written to the file-like object `fd`, each line of
        the output is prefixed with the string `prefix`.
        """
        self.check()

        from time import strftime
        params.setdefault('date', strftime("%Y-%m-%d %H:%M:%S"))
        params['version'] = VERSION

        write_block(fd, 0, """# LR(1) parser, autogenerated on %(date)s
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
        if self.replace_nonterminals:
            write_block(fd, 4, """
            In the returned parse trees, nonterminal symbols are
            replaced by numbers.  You can use the dictionary
            `Parser.nonterminals` to map back the numeric codes to the
            corresponding symbols.
            """)
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
        nt_tab = self.nt_tab
        transparent = params.get("transparent_tokens", set())
        transparent &= self.g.nonterminals
        if self.replace_nonterminals:
            symbols = self.g.nonterminals-set([self.g.start])-transparent
            nonterminals = sorted(symbols)
            tt = [ "%d: %s"%(nt_tab[X],repr(X)) for X in nonterminals ]
            for l in split_it(tt, padding="    ",
                              start1="nonterminals = { ", end2=" }"):
                fd.write(l+'\n')
        if transparent:
            tt = [ repr(nt_tab[X]) for X in sorted(transparent) ]
            for l in split_it(tt, padding="    ",
                              start1="_transparent = [ ", end2=" ]"):
                fd.write(l+'\n')

        fd.write("    EOF = Unique('EOF')\n")
        fd.write("    S = Unique('S')\n")

        # halting state
        fd.write('\n')
        fd.write("    _halting_state = %s\n"%self.halting_state)

        # reduce actions
        rtab = self.rtab
        r_items = [ "%s: %s"%(repr(key),repr(rtab[key]))
                    for key in sorted(self.rtab) ]
        fd.write("    _reduce = {\n")
        for l in split_it(r_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        # goto table
        gtab = self.gtab
        g_items = [ "%s: %s"%(repr(key),repr(gtab[key]))
                    for key in sorted(self.gtab) ]
        fd.write("    _goto = {\n")
        for l in split_it(g_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        # shift table
        stab = self.stab
        s_items = [ "%s: %s"%(repr(key),repr(stab[key]))
                    for key in sorted(self.stab) ]
        fd.write("    _shift = {\n")
        for l in split_it(s_items, padding="        "):
            fd.write(l+'\n')
        fd.write("    }\n")

        write_block(fd, 4, getsource(template.Parser.__init__), params)
        write_block(fd, 4, getsource(template.Parser.leaves), params)
        write_block(fd, 4, getsource(template.Parser._parse), params)
        write_block(fd, 4, getsource(template.Parser._try_parse), params)
        write_block(fd, 4, getsource(template.Parser.parse), params)
