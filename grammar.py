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

from time import strftime
from inspect import getcomments

from text import split_it, write_block
from version import VERSION
import template


class GrammarError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class Unique(object):

    """Unique objects for use as markers."""

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return self.label

class Grammar(object):

    """Represent a context free grammar."""

    def __init__(self, rules, cleanup=True, **kwargs):
        """Create a new grammar instance.

        The argument 'rules' must be an iterable, listing all
        production rules.  Each production rule must be a list or
        tuple with a non-terminal as the first element, and the
        replacement of the non-terminal in the remaining elements.

        The optional keyword argument 'start' denotes the start symbol
        of the grammar.  If it is not given, the head of the first
        rule is used as the start symbol.
        """
        self.rules = {}
        self.symbols = set()
        self.terminals = set()
        self.nonterminals = set()

        rules = dict(enumerate(rules))
        if not rules:
            raise GrammarError("empty grammar")
        first = True
        for key, r in rules.iteritems():
            self.rules[key] = r
            self.nonterminals.add(r[0])
            if first:
                self.start = r[0]
                first = False
            for s in r[1:]:
                self.symbols.add(s)

        if "start" in kwargs:
            self.start = kwargs["start"]
            if self.start not in self.nonterminals:
                msg = "start symbol %s is not a nonterminal"%repr(self.start)
                raise GrammarError(msg)

        self.terminals = self.symbols - self.nonterminals
        if cleanup:
            self._cleanup()
        self.nonterminals = frozenset(self.nonterminals)
        self.terminals = frozenset(self.terminals)
        self.symbols = frozenset(self.symbols)

        # precompute the set of all nullable symbols
        self.nullable = frozenset(self._compute_nbtab())

        # precompute the table of all possible first symbols in expansions
        fitab = self._compute_fitab()
        self.fitab = {}
        for s in self.nonterminals|self.terminals:
            self.fitab[s] = frozenset(fitab[s])

        # precompute the table of all possible follow-up symbols
        fotab = self._compute_fotab()
        self.fotab = {}
        for s in self.nonterminals|self.terminals:
            self.fotab[s] = frozenset(fotab[s])

    def _cleanup(self):
        """Remove unnecessary rules and symbols."""
        # remove nonterminal symbols which do not expand into terminals
        N = set()
        T = self.terminals
        R = self.rules.keys()
        done = False
        while not done:
            done = True
            for key in R:
                r = self.rules[key]
                if r[0] in N:
                    continue
                if set(r[1:])&(N|T):
                    N.add(r[0])
                    done = False
        if self.start not in N:
            tmpl = "start symbal %s doesn't generate terminals"
            raise GrammarError(tmpl%repr(self.start))
        for key in R:
            if not set(self.rules[key]) <= (N|T):
                del self.rules[key]

        # remove unreachable symbols
        gamma = set([self.start])
        done = False
        while not done:
            done = True
            for key in R:
                r = self.rules[key]
                if r[0] not in gamma:
                    continue
                for w in r[1:]:
                    if w not in gamma:
                        gamma.add(w)
                        done = False
        N &= gamma
        T &= gamma
        for key in R:
            if not set(self.rules[key]) <= (N|T):
                del self.rules[key]

        # generate a terminator symbol
        s = Unique('EOF')
        T.add(s)
        self.EOF = s

        # generate a private start symbol
        s = Unique('S')
        N.add(s)
        self.rules[-1] = (s, self.start, self.EOF)
        self.start = s

        self.nonterminals = N
        self.terminals = T
        self.symbols = N|T

    def _compute_nbtab(self):
        """Compute the set of nullable symbols."""
        nbtab = set()
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                if r[0] in nbtab:
                    continue
                for s in r[1:]:
                    if s not in nbtab:
                        break
                else:
                    nbtab.add(r[0])
                    done = False
        return nbtab

    def _compute_fitab(self):
        """Compute the table of all possible first symbols in expansions."""
        fitab = {}
        for s in self.nonterminals:
            fitab[s] = set()
        for s in self.terminals:
            fitab[s] = set([s])
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                fi = set()
                for s in r[1:]:
                    fi |= fitab[s]
                    if s not in self.nullable:
                        break
                if not(fi <= fitab[r[0]]):
                    fitab[r[0]] |= fi
                    done = False
        return fitab

    def _compute_fotab(self):
        fotab = {}
        for s in self.nonterminals|self.terminals:
            fotab[s] = set()
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                for i in range(1,len(r)):
                    fo = set()
                    for s in r[i+1:]:
                        fo |= self.fitab[s]
                        if s not in self.nullable:
                            break
                    else:
                        fo |= fotab[r[0]]
                    if not (fo <= fotab[r[i]]):
                        fotab[r[i]] |= fo
                        done = False
        return fotab

    def is_nullable(self, word):
        """Check whether 'word' can derive the empty word.

        'word' must be a list of symbols.  The return value is True,
        if every symbol in 'word' is nullable.  Otherwise the return
        value is false.
        """
        for x in word:
            if x not in self.nullable:
                return False
        return True

    def first_tokens(self, word):
        """Get all possible first terminals in derivations of 'word'.

        'word' must be a list of symbols.  The return value is the set
        of all possible terminal symbols which can be the start of a
        derivation from 'word'.
        """
        fi = set()
        for s in word:
            fi |= self.fitab[s]
            if s not in self.nullable:
                break
        return fi

    def follow_tokens(self, x):
        """Get all possible follow-up tokens after 'x'.

        'x' must be a symbol.  The return value is the set of all
        terminals which can directly follow 'x' in a derivation.
        """
        return self.fotab[x]

    def shortcuts(self):
        """Return a dictionary containing short expansions for every symbol.

        Nullable symbols are expanded to empty sequences, terminal
        symbols are mapped to one-element sequences containing
        themselves.
        """
        res = {}
        for X in self.terminals:
            res[X] = (X,)
        todo = set()
        for X in self.nonterminals:
            if X in self.nullable:
                res[X] = ()
            else:
                todo.add(X)

        rtab = {}
        for X in todo:
            rtab[X] = []
        for r in self.rules.itervalues():
            if r[0] in todo:
                rtab[r[0]].append(r[1:])

        while todo:
            still_todo = set()
            for X in todo:
                good_rules = []
                for r in rtab[X]:
                    for Y in r:
                        if Y not in res:
                            break
                    else:
                        good_rules.append(r)
                if good_rules:
                    word = reduce(lambda x,y: x+y,
                                  (res[Y] for Y in good_rules[0]),
                                  ())
                    for r in good_rules[1:]:
                        w2 = reduce(lambda x,y: x+y,
                                    (res[Y] for Y in r),
                                    ())
                        if len(w2) < len(word):
                            word = w2
                    res[X] = word
                else:
                    still_todo.add(X)
            todo = still_todo
        return res

    def write_terminals(self, fd, prefix=""):
        fd.write(prefix+"terminal symbols:\n")
        tt = map(repr, sorted(self.terminals-set([self.EOF])))
        for l in split_it(tt, padding=prefix+"  "):
            fd.write(l+"\n")

    def write_nonterminals(self, fd, prefix=""):
        fd.write(prefix+"nonterminal symbols:\n")
        tt = map(repr, sorted(self.nonterminals-set([self.start])))
        for l in split_it(tt, padding=prefix+"  "):
            fd.write(l+"\n")

    def write_productions(self, fd, prefix=""):
        fd.write(prefix+"production rules:\n")
        keys = sorted(self.rules.keys())
        for key in keys:
            r = self.rules[key]
            if r[0] == self.start:
                continue
            head = repr(r[0])
            tail = " ".join(map(repr, r[1:]))
            fd.write(prefix+"  %s -> %s\n"%(head, tail))

    def write_parser(self, fd, params):
        params.setdefault('date', strftime("%Y-%m-%d %H:%M:%S"))
        params['version'] = VERSION
        write_block(fd, 0, """#! /usr/bin/env python
# %(type)s parser, autogenerated on %(date)s
# generator: wisent %(version)s, http://seehuhn.de/pages/wisent
        """%params, first=True)
        if 'fname' in params:
            fd.write("# source: %(fname)s\n"%params)

        write_block(fd, 0, """
# All parts of this file which are not taken verbatim from the input grammar
# are covered by the following notice:
#""")
        fd.write(getcomments(template))
