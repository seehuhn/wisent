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

import sys

from text import split_it
from scanner import tokens
from parser import Parser


def _print_error(msg, lineno=None, offset=None, fname=None):
    """Emit error messages to stderr."""
    parts = []
    if fname is not None:
        parts.append("%s:"%fname)
    if lineno is not None:
        parts.append("%d:"%lineno)
        if offset is not None:
            parts.append("%d:"%offset)
    prefix = "".join(parts)
    if prefix:
        prefix = prefix+" "
    print >>sys.stderr, prefix+str(msg)

class RulesError(Exception):

    """Error conditions in the set of production rules."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class Conflicts(Exception):

    """Lists of conflicts in LR(1) grammars."""

    def __init__(self):
        self.list = {}

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return self.list.iteritems()

    def add(self, data, text):
        """Add another conflict to the list."""
        if data in self.list:
            if len("".join(text)) >= len("".join(self.list[data])):
                return
        self.list[data] = text

    def print_conflicts(self, rules, rule_locations=None, fname=None):
        """Print error messages to stderr."""
        ee = []
        def rule_error(k, n):
            r = [ repr(X) for X in rules[k] ]
            if n < len(r):
                tail = " ".join(r[1:n])+"."+" ".join(r[n:])
            else:
                tail = " ".join(r[1:])
            ee.append("    "+r[0]+": "+tail+";")
            if rule_locations is None:
                loc = (None,None)
            else:
                loc = rule_locations[k][n]
            while ee:
                msg = ee.pop(0)
                _print_error(msg, loc[0], loc[1], fname=fname)

        for res, text in self:
            shift = []
            red = []
            for m in res:
                if m[0] == 'S':
                    shift.append(m[1:])
                else:
                    red.append(m[1])

            if len(red)>1:
                conflict = "reduce-reduce"
            else:
                conflict = "shift-reduce"
            ee.append("%s conflict: the input"%conflict)
            head = " ".join(x for x in text[:-1] if x)
            ee.append("    "+head+"."+text[-1]+" ...")

            if shift:
                msg = "  can be shifted using "
                if len(shift)>1:
                    msg += "one of the production rules"
                else:
                    msg += "the production rule"
                ee.append(msg)
                for k, n in shift:
                    rule_error(k, n)
                cont = "or "
            else:
                cont = ""

            for k in red:
                rule = rules[k]
                n = len(rule)
                ee.append("  %scan be reduced to"%cont)
                head = "".join(x+" " for x in text[:-n] if x)
                repl = head+repr(rule[0])+"."+text[-1]
                ee.append("    "+repl+" ...")
                ee.append("  using the production rule")
                rule_error(k, n)
                cont = "or "

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
            raise RulesError("empty grammar")
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
                raise RulesError(msg)

        self.terminals = self.symbols - self.nonterminals
        if cleanup:
            self._cleanup()
        self.nonterminals = frozenset(self.nonterminals)
        self.terminals = frozenset(self.terminals)
        self.symbols = frozenset(self.symbols)

        self.rule_from_head = {}
        for X in self.symbols:
            self.rule_from_head[X] = []
        for k, s in self.rules.iteritems():
            self.rule_from_head[s[0]].append((k,len(s)))

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
        # remove nonterminal symbols which do generate terminals
        N = set([r[0] for r in self.rules.values() if len(r) == 1])
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
            tmpl = "start symbol %s doesn't generate terminals"
            raise RulesError(tmpl%repr(self.start))
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

######################################################################
# read grammar files

def _parse_grammar_file(fname):
    """Read a grammar file and return the resulting parse tree.

    The return value of this function is a tuple, consisting of the
    parse tree (or None in case of an unrecoverable error) and a
    boolean indicating whether errors (recoverable or unrecoverable)
    were found.

    If the grammar file contains errors, error messages are printed to
    stderr.
    """
    p = Parser()
    try:
        fd = open(fname)
        tree = p.parse_tree(tokens(fd))
        fd.close()
        has_errors = False
    except SyntaxError, e:
        _print_error(e.msg, e.lineno, e.offset, e.filename)
        tree = None
        has_errors = True
    except p.ParseErrors, e:
        for token,expected in e.errors:
            if token[0] == p.EOF:
                _print_error("unexpected end of file", fname=fname)
                continue

            def quote(x):
                s = str(x)
                if not s.isalpha():
                    s = "'"+s+"'"
                return s
            tp = quote(token[0])
            val = quote(token[1])
            if val and tp != val:
                found = "%s %s"%(tp, repr(token[1]))
            else:
                found = tp

            if p.EOF in expected:
                expected.remove(p.EOF)
                expect_eol = True
            else:
                expect_eol = False
            if len(expected) == 1:
                missing = quote(expected[0])
                _print_error("missing %s (found %s)"%(missing, found),
                             token[2], token[3], fname)
                continue

            msg1 = "parse error before %s"%found
            l = sorted([ quote(s) for s in expected ])
            if expect_eol:
                l.append("end of line")
            msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
            _print_error(msg1+", "+msg2, token[2], token[3], fname)
        tree = e.tree
        has_errors = True
    return tree, has_errors

def _extract_rules(tree, aux):
    """Extract the grammar rules from the parse tree.

    This generator yields the grammar rules one by one.  The special
    "*" and "+" suffix tokens are expanded here.

    As a side-effect, all transparent symbols are added to the set
    'aux'.
    """
    for rule in tree[1:]:
        # rule[0] == 'rule'
        head = rule[1]
        if not head:
            # repaired trees have no payload
            head = ('', )+rule[2][2:]
        if head[0] == "token" and head[1].startswith("_"):
            aux.add(head[1])
        # rule[2] == (':', ...)
        for r in rule[3:]:
            if r[0] == "list":
                tail = list(r[1:])
                for i,x in enumerate(tail):
                    if not x:
                        # repaired trees have no payload
                        tail[i] = ('', )+rule[2][2:]
            else:
                # at a '|' or ';'
                res = [ head ]+tail+[ (';',';')+r[2:] ]

                todo = []
                for i in range(len(res)-2, 1, -1):
                    y = res[i]
                    if y[0] in [ '+', '*' ]:
                        x = res[i-1]
                        new = x[1]+y[0]
                        if new not in aux:
                            aux.add(new)
                            todo.append((new,)+x[1:])
                        res[i-1:i+1] = [ ('token',new)+x[2:] ]

                force = []
                i = 0
                while i < len(res):
                    x = res[i]
                    if x[0] == "!":
                        force.append(i)
                        del(res[i])
                    else:
                        i += 1

                yield [ x[1:] for x in res ], force
                for x in todo:
                    h = x[0]
                    a = (h,)+x[2:]
                    b = x[1:]
                    c = (';',)+x[2:]
                    if h[-1] == '+':
                        yield [ a, b, c ], []
                        yield [ a, a, b, c ], []
                    elif h[-1] == '*':
                        yield [ a, c ], []
                        yield [ a, a, b, c ], []

def read_grammar(fname, params={}, checkfunc=None):
    """Convert a textual description of a grammar into a `Grammar` object.

    This function reads the description of a grammar from a text file.
    If the contents of this file are valid, a `Grammar` object is
    returned.  Otherwise a list of errors is printed to `stderr` and
    the program is terminated.
    """
    params.setdefault("fname", fname)
    tree, has_errors = _parse_grammar_file(fname)
    if tree is None:
        raise SystemExit(1)

    def postprocess(rr, rule_locations, overrides):
        """Postprocess the output of `rules`

        This removes trailing semi-colons and extracts the line number
        information and the conflict override information.
        """
        for k,r_f in enumerate(rr):
            r,force = r_f
            rule_locations[k] = tuple(x[1:] for x in r)
            overrides[k] = frozenset(force)
            yield tuple(x[0] for x in r[:-1])

    aux = set()
    rule_locations = {}
    overrides = {}
    rr = postprocess(_extract_rules(tree, aux), rule_locations, overrides)
    params['transparent_tokens'] = aux
    params['overrides'] = overrides

    try:
        g = Grammar(rr)
    except RulesError, e:
        _print_error(e, fname=fname)
        raise SystemExit(1)

    if checkfunc is not None:
        try:
            res = checkfunc(g, params)
        except Conflicts, e:
            e.print_conflicts(g.rules, rule_locations, fname)
            _print_error("%d conflicts, aborting ..."%len(e), fname=fname)
            has_errors = True
    else:
        res = g

    if has_errors:
        raise SystemExit(1)

    return res
