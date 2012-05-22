# grammar.py - the Grammar class and related code
#
# Copyright (C) 2008, 2009, 2012  Jochen Voss <voss@seehuhn.de>
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
from os.path import basename
from random import choice, uniform
from inspect import getsource

from text import split_it, write_block
from scanner import tokens
from parser import Parser
import template


def _print_error(msg, lineno=None, offset=None, fname=None):
    """Emit error messages to stderr."""
    parts = []
    if fname is not None:
        parts.append("%s:"%fname)
    else:
        parts.append("error:")
    if lineno is not None:
        parts.append("%d:"%lineno)
        if offset is not None:
            parts.append("%d:"%offset)
    prefix = "".join(parts)
    if prefix:
        prefix = prefix+" "
    print >>sys.stderr, prefix+unicode(msg)

class RulesError(Exception):

    """Error conditions in the set of production rules."""

    def __init__(self, msg):
        """Create an exception describing an error in a rule set.

        `msg` should be a human-readable description of the problem
        for use in an error message.
        """
        super(RulesError, self).__init__(msg)

class Conflicts(Exception):

    """Lists of conflicts in LR(1) grammars.

    In order to allow Wisent to report all discovered conflicts in one
    run, this exception represents lists of grammar conflicts.
    """

    def __init__(self):
        """Create a new Conflicts exception.

        At creation time, the exception object contains no information
        about conflicts.  All errors should be added using the `add`
        method before the exception is raised.

        Iterating over the exception object returns the recorded
        conflicts one by one.
        """
        self.list = {}

    def __len__(self):
        """The number of conflicts recorded in the exception."""
        return len(self.list)

    def __iter__(self):
        return self.list.iteritems()

    def add(self, data, text):
        """Add another conflict to the list.

        `data` is a list of tuples describing the conflict, each tuple
        encoding information about one of the conflicting actions.
        For shift actions the first element of the tuple is the string
        'S', the second element is the index of the corresponding
        production rule and the third element is the position of the
        shifted element within the rule.  For reduce actions the first
        element of the tuple is the string 'R' and the second element
        is the index of the production rule involved.

        `text` is a string of terminal symbols which illustrates the
        conflict: after the tokens from `text[:-1]` are read and with
        lookahead symbol `text[-1]`, each of the actions described by
        `data` can be applied.
        """
        if data in self.list:
            if len("".join(text)) >= len("".join(self.list[data])):
                return
        self.list[data] = text

    def print_conflicts(self, rules, rule_locations={}, fname=None):
        """Print a human-readable description of the errors to stderr.

        `rules` must be a dictionary mapping rule indices to
        production rules.  The optional argument `rule_locations`, if
        present, must be a dictionary such that `rule_locations[k][n]`
        is a tuple giving the line and column of the `n`th token of
        the `k`th grammar rule in the source file.  `fname`, if given,
        should be the input file name.
        """
        ee = []
        def rule_error(k, n):
            r = [ repr(X) for X in rules[k] ]
            if n < len(r):
                tail = " ".join(r[1:n])+"."+" ".join(r[n:])
            else:
                tail = " ".join(r[1:])
            ee.append("    "+r[0]+": "+tail+";")
            try:
                loc = rule_locations[k][n]
            except KeyError:
                loc = (None,None)
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

    """Unique objects for use as markers.

    These objects are internally used to represent the start symbol
    and the end-of-input marker of the grammar.
    """

    def __init__(self, label):
        """Create a new unique object.

        `label` is a string which is used as a textual representation
        of the object.
        """
        self.label = label

    def __repr__(self):
        """Return the `label` given at object construction."""
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

        if self.start[0] == "_":
            msg = "start symbol '%s' is transparent"%repr(self.start)
            raise RulesError(msg)

        if self.start not in self.nonterminals:
            msg = "start symbol '%s' is not a nonterminal"%repr(self.start)
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
        for k, rule in self.rules.iteritems():
            self.rule_from_head[rule[0]].append((k,len(rule)))

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
            if still_todo == todo:
                msg = "symbols without finite expansion ("
                syms = sorted(x for x in todo if x != self.start)
                msg = msg + ", ".join('"%s"'%x for x in syms) + ")"
                raise RulesError(msg)
            todo = still_todo
        return res

    def write_terminals(self, fd=sys.stdout, prefix=""):
        fd.write(prefix+"terminal symbols:\n")
        tt = map(repr, sorted(self.terminals-set([self.EOF])))
        for l in split_it(tt, padding=prefix+"  "):
            fd.write(l+"\n")

    def write_nonterminals(self, fd=sys.stdout, prefix=""):
        fd.write(prefix+"nonterminal symbols:\n")
        nterms = self.nonterminals
        symbols = [ x for x in nterms-set([self.start]) if str(x)[0] != '_' ]
        tt = map(repr, sorted(symbols))
        for l in split_it(tt, padding=prefix+"  "):
            fd.write(l+"\n")

    def write_productions(self, fd=sys.stdout, prefix=""):
        fd.write(prefix+"production rules:\n")
        keys = sorted(self.rules.keys())
        for key in keys:
            r = self.rules[key]
            if r[0] == self.start:
                continue
            head = repr(r[0])
            tail = " ".join(map(repr, r[1:]))
            fd.write((prefix+"  %s -> %s"%(head, tail)).rstrip()+"\n")

    def write_example(self, fd=sys.stdout, params={}):
        word = [ self.rules[-1][1] ]
        todo = set(self.rules.keys())

        nt = self.nonterminals
        def count_nt(k):
            return len([X for X in self.rules[k][1:] if X in nt])

        while todo:
            actions = []
            for i,X in enumerate(word):
                if X not in nt:
                    continue
                rules = set(k for k,l in self.rule_from_head[X])&todo
                for k in rules:
                    actions.append((i,k))
            good_actions = [ a for a in actions if count_nt(a[1])>1 ]
            if good_actions:
                actions = good_actions
            try:
                i,k = choice(actions)
            except IndexError:
                break
            word[i:i+1] = self.rules[k][1:]
            if uniform(0,1)<0.1*len(word):
                todo.discard(k)
        short = self.shortcuts()
        res = []
        for X in word:
            res.extend(repr((Y,)) for Y in short[X])

        parser = params.get("parser_name", "")
        if parser.endswith(".py"):
            parser = basename(parser)[:-3]
        else:
            parser = "..."

        write_block(fd, 0, """
        #! /usr/bin/env python
        # %(example_name)s - illustrate the use of a Wisent-generated parser
        # example code autogenerated on %(date)s
        # generator: wisent %(version)s, http://seehuhn.de/pages/wisent
        """%params, first=True)
        if 'fname' in params:
            fd.write("# source: %(fname)s\n"%params)

        fd.write('\n')
        fd.write('from sys import stderr\n')
        fd.write('\n')
        fd.write('from %s import Parser\n'%parser)

        write_block(fd, 0, getsource(template.print_tree))

        fd.write('\n')
        for l in split_it(res, start1="input = [ ", end2=" ]"):
            fd.write(l+'\n')
        write_block(fd, 0, """
        p = Parser()
        try:
            tree = p.parse(input)
        except p.ParseErrors, e:
            for token,expected in e.errors:
                if token[0] == p.EOF:
                    print >>stderr, "unexpected end of file"
                    continue

                found = repr(token[0])
                if len(expected) == 1:
                    msg = "missing %s (found %s)"%(repr(expected[0]), found)
                else:
                    msg1 = "parse error before %s, "%found
                    l = sorted([ repr(s) for s in expected ])
                    msg2 = "expected one of "+", ".join(l)
                    msg = msg1+msg2
                print >>stderr, msg
            raise SystemExit(1)
        """)
        fd.write('\n')
        fd.write('print_tree(tree, p.terminals)\n')

######################################################################
# read grammar files

def _parse_grammar_file(fd, params={}):
    """Read a grammar file and return the resulting parse tree.

    The return value of this function is a tuple, consisting of the
    parse tree (or None in case of an unrecoverable error) and a
    boolean indicating whether errors (recoverable or unrecoverable)
    were found.

    If the grammar file contains errors, error messages are printed to
    stderr.
    """
    max_err = 100
    p = Parser(max_err=max_err)
    try:
        tree = p.parse(tokens(fd))
        has_errors = False
    except SyntaxError, e:
        _print_error(e.msg, e.lineno, e.offset,
                     fname=params.get("fname", None))
        tree = None
        has_errors = True
    except p.ParseErrors, e:
        for token,expected in e.errors:
            if token[0] == p.EOF:
                _print_error("unexpected end of file",
                             fname=params.get("fname", None))
                continue

            def quote(x):
                s = unicode(x)
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
                             token[2], token[3],
                             fname=params.get("fname", None))
                continue

            msg1 = "parse error before %s"%found
            l = sorted([ quote(s) for s in expected ])
            if expect_eol:
                l.append("end of line")
            msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
            _print_error(msg1+", "+msg2, token[2], token[3],
                         fname=params.get("fname", None))
        tree = e.tree
        has_errors = True
        if len(e.errors) == max_err and tree is None:
            _print_error("too many errors, giving up ...",
                         fname=params.get("fname", None))
    return tree, has_errors

def _fixup(tokens):
    """Fix up the payload for repaired trees."""
    # find data for use in an initial stretch of damaged tokens
    for i,r in enumerate(tokens):
        if i == 0 or r[0] not in Parser.terminals:
            continue
        if len(r) > 1:
            data = r[2:]
            break
    else:
        data = ()

    res = [ ]
    for i,r in enumerate(tokens):
        if i == 0 or r[0] not in Parser.terminals:
            res.append(r)
        elif len(r) > 1:
            res.append(r)
            data = r[2:]
        else:
            res.append((r[0], '['+r[0]+']')+data)
    return tuple(res)

class NameInventor(object):

    def __init__(self):
        self.idx = 0

    def __call__(self, op):
        if op == "(":
            res = "_(%d)"%self.idx
        elif op.isalnum():
            res = "_%d%s."%(self.idx, op)
        else:
            res = "_%d%s"%(self.idx, op)
        self.idx += 1
        return res

_invent = NameInventor()

def _expand_globbing(head, tail):
    todo = []
    i = 0
    while i < len(tail):
        x = tail[i]
        if x[0] == 'group':
            assert x[1][0] == '('
            newhead = ('token', _invent('(')) + x[1][2:]
            todo.append(('(',newhead)+x[2:])
            assert x[-1][0] == ')'
            tail[i:i+1] = [ newhead ]
        if i+1 < len(tail) and tail[i+1][0] in [ '?', '*', '+' ]:
            op = tail[i+1][0]
            newhead = ('token', _invent(op)) + tail[i][2:]
            todo.append((op,newhead,tail[i],tail[i+1]))
            tail[i:i+2] = [ newhead ]
        i += 1

    yield [head]+tail

    for item in todo:
        op = item[0]
        head = item[1]
        tail = item[2:]
        if op == '(':
            for r in _expand_alternatives(head, tail):
                yield r
        elif op == '?':
            assert len(tail) == 2
            yield [ head, tail[1] ]
            yield [ head, tail[0], tail[1] ]
        elif op == '*':
            assert len(tail) == 2
            yield [ head, tail[1] ]
            yield [ head, head, tail[0], tail[1] ]
        elif op == '+':
            assert len(tail) == 2
            yield [ head, tail[0], tail[1] ]
            yield [ head, head, tail[0], tail[1] ]

def _expand_alternatives(head, tail):
    """Expand the "|" operator.

    The value 'tail' must be of the form "list | ... | list ;".
    """
    for t in tail:
        if t[0] == "list":
            t = _fixup(t)
            rule = list(t[1:])
        else:
            for r in _expand_globbing(head, rule+[t]):
                yield r

def extract_rules(tree):
    """Extract the grammar rules from the parse tree.

    This generator yields the grammar rules one by one (without the
    colon after the head but still with the terminating semi-colon).
    The special '?', '*' and '+' suffix tokens are expanded here.
    """
    res = []
    for rule in tree[1:]:
        rule = _fixup(rule)
        assert rule[0] == 'rule'
        head = rule[1]
        assert rule[2][0] == ':'
        for r in _expand_alternatives(head, rule[3:]):
            res.append(r)
    return res

def _rules_by_head(rules):
    A = {}
    head_repl = Unique("HEAD")
    for r in rules:
        headsym = r[0][1]
        if headsym[0] != "_":
            # no optimisations possible for user-visible symbols
            continue
        tail = []
        for x in r[1:]:
            if x[0] == 'token' and x[1] == headsym:
                tail.append(head_repl)
            else:
                tail.append((x[0],x[1]))
        A[headsym] = A.get(headsym,[]) + [ tuple(tail) ]
    return A

def _substitute(rules, old_names, new_name):
    res = []
    for r in rules:
        head = r[0]
        if head[1] in old_names:
            continue
        s = [ head ]
        for x in r[1:]:
            if x[0] == 'token' and x[1] in old_names:
                s.append(('token',new_name,)+x[2:])
            else:
                s.append(x)
        res.append(s)
    return res

def _inline(rules, old_name, repl_list):
    res = []
    for r in rules:
        head = r[0]
        if head[1] == old_name:
            continue

        changed = False
        for repl in repl_list:
            tail = [ head ]
            for x in r[1:]:
                if x[0] == 'token' and x[1] == old_name:
                    tail.extend(repl)
                    changed = True
                else:
                    tail.append(x)
            res.append(tail)
            if not changed:
                break
    return res

def optimise_rules(rules):
    """Optimise the rule-set returned from `extract_rules`.

    The following optimisations are performed by this function:
    * Removes duplicate rules where the head is a transparent
      symbol.  These rules are most often autogenerated rules from
      the '*', '?' and '+' operators.
    * Selectively inline some rules.
    """
    rules = list(rules)

    # repeat steps 1 and 2 below until the result is stable
    changed = True
    while changed:
        changed = False

        # step 1: Remove duplicate rules.
        A = _rules_by_head(rules)
        B = {}
        for head,rr in A.iteritems():
            rr = frozenset(rr)
            B[rr] = B.get(rr,[]) + [head]
        for hh in B.itervalues():
            if len(hh) < 2:
                continue
            head = hh.pop()
            rules = _substitute(rules, hh, head)
            changed = True

        # step 2: Inline rules which only occur once.
        # Inlining a rule changes the length of the ruleset
        # as follows.
        #
        # 1) Removing a rule of length l (not including the
        #    trailing semi-colon) removes l+1 tokens, i.e. in
        #    total R = l1+...+lk+k tokens are removed.
        # 2) Each replacement in a rule of length l adds
        #    l+l1 + ... + l+lk - (l+1) = (k-1)*l + l1+...+lk - 1
        #    tokens, i.e. in total
        #    A = (k-1)*(l1+...+ln) + (l1+...+lk-1)*n
        #    tokens are added.
        #
        # If the symbol occurs several times on the rhs of the
        # same rule, "many" new tokens would appear and we avoid
        # expansion.  If the symbol appears as the head and on the
        # right-hand side of the same rule, expansion is
        # impossible.

        # compute lengths of all replacements
        repl = {}
        for r in rules:
            sym = r[0][1]
            if sym[0] != "_":
                # no optimisations possible for user-visible symbols
                continue
            # be careful to not include the terminator in the replacement
            if sym in repl:
                repl[sym].append(r[1:-1])
            else:
                repl[sym] = [ r[1:-1] ]

        # compute lengths of all texts into which we could replace
        rlength = {}
        for r in rules:
            seen = set()
            headsym = r[0][1]
            for x in r[1:]:
                sym = x[1]
                if x[0] != 'token' or sym not in repl:
                    continue
                if sym in seen or sym == headsym:
                    del repl[sym]
                seen.add(sym)
                # be careful to not count the terminator
                if sym in rlength:
                    rlength[sym].append(len(r[1:-1]))
                else:
                    rlength[sym] = [ len(r[1:-1]) ]

        savings = []
        for sym,rr in repl.iteritems():
            k = len(rr)
            sk = sum(len(r) for r in rr)
            n_remove = sk + k
            n = len(rlength[sym])
            sn = sum(rlength[sym])
            n_add = (k-1)*sn + (sk-1)*n
            if n_remove > n_add:
                savings.append((n_remove-n_add, sym))
        if savings:
            savings.sort()
            _,sym = savings[-1]
            rules = _inline(rules, sym, repl[sym])
            changed = True
    return rules

def read_grammar(fd, params={}, checkfunc=None):
    """Convert a grammar file into a `Grammar` object.

    This function reads the textual description of a grammar from a
    file.  If the contents of this file are valid, a `Grammar` object
    is returned.  Otherwise a list of errors is printed to `stderr`
    and the program is terminated.
    """
    fname = params.get("fname", None)
    tree, has_errors = _parse_grammar_file(fd, params)
    if tree is None:
        raise SystemExit(1)

    rules = extract_rules(tree)
    if not rules:
        _print_error("no rules found", fname=fname)
        raise SystemExit(1)
    start = rules[0][0]
    if start[1].startswith("_"):
        _print_error("start symbol '%s' is transparent"%start[1],
                     start[2], start[3], fname=fname)
        raise SystemExit(1)

    rules = optimise_rules(rules)

    rule_locations = {}
    overrides = {}
    rr = []
    for k,r in enumerate(rules):
        force = []
        i = 0;
        while i < len(r):
            if r[i][0] == '!':
                force.append(i)
                del r[i]
            else:
                i += 1
        overrides[k] = frozenset(force)

        rule_locations[k] = tuple(x[2:] for x in r)
        rr.append(tuple(x[1] for x in r[:-1]))
    transparent = [ r[0] for r in rr if r[0].startswith("_") ]
    params['transparent_tokens'] = frozenset(transparent)
    params['overrides'] = overrides

    try:
        g = Grammar(rr)
    except RulesError, e:
        _print_error(e, fname=fname)
        raise SystemExit(1)

    # check for infinite loops
    try:
        g.shortcuts()
    except RulesError, e:
        _print_error(e)
        raise SystemExit(1)

    if checkfunc is not None:
        try:
            res = checkfunc(g, params)
        except Conflicts, e:
            e.print_conflicts(g.rules, rule_locations, fname)
            n = len(e)
            if n == 1:
                msg = "1 conflict"
            else:
                msg = "%d conflicts"%n
            _print_error("%s, aborting ..."%msg, fname=fname)
            has_errors = True
    else:
        res = g

    if has_errors:
        raise SystemExit(1)

    return res
