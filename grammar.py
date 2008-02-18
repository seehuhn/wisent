#! /usr/bin/env python

from text import split_it

class GrammarError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class Marker(object):

    def __init__(self, text):
        self.texts = [ text ]

    def __repr__(self):
        return self.texts[-1]

    def push(self, text):
        self.texts.append(text)

    def pop(self):
        return self.texts.pop()

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
        for arg in kwargs:
            if arg == "start":
                continue
            raise TypeError("invalid keyword argument '%s'"%arg)

        self.rules = {}
        self.symbols = set()
        self.terminal = set()
        self.nonterminal = set()

        rules = dict(enumerate(rules))
        if not rules:
            raise GrammarError("empty grammar")
        first = True
        for key, r in rules.iteritems():
            self.rules[key] = r
            self.nonterminal.add(r[0])
            if first:
                self.start = r[0]
                first = False
            for s in r[1:]:
                self.symbols.add(s)

        if "start" in kwargs:
            self.start = kwargs["start"]
            if self.start not in self.nonterminal:
                msg = "start symbol %s is not a nonterminal"%repr(self.start)
                raise GrammarError(msg)

        self.terminal = self.symbols - self.nonterminal
        if cleanup:
            self._cleanup()
        self.nonterminal = frozenset(self.nonterminal)
        self.terminal = frozenset(self.terminal)
        self.symbols = frozenset(self.symbols)

        # precompute the set of all nullable symbols
        self.nbtab = frozenset(self._compute_nbtab())

        # precompute the table of all possible first symbols in expansions
        fitab = self._compute_fitab()
        self.fitab = {}
        for s in self.nonterminal|self.terminal:
            self.fitab[s] = frozenset(fitab[s])

        # precompute the table of all possible follow-up symbols
        fotab = self._compute_fotab()
        self.fotab = {}
        for s in self.nonterminal|self.terminal:
            self.fotab[s] = frozenset(fotab[s])

    def _cleanup(self):
        """Remove unnecessary rules and symbols."""
        # remove nonterminal symbols which do not expand into terminals
        N = set()
        T = self.terminal
        R = self.rules.keys()
        done = False
        while not done:
            done = True
            for key in R:
                r = self.rules[key]
                if r[0] in N: continue
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
                if r[0] not in gamma: continue
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
        s = Marker('$')
        T.add(s)
        self.terminator = s

        # generate a private start symbol
        s = Marker('S')
        N.add(s)
        self.rules[-1] = (s, self.start, self.terminator)
        self.start = s

        self.nonterminal = N
        self.terminal = T
        self.symbols = N|T

    def _compute_nbtab(self):
        """Compute the set of nullable symbols."""
        nbtab = set()
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                if r[0] in nbtab: continue
                for s in r[1:]:
                    if s not in nbtab: break
                else:
                    nbtab.add(r[0])
                    done = False
        return nbtab

    def _compute_fitab(self):
        """Compute the table of all possible first symbols in expansions."""
        fitab = {}
        for s in self.nonterminal:
            fitab[s] = set()
        for s in self.terminal:
            fitab[s] = set([s])
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                fi = set()
                for s in r[1:]:
                    fi |= fitab[s]
                    if s not in self.nbtab: break
                if not(fi <= fitab[r[0]]):
                    fitab[r[0]] |= fi
                    done = False
        return fitab

    def _compute_fotab(self):
        fotab = {}
        for s in self.nonterminal|self.terminal:
            fotab[s] = set()
        done = False
        while not done:
            done = True
            for key, r in self.rules.iteritems():
                for i in range(1,len(r)):
                    fo = set()
                    for s in r[i+1:]:
                        fo |= self.fitab[s]
                        if s not in self.nbtab: break
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
            if x not in self.nbtab: return False
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
            if s not in self.nbtab: break
        return fi

    def follow_tokens(self, x):
        """Get all possible follow-up tokens after 'x'.

        'x' must be a symbol.  The return value is the set of all
        terminals which can directly follow 'x' in a derivation.
        """
        return self.fotab[x]

    def write_terminals(self, fd, prefix=""):
        fd.write(prefix+"terminal symbols:\n")
        tt = map(repr, sorted(self.terminal-set([self.terminator])))
        for l in split_it(tt, padding=prefix+"  "):
            fd.write(l+"\n")

    def write_nonterminals(self, fd, prefix=""):
        fd.write(prefix+"nonterminal symbols:\n")
        tt = map(repr, sorted(self.nonterminal-set([self.start])))
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
