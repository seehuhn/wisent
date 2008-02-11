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

    def _write_tables(self, fd):
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
        fd.write('from itertools import chain\n\n')
        fd.write('class Parser(object):\n\n')
        write_block(fd, 4, """
        class ParseErrors(Exception):

            def __init__(self, errors, tree):
                self.errors = errors
                self.tree = tree

            def __str__(self):
                n = len(self.errors)
                if n == 1:
                    msg = '1 syntax error'
                else:
                    msg = '%d syntax errors'%n
                if self.tree is None:
                    msg += ', unrecoverable'
                return "<"+msg+">"
        """)
        fd.write('\n')
        tt = map(repr, sorted(self.terminal-set([self.terminator])))
        for l in list_lines("    terminal = [ ", tt, " ]"):
            fd.write(l+'\n')

        self._write_tables(fd)
        fd.write('\n')

        write_block(fd, 4, """
        def __init__(self, max_err=None, errcorr_pre=4, errcorr_post=4):
            self.max_err = max_err
            self.m = errcorr_pre
            self.n = errcorr_post
        """)
        fd.write('\n')

        write_block(fd, 4, """
        @staticmethod
        def leaves(tree):
            if tree[0]:
                yield tree[1:]
            else:
                for x in tree[2:]:
                    for t in Parser.leaves(x):
                        yield t
        """)
        fd.write('\n')

        write_block(fd, 4, """
        def _parse_tree(self, input, stack, state):
            read_next = True
            while True:
                if read_next:
                    try:
                        readahead = input.next()
                    except StopIteration:
                        return (False, state, None)
                    read_next = False
                token = readahead[0]
                if (state,token) in self._reduce:
                    X,n = self._reduce[(state,token)]
                    if n > 0:
                        state = stack[-n][0]
                        tree = (False,X)+tuple(s[1] for s in stack[-n:])
                        del stack[-n:]
                    else:
                        tree = (False,X)
                    stack.append((state,tree))
                    state = self._goto[(state,X)]
                elif (state,token) in self._shift:
                    if token == self.EOF:
                        break
                    stack.append((state,(True,)+readahead))
                    read_next = True
                    state = self._shift[(state,token)]
                else:
                    return (False,state,readahead)
            return (True,state,None)
        """)
        fd.write('\n')

        write_block(fd, 4, """
        def _try_correction(self, stack, state, input):
            read_next = True
            pos = 0
            maxpos = len(input)
            while pos < maxpos:
                token = input[pos][0]
                if (state,token) in self._reduce:
                    X,n = self._reduce[(state,token)]
                    if n > 0:
                        state = stack[-n]
                        del stack[-n:]
                    stack.append(state)
                    state = self._goto[(state,X)]
                elif (state,token) in self._shift:
                    if token == self.EOF:
                        break
                    stack.append(state)
                    pos += 1
                    state = self._shift[(state,token)]
                else:
                    break
            return maxpos - pos
        """)
        fd.write('\n')

        write_block(fd, 4, """
        def parse_tree(self, input):
            errors = []
            input = chain(input, [(self.EOF,)])
            stack = []
            state = 0
            while True:
                done,state,readahead = self._parse_tree(input, stack, state)
                if done:
                    break

                expect = [ t for s,t in self._reduce.keys()+self._shift.keys()
                           if s == state ]
                errors.append(([ s[1] for s in stack ], readahead, expect))
                if self.max_err is not None and len(errors) >= self.max_err:
                    raise self.ParseErrors(errors, None)

                queue = []
                def split_input(m, stack, readahead, input, queue):
                    for s in stack:
                        for t in self.leaves(s[1]):
                            queue.append(t)
                            if len(queue) > m:
                                yield queue.pop(0)
                    queue.append(readahead)
                in2 = split_input(self.m, stack, readahead, input, queue)
                stack = []
                done,state,readahead = self._parse_tree(in2, stack, 0)
                m = len(queue)
                for i in range(0, self.n):
                    try:
                        queue.append(input.next())
                    except StopIteration:
                        break

                def vary_queue(queue, m):
                    for i in range(self.m, -1, -1):
                        for t in self.terminal:
                            yield queue[:i]+[(t,)]+queue[i:]
                        if queue[i][0] == self.EOF:
                            continue
                        for t in self.terminal:
                            if t == queue[i]:
                                continue
                            yield queue[:i]+[(t,)]+queue[i+1:]
                        yield queue[:i]+queue[i+1:]
                best_rest = len(queue)+2
                for q2 in vary_queue(queue, m):
                    rest = self._try_correction([ s[0] for s in stack ], state, q2)
                    if rest < best_rest:
                        best_rest = rest
                        best_queue = q2
                        if rest == 0:
                            break
                if best_rest >= self.n:
                    raise self.ParseErrors(errors, None)
                input = chain(best_queue, input)

            tree = stack[0][1]
            if errors:
                raise self.ParseErrors(errors, tree)
            return tree
        """)
