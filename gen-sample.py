#! /usr/bin/env python

from sys import argv
import random
from wifile import read_rules
from grammar import Grammar

rng = random.Random()

g = Grammar(read_rules(argv[1]))

def terminate(text, maxdepth):
    ii = [ i for i,X in enumerate(text) if X in g.nonterminal ]
    if not ii:
        yield text
        return
    if maxdepth < len(ii):
        return

    i = ii[0]
    pre = text[:i]
    X = text[i]
    post = text[i+1:]
    rr = [ r[1:] for r in g.rules.values() if r[0] == X ]
    for r in rr:
        for res in terminate(r+post, maxdepth-1):
            yield pre + res

terminations = {}
for X in g.nonterminal:
    res = set()
    i = 5
    while not res:
        for word in terminate((X,), i):
            res.add(word)
        i += 1
    terminations[X] = list(res)
for X in g.terminal:
    terminations[X] = [(X,)]

grow_rules = {}
for X in g.nonterminal:
    grow_rules[X] = []
for r in g.rules.values():
    n_nonterminal = len([ X for X in r[1:] if X in g.nonterminal ])
    if n_nonterminal >= 1:
        grow_rules[r[0]].append(list(r[1:]))

def grow(text, maxdepth, minlen):
    if len(text) >= minlen:
        yield text
        return
    if maxdepth <= 0:
        return

    ii = [ i for i,X in enumerate(text) if X in grow_rules ]
    rng.shuffle(ii)
    for i in ii:
        pre = text[:i]
        post = text[i+1:]
        rr = grow_rules[text[i]]
        for r in rr:
            for res in grow(pre+r+post, maxdepth-1, minlen):
                yield res

for skel in grow([ g.start ], 1000, 1000):
    res = []
    for X in skel:
        res += rng.choice(terminations[X])
    print " ".join(map(repr, res[:-1]))
    break
raise SystemExit(1)


i = 1
done = False
while not done:
    print "depth %d"%i
    maxlen = 0
    for res in all_expansions([ g.start ], i):
        n = len(res)
        if n > maxlen:
            maxlen = n
        if n>20:
            done = True
            break
    else:
        print "  maxlen = %d"%maxlen
    i += 1
print "-->"+" ".join(map(repr, res))
