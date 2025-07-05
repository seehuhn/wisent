#! /usr/bin/env python3

from sys import stderr, argv

from scanner import tokenize
from parser import Parser

def prepare(l):
    for tp, val in tokenize(l):
        if tp == "comment":
            pass
        elif tp == "special":
            yield (val, val)
        else:
            yield (tp, val)

p = Parser()

res = {}
for l in open("list", encoding="utf-8"):
    l = l.strip()
    try:
        tree = p.parse(prepare(l))
    except p.ParseErrors as e:
        continue

    for x in tree[1::2]:
        if x[0] == "mailbox":
            t = x[1]
            res.setdefault(t, 0)
            res[t] += 1
        elif x[0] == "group":
            for y in x[3:-1:2]:
                t = y[1]
                res.setdefault(t, 0)
                res[t] += 1
        else:
            print(x)
            raise NotImplementedError()

for t,n in sorted(res.items(), key=lambda x:(x[1],x[0])):
    if t[0] == "name-addr":
        print(n, "".join(x[1] for x in p.leaves(t[2][2])), " ".join(x[1] for x in p.leaves(t[1])))
    elif t[0] == "addr-spec":
        print(n, "".join(x[1] for x in p.leaves(t)))
    else:
        raise NotImplementedError()
