#! /usr/bin/env python

from sys import argv

from scanner import tokens
from parser import Parser

def rules(tree):
    for rule in tree[2:]:
        target = rule[2][1:3]
        for l in rule[4:-1]:
            if l[1] != "list":
                continue
            yield tuple([target]+[x[1:3] for x in l[2:]])

def read_rules(fname, aux):
    p = Parser()
    fd = open(fname)
    res = p.parse_tree(tokens(fd))
    fd.close()

    for l in rules(res):
        if l[0][0] == 'token' and l[0][1].startswith("_"):
            aux.add(l[0][1])
        todo = []
        ll = []
        attention = ""
        for token in reversed(l):
            if attention == "+":
                seq = token[1]+"+"
                if seq not in aux:
                    todo.append((seq, token[1]))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                attention = False
            elif attention == "*":
                seq = token[1]+"*"
                if seq not in aux:
                    todo.append((seq,))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                attention = False
            elif token[0] == '*':
                attention = "*"
            elif token[0] == '+':
                attention = "+"
            else:
                ll.append(token[1])
        yield tuple(reversed(ll))
        while todo:
            yield todo.pop(0)
