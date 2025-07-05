#! /usr/bin/env python3

from sys import stderr
import math

from parser import Parser

def tokenize(str):
    from re import match

    res = []
    while str:
        if str[0].isspace():
            str = str[1:]
            continue

        m = match('[0-9.]+', str)
        if m:
            res.append(('NUMBER', float(m.group(0))))
            str = str[m.end(0):]
            continue

        m = match('[a-z]+', str)
        if m:
            res.append(('SYMBOL', m.group(0)))
            str = str[m.end(0):]
            continue

        res.append((str[0],))
        str = str[1:]

    return res

def eval_tree(tree):
    if tree[0] == 'expr':
        return eval_tree(tree[1])
    elif tree[0] == 'sum':
        return eval_tree(tree[1]) + eval_tree(tree[3])
    elif tree[0] == 'difference':
        return eval_tree(tree[1]) - eval_tree(tree[3])
    elif tree[0] == 'product':
        return eval_tree(tree[1]) * eval_tree(tree[3])
    elif tree[0] == 'quotient':
        return eval_tree(tree[1]) / eval_tree(tree[3])
    elif tree[0] == 'NUMBER':
        return tree[1]
    elif tree[0] == 'brackets':
        return eval_tree(tree[2])
    elif tree[0] == 'function':
        fn = getattr(math, tree[1][1])
        return fn(eval_tree(tree[3]))

p = Parser()
while True:
    try:
        s = input("calc: ")
    except EOFError:
        print()
        break
    tokens = tokenize(s)

    try:
        tree = p.parse(tokens)
    except p.ParseErrors as e:
        for token,expected in e.errors:
            if token[0] == p.EOF:
                print("unexpected end of file", file=stderr)
                continue

            found = repr(token[0])
            if len(expected) == 1:
                msg = "missing %s (found %s)"%(repr(expected[0]), found)
            else:
                msg1 = "parse error before %s, "%found
                l = sorted([ repr(s) for s in expected ])
                msg2 = "expected one of "+", ".join(l)
                msg = msg1+msg2
            print(msg, file=stderr)
        continue

    print(eval_tree(tree))
