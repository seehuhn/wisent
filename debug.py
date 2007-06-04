#! /usr/bin/env python

def print_lr0_states(g, T):
    keys = sorted(T.keys())
    for i in keys:
        print "state %s:"%i
        for k,l,n in T[i]:
            r = g.rules[k]
            rr = map(repr, r)
            print "  "+rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])
        print

def print_lr1_states(g, T):
    keys = sorted(T.keys())
    for i in keys:
        print "state %s:"%i
        for k,l,n,next in T[i]:
            r = g.rules[k]
            rr = map(repr, r)
            print "  "+rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])+"|"+repr(next)
        print
