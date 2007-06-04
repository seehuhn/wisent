#! /usr/bin/env python

def layout_list(prefix, bits, postfix):
    output = prefix+", ".join(bits)+postfix
    while len(output)>79:
	try:
	    i = output[:80].rindex(", ")
	    yield output[:i+1]
	    output = " "*len(prefix)+output[i+2:]
	except:
	    break
    yield output
