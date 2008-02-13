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

def list_lines(prefix, bits, postfix):
    line = prefix+bits[0]
    for b in bits[1:]:
        test = line+", "+b
        if len(test)>=79:
            yield line+","
            line = " "*len(prefix) + b
        else:
            line = test
    yield line+postfix

def write_block(fd, indent, str, params={}):
    lines = [l.rstrip().expandtabs() for l in str.splitlines()]
    while lines and not lines[0]:
        del lines[0]
    while lines and not lines[-1]:
        del lines[-1]
    if not lines:
        return

    fd.write("\n")
    strip = min([len(l)-len(l.lstrip()) for l in lines if l!=""])
    stack = [ True ]
    for l in lines:
        l = l[strip:].rstrip()
        l0 = l.lstrip()
        if l0.startswith('#@'):
            token = l0[2:].split()
            if token[0] == "IF":
                stack.append(params.get(token[1], False))
            elif token[0] == "ELSE":
                stack[-1] = not stack[-1]
            elif token[0] == "ENDIF":
                stack.pop()
            continue
        if stack[-1]:
            fd.write(" "*indent+l+"\n")
