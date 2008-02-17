#! /usr/bin/env python

def split_it(args, padding="", start1="", start2=None, sep=", ",
             end1=",", end2="", maxwidth=79):
    """A generator to format args and split into lines.

    The elements of the list 'args' are converted into strings and
    grouped into lines.  'args' must not be empty.

    The first line is preceeded by 'padding+start1', all subsequent
    lines are preceeded by 'padding+start2' (or by 'padding+" "*len(start1)',
    if 'start2' is None).  The elements within a line are separated by
    'sep'.  All lines except for the last are terminated by 'end1',
    the last line is terminated by 'end2'.  If possible, lines are at
    most 'maxwidth' characters long.
    """
    if start2 is None:
        start2 = " "*len(start1)
    args = [ str(arg) for arg in args[:-1] ] + [ str(args[-1])+end2 ]

    line = padding + start1 + args.pop(0)
    while args:
        test = sep.join([line]+args)
        if len(test) <= maxwidth:
            line = test
            break

        arg = args.pop(0)
        if len(line+sep+arg+end1) > maxwidth:
            yield line+end1
            line = padding + start2 + arg
        else:
            line += sep+arg
    yield line

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
            fd.write((" "*indent+l).rstrip()+"\n")
