#! /usr/bin/env python

from sys import stderr, stdout
from time import strftime
from optparse import OptionParser

from lr1 import LR1
from text import write_block
from scanner import tokens
from parser import Parser

wisent_version = "0.1"

parser_types = {
    "ll1": ("LL(1)",),
    "lr0": ("LR(0)",),
    "slr": ("SLR",),
    "lr1": ("LR(1)",),
}

######################################################################
# command line options

getopt = OptionParser("usage: %prog [options] grammar")
getopt.remove_option("-h")
getopt.add_option("-h", "--help", action="store_true", dest="help_flag",
                  help="show this message")
getopt.add_option("-t", "--type", action="store", type="string",
                  dest="type", default="lr1",
                  help="choose parse type (%s)"%", ".join(parser_types.keys()),
                  metavar="T")
getopt.add_option("-V","--version",action="store_true",dest="version_flag",
                  help="show version information")
(options,args)=getopt.parse_args()

if options.help_flag:
    getopt.print_help()
    print ""
    print "Please report bugs to <voss@seehuhn.de>."
    raise SystemExit(0)
if options.version_flag:
    print """wisent %s
Copyright (C) 2007 Jochen Voss <voss@seehuhn.de>
Wisent comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by law.  You may redistribute copies of Jvterm under
the terms of the GNU General Public License.  For more
information about these matters, see the file named COPYING."""%wisent_version
    raise SystemExit(0)

if len(args) < 1:
    getopt.error("no grammar file specified")
if len(args) > 1:
    getopt.error("too many command line arguments")
fname = args[0]

if options.type not in parser_types:
    getopt.error("invalid parser type %s"%options.type)
parser_name, = parser_types[options.type]

######################################################################
# collect/prepare global parameters

aux = set()

params = {
    'date': strftime("%Y-%m-%d %H:%M:%S"),
    'version': wisent_version,
    'fname': fname,
    'type': parser_name,
    'transparent_tokens': aux,
}

######################################################################
# read the grammar file

errors_only = False

def rules(tree):
    for rule in tree[2:]:
        target = rule[2][1:3]
        for l in rule[4:-1]:
            if l[1] != "list":
                continue
            yield tuple([target]+[x[1:3] for x in l[2:]])

def read_rules(p, fname, aux):
    """Read and parse the input file.

    This generator yields the grammar rules one by one.  The special
    "*" and "+" suffix tokens are expanded here.  All transparent
    symbols are added to aux.
    """
    fd = open(fname)
    res = p.parse_tree(tokens(fd))
    fd.close()

    for l in rules(res):
        if l[0][0] == 'token' and l[0][1].startswith("_"):
            aux.add(l[0][1])
        todo = []
        ll = []
        special = ""
        for token in reversed(l):
            if special == "+":
                seq = token[1]+"+"
                if seq not in aux:
                    todo.append((seq, token[1]))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                special = False
            elif special == "*":
                seq = token[1]+"*"
                if seq not in aux:
                    todo.append((seq,))
                    todo.append((seq, seq, token[1]))
                    aux.add(seq)
                ll.append(seq)
                special = False
            elif token[0] == '*':
                special = "*"
            elif token[0] == '+':
                special = "+"
            else:
                ll.append(token[1])
        yield tuple(reversed(ll))
        while todo:
            yield todo.pop(0)

p = Parser()
try:
    g = LR1(read_rules(p, fname, aux))
except SyntaxError, e:
    print >>stderr, "%s:%d:%d: %s"%(e.filename, e.lineno, e.offset, e.msg)
    raise SystemExit(1)
except p.ParseErrors, e:
    for token,expected in e.errors:
        if token[0] == p.EOF:
            print >>stderr, "%s: unexpected end of file"%fname
            continue

        def quote(x):
            s = str(x)
            if not s.isalpha():
                s = "'"+s+"'"
            return s
        tp = quote(token[0])
        val = quote(token[1])
        if val and tp != val:
            found = "%s %s"%(tp, repr(token[1]))
        else:
            found = tp

        if p.EOF in expected:
            expected.remove(p.EOF)
            expect_eol = True
        else:
            expect_eol = False
        if len(expected) == 1:
            missing = quote(expected[0])
            tmpl = "%s:%d:%d: missing %s (found %s)"
            print >>stderr, tmpl%(fname, token[2], token[3], missing, found)
            continue

        msg1 = "parse error before %s"%found
        l = sorted([ quote(s) for s in expected ])
        if expect_eol:
            l.append("end of line")
        msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
        tmpl = "%s:%d:%d: %s, %s"
        print >>stderr, tmpl%(fname, token[2], token[3], msg1, msg2)
    res = e.tree
    if res is None:
        raise SystemExit(1)
    else:
        errors_only = True

######################################################################
# emit the parser

if errors_only:
    raise SystemExit(1)

fd = stdout

fd.write("#! /usr/bin/env python\n"%params)
fd.write("# %(type)s parser, autogenerated on %(date)s\n"%params)
fd.write("# generator: wisent %(version)s, http://seehuhn.de/pages/wisent\n"%params)
fd.write("# source: %(fname)s\n"%params)
g.write_parser(fd, params)
