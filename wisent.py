#! /usr/bin/env python
# wisent - a Python parser generator
#
# Copyright (C) 2008  Jochen Voss <voss@seehuhn.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys
# FIX PATH

from optparse import OptionParser

from grammar import GrammarError
from scanner import tokens
from parser import Parser
from text import write_block
from version import VERSION


parser_types = {
    "lr0": ("LR(0)", "lr0", "LR0"),
    "lr1": ("LR(1)", "lr1", "LR1"),
#     "ll1": ("LL(1)",),
#     "slr": ("SLR",),
#     "lalr1": ("SLR",),
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
getopt.add_option("-d", "--debug", action="store", type="string",
                  dest="debug", default="",
                  help="enable debugging (p=parser)",
                  metavar="CHARS")
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
Copyright (C) 2008 Jochen Voss <voss@seehuhn.de>
Wisent comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by law.  You may redistribute copies of Wisent under
the terms of the GNU General Public License.  For more
information about these matters, see the file named COPYING."""%VERSION
    raise SystemExit(0)

if len(args) < 1:
    getopt.error("no grammar file specified")
if len(args) > 1:
    getopt.error("too many command line arguments")
fname = args[0]

if options.type not in parser_types:
    getopt.error("invalid parser type %s"%options.type)
parser_name,grammar_module,grammar_class = parser_types[options.type]

Gmodule = __import__(grammar_module)
G = getattr(Gmodule, grammar_class)

params = {
    'fname': fname,
}
if "p" in options.debug:
    params["parser_comment"] = True
    params["parser_debugprint"] = True

######################################################################
# error messages

def error(msg, lineno=None, offset=None, fname=fname):
    parts = []
    parts.append("%s:"%fname)
    if lineno is not None:
        parts.append("%d:"%lineno)
        if offset is not None:
            parts.append("%d:"%offset)
    parts.append(" "+str(msg))
    print >>sys.stderr, "".join(parts)

######################################################################
# read the grammar file

errors_only = False

p = Parser()
try:
    fd = open(fname)
    tree = p.parse_tree(tokens(fd))
    fd.close()
except SyntaxError, e:
    error(e.msg, e.lineno, e.offset, e.filename)
    raise SystemExit(1)
except p.ParseErrors, e:
    for token,expected in e.errors:
        if token[0] == p.EOF:
            error("unexpected end of file")
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
            error("missing %s (found %s)"%(missing, found),
                  token[2], token[3], fname)
            continue

        msg1 = "parse error before %s"%found
        l = sorted([ quote(s) for s in expected ])
        if expect_eol:
            l.append("end of line")
        msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
        error(msg1+", "+msg2, token[2], token[3], fname)
    tree = e.tree
    if tree is None:
        raise SystemExit(1)
    else:
        errors_only = True
del p

######################################################################
# extract the rules from the parse tree

def rules(tree, aux):
    """Extract the grammar rules from the parse tree.

    This generator yields the grammar rules one by one.  The special
    "*" and "+" suffix tokens are expanded here.  All transparent
    symbols are added to aux.
    """
    for rule in tree[1:]:
        # rule[0] == 'rule'
        head = rule[1]
        if not head:
            # repaired trees have no payload
            head = ('', )+rule[2][2:]
        if head[0] == "token" and head[1].startswith("_"):
            aux.add(head[1])
        # rule[2] == (':', ...)
        for r in rule[3:]:
            if r[0] == "list":
                tail = list(r[1:])
                for i,x in enumerate(tail):
                    if not x:
                        # repaired trees have no payload
                        tail[i] = ('', )+rule[2][2:]
            else:
                # at a '|' or ';'
                res = [ head ]+tail+[ (';',';')+r[2:] ]
                todo = []
                for i in range(len(res)-2, 1, -1):
                    y = res[i]
                    if y[0] in [ '+', '*' ]:
                        x = res[i-1]
                        new = x[1]+y[0]
                        if new not in aux:
                            aux.add(new)
                            todo.append((new,)+x[1:])
                        res[i-1:i+1] = [ ('token',new)+x[2:] ]
                yield [ x[1:] for x in res ]
                for x in todo:
                    h = x[0]
                    a = (h,)+x[2:]
                    b = x[1:]
                    c = (';',)+x[2:]
                    if h[-1] == '+':
                        yield [ a, b, c ]
                        yield [ a, a, b, c ]
                    elif h[-1] == '*':
                        yield [ a, c ]
                        yield [ a, a, b, c ]

def locate(rr, rule_locations):
    for k,r in enumerate(rr):
        rule_locations[k] = tuple(x[1:] for x in r)
        yield tuple(x[0] for x in r[:-1])

aux = set()
rule_locations = {}
rr = locate(rules(tree, aux), rule_locations)

######################################################################
# construct the grammar from the rules

try:
    g = G(rr)
except GrammarError, e:
    error(e)
    raise SystemExit(1)

try:
    g.check()
except g.Errors, e:
    for res, text in e:
        shift = []
        red = []
        for m in res:
            if m[0] == 'S':
                shift.append(m[1:])
            else:
                red.append(m[1])

        ee = []
        def rule_error(k, n):
            r = [ repr(X) for X in g.rules[k] ]
            if n < len(r):
                tail = " ".join(r[1:n])+"."+" ".join(r[n:])
            else:
                tail = " ".join(r[1:])
            ee.append("    "+r[0]+": "+tail+";")
            loc = rule_locations[k][n]
            while ee:
                msg = ee.pop(0)
                error(msg, loc[0], loc[1])

        if len(red)>1:
            conflict = "reduce-reduce"
        else:
            conflict = "shift-reduce"
        ee.append("%s conflict: the input"%conflict)
        ee.append("    "+" ".join(text[:-1])+"."+text[-1]+" ...")

        if shift:
            msg = "  can be shifted using "
            if len(shift)>1:
                msg += "one of the production rules"
            else:
                msg += "the production rule"
            ee.append(msg)
            for k, n in shift:
                rule_error(k, n)
            cont = "or "
        else:
            cont = ""

        for k in red:
            rule = g.rules[k]
            n = len(rule)
            ee.append("  %scan be reduced to"%cont)
            repl = "".join(x+" " for x in text[:-n])+repr(rule[0])+"."+text[-1]
            ee.append("    "+repl+" ...")
            ee.append("  using the production rule")
            rule_error(k, n)
            cont = "or "

    error("%d conflicts, aborting ..."%len(e))
    errors_only = True

if errors_only:
    raise SystemExit(1)

######################################################################
# emit the parser

fd = sys.stdout

params['transparent_tokens'] = aux
g.write_parser(fd, params)
