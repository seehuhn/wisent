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
from lr1 import LR1
from scanner import tokens
from parser import Parser
from text import write_block
from version import VERSION


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
parser_name, = parser_types[options.type]

params = {
    'fname': fname,
    'type': parser_name,
}
if "p" in options.debug:
    params["parser_comment"] = True
    params["parser_debugprint"] = True

######################################################################
# error messages

def error(msg, fname=fname, lineno=None, offset=None):
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
    error(e.msg, e.filename, e.lineno, e.offset)
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
                  fname, token[2], token[3])
            continue

        msg1 = "parse error before %s"%found
        l = sorted([ quote(s) for s in expected ])
        if expect_eol:
            l.append("end of line")
        msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
        error(msg1+", "+msg2, fname, token[2], token[3])
    tree = e.tree
    if tree is None:
        raise SystemExit(1)
    else:
        errors_only = True
del p

def rules(tree, aux):
    """Extract the grammar rules from the parse tree.

    This generator yields the grammar rules one by one.  The special
    "*" and "+" suffix tokens are expanded here.  All transparent
    symbols are added to aux.
    """

    def extract(tree):
        for rule in tree[1:]:
            target = rule[1][0:2]
            for l in rule[3:-1]:
                if l[0] != "list":
                    continue
                yield tuple([target]+[x[0:2] for x in l[1:]])

    for l in extract(tree):
        if l[0][0] == 'token' and len(l[0])>1 and l[0][1].startswith("_"):
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

aux = set()
try:
    g = LR1(rules(tree, aux))
except GrammarError, e:
    error(e)
    raise SystemExit(1)

try:
    g.check()
except g.LR1Errors, e:
    errors_only = True
    for res, text in e:
        ee = []

        shift = []
        red = []
        conflict = "reduce-reduce"
        for m in res:
            if m[0] == 'S':
                conflict = "shift-reduce"
                shift.append(m[1:])
            else:
                red.append(m[1])

        # TODO: add a way to ignore/resolve shift-reduce conflicts

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
                r = [ repr(X) for X in g.rules[k] ]
                tail = " ".join(r[1:n])+"."+" ".join(r[n:])
                ee.append("    "+r[0]+": "+tail)
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
            tail = " ".join(repr(X) for X in rule[1:])
            ee.append("    "+repr(rule[0])+": "+tail+";")
            cont = "or "

        for e in ee:
            error(e)

if errors_only:
    raise SystemExit(1)

######################################################################
# emit the parser

fd = sys.stdout

params['transparent_tokens'] = aux
g.write_parser(fd, params)
