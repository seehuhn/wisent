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

from time import strftime
from optparse import OptionParser
from inspect import getcomments

from grammar import GrammarError
from lr1 import LR1
from scanner import tokens
from parser import Parser
from text import write_block
import template
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
    'date': strftime("%Y-%m-%d %H:%M:%S"),
    'version': VERSION,
    'fname': fname,
    'type': parser_name,
}
if "p" in options.debug:
    params["parser_comment"] = True
    params["parser_debugprint"] = True

######################################################################
# read the grammar file

errors_only = False

p = Parser()
try:
    fd = open(fname)
    tree = p.parse_tree(tokens(fd))
    fd.close()
except SyntaxError, e:
    print >>sys.stderr, "%s:%d:%d: %s"%(e.filename, e.lineno, e.offset, e.msg)
    raise SystemExit(1)
except p.ParseErrors, e:
    for token,expected in e.errors:
        if token[0] == p.EOF:
            print >>sys.stderr, "%s: unexpected end of file"%fname
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
            print >>sys.stderr, tmpl%(fname, token[2], token[3], missing, found)
            continue

        msg1 = "parse error before %s"%found
        l = sorted([ quote(s) for s in expected ])
        if expect_eol:
            l.append("end of line")
        msg2 = "expected "+", ".join(l[:-1])+" or "+l[-1]
        tmpl = "%s:%d:%d: %s, %s"
        print >>sys.stderr, tmpl%(fname, token[2], token[3], msg1, msg2)
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
        for rule in tree[2:]:
            target = rule[2][1:3]
            for l in rule[4:-1]:
                if l[1] != "list":
                    continue
                yield tuple([target]+[x[1:3] for x in l[2:]])

    for l in extract(tree):
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

aux = set()
try:
    g = LR1(rules(tree, aux))
except GrammarError, e:
    print >>sys.stderr, "%s: %s"%(fname, e)
    raise SystemExit(1)

if errors_only:
    raise SystemExit(1)

params['transparent_tokens'] = aux

######################################################################
# emit the parser

fd = sys.stdout

fd.write("#! /usr/bin/env python\n"%params)
fd.write("# %(type)s parser, autogenerated on %(date)s\n"%params)
fd.write("# generator: wisent %(version)s, http://seehuhn.de/pages/wisent\n"%params)
fd.write("# source: %(fname)s\n"%params)
fd.write("""
# All parts of this file which are not taken verbatim from the input grammar
# are covered by the following notice:
#
""")
fd.write(getcomments(template))

g.write_parser(fd, params)
