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

from os.path import basename
from optparse import OptionParser

from grammar import read_grammar
from lr1 import Automaton
from version import VERSION

######################################################################
# command line options

getopt = OptionParser("usage: %prog [options] grammar")
getopt.remove_option("-h")
getopt.add_option("-d", "--debug", action="store", type="string",
                  dest="debug", default="",
                  help="enable debugging (p=parser)",
                  metavar="CHARS")
getopt.add_option("-e", "--example", action="store", dest="example_fname",
                  help="store example source code into NAME",
                  metavar="NAME")
getopt.add_option("-h", "--help", action="store_true", dest="help_flag",
                  help="show this message")
getopt.add_option("-o", "--output", action="store", dest="output_fname",
                  help="set the output file name (default is stdout)",
                  metavar="NAME")
getopt.add_option("-r", "--replace", action="store_true", dest="replace_flag",
                  help="replace nonterminals by numbers")
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

######################################################################
# collect file names and other info

params = {}

progname = basename(sys.argv[0])

if len(args) < 1:
    f_in = None
elif len(args) > 1:
    getopt.error("too many command line arguments")
else:
    f_in = args[0]

f_out = options.output_fname
f_ex = options.example_fname

if "p" in options.debug:
    params["parser_comment"] = True
    params["parser_debugprint"] = True
params["replace_nonterminals"] = options.replace_flag

######################################################################
# read the grammar

def check(g, params):
    a = Automaton(g, params)
    a.check()
    return a

if f_in is None:
    a = read_grammar(sys.stdin, params, check)
else:
    params.setdefault("fname", f_in)
    try:
        fd = open(f_in, "r")
        a = read_grammar(fd, params, check)
        fd.close()
    except IOError, e:
        msg = '%s: error while reading "%s": %s'%(f_in, f_in, e.strerror)
        print >>sys.stderr, msg
        raise SystemExit(1)

######################################################################
# emit the parser

if f_out is None:
    a.write_parser(sys.stdout, params)
else:
    params.setdefault("parser_name", f_out)
    try:
        fd = open(f_out, "w")
        a.write_parser(fd, params)
        fd.close()
    except IOError, e:
        msg = '%s: error while writing "%s": %s'%(progname, f_out, e.strerror)
        print >>sys.stderr, msg
        raise SystemExit(1)

######################################################################
# emit the example source code

if f_ex is not None:
    params.setdefault("example_name", f_ex)
    try:
        fd = open(f_ex, "w")
        a.g.write_example(fd, params)
        fd.close()
    except IOError, e:
        msg = '%s: error while writing "%s": %s'%(progname, f_ex, e.strerror)
        print >>sys.stderr, msg
        raise SystemExit(1)
