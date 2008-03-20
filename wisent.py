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

from grammar import read_grammar, Conflicts
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
getopt.add_option("-h", "--help", action="store_true", dest="help_flag",
                  help="show this message")
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

if len(args) < 1:
    getopt.error("no grammar file specified")
if len(args) > 1:
    getopt.error("too many command line arguments")
fname = args[0]

params = {}
if "p" in options.debug:
    params["parser_comment"] = True
    params["parser_debugprint"] = True
params["replace_nonterminals"] = options.replace_flag

######################################################################
# emit the parser

def check(g, params):
    a = Automaton(g, params)
    a.check()
    return a
a = read_grammar(fname, params, check)
a.write_parser(sys.stdout, params)
