#! /usr/bin/env python
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

from grammar import Grammar

def emit_class_parseerror():
    print "class ParseError(Exception):"
    print
    print "    def __init__(self, msg, data=None):"
    print "        self.msg = msg"
    print "        self.data = data"
    print
    print "    def __str__(self):"
    print "        if self.data is not None:"
    print "            return 'parse error: %s, %s'%(self.msg,self.data)"
    print "        else:"
    print "            return 'parse error: %s'%self.msg"

def emit_rules(g):
    keys = sorted(g.rules.keys())
    print "    rules = {"
    for k in keys:
        print "        %s: %s,"%(repr(k), repr(g.rules[k]))
    print "    }"

