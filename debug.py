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

def print_lr0_states(g, T):
    keys = sorted(T.keys())
    for i in keys:
        print "state %s:"%i
        for k,l,n in T[i]:
            r = g.rules[k]
            rr = map(repr, r)
            print "  "+rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])
        print

def print_lr1_states(g, T):
    keys = sorted(T.keys())
    for i in keys:
        print "state %s:"%i
        for k,l,n,next in T[i]:
            r = g.rules[k]
            rr = map(repr, r)
            print "  "+rr[0]+" -> "+" ".join(rr[1:n])+"."+" ".join(rr[n:l])+"|"+repr(next)
        print
