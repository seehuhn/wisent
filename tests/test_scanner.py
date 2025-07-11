#! /usr/bin/env python3
# check2.py - check the scanner used in Wisent
#
# Copyright (C) 2010  Jochen Voss <voss@seehuhn.de>
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

from wisent_pkg.scanner import tokens

in1 = ""
out1 = [ ]

in2 = r"""
# c1
a: bc; # c2
"""
out2 = [
  ('token', 'a', 3, 1),
  (':', ':', 3, 2),
  ('token', 'bc', 3, 4),
  (';', ';', 3, 6)
]

in3 = r"""
"this is a
string"
"this is a \"string\""
"'"
'"'
"""
out3 = [
  ('string', 'this is a\nstring', 2, 1),
  ('string', 'this is a "string"', 4, 1),
  ('string', "'", 5, 1),
  ('string', '"', 6, 1)
]

names = sorted(name for name in dir() if name.startswith("in"))
for name in names:
    label = name[2:]
    text = eval(name)
    result = eval("out"+label)

    tt = list(tokens(text.splitlines()))
    if tt == result:
        print("test %s: OK"%label)
    else:
        print("test %s: FAIL"%label)
        for t in tt:
            print(t)
