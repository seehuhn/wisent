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
    seplen = len(sep)
    argslen = sum(len(a) for a in args)
    while args:
        if len(line)+argslen+len(args)*seplen <= maxwidth:
            line = sep.join([line]+args)
            break

        arg = args.pop(0)
        argslen -= len(arg)
        if len(line+sep+arg+end1) > maxwidth:
            yield line+end1
            line = padding+start2+arg
        else:
            line += sep+arg
    yield line

def write_block(fd, indent, str, params={}, first=False):
    """Write a multi-line string into a file.

    This function re-indents `str` to level `indent`, removes leading
    and trailing empty lines and white-space at the end of line,
    expands all tabs, and writes the result to `fd`.

    If `first` is False, a leading empty line is added.

    Blocks between lines of the form '#@ IF cond' and '#@ ENDIF' are
    removed if 'params[cond]' is not True.
    """
    lines = [l.rstrip().expandtabs() for l in str.splitlines()]
    while lines and not lines[0]:
        del lines[0]
    while lines and not lines[-1]:
        del lines[-1]
    if not lines:
        return

    if not first:
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
