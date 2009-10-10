# helpers.py - Wisent helper functions
#
# Copyright (C) 2009  Jochen Voss <voss@seehuhn.de>
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

import os

def open_executable(fname, mode='r', bufsize=-1):
    """Open a file with the executable bit set.

    The arguments have the same meaning as for the builtin `open` function.
    """
    flags = os.O_CREAT
    if "r" in mode and "w" in mode:
        flags |= os.O_RDWR
    elif "w" in mode:
        flags |= os.O_WRONLY
    elif "r" in mode:
        flags |= os.O_RDONLY
    if "a" in mode:
        flags |= os.O_APPEND
    else:
        flags |= os.O_TRUNC
    fd = os.open(fname, flags, 0777)
    return os.fdopen(fd, mode, bufsize)
