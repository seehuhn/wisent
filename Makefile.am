## Process this file with automake to produce Makefile.in
# Copyright 2008  Jochen Voss

SUBDIRS = doc examples

EXTRA_DIST = wisent.py check.py
BUILT_SOURCES = version.py

bin_SCRIPTS = wisent
pkgpython_PYTHON = grammar.py lr1.py scanner.py parser.py text.py	\
	template.py version.py

TESTS = check.py

version.py: configure.ac Makefile.am
	cd $(srcdir) && \
	echo "#! /usr/bin/env python" >$@ && \
	echo "PACKAGE=\"@PACKAGE@\"" >>$@ && \
	echo "VERSION=\"@VERSION@\"" >>$@

wisent: wisent.py Makefile.am
	sed -e "2 i# WARNING: automatically generated from $<, do not edit" \
	  -e "2 i#" \
	  -e "s;^# FIX PATH$$;sys.path = ['@pkgpythondir@'] + sys.path;" \
	  $< >$@
	chmod +x wisent

CLEANFILES = wisent
