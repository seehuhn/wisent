## Process this file with automake to produce Makefile.in
# Copyright 2009  Jochen Voss

EXTRA_DIST = conf.py ch1intro.txt ch2tutorial.txt ch3wisent.txt		\
        ch4parser.txt ch5references.txt index.txt wisent1500.jpg html

CACHEDIR = .cache

clean-local:
	-rm -rf $(CACHEDIR) latex

distclean-local:
	-rm -rf $(CACHEDIR) $(CACHEDIR)

######################################################################

.PHONY: gen-html gen-latex

gen-html:
	mkdir -p html $(CACHEDIR)
	sphinx-build -b html -d $(CACHEDIR) . html
	@echo
	@echo "Build finished; the HTML files are in html/ ."

gen-latex:
	mkdir -p latex $(CACHEDIR)
	sphinx-build -b latex -d $(CACHEDIR) . latex
	@echo
	@echo "Build finished; the LaTeX files are in latex/ ."
	@echo "Now run \`make all-pdf' or \`make all-ps' in that directory."
