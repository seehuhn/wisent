CACHEDIR = .cache

.PHONY: html latex clean

html:
	mkdir -p html $(CACHEDIR)
	sphinx-build -b html -d $(CACHEDIR) . html
	@echo
	@echo "Build finished; the HTML files are in html/ ."

latex:
	mkdir -p latex $(CACHEDIR)
	sphinx-build -b latex -d $(CACHEDIR) . latex
	@echo
	@echo "Build finished; the LaTeX files are in latex/ ."
	@echo "Now run \`make all-pdf' or \`make all-ps' in that directory."

clean:
	-rm -rf $(CACHEDIR) html latex
