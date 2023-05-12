# make inkscape_sliceforms-installable-r0.3.zip
%.zip:
	prefix=$$(echo $@ | sed 's/\.zip//;s/-installable//'); mkdir -p $$prefix/common; cp LICENSE README.md *.py *.inx $$prefix; cp common/LICENSE common/README.md common/*.py $$prefix/common; zip -r $@ $$prefix
