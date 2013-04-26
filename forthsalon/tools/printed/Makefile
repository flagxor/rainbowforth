VPATH=src
OBJECTS:=$(patsubst src/%.ps,out/%.pdf,$(wildcard src/*.ps))

.PHONY: all
all: $(OBJECTS)

out:
	mkdir -p out

out/%.pdf: src/%.ps | out
	ps2pdf $< $@ || (rm $@ && false)

.PHONY: test
test:
	echo $(OBJECTS)

.PHONY: clean
clean:
	rm -rf out
