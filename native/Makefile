# Makefile for rainbowforth

TARGET=rainbowforth$(EXE)
OBJECTS=main.o editor.o compiler.o console.o library.o
CFLAGS=-g -m32 -Wall -Werror $(PLATFORM_CFLAGS)

$(TARGET): $(OBJECTS)
	gcc $(CFLAGS) $(OBJECTS) -o $(TARGET) $(LIBS)

%.o: %.c
	gcc $(CFLAGS) -c $<

clean:
	rm -f $(TARGET) $(OBJECTS)

website:
	./block_view <rainbowforth_data >web/blocks.html


# handle platform specific
ifeq ($OSTYPE,Cygwin)
  PLATFORM_CFLAGS=-D_WIN32 -mno-cygwin
  LIBS=-mno-cygwin
  EXE=.exe
else
  LIBS=-lncurses
  EXE=
endif
