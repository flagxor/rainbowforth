# Makefile for rainbowforth

TARGET=rainbowforth
OBJECTS=main.o editor.o compiler.o console.o
CFLAGS=-g -Wall -Werror $(PLATFORM_CFLAGS)

$(TARGET): $(OBJECTS)
	gcc $(OBJECTS) -o $(TARGET) $(LIBS)

%.o: %.c
	gcc $(CFLAGS) -c $<

clean:
	rm -f $(TARGET) $(OBJECTS)


# handle platform specific
ifeq ($(shell uname -o),Cygwin)
  PLATFORM_CFLAGS=-D_WIN32 -mwindows
  LIBS=-mwindows
else 
  LIBS=-lcurses
endif


