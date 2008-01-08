
TARGET=rainbowforth
OBJECTS=main.o editor.o compiler.o console.o

$(TARGET): $(OBJECTS)
	gcc $(OBJECTS) -o $(TARGET) -lcurses

%.o: %.c
	gcc -g -Wall -Werror -c $<

clean:
	rm -f $(TARGET) $(OBJECTS)


