/*

   Copyright 2008 Bradley Nelson

   This file is part of Rainbow Forth.

   Rainbow Forth is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Rainbow Forth is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Rainbow Forth.  If not, see <http://www.gnu.org/licenses/>.

*/

#ifndef _console_h
#define _console_h

// color codes
#define CONSOLE_WHITE 1
#define CONSOLE_RED 2
#define CONSOLE_YELLOW 3
#define CONSOLE_GREEN 4
#define CONSOLE_CYAN 5
#define CONSOLE_BLUE 6
#define CONSOLE_MAGENTA 7
// other attribs
#define CONSOLE_UNDERLINE 8

// keys
#define CONSOLE_KEY_ESCAPE 27
#define CONSOLE_KEY_TAB '\t'
#define CONSOLE_KEY_UP (-1)
#define CONSOLE_KEY_DOWN (-2)
#define CONSOLE_KEY_LEFT (-3)
#define CONSOLE_KEY_RIGHT (-4)
#define CONSOLE_KEY_PGUP (-5)
#define CONSOLE_KEY_PGDN (-6)
#define CONSOLE_KEY_HOME (-7)
#define CONSOLE_KEY_END (-8)
#define CONSOLE_KEY_INS (-9)
#define CONSOLE_KEY_DEL (-10)
#define CONSOLE_KEY_BACKSPACE (-11)
#define CONSOLE_KEY_ENTER (-12)
#define CONSOLE_KEY_F(x) (-100+(x))
#define CONSOLE_KEY_CTRL(x) ((x)-'A'+1)

// startup
extern void console_startup(void);
// shutdown
extern void console_shutdown(void);
// refresh display
extern void console_refresh(void);
// set position
extern void console_move(int x, int y);
// set attribs
extern void console_style(int attrib);
// write text
extern void console_write(const char *str);
// write single character
extern void console_write_char(char ch);
// draw a box
extern void console_box(int x, int y, int w, int h);
// read character
extern int console_read(void);

#endif


