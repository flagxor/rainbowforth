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

#include "console.h"
#include <curses.h>

void console_startup(void) {
  // setup curses
  initscr();
  start_color();
  raw();
  noecho();
  nonl();
  intrflush(stdscr, FALSE);
  keypad(stdscr, TRUE);
  // setup colors
  init_pair(CONSOLE_WHITE, COLOR_WHITE, COLOR_BLACK);
  init_pair(CONSOLE_RED, COLOR_RED, COLOR_BLACK);
  init_pair(CONSOLE_YELLOW, COLOR_YELLOW, COLOR_BLACK);
  init_pair(CONSOLE_GREEN, COLOR_GREEN, COLOR_BLACK);
  init_pair(CONSOLE_CYAN, COLOR_CYAN, COLOR_BLACK);
  init_pair(CONSOLE_BLUE, COLOR_BLUE, COLOR_BLACK);
  init_pair(CONSOLE_MAGENTA, COLOR_MAGENTA, COLOR_BLACK);
  // set default to white
  console_style(CONSOLE_WHITE);
}

void console_shutdown(void) {
  endwin();
}

void console_refresh(void) {
  refresh();
}

void console_move(int x, int y) {
  move(y, x);
}

void console_style(int attrib) {
  if(attrib & CONSOLE_UNDERLINE) {
    attrib^=CONSOLE_UNDERLINE;
    attrset(COLOR_PAIR(attrib) | A_BOLD | A_UNDERLINE);
  } else {
    attrset(COLOR_PAIR(attrib) | A_BOLD);
  }
}

void console_write(const char *str) {
  addstr(str);
}

void console_write_char(char ch) {
  addch(ch);
}

void console_box(int x, int y, int w, int h) {
  int i;

  // move to top left
  move(y, x);
  // draw top row
  addch(ACS_ULCORNER);
  for(i=0;i<w-2;i++) addch(ACS_HLINE);
  addch(ACS_URCORNER);
  // draw left and right sides
  for(i=0;i<h-2;i++) {
    // left side
    move(y+i+1, x);
    addch(ACS_VLINE);
    // right side
    move(y+i+1, x+w-1);
    addch(ACS_VLINE);
  }
  // move to bottom left
  move(y+h-1, x);
  // draw bottom row
  addch(ACS_LLCORNER);
  for(i=0;i<w-2;i++) addch(ACS_HLINE);
  addch(ACS_LRCORNER);
}

int console_read(void) {
  int ch;

  for(;;) {
    ch=getch();
    switch(ch) {
      // handle special keys
      case KEY_UP: return CONSOLE_KEY_UP;
      case KEY_DOWN: return CONSOLE_KEY_DOWN;
      case KEY_LEFT: return CONSOLE_KEY_LEFT;
      case KEY_RIGHT: return CONSOLE_KEY_RIGHT;
      case KEY_PPAGE: return CONSOLE_KEY_PGUP;
      case KEY_NPAGE: return CONSOLE_KEY_PGDN;
      case KEY_HOME: return CONSOLE_KEY_HOME;
      case KEY_END: return CONSOLE_KEY_END;
      case KEY_IC: return CONSOLE_KEY_INS;
      case KEY_DC: return CONSOLE_KEY_DEL;
      case KEY_BACKSPACE: return CONSOLE_KEY_BACKSPACE;
      case CONSOLE_KEY_CTRL('M'):
      case KEY_ENTER: 
        return CONSOLE_KEY_ENTER;
      default:
        // handle F1-F12 (assumes KEY_F(n) goes up by 1)
	if(ch>=KEY_F(1) && ch<=KEY_F(12)) return ch-KEY_F(1)+CONSOLE_KEY_F(1);
	// handle normal keys (including CTRL keys)
	if(ch>=1 && ch<127) return ch;
	break;
    }
  }
}



