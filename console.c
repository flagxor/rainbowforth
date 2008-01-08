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

#ifdef _WIN32

#include <windows.h>
#include <stdio.h>
#include <assert.h>

// globals for console
static HANDLE console_sbuf;
static HANDLE console_ibuf;

void console_startup(void) {
  // give use a console
  AllocConsole();
  // get the screen buffer handle
  console_sbuf=CreateConsoleScreenBuffer(GENERIC_READ | GENERIC_WRITE, 0, 
                                         NULL, CONSOLE_TEXTMODE_BUFFER, NULL);
  // make it active
  SetConsoleActiveScreenBuffer(console_sbuf);
  // get input
  console_ibuf=GetStdHandle(STD_INPUT_HANDLE);
  // allow Ctrl-C
  SetConsoleMode(console_ibuf, 0);
}

void console_shutdown(void) {
  // close down screen
  CloseHandle(console_sbuf);
  // close down input
  CloseHandle(console_ibuf);
}

void console_refresh(void) {
  // windows doesn't have this
}

void console_move(int x, int y) {
  COORD coord;
 
  coord.X=x;
  coord.Y=y;
  SetConsoleCursorPosition(console_sbuf, coord);
}

void console_style(int attrib) {
  DWORD t;
  DWORD r, g, b;

  // do reverse for underline on windows
  if(attrib&CONSOLE_UNDERLINE) {
    attrib^=CONSOLE_UNDERLINE;
    t=BACKGROUND_INTENSITY;
    r=BACKGROUND_RED;
    g=BACKGROUND_GREEN;
    b=BACKGROUND_BLUE;
  } else {
    t=FOREGROUND_INTENSITY;
    r=FOREGROUND_RED;
    g=FOREGROUND_GREEN;
    b=FOREGROUND_BLUE;
  }

  // pick color
  switch(attrib) {
    case CONSOLE_WHITE:   t=t| r|g|b; break;
    case CONSOLE_RED:     t=t| r    ; break;
    case CONSOLE_YELLOW:  t=t| r|g  ; break;
    case CONSOLE_GREEN:   t=t|   g  ; break;
    case CONSOLE_CYAN:    t=t|   g|b; break;
    case CONSOLE_BLUE:    t=t|     b; break;
    case CONSOLE_MAGENTA: t=t| r|  b; break;
    default: break;
  }
  
  // set it
  SetConsoleTextAttribute(console_sbuf, t);
}

void console_write(const char *str) {
  DWORD junk;

  WriteConsole(console_sbuf, str, strlen(str), &junk, NULL);
}

void console_write_char(int ch) {
  char str[2];
  str[0]=(char)ch; str[1]=0;
  console_write(str);
}

int console_read(void) {
  INPUT_RECORD inp;
  DWORD count;
  WORD ascii, k;

next:
  // get one character
  while(!ReadConsoleInput(console_ibuf, &inp, 1, &count) ||
        count!=1 ||
        inp.EventType!=KEY_EVENT ||
        !inp.Event.KeyEvent.bKeyDown);

  // get codes
  ascii=inp.Event.KeyEvent.uChar.AsciiChar;
  k=inp.Event.KeyEvent.wVirtualKeyCode;

  // handle others
  switch(k) {
    case VK_ESCAPE: return CONSOLE_KEY_ESCAPE;
    case VK_UP: return CONSOLE_KEY_UP;
    case VK_DOWN: return CONSOLE_KEY_DOWN;
    case VK_LEFT: return CONSOLE_KEY_LEFT;
    case VK_RIGHT: return CONSOLE_KEY_RIGHT;
    case VK_PRIOR: return CONSOLE_KEY_PGUP;
    case VK_NEXT: return CONSOLE_KEY_PGDN;
    case VK_HOME: return CONSOLE_KEY_HOME;
    case VK_END: return CONSOLE_KEY_END;
    case VK_INSERT: return CONSOLE_KEY_INS;
    case VK_DELETE: return CONSOLE_KEY_DEL;
    case VK_BACK: return CONSOLE_KEY_BACKSPACE;
    case VK_RETURN: return CONSOLE_KEY_ENTER;
    case VK_TAB: return CONSOLE_KEY_TAB;
    default:
      // handle function keys
      if(k>=VK_F1 && k<=VK_F12) return k-VK_F1+CONSOLE_KEY_F(1);
      // check for remaining ascii
      if(ascii>0 && ascii<127) return ascii;
      break;
  }
  
  // get another
  goto next;
}

// special characters
#define CONSOLE_VLINE '\xb3'
#define CONSOLE_HLINE '\xc4'
#define CONSOLE_ULCORNER '\xda'
#define CONSOLE_URCORNER '\xbf'
#define CONSOLE_LLCORNER '\xc0'
#define CONSOLE_LRCORNER '\xd9'


#else


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

void console_write_char(int ch) {
  addch(ch);
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

// special characters
#define CONSOLE_VLINE ACS_VLINE
#define CONSOLE_HLINE ACS_HLINE
#define CONSOLE_ULCORNER ACS_ULCORNER
#define CONSOLE_URCORNER ACS_URCORNER
#define CONSOLE_LLCORNER ACS_LLCORNER
#define CONSOLE_LRCORNER ACS_LRCORNER

#endif

void console_box(int x, int y, int w, int h) {
  int i;

  // move to top left
  console_move(x, y);
  // draw top row
  console_write_char(CONSOLE_ULCORNER);
  for(i=0;i<w-2;i++) console_write_char(CONSOLE_HLINE);
  console_write_char(CONSOLE_URCORNER);
  // draw left and right sides
  for(i=0;i<h-2;i++) {
    // left side
    console_move(x, y+i+1);
    console_write_char(CONSOLE_VLINE);
    // right side
    console_move(x+w-1, y+i+1);
    console_write_char(CONSOLE_VLINE);
  }
  // move to bottom left
  console_move(x, y+h-1);
  // draw bottom row
  console_write_char(CONSOLE_LLCORNER);
  for(i=0;i<w-2;i++) console_write_char(CONSOLE_HLINE);
  console_write_char(CONSOLE_LRCORNER);
}


