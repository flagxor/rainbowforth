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

#include "editor.h"
#include "common.h"
#include "console.h"
#include "compiler.h"
#include <stdio.h>
#include <string.h>

// page size
#define WIDTH 64
#define HEIGHT (BLOCK_SIZE/WIDTH)
// page offset
#define OFFSET_X (80/2-WIDTH/2-1)
#define OFFSET_Y 2

// global context
static struct {
  int cursor_pos;
  unsigned char buffer[BLOCK_SIZE];
  unsigned char clipboard[BLOCK_SIZE];
  int clipboard_rows;
  int clipboard_in_action;
  const char *block_filename;
  FILE *file;
  int block;
  int changed;
  unsigned char space;
  int need_redraw;
} ctx;

// functions called out of sequence
static void run(void);
static void redraw(void);

static void cursor_adjust(void) {
  console_move(OFFSET_X+ctx.cursor_pos%WIDTH,
               OFFSET_Y+ctx.cursor_pos/WIDTH);
}

static void update_cursor(void) {
  // clip it
  if(ctx.cursor_pos<0) {
    ctx.cursor_pos=(ctx.cursor_pos+WIDTH*HEIGHT)%WIDTH;
  }
  if(ctx.cursor_pos>=BLOCK_SIZE) {
    ctx.cursor_pos=BLOCK_SIZE-WIDTH+(ctx.cursor_pos%WIDTH);
  }
}

static void update_status(void) {
  char str[100];

  // do redraw if needed
  if(ctx.need_redraw) redraw();
  // show status line on top
  console_style(CONSOLE_WHITE);
  console_move(OFFSET_X+1, 0);
  sprintf(str, "block=%d        column=%d row=%d               ", 
          ctx.block, ctx.cursor_pos%WIDTH, ctx.cursor_pos/WIDTH);
  console_write(str);
  // move to proper position
  cursor_adjust();
}

static void set_color(int i) {
  // find next color code
  for(;i<BLOCK_SIZE;i++) {
    switch(ctx.buffer[i]) {
      case SPACE_WHITE: console_style(CONSOLE_WHITE); return;
      case SPACE_RED: console_style(CONSOLE_RED); return;
      case SPACE_YELLOW: console_style(CONSOLE_YELLOW); return;
      case SPACE_GREEN: console_style(CONSOLE_GREEN); return;
      case SPACE_CYAN: console_style(CONSOLE_CYAN); return;
      case SPACE_BLUE: console_style(CONSOLE_BLUE); return;
      case SPACE_MAGENTA: console_style(CONSOLE_MAGENTA); return;
    }
  }
  // default to white
  console_style(CONSOLE_WHITE);
}

static int is_space(unsigned char ch) {
  if(ch==' ' || ch>SPACE_LAST) return 1;
  return 0;
}

static unsigned char filter_char(unsigned char ch) {
  if(is_space(ch)) return ' ';
  return ch;
}

static void redraw(void) {
  int i, j;

  // note it was done
  ctx.need_redraw=0;
  // redraw buffer
  for(i=0;i<HEIGHT;i++) {
    console_move(OFFSET_X, OFFSET_Y+i);
    for(j=0;j<WIDTH;j++) {
      set_color(j+i*WIDTH);
      console_write_char(filter_char(ctx.buffer[j+i*WIDTH]));
    }
  }
}

static void write_symbol(unsigned char ch) {
  // note change
  ctx.changed=1;
  // do a redraw when covering a space
  if(is_space(ctx.buffer[ctx.cursor_pos])) ctx.need_redraw=1;
  // set character
  ctx.buffer[ctx.cursor_pos]=ch;
  // move cursor to target
  cursor_adjust();
  // pick color
  set_color(ctx.cursor_pos);
  // change display
  console_write_char(filter_char(ch));
  // update position
  ctx.cursor_pos++;
  // adjust cursor
  update_cursor();
  // do a redraw when adding space
  if(is_space(ch)) ctx.need_redraw=1;
}

static void write_normal_symbol(int key) {
  int old;

  // write it as above
  write_symbol(key);
  // alter space if needed
  if(ctx.buffer[ctx.cursor_pos]!=ctx.space &&
     is_space(ctx.buffer[ctx.cursor_pos])) {
    // add in space
    old=ctx.cursor_pos;
    write_symbol(ctx.space);
    ctx.cursor_pos=old;
    // adjust cursor
    update_cursor();
  }
}

static void load(void) {
  // jump to block
  fseek(ctx.file, ctx.block*BLOCK_SIZE, SEEK_SET);
  // blank memory
  memset(ctx.buffer, ' ', BLOCK_SIZE);
  // try to load it
  fread(ctx.buffer, BLOCK_SIZE, 1, ctx.file);
}

static void save(void) {
  // skip if no changed
  if(!ctx.changed) return;
  // jump to block
  fseek(ctx.file, ctx.block*BLOCK_SIZE, SEEK_SET);
  // save it
  fwrite(ctx.buffer, BLOCK_SIZE, 1, ctx.file);
  // flush it
  fflush(ctx.file);
  // update flag
  ctx.changed=0;
}

static void change_block(int i) {
  // clip to zero
  if(i<0) i=0;
  // save current block if needed
  save(); 
  // set new block
  ctx.block=i;
  // load it
  load();
  // draw it
  ctx.need_redraw=1;
}

static void backspace(void) {
  int old_pos;
  int eol;

  // skip if at top
  if(ctx.cursor_pos==0) return;
  // save old position
  old_pos=ctx.cursor_pos;
  // find end of line
  eol=ctx.cursor_pos/WIDTH*WIDTH+WIDTH-1;
  // pull line back
  ctx.cursor_pos--;
  while(ctx.cursor_pos<eol) {
    write_symbol(ctx.buffer[ctx.cursor_pos+1]);
  }
  // put space at end
  ctx.cursor_pos=eol;
  write_symbol(ctx.space);
  // move back one
  ctx.cursor_pos=old_pos-1;
  // fix up cursor
  update_cursor();
}

static void insert(void) {
  int old_pos;
  int i;
  int eol;

  // save old position
  old_pos=ctx.cursor_pos;
  // find end of line
  eol=ctx.cursor_pos/WIDTH*WIDTH+WIDTH-1;
  // push line forward
  i=eol;
  while(i>old_pos) {
    ctx.cursor_pos=i;
    write_symbol(ctx.buffer[ctx.cursor_pos-1]);
    i--;
  }
  // restore position
  ctx.cursor_pos=old_pos;
  // add a space
  write_symbol(ctx.space);
  // restore position
  ctx.cursor_pos=old_pos;
  // fix up cursor
  update_cursor();
}

static void copy(void) {
  int front;

  // reset if not in action
  if(!ctx.clipboard_in_action) ctx.clipboard_rows=0;
  // skip if clipboad full
  if(ctx.clipboard_rows>=HEIGHT) return;
  // find front
  front=ctx.cursor_pos/WIDTH*WIDTH;
  // copy it out
  memcpy(ctx.clipboard+ctx.clipboard_rows*WIDTH, ctx.buffer+front, WIDTH);
  ctx.clipboard_rows++;
  ctx.clipboard_in_action=1;
  // move to next line
  ctx.cursor_pos=front+WIDTH;
  update_cursor();
}

static void cut(void) {
  int i;

  // save position
  i=ctx.cursor_pos;
  // do copy
  copy();
  // restore row
  ctx.cursor_pos=i/WIDTH*WIDTH;
  // blank it
  for(i=0;i<WIDTH;i++) {
    write_symbol(' ');
  }
}

static void paste(void) {
  int i;

  // move to the front of the line
  ctx.cursor_pos/=WIDTH;
  ctx.cursor_pos*=WIDTH;
  // write clipboard contents
  for(i=0;i<WIDTH*ctx.clipboard_rows;i++) {
    write_symbol(ctx.clipboard[i]);
  }
}

static void update_key(void) {
  static const struct {
    const char *name;
    int color;
    unsigned char ch;
  } key[]={
    {"F2=create", CONSOLE_RED, SPACE_RED},
    {"F3=execute", CONSOLE_YELLOW, SPACE_YELLOW},
    {"F4=compile", CONSOLE_GREEN, SPACE_GREEN},
    {"F5=inline", CONSOLE_CYAN, SPACE_CYAN},
    {"F6=lookup", CONSOLE_BLUE, SPACE_BLUE},
    {"F7=variable", CONSOLE_MAGENTA, SPACE_MAGENTA},
    {"F8=comment", CONSOLE_WHITE, SPACE_WHITE},
  };
  int i;

  // draw color key
  console_move(1, OFFSET_Y+HEIGHT+1);
  // add each in
  for(i=0;i<sizeof(key)/sizeof(key[0]);i++) {
    // red
    console_style(key[i].color | 
                  (ctx.space==key[i].ch?CONSOLE_UNDERLINE:0));
    console_write(key[i].name);
    console_style(CONSOLE_WHITE);
    console_write(" ");
  }
  // put back cursor
  cursor_adjust();
}

static int prompt(int x, int y, const char *prompt_text, 
                  char *dst, int dst_limit) {
  int prompt_text_len;
  int pos;
  int key;
  int ret=0;

  // get text length
  prompt_text_len=strlen(prompt_text);
  // move to target
  console_move(x, y);
  // draw prompt
  console_write(prompt_text);
  // read input
  pos=0;
  for(;;) {
    // get a key
    key=console_read();
    // add it in if its a valid character
    if(key>=' ' && key<127 && pos<dst_limit-1) {
      console_write_char(key);
      dst[pos]=key;
      pos++;
    } else if(key==CONSOLE_KEY_BACKSPACE && pos>0) {
      pos--;
      console_move(x+prompt_text_len+pos, y);
      console_write_char(' ');
      console_move(x+prompt_text_len+pos, y);
    } else if(key==CONSOLE_KEY_ENTER) {
      dst[pos]=0;
      ret=1;
      break;
    } else if(key==CONSOLE_KEY_ESCAPE) {
      break;
    }
  }
  // blank prompt area
  console_move(x, y);
  for(pos=0;pos<prompt_text_len+dst_limit;pos++) {
    console_write_char(' ');
  }
  // put cursor back
  update_cursor();
  // return result
  return ret;
}

static void goto_block(void) {
  char line[20];
  int blk;

  // use white text
  console_style(CONSOLE_WHITE);
  // do prompt
  if(prompt(5, OFFSET_Y+HEIGHT+5, "Goto Block: ", line, 20) &&
     sscanf(line, "%d", &blk)==1) {
    change_block(blk);
  }
}

static void editor(void) {
  int key;

  // jump to top block
  change_block(0);

  // main loop
  for(;;) {
    // update status info
    update_status();
    // get a key
    key=console_read();
    // keep track of clipboard state
    if(key!=CONSOLE_KEY_CTRL('C') && 
       key!=CONSOLE_KEY_CTRL('X')) ctx.clipboard_in_action=0;
    // handle key
    switch(key) {
      // handle arrow keys
      case CONSOLE_KEY_UP: ctx.cursor_pos-=WIDTH; update_cursor(); break;
      case CONSOLE_KEY_DOWN: ctx.cursor_pos+=WIDTH; update_cursor(); break; 
      case CONSOLE_KEY_LEFT: 
        if(ctx.cursor_pos>0) {
	  ctx.cursor_pos--; update_cursor(); 
	}
	break;
      case CONSOLE_KEY_RIGHT: 
        if(ctx.cursor_pos<BLOCK_SIZE-1) {
          ctx.cursor_pos++; update_cursor(); 
        }
	break;

      // handle home and end
      case CONSOLE_KEY_HOME: 
        ctx.cursor_pos=ctx.cursor_pos/WIDTH*WIDTH; 
	update_cursor(); 
	break;
      case CONSOLE_KEY_END: 
        ctx.cursor_pos=ctx.cursor_pos/WIDTH*WIDTH+WIDTH-1; 
	update_cursor(); 
	break;

      // handle block movement
      case CONSOLE_KEY_PGUP: change_block(ctx.block-1); break;
      case CONSOLE_KEY_PGDN: change_block(ctx.block+1); break;
      
      // handle enter
      case CONSOLE_KEY_ENTER: 
        ctx.cursor_pos+=WIDTH; 
	ctx.cursor_pos=(ctx.cursor_pos/WIDTH*WIDTH);
	update_cursor();
	break;
   
      // handle backspace and delete
      case CONSOLE_KEY_BACKSPACE: backspace(); break;
      case CONSOLE_KEY_DEL: ctx.cursor_pos++; backspace(); break;
      // handle insert
      case CONSOLE_KEY_INS: insert(); break;

      // handle cut, copy, paste
      case CONSOLE_KEY_CTRL('X'): cut(); break;
      case CONSOLE_KEY_CTRL('C'): copy(); break;
      case CONSOLE_KEY_CTRL('V'): paste(); break;

      // run code on request
      case CONSOLE_KEY_CTRL('R'): run(); break;
      
      // try to jump to a block
      case CONSOLE_KEY_CTRL('G'): goto_block(); break;

      // handle color change
      case CONSOLE_KEY_F(2): ctx.space=SPACE_RED; update_key(); break;
      case CONSOLE_KEY_F(3): ctx.space=SPACE_YELLOW; update_key(); break;
      case CONSOLE_KEY_F(4): ctx.space=SPACE_GREEN; update_key(); break;
      case CONSOLE_KEY_F(5): ctx.space=SPACE_CYAN; update_key(); break;
      case CONSOLE_KEY_F(6): ctx.space=SPACE_BLUE; update_key(); break;
      case CONSOLE_KEY_F(7): ctx.space=SPACE_MAGENTA; update_key(); break;
      case CONSOLE_KEY_F(8): ctx.space=SPACE_WHITE; update_key(); break;

      // handle CTRL-L
      case CONSOLE_KEY_CTRL('L'): redraw(); console_refresh(); break;

      // handle quit
      case CONSOLE_KEY_ESCAPE:
      case CONSOLE_KEY_CTRL('Q'): 
        save(); 
	return;

      // handle tab
      case CONSOLE_KEY_TAB: insert(); insert(); insert(); insert(); break;

      // handle space
      case ' ': write_symbol(ctx.space); break;

      // handle others
      default:
        if(key>' ' && key<127) write_normal_symbol(key);
	break;
    }
  }
}

static void startup_layout(void) {
  // clear things
  console_clear();
  // draw white box around edit area
  console_style(CONSOLE_WHITE);
  console_box(OFFSET_X-1, OFFSET_Y-1, WIDTH+2, HEIGHT+2); 
  // draw color key
  update_key();
  // clipboard keys
  console_move(5, OFFSET_Y+HEIGHT+2);
  console_style(CONSOLE_WHITE);
  console_write("Ctrl-X=cut   ");
  console_write("Ctrl-C=copy   ");
  console_write("Ctrl-V=paste   ");
  // other keys
  console_move(5, OFFSET_Y+HEIGHT+3);
  console_write("Ctrl-G=goto   ");
  console_write("Ctrl-R=run   ");
  console_write("Ctrl-Q=quit   ");
}

static void startup(void) {
  // startup console
  console_startup();
  // set title
  console_title("Rainbow Forth");
  // draw layout
  startup_layout();
}

static void shutdown(void) {
  console_shutdown();
}

static void run(void) {
  COMPILER_ERROR err;

  // save current block
  save();
  // clear things
  console_clear();
  // go to white text
  console_style(CONSOLE_WHITE);

  // run it
  compiler_run(ctx.block_filename, ctx.block, 
               console_write, console_read, &err);

  // goto error if any
  if(err.is_error) {
    // restore layout
    startup_layout();
    // goto error
    ctx.cursor_pos=err.offset;
    change_block(err.block);
    // show message
    console_style(CONSOLE_RED | CONSOLE_UNDERLINE);
    console_move(5, OFFSET_Y+HEIGHT+5);
    console_write(err.message);
    // put back cursor
    update_cursor();
    // get key
    console_read();
    // blank it 
    console_move(5, OFFSET_Y+HEIGHT+5);
    {
      int i;
      int len;
      len=strlen(err.message);
      for(i=0;i<len;i++) console_write_char(' ');
    }
  } else {
    // show message
    console_write("\n------ PRESS ANY KEY TO CONTINUE ------\n");
    // wait for a key
    console_read();
  }

  // refresh
  startup_layout();
  redraw(); 
  console_refresh();
}

int editor_run(const char *block_filename) {
  // init context
  memset(&ctx, 0, sizeof(ctx));

  // set default color
  ctx.space=SPACE_WHITE;

  // store pointer to filename
  ctx.block_filename=block_filename;

  // open file
  ctx.file=fopen(block_filename, "r+");
  if(!ctx.file) ctx.file=fopen(block_filename, "w+");
  if(!ctx.file) {
    fprintf(stderr, "ERROR: can't open '%s'\n", block_filename);
    return -2;
  }
 
  // do display setup
  startup();
  // do main edit loop
  editor();
  // shutdown nicely
  shutdown();

  // close main file
  fclose(ctx.file);

  return 0;
}


