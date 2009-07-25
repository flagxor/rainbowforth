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

#include "compiler.h"
#include "common.h"
#include "library.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// data type of cell
typedef int CELL;

// maximum word length
#define MAX_WORD_SIZE 32
// size of heaps
#define CODE_HEAP_SIZE (10*1024*1024)
#define DATA_HEAP_SIZE (10*1024*1024)
// size of dstack
#define DSTACK_SIZE (64*1024)

// constants for find
#define FIND_FORTH 0
#define FIND_MACRO 1

// guard values
#define GUARD_VALUE 0xbeefbeef
#define GUARD_SIZE 5

// suffix to make words yellow
#define EXECUTE_STRING "\xfe"
// special word used to enter forth
#define WORD_EXECUTE_FORTH_RAW "execute-forth"
// user-defined forth words that are relied upon
#define WORD_VARIABLE ("variable" EXECUTE_STRING)
#define WORD_COMPILE ("compile," EXECUTE_STRING)
#define WORD_LITERAL ("literal" EXECUTE_STRING)
#define WORD_EXECUTE_FORTH (WORD_EXECUTE_FORTH_RAW EXECUTE_STRING)

// a dictionary cell
typedef struct _DICTIONARY_ENTRY {
  struct _DICTIONARY_ENTRY *next; // OFFSET 0
  void *code_addr; // OFFSET 4
  void *data_addr; // OFFSET 8
  int is_macro; // OFFSET 12
  int smudged; // OFFSET 16
  int name_len; // OFFSET 20
  unsigned char name[MAX_WORD_SIZE+1]; // OFFSET 24
} DICTIONARY_ENTRY;

// global context type
typedef struct {
  // dstack pointer (OFFSET 0)
  CELL *dstack_ptr;
  // code here pointer (OFFSET 4)
  unsigned char *code_here;
  // macro/forth flag (OFFSET 8)
  int is_macro;
  // table of c functions to call in forth (OFFSET 12)
  void **function_table;
  // last dictionary word (OFFSET 16)
  DICTIONARY_ENTRY *dictionary;
  // data heap here (OFFSET 20)
  unsigned char *data_here;
  // other random ones
  FILE *file;
  // code heap
  unsigned char *code_heap;
  // data heap
  unsigned char *data_heap;
  // bottom guard on stack
  int dstack_guard_bottom[GUARD_SIZE];
  // data stack
  CELL dstack[DSTACK_SIZE];
  // top guard on stack
  int dstack_guard_top[GUARD_SIZE];
  // current word being built
  unsigned char current_word[MAX_WORD_SIZE];
  int current_word_len;
  // place to record error info (including current parse position)
  COMPILER_ERROR *err;
  // i/o operations
  COMPILER_WRITE write;
  COMPILER_READ read;
} COMPILER_CONTEXT;

// execute-forth function pointer type
typedef void (*EXECUTE_FORTH_FUNC)(COMPILER_CONTEXT*);

// global context
static COMPILER_CONTEXT ctx;

// functions referenced recursively
static void execute(const unsigned char *buf, int len, int update_err);
static void load(int block);

static void execute_cstr(const char *str) {
  execute((const unsigned char*)str, strlen(str), 0);
}

static int is_space(unsigned char ch) {
  if(ch==' ' || ch>SPACE_LAST) return 1;
  return 0;
}

static int counted_string_equal(unsigned const char *a, int a_len,
                                const char *b, int b_len) {
  if(a_len<0) a_len=strlen((const char*)a);
  if(b_len<0) b_len=strlen(b);
  return a_len==b_len && memcmp(a, b, a_len)==0;
}

static void dstack_push(CELL value) {
  ctx.dstack_ptr++;
  (*ctx.dstack_ptr)=value;
}

static CELL dstack_pop(void) {
  CELL ret=(*ctx.dstack_ptr);
  ctx.dstack_ptr--;
  return ret;
}

static void dstack_check(void) {
  int i;

  for(i=0;i<GUARD_SIZE;i++) {
    assert(ctx.dstack_guard_top[i]==GUARD_VALUE &&
           ctx.dstack_guard_bottom[i]==GUARD_VALUE);
  }
  if(ctx.dstack_ptr<&ctx.dstack[-1]) {
    assert(0);
  } else if(ctx.dstack_ptr>=&ctx.dstack[DSTACK_SIZE]) {
    assert(0);
  }
}

static void heap_dump(void) {
  FILE *file;

  // open log file
  file=fopen("heap_dump", "wb");
  if(!file) return;

  // write heap to it
  fwrite(ctx.code_heap, ctx.code_here-ctx.code_heap, 1, file);

  // close it
  fclose(file);
}

static void word_dump(void) {
  FILE *file;
  DICTIONARY_ENTRY *e;

  // open log file
  file=fopen("word_dump", "w");
  if(!file) return;

  // write each word to it
  for(e=ctx.dictionary;e;e=e->next) {
    fwrite(e->name, 1, e->name_len, file);
    fprintf(file, " -> %x\n", (unsigned char*)e->code_addr-ctx.code_heap);
  }

  // close it
  fclose(file);
}

static int execute_built_in(const unsigned char *word, int word_len) {
  int i, j;

  if(counted_string_equal(word, word_len, "macro", -1)) {
    ctx.is_macro=1;
  } else if(counted_string_equal(word, word_len, "forth", -1)) {
    ctx.is_macro=0;
  } else if(counted_string_equal(word, word_len, "unsmudge", -1)) {
    ctx.dictionary->smudged=0;
  } else if(counted_string_equal(word, word_len, "smudge", -1)) {
    ctx.dictionary->smudged=1;
  } else if(counted_string_equal(word, word_len, "heap-dump", -1)) {
    heap_dump();
  } else if(counted_string_equal(word, word_len, "word-dump", -1)) {
    word_dump();
  } else if(counted_string_equal(word, word_len, "b,", -1)) {
    (*ctx.code_here)=dstack_pop();
    ctx.code_here++;
  } else if(counted_string_equal(word, word_len, "windows?", -1)) {
#ifdef _WIN32
    dstack_push(1);
#else
    dstack_push(0);
#endif
  } else if(counted_string_equal(word, word_len, "load", -1)) {
    load(dstack_pop());
  } else if(counted_string_equal(word, word_len, "thru", -1)) {
    j=dstack_pop();
    i=dstack_pop();
    for(;i<=j;i++) load(i);
  } else {
    return 0;
  }
  return 1;
}

static void blank_current_word(void) {
  ctx.current_word_len=0;
}

static DICTIONARY_ENTRY *find(int find_macros) {
  DICTIONARY_ENTRY *e;

  for(e=ctx.dictionary;e;e=e->next) {
    if(!e->smudged &&
       e->name_len==ctx.current_word_len &&
       memcmp(e->name, ctx.current_word, e->name_len)==0 &&
       e->is_macro==find_macros) {
      return e;
    }
  }
  return 0;
}

static int parse_number(void) {
  char tmp[MAX_WORD_SIZE+1];
  int x=0;

  // copy it over for sscanf
  memcpy(tmp, ctx.current_word, ctx.current_word_len);
  tmp[ctx.current_word_len]=0;
  // check for h (for hex)
  if(ctx.current_word[ctx.current_word_len-1]=='h') {
    // try hex
    if(sscanf(tmp, "%x", &x)!=1) {
      ctx.err->is_error=1;
      sprintf(ctx.err->message, "unknown word '%s'", tmp);
    }
  } else {
    // try decimal
    if(sscanf(tmp, "%d", &x)!=1) {
      ctx.err->is_error=1;
      sprintf(ctx.err->message, "unknown word '%s'", tmp);
    }
  }
  return x;
}

static void create(void) {
  DICTIONARY_ENTRY *e;

  // alloc entry
  e=(DICTIONARY_ENTRY*)calloc(1, sizeof(DICTIONARY_ENTRY));
  assert(e);

  // copy name
  memcpy(e->name, ctx.current_word, ctx.current_word_len);
  e->name_len=ctx.current_word_len;
  // add null so c functions can use name
  e->name[e->name_len]=0;

  // set addresses
  e->code_addr=ctx.code_here;
  e->data_addr=ctx.data_here;
  // set is_macro
  e->is_macro=ctx.is_macro;

  // add to dictionary
  e->next=ctx.dictionary;
  ctx.dictionary=e;
}

static void execute_word(void) {
  DICTIONARY_ENTRY *e;

  // find it
  e=find(FIND_FORTH);
  // do it if its there
  if(e) {
    // handle execute-forth word specially
    if(counted_string_equal(e->name, e->name_len, 
                            WORD_EXECUTE_FORTH_RAW, -1)) {
      // check dstack
      dstack_check();
      // jump directly to forth word address
      ((EXECUTE_FORTH_FUNC)e->code_addr)(&ctx);
      // check dstack
      dstack_check();
    } else {
      // call special execute-forth word
      dstack_push((CELL)e->code_addr);
      execute_cstr(WORD_EXECUTE_FORTH);
    }
  } else if(execute_built_in(ctx.current_word, ctx.current_word_len)) {
    // the above function does what's needed
  } else {
    dstack_push(parse_number());
  }
}

static void compile_word(int force_macros) {
  DICTIONARY_ENTRY *e;

  // find it
  if(force_macros) {
    e=find(FIND_MACRO);
  } else {
    e=find(FIND_MACRO);
    if(!e) e=find(FIND_FORTH);
  }
  // handle numbers
  if(!e) {
    dstack_push(parse_number());
    execute_cstr(WORD_LITERAL);
  } else {
    // execute if a macro
    if(!force_macros && e->is_macro) {
      dstack_push((CELL)e->code_addr);
      execute_cstr(WORD_EXECUTE_FORTH);
    } else {
      dstack_push((CELL)e->code_addr);
      execute_cstr(WORD_COMPILE);
    }
  }
}

static void lookup_word(void) {
  DICTIONARY_ENTRY *e;

  // find it
  e=find(FIND_FORTH);
  if(!e) e=find(FIND_MACRO);
  // add to stack if there (or zero on fail)
  if(e) {
    dstack_push((CELL)e->code_addr);
  } else {
    ctx.err->is_error=1;
    sprintf(ctx.err->message, "unknown word '%s'", ctx.current_word);
  }
}

static void execute_char(unsigned char ch) {
  // skip if error has happened
  if(ctx.err->is_error) return;
  // handle non-spaces
  if(!is_space(ch)) {
    // add normal characters to the current word
    // up to the max word size
    if(ctx.current_word_len<MAX_WORD_SIZE) {
      ctx.current_word[ctx.current_word_len]=ch;
      ctx.current_word_len++;
    }
    return;
  }

  // done if current word is empty
  if(ctx.current_word_len==0) return;

  // handle by type of space
  switch(ch) {
    // skip comments
    case SPACE_WHITE: break;

    // create new words
    case SPACE_RED: create(); break;

    // create new variable
    case SPACE_MAGENTA:
      create();
      execute_cstr(WORD_VARIABLE);
      break;

    // execute a word
    case SPACE_YELLOW: execute_word(); break;

    // compile a word (executes macros)
    case SPACE_GREEN: compile_word(0); break;

    // compile a word (compiles macros)
    case SPACE_CYAN: compile_word(1); break;

    // get word address
    case SPACE_BLUE: lookup_word(); break;

    // nothing otherwise
    default: break;
  }

  // blank out this word
  blank_current_word();
}

static void execute(const unsigned char *buf, int len, int update_err) {
  int pos;

  // skip if error has happened
  if(ctx.err->is_error) return;
  // reflect position for error info
  if(update_err) ctx.err->offset=0;
  // blank current word
  blank_current_word();
  // go thru
  for(pos=0;pos<len && !ctx.err->is_error;pos++) {
    // update current offset if requested
    if(update_err) ctx.err->offset=pos;
    // handle this one character
    execute_char(buf[pos]);
  }
}

static void load(int block) {
  unsigned char buf[BLOCK_SIZE];
  int old_block=ctx.err->block;

  // set error block to match
  if(!ctx.err->is_error) ctx.err->block=block;
  // blank current word
  blank_current_word();
  // load the data
  fseek(ctx.file, block*BLOCK_SIZE, SEEK_SET);
  memset(buf, ' ', BLOCK_SIZE);
  fread(buf, BLOCK_SIZE, 1, ctx.file);
  // execute the block
  execute(buf, BLOCK_SIZE, 1);
  // restore if no errors
  if(!ctx.err->is_error) ctx.err->block=old_block;
}

static void print_number(CELL i) {
  char str[100];
  sprintf(str, "%d ", i);
  ctx.write(str);
}

static int key(void) {
  return ctx.read();
}

static void emit(int ch) {
  char str[2];
  str[0]=ch; str[1]=0;
  ctx.write(str);
}

static void *util_functions[]={
  load,
  print_number,
  key,
  emit,
  library_load,
  library_symbol,
};

void compiler_run(const char *block_filename, int extra_block,
                  COMPILER_WRITE write, COMPILER_READ read,
                  COMPILER_ERROR *err) {
  int i;

  // init global context
  memset(&ctx, 0, sizeof(ctx));

  // store i/o operations
  ctx.write=write;
  ctx.read=read;

  // store error info pointer
  ctx.err=err;
  // init error info
  memset(err, 0, sizeof(COMPILER_ERROR));

  // init function table
  ctx.function_table=util_functions;
  // init stack
  ctx.dstack_ptr=&ctx.dstack[-1];
  // init guards
  for(i=0;i<GUARD_SIZE;i++) {
    ctx.dstack_guard_top[i]=GUARD_VALUE;
    ctx.dstack_guard_bottom[i]=GUARD_VALUE;
  }

  // open file
  ctx.file=fopen(block_filename, "r");
  if(!ctx.file) {
    ctx.err->is_error=1;
    sprintf(ctx.err->message, "can't open '%s'", block_filename);
    return;
  }

  // init code heap
  ctx.code_heap=malloc(CODE_HEAP_SIZE);
  assert(ctx.code_heap);
  // point here at heap
  ctx.code_here=ctx.code_heap;

  // init code heap
  ctx.data_heap=malloc(DATA_HEAP_SIZE);
  assert(ctx.data_heap);
  // point here at heap
  ctx.data_here=ctx.data_heap;

  // load block 0
  load(0);

  // load extra block if any
  if(extra_block>=0) load(extra_block);

  // cleanup heaps
  free(ctx.code_heap);
  free(ctx.data_heap);

  // close main file
  fclose(ctx.file);
}
