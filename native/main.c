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
#include "compiler.h"
#include <stdio.h>
#include <string.h>

static void simple_write(const char *str) {
  fputs(str, stdout);
  fflush(stdout);
}

static int simple_read(void) {
  return fgetc(stdin);
}

int main(int argc, char *argv[]) {
  COMPILER_ERROR err;

  // decide how to run it
  if(argc==1) {
    // run editor on default block-file
    return editor_run("rainbowforth_data");
  } else if(argc==2) {
    // compile and run
    compiler_run(argv[1], -1, simple_write, simple_read, &err);
    if(err.is_error) {
      fprintf(stderr, "ERROR at [%d]%d,%d: %s\n", 
              err.block, err.offset%64, err.offset/64, err.message);
      return -1;
    }
    return 0;
  } else if(argc==3 && strcmp(argv[1], "-e")==0) {
    // run editor
    return editor_run(argv[2]);
  } else {
    // show usage
    fprintf(stderr, "USAGE: rainbowforth <block-filename>     (run it)\n");
    fprintf(stderr, "       rainbowforth -e <block-filename>  (edit it)\n");
    return -1;
  }
}


