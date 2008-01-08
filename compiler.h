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

#ifndef _compiler_h
#define _compiler_h

// limits
#define COMPILE_MAX_ERROR 80

// optional error output target
typedef struct {
  int is_error;
  int block;
  int offset;
  char message[COMPILE_MAX_ERROR];
} COMPILER_ERROR;

// compiles starting at block 0
// extra_block>=0 will run block extra_block after block 0 is done
extern void compiler_run(const char *block_filename, int extra_block,
                         COMPILER_ERROR *err);

#endif


