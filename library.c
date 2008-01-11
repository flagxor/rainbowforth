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

#include "library.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#ifdef _WIN32

#include <windows.h>

// mimic unix
static void *dlopen(const char *filename, int flag) {
  return (void*)LoadLibrary(filename);
}

// mimic unix
static void *dlsym(void *handle, const char *name) {
  return (void*)GetProcAddress((HMODULE)handle, name);
}

#else

#include <dlfcn.h>

#endif

// structure for library list
typedef struct _LIBRARY_ENTRY {
  struct _LIBRARY_ENTRY *next;
  const char *name;
  void *handle;
} LIBRARY_ENTRY;

// list of libraries
static LIBRARY_ENTRY *library_head=0;

void library_load(const char *name) {
  LIBRARY_ENTRY *e;
  LIBRARY_ENTRY **t;
  void *lib;

  // check for existing
  for(t=&library_head;(*t);t=&(*t)->next) {
    if(strcmp((*t)->name, name)==0) {
      // move to front
      e=(*t);
      (*t)=e->next;
      e->next=library_head;
      library_head=e;
      // done
      return;
    }
  }

  // try to load it
  lib=dlopen(name, RTLD_LAZY);
  if(!lib) return;

  // add it
  e=(LIBRARY_ENTRY*)malloc(sizeof(LIBRARY_ENTRY));
  assert(e);
  // fill it out
  e->name=name;
  e->handle=lib;
  // add it in
  e->next=library_head;
  library_head=e;
}

void *library_symbol(const char *name) {
  LIBRARY_ENTRY *e;
  void *ret;

  // try each library
  for(e=library_head;e;e=e->next) {
    // check this one
    ret=dlsym(e->handle, name);
    // look it up
    if(ret) return ret;
  }
  // failure
  return 0;
}



