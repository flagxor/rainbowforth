: load   raw-read drop push raw-load ;
: nip   swap drop ;
: ifskip,   ' ifskip [ literal ] , ;
: push,   ' push [ literal ] , ;
: rawdo,   ' rawdo [ literal ] , ;
: rawdo-,   ' rawdo- [ literal ] , ;
: rawloop,   ' rawloop [ literal ] , ;
: +rawloop,   ' +rawloop [ literal ] , ;
: jump-later,   here 0 literal ;

[ macro ]
: if   ifskip, jump-later, ;
: then   here swap jump! ;
: else    jump-later,  swap  { then } ;
: begin   here ;
: while   ifskip, jump-later, ;
: repeat   swap  jump-later, jump!  { then } ;
: until   ifskip,  jump-later, jump! ;
: again   jump-later, jump! ;
: do   push, push, here rawdo, jump-later, ;
: -do   push, push, here rawdo-, jump-later, ;
: loop   rawloop, { repeat } ;
: +loop   +rawloop, { repeat } ;
[ forth ]

: color-ch
     dup 255 = if ff0000h foreground then
     dup 254 = if ffff00h foreground then
     dup 253 = if 00ff00h foreground then
     dup 252 = if 00ffffh foreground then
     dup 251 = if 0000ffh foreground then
     dup 250 = if ff00ffh foreground then
     dup 32  = if ffffffh foreground then
     dup 250 >= if drop 32 emit else emit then ;

: width   [ sizexy drop literal ] ;
: height   [ sizexy nip 2 - literal ] ;

: no-own 32 ;
: u-own 117 ;
: o-own 111 ;

variable cursor-pos
variable cursor-pos-old
variable cursor-mark
variable cursor-block
variable block-state [ no-own block-state ! ]
variable cursor-color [ 32 cursor-color ! ]
variable editor-dirty
variable edit-buffer [ 20 allot  here 1024 allot edit-buffer !  20 allot ]
variable grab-buffer [ here 1024 allot grab-buffer ! ]
variable grab-size [ 0 grab-size ! ]
variable font-size [ 200 font-size !  font-size @ set-font-size ]

: clip-cursor  cursor-pos @  0 max  width height * 1 - min  cursor-pos ! ;
: handle-cursor
     cursor-pos @ = if 777777h background else 0 background then ;
: blanks    0 do 32 emit loop ;
: show-page   0 17 setxy 777777h foreground
                         0 background cursor-block @ .
                         4 blanks block-state @ emit
                         3 blanks cursor-color @ color-ch 42 emit
                         10 blanks ;
: redraw-one   dup handle-cursor dup setraw edit-buffer @ + @ color-ch ;
: redraw-range   -do i redraw-one drop -1 +loop ;
: redraw-whole   -1 1023 redraw-range ;
: filter-null   dup 0 = if drop 32 ; then ;
: filter-block 1024 0 do dup i + @ filter-null over i + ! loop ;
: is-space   dup 32 = if drop 1 ; then 250 >= ;
: next-space   begin dup edit-buffer @ + @ is-space not while 1+ repeat
                   1023 min ;
: last-space   begin dup edit-buffer @ + @ is-space not while 1- repeat
                   1 - -1 max ;
: space-range   dup push 1 - last-space pop next-space ;
: redraw-around   space-range redraw-range ;
: redraw-around-cursor   cursor-pos @ redraw-around ;
: redraw-around-old   cursor-pos-old @ redraw-around ;
: redraw-all   redraw-whole show-page ;
: redraw-most   redraw-around-cursor redraw-around-old ;

: type-one-raw   block-status @ u-own <> if drop ; then
                 edit-buffer @ cursor-pos @ + !
                 1 editor-dirty !
                 1 cursor-pos +! ;
: type-one   type-one-raw cursor-pos @ dup
             edit-buffer @ is-space if
                     cursor-color @ type-one-raw then
             cursor-pos ! ;

: editor-save-raw   cursor-block @ edit-buffer @ write redraw-whole ;
: editor-save   editor-dirty @ if editor-save-raw 0 editor-dirty ! then ;
: editor-load   cursor-block @ edit-buffer @ read block-state !
                               edit-buffer @ filter-null redraw-all ;
: editor-delete   cursor-block @ delete  editor-load ;

: editor-copy    cursor-pos @ 1+ cursor-mark @ -  0 max  grab-size !
                 edit-buffer @ cursor-mark @ +
                 grab-buffer @   grab-size @  copy ;
: editor-paste   block-status @ u-own <> if ; then
                 grab-buffer @
                 edit-buffer @ cursor-pos @ +
                 grab-size @  copy   1 editor-dirty !   redraw-all ;

: editor-claim   block-status @ no-own <> if ; then
                 1 editor-dirty !  editor-save editor-load ;

: special-mode    begin key
     dup 114 = if 255 cursor-color ! ; then
     dup 121 = if 254 cursor-color ! ; then
     dup 103 = if 253 cursor-color ! ; then
     dup 99 = if 252 cursor-color ! ; then
     dup 98 = if 251 cursor-color ! ; then
     dup 109 = if 250 cursor-color ! ; then
     dup 119 = if 32 cursor-color ! ; then
     dup 91 = if cursor-pos @ cursor-mark ! ; then
     dup 93 = if editor-copy ; then
     dup 112 = if editor-paste ; then
     dup 45 = if -20 font-size +! font-size @ set-font-size ; then
     dup 61 = if 20 font-size +! font-size @ set-font-size ; then
     dup 65 = if edit-buffer @ 1024 download ; then
     dup 68 = if editor-delete ; then
     dup 32 = if editor-claim 65 emit ; then
     dup 13 = if editor-save cursor-block @ load ; then
     dup 108 = if cls redraw-all ; then
     dup 92 = if 92 type-one ; then
     clip-cursor
     redraw-most drop again ;

: edit-mode    begin key
     cursor-pos @ cursor-pos-old !
     dup -37 = if -1 cursor-pos +! then
     dup -39 = if 1 cursor-pos +! then
     dup -38 = if width negate cursor-pos +! then
     dup -40 = if width cursor-pos +! then
     dup -33 = if cursor-block @ 0 > if
         editor-save -1 cursor-block +! editor-load then then
     dup -34 = if editor-save 1 cursor-block +! editor-load then
     dup 92 = if special-mode show-page else
        dup 33 >= if dup 126 <= if type-one then then then
     dup 32 = if cursor-color @ type-one then
     dup 13 = if cursor-pos @ 64 + 64 / 64 * cursor-pos ! then
     clip-cursor
     redraw-most drop again ;

: main   editor-load edit-mode ;
[ main ]

