(Pretty) (naive) try to compile javascript to native code, with python.

python compiler.py script.js

Implementation
-------------
Values are represented as 32 bit integers, called BoxedInt (in v8 this is called smi):
    [ 31b data | 1b tag]
    tag: 1 = object, 0 = integer
    data: pointer/integer

Currently we lack any kind of memory allocator or garbage collector.
If you always wanted to test some GC scheme, that's your chance, go ahead and implement it.

Only some basic operations are implemented, the most of them as so named stub calls
(call to python function instead of machine code).

*Variable Deceleration*

     var x = 1, y; var z;

*Identifier assignment* (needs to be a declared variable)

     x = 'hello world';

*if / conditional operator / for*

     if (true) {
     }
     (x ? true : else);
     for (var i = 0; ; i++) { /* attention! never stops */
     }

*(unary) plus / minus*

     -1, +15, 1 + 1, x - 16.5;

*increment / decrement*
*void (used for logging)*

     void 'foobar' /* would generator console output [heap object] @ 0xdeadbeef [string] "foobar" */

*Array literals*

     [1, 2, 3, 4];

*Some other stuff that's merely an idea or doesn't work*

     "".length, [].length

Credits
-------
- [SpiderMonkey](https://wiki.mozilla.org/JavaScript:Home_Page)
- [v8](http://code.google.com/p/v8/) (clever stuff there!)
- [pynarcissus](http://code.google.com/p/pynarcissus/) (used for generating the ast)
- [pyasm](http://codeflow.org/entries/2009/jul/31/pyasm-python-x86-assembler/)

License
-------
pyasm
>:copyright: 2008 by Florian Boesch <pyalot@gmail.com>.
>:license: GNU AGPL v3 or later, see LICENSE for more details.
pynarcissus
>Version: MPL 1.1/GPL 2.0/LGPL 2.1
>The Initial Developer of the Original Code is
>Brendan Eich <brendan@mozilla.org>.
>Portions created by the Initial Developer are Copyright (C) 2004
>the Initial Developer. All Rights Reserved.

