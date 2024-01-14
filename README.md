# Qrawlr

Qrawlr is a simple text crawler that can be used to build syntax trees from (binary) text. It is currently written in Python but will be ported to C++ and [QINP](https://github.com/eQosys/QINP) when it is more mature.

## Usage

TODO

## Next steps/features

 - [ ] escape sequences (e.g. "\xhh")
 - [x] count specifier (e.g. "h"#2 or "h"#2-5)
 - [x] match replacement (e.g. "h"->"H", "h"->ParsedH)
 - [ ] insert content modifier (e.g. String^)