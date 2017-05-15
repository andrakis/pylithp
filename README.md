# pylithp
Python version of Lithp, because C++ is too hard.

This implements a syntax-compatible version of [Lithp](https://github.com/andrakis/node-lithp) in Python.

The benefits of this are:

* Potentially faster execution
* Larger number support
* Greater platform compatibility
* The large library of Python modules available

# Status

## Version: 0.7

Version 0.7 introduces the `recurse/*` function.

Version 0.5 is now syntax compatible with [node-lithp](https://github.com/andrakis/node-lithp).

It implements the Bootstrap parser and a small subset of the builtin library. The builtin library
is now the primary focus so that modules work.

## Working so far

* `print/*`, `def/2`, `get/1`, basic arithmatic
* Basic types
* User defined functions
* Debug output
* Test of user defined function `add`
* AST parser
* Bootstrap parser
* `if/2`, `if/3`, `else/1`, comparison operators
* Factorial sample
* `recurse/*`

## In progress

* Builtin library
  * modules support
  * `import/1`, `export/*`, `export-global/*`
  * ability to import python modules