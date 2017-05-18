import sys
import time
from interpreter import Interpreter
from builtins import Builtins
from lithpparser import BootstrapParser

Interpreter.Debug = False

f = open(sys.argv[1])
interp = Interpreter()
builtins = Builtins()
code = f.read()
f.close()

t0 = time.time()
compiled = BootstrapParser(code)
builtins.fillClosure(compiled.closure)
t1 = time.time()
print "Compiled in", t1 - t0
interp.run(compiled)
t2 = time.time()
print interp.functioncalls, "function calls run in ", t2 - t1