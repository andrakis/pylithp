import sys
import time
from lithpparser import BootstrapParser
from interpreter import Interpreter
from builtins import Builtins

Interpreter.Debug = True

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
print "Run complete in ", t2 - t1