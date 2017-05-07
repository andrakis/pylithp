# Python (2.7) port of Lithp
# Because C++ is too hard.

#

from lithptypes  import *
from builtins    import Builtins
from interpreter import Interpreter
import time

if __name__ == "__main__":
	t0 = time.time()
	builtins = Builtins()
	chain = OpChain()
	builtins.fillClosure(chain.closure)
	t1 = time.time()
	print "Standard library loaded in ", t1 - t0

	fndef = FunctionDefinition(["A", "B"], OpChain(None, [
		FunctionCall("+/*", [
			FunctionCall("get/1", "A"),
			FunctionCall("get/1", "B")
		])
	]))
	fncall = FunctionCall("def/2", [
		Atom.Get("add"), fndef
	])
	chain.add(fncall)
	fncall = FunctionCall("print/2", [
		 FunctionCall("add/2", [Literal("Testing:"),Literal(2), Literal(3)])])
	chain.add(fncall)
	interp = Interpreter()

	t2 = time.time()
	print "Code compiled in ", t2 - t1

	interp.run(chain)
	t3 = time.time()
	print "Execution done in ", t3 - t2
