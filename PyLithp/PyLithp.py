# Python (2.7) port of Lithp
# Because C++ is too hard.

#

from lithptypes  import *
from builtins    import Builtins
from interpreter import Interpreter
import time

if __name__ == "__main__":
	interp = Interpreter()
	t0 = time.time()
	builtins = Builtins()
	chain = OpChain()
	builtins.fillClosure(chain.closure)
	t1 = time.time()
	print "Standard library loaded in ", t1 - t0

	# (def add #A,B :: ((+ A B))
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

	# (var A 2)
	fncall = FunctionCall("var/2", [VariableReference("A"), Literal(2)])
	chain.add(fncall)

	# (var B 3)
	fncall = FunctionCall("var/2", [VariableReference("B"), Literal(3)])
	chain.add(fncall)

	# (print (+ "Testing " A " + " B ": " (add A B)))
	fncall = FunctionCall("print/2", [
		 FunctionCall("+/*", [
			 Literal("Testing "), FunctionCall("get/1", [VariableReference("A")]),
			 Literal(" + "), FunctionCall("get/1", [VariableReference("B")]),
			 Literal(": "),
			 FunctionCall("add/2", [
				FunctionCall("get/1", [VariableReference("A")]),
				FunctionCall("get/1", [VariableReference("B")])
			])
		])
	])
	chain.add(fncall)

	t2 = time.time()
	print "Code compiled in ", t2 - t1

	interp.run(chain)
	t3 = time.time()
	print "Execution done in ", t3 - t2
