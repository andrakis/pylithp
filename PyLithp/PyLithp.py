# Python (2.7) port of Lithp
# Because C++ is too hard.

#

from lithptypes  import *
from builtins    import Builtins
from interpreter import Interpreter
from lithpparser import BootstrapParser
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
	fndef = FunctionDefinition(chain, "add/2", ["A", "B"], OpChain(chain, [
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

	code = '( \
		(def add #A,B :: ((+ (get A) (get B)))) \
		(var A 5) \
		(var B 10) \
		(print (+ "Add " A "+" B ": " (add A B))))'
	compiled = BootstrapParser(code)
	builtins.fillClosure(compiled.closure)
	t4 = time.time()
	print "Compile done in ", t4 - t3

	interp.run(compiled)
	t5 = time.time()
	print "Run complete in ", t5 - t4

	code = '( \
		(def is_zero #N :: ((== 0 N))) \n\
			(def test #N :: ( \n\
				(if (is_zero N) ( \n\
					(print "N is zero") \n\
				) (else ( \n\
					(print "N is not zero, it is: " N) \n\
				))) \n\
			)) \n\
		(test 1) \n\
		(test 0) \n\
	)'
	compiled = BootstrapParser(code)
	builtins.fillClosure(compiled.closure)
	t6 = time.time()
	print "Compiled in ", t6 - t5

	interp.run(compiled)
	t7 = time.time()
	print "Run complete in ", t7 - t6