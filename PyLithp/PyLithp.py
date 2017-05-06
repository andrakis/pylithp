# Python (2.7) port of Lithp
# Because C++ is too hard.

#

from lithptypes  import *
from builtins    import Builtins
from interpreter import Interpreter

if __name__ == "__main__":
	builtins = Builtins()
	chain = OpChain()
	builtins.fillClosure(chain.closure)

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
	fncall = FunctionCall("print/2",
		[Literal("Testing: "),
		 FunctionCall("add/2", [Literal(2), Literal(3)])])
	chain.add(fncall)

	interp = Interpreter()
	interp.run(chain)
