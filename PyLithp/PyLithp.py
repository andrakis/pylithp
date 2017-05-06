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

	fncall = FunctionCall("print/*",
		[Literal("Testing: "),
		 FunctionCall("+/*", [Literal(2), Literal(3)])])
	chain.add(fncall)

	interp = Interpreter()
	interp.run(chain)
