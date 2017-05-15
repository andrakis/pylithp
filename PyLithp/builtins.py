from lithptypes import *
from excepts import *

EmptyChain = OpChain()

class Builtins(object):
	def __init__(self):
		self.builtins = Closure()
		self.builtin("head", ["List"], lambda List,Chain,Interp: Builtins.OpHead([List]))
		self.builtin("tail", ["List"], lambda List,Chain,Interp: Builtins.OpTail([List]))
		self.builtin("def", ["Name", "Body"], lambda Args,Chain,Interp: Builtins.OpDef(Args, Chain))
		self.builtin("get", ["Name"], lambda Args,Chain,Interp: Builtins.OpGet(Args, Chain))
		self.builtin("set", ["Name", "Value"], lambda Args,Chain,Interp: Builtins.OpSet(Args, Chain))
		self.builtin("var", ["Name", "Value"], lambda Args,Chain,Interp: Builtins.OpVar(Args, Chain))
		self.builtin("+/*", [], lambda Args,Chain,Interp: Builtins.OpAdd(Args))
		self.builtin("-/*", [], lambda Args,Chain,Interp: Builtins.OpSub(Args))
		self.builtin("*/*", [], lambda Args,Chain,Interp: Builtins.OpMult(Args))
		self.builtin("//*", [], lambda Args,Chain,Interp: Builtins.OpDiv(Args))
		self.builtin("print/*", [], lambda Args,Chain,Interp: Builtins.OpPrint(Args))
		self.builtin("scope", ["Target"], lambda Args,Chain,Interp: Builtins.OpScope(Args, LithpOpChainMember))
		self.builtin("==", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] == Args[1]))
		self.builtin("!=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] != Args[1]))
		self.builtin(">", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] > Args[1]))
		self.builtin(">=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] >= Args[1]))
		self.builtin("<", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] < Args[1]))
		self.builtin("<=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] <= Args[1]))
		self.builtin("!", ["X"], lambda Args,Chain,Interp: Builtins.Truthy(not Args[0]))
		self.builtin("?", ["Pred", "X", "Y"], lambda Args,Chain,Interp:
			Builtins.Truthy(Args[0] == Atoms.True, Args[1], Args[2]))
		self.builtin("if/2", ["Test", "Action"], lambda Args,Chain,Interp:
			self.builtins["if/3"].body([Args[0], Args[1], Builtins.EmptyChain], \
				Chain, Interp))
		self.builtin("if/3", ["Test", "Action", "Else"], lambda Args,Chain,Interp:
			Builtins.TestIf(Args[0], Args[1], Args[2]))
		self.builtin("else", ["Chain"], lambda Args,Chain,Interp: Args[0].call_immediate())
		self.builtin("while", ["Test", "Action"], lambda Args,Chain,Interp:
			Builtins.OpWhile(Args[0], Args[1], Chain, Interp))
		self.builtin("list/*", [], lambda Args,Chain,Interp: Args)
		self.builtin("map", ["List", "Callback"], lambda Args,Chain,Interp:
			   Builtins.OpMap(Args[0], Args[1], Chain, Interp))
		self.builtin("@", ["X", "Y"], lambda Args,Chain,Interp: Args[0] % Args[1])
		self.builtin("&", ["X", "Y"], lambda Args,Chain,Interp: Args[0] & Args[1])
		self.builtin("|", ["X", "Y"], lambda Args,Chain,Interp: Args[0] | Args[1])
		self.builtin("^", ["X", "Y"], lambda Args,Chain,Interp: Args[0] ^ Args[1])
		self.builtin("<<", ["X", "Y"], lambda Args,Chain,Interp: Args[0] << Args[1])
		self.builtin(">>", ["X", "Y"], lambda Args,Chain,Interp: Args[0] >> Args[1])
		self.builtin("split", ["String", "Split"], lambda Args,Chain,Interp:
			   Args[0].split(Args[1]))
		self.builtin("repeat", ["String", "Count"], lambda Args,Chain,Interp: Args[0] * Args[1])
		self.builtin("join", ["List", "JoinChar"], lambda Args,Chain,Interp: Args[1].join(Args[0]))
		self.builtin("index", ["List", "Index"], lambda Args,Chain,Interp: Args[0][Args[1]])
		self.builtin("length", ["List"], lambda Args,Chain,Interp: len(Args[0]))
		self.builtin("parse-int", ["Str"], lambda Args,Chain,Interp: int(Args[0]))
		self.builtin("parse-float/1", ["Str"], lambda Args,Chain,Interp: float(Args[0]))
		self.builtin("call/*", [], lambda Args,Chain,Interp:
			   Builtins.OpCall(Args[0], Args[1:], Chain, Interp))
		self.builtin("apply/*", [], lambda Args,Chain,Interp:
			   Builtins.OpApply(Args[0], Chain, Interp))
		self.builtin("catch", ["OpChain"], lambda Args,Chain,Interp: Args[0])
		self.builtin("throw", ["Message"], lambda Args,Chain,Interp: Builtins.OpThrow(Args[0]))
		self.builtin("to-string", ["Arg"], lambda Args,Chain,Interp: str(Args[0]))
		self.builtin("export/*", [], lambda Args,Chain,Interp: Builtins.OpExport(Args[0], Chain, KeyboardInterrupt))
		self.builtin("recurse/*", [], lambda Args,Chain,Interp: Builtins.OpRecurse(Args[0], Chain))

	def builtin (self,name, params, body):
		fndef = FunctionDefinitionNative(name, params, body)
		self.builtins[fndef.name] = fndef

	def fillClosure(self, closure):
		for key in self.builtins:
			closure[key] = self.builtins[key]

	def __str__(self):
		return str(self.builtins)

	@staticmethod
	def Truthy(result, X = None, Y = None):
		if X == None:
			X = Atom.True
		if Y == None:
			Y = Atom.False
		if result:
			return X
		else:
			return Y

	@staticmethod
	def GetIfResult(value):
		if isinstance(value, OpChain):
			return value.call_immediate()
		return value

	@staticmethod
	def TestIf(Test, Action, Else):
		if Test == Atom.True:
			return Builtins.GetIfResult(Action)
		else:
			return Builtins.GetIfResult(Else)

	@staticmethod
	def OpGet(Args, chain):
		[Name] = Args
		if isinstance(Name, VariableReference):
			Name = Name.name
		if isinstance(Name, Atom):
			Name = Name.name
		value = chain.closure.get_or_missing(Name)
		if value == Missing:
			raise NameError()
		return value

	@staticmethod
	def OpSet(Args, chain):
		[Name, Value] = Args
		if isinstance(Name, VariableReference):
			Name = Name.name
		if isinstance(Name, Atom):
			Name = Name.name
		chain.closure.set(Name, Value)
		return Value

	@staticmethod
	def OpVar(Args, chain):
		[Name, Value] = Args
		if isinstance(Name, VariableReference):
			Name = Name.name
		if isinstance(Name, Atom):
			Name = Name.name
		chain.closure.set_immediate(Name, Value)
		return Value

	@staticmethod
	def OpDef(Args, chain):
		[Name, Body] = Args
		if isinstance(Name, Atom) == False:
			raise NotImplementedError()
		if isinstance(Body, FunctionDefinition) == False:
			raise NotImplementedError()
		realName = Name.name
		arityIndex = realName.find("/")
		if arityIndex == -1:
			realName += "/" + str(len(Body.args))
		else:
			Body.arity = realName[-arityIndex:]
			if Body.arity != "*":
				Body.arity = int(Body.arity)

		Body.readable_name = Name.name
		chain.closure.set_immediate(realName, Body)
		return Body

	@staticmethod
	def OpWhile(Test, Action, Chain, Interp):
		Test.parent = Chain
		Test.closure.parent = Chain.closure
		Action.parent = Chain
		Action.closure.parent = Chain.closure
		Test.rewind()
		Action.rewind()
		val = None
		while Interp.run(Test) == Atom.True:
			Test.rewind()
			Action.rewind()
			val = Interp.run(Action)
		return val

	@staticmethod
	def OpMap(List, Callback, Chain, Interp):
		return map(lambda I: Interp.invoke_functioncall(Chain, Callback, [I]))
	
	@staticmethod
	def OpDictToString(d):
		result = "{"
		first = True
		for key in d:
			if first:
				first = False
			else:
				result += ", "
			result += key + ": " + str(d[key])
		result += "}"
		return result

	@staticmethod
	def OpAdd(Args):
		Args = Args[0]
		result = Builtins.OpHead([Args])
		tail = Builtins.OpTail([Args])
		is_string = isinstance(result, basestring)
		for value in tail:
			if is_string or isinstance(value, basestring):
				result += str(value)
			else:
				result += value
		return result

	@staticmethod
	def OpSub(Args):
		Args = Args[0]
		result = Builtins.OpHead([Args])
		tail = Builtins.OpTail([Args])
		for value in tail:
			result -= value
		return result

	@staticmethod
	def OpMult(Args):
		Args = Args[0]
		result = Builtins.OpHead([Args])
		tail = Builtins.OpTail([Args])
		for value in tail:
			result *= value
		return result

	@staticmethod
	def OpDiv(Args):
		Args = Args[0]
		result = Builtins.OpHead([Args])
		tail = Builtins.OpTail([Args])
		for value in tail:
			result /= value
		return result

	@staticmethod
	def OpPrint(Args):
		Args = Args[0]
		result = ""
		first = True
		for arg in Args:
			if first:
				first = False
			else:
				result += " "
			result += str(arg)
		print result
		return None
	
	@staticmethod
	def OpHead(List):
		[List] = List
		it = iter(List)
		return it.next()
	
	@staticmethod
	def OpTail(List):
		[List] = List
		it = iter(List)
		it.next()
		return list(it)

	@staticmethod
	def OpScope(Args, Parent):
		[FnDef] = Args
		if not instanceof(FnDef, FunctionDefinition):
			raise InvalidArgumentError(FnDef)
		return FnDef.cloneWithScope(Parent)

	@staticmethod
	def OpFlatten(List):
		result = []
		nodes = List
		if len(List) == 0:
			return result

		node = nodes.pop()

		while 1:
			if isinstance(node, list):
				nodes.append(node)
			else:
				result.push(node)
			if len(nodes) > 0:
				node = nodes.pop()
			else:
				break

		result.reverse()
		return result

	@staticmethod
	def OpCall(Fn, Args, Chain, Interp):
		val = None
		if callable(Fn):
			val = Fn(Args, Chain, Interp)
		else:
			if isinstance(Fn, Atom):
				Fn = Fn.name
			if isinstance(Fn, basestring):
				fndef = Chain.closure.get_or_missing(Fn)
				if fnDef == Atom.Missing:
					fndef = Chain.closure.get_or_missing(Fn + "/*")
					if fndef == Atom.Missing:
						raise KeyNotFoundError(fndef)
					Fn = fndef
			val = Interp.invoke_functioncall(Chain, Fn, Params)
		return val

	@staticmethod
	def OpApply(Params, Chain, Interp):
		return Builtins.OpCall(Params[0], Params[1:], Chain, Interp)

	@staticmethod
	def OpTry(Call, Catch, Chain, Interp):
		assert isinstance(Chain, OpChain)
		Call.parent = Chain
		Call.fillClosure.parent = Chain.closure
		Call.rewind()
		try:
			return Interp.run(Call)
		except Exception as e:
			return Interp.invoke_functioncall(Chain, Catch, [e])

	@staticmethod
	def OpThrow(Message):
		raise LithpError(Message)

	ExportDestinations = []
	@staticmethod
	def OpExport(Names, Chain, Interp):
		if len(Builtins.ExportDestinations) == 0:
			Builtins.ExportDestinations = [[Interp, Chain]]
		# Get current destination
		destination = ExportDestinations[:-1]
		[dest_lithp, dest_chain] = destination
		top_chain = dest_chain.getTopParent()
		fndefs = Builtins.exportFunctions(Interp, Names, Chain, top_chain)
		top_chain.importClosure(fndefs)
		return None

	@staticmethod
	def exportFunctions(Interp, Names, Chain, Top):
		True

	@staticmethod
	def OpRecurse(Params, Chain):
		assert isinstance(Chain, OpChain)
		target = Chain.parent
		assert isinstance(target, OpChain)

		while target != None and not target.function_entry:
			target = target.parent
		if target == None:
			raise KeyNotFoundError()

		target.rewind()

		# Get the OpChain function name with arity
		fn = target.function_entry
		fnAndArity = fn + "/" + str(len(Params))
		fndef = target.closure.get_or_missing(fnAndArity)
		if fndef == Atom.Missing:
			fnAndArity = re.sub(r'\d+$/', "*", fnAndArity)
			fndef = target.closure.get_or_missing(fnAndArity)
			if fndef == Atom.Missing:
				raise RuntimeError("Unknown function: " + fnAndArity)

		assert isinstance(fndef, FunctionDefinitionBase)
		for index, name in enumerate(fndef.args):
			target.closure.set_immediate(name, Params[index])

		# Nothing is returned, it's up to the given function to eventually stop recursion
		# and return a value.

from interpreter import Interpreter
