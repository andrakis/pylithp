from lithptypes import *

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

		Body.readable_name = realName
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