from lithptypes import *

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

	def builtin (self,name, params, body):
		fndef = FunctionDefinitionNative(name, params, body)
		self.builtins[fndef.name] = fndef

	def fillClosure(self, closure):
		for key in self.builtins:
			closure[key] = self.builtins[key]

	def __str__(self):
		return str(self.builtins)

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