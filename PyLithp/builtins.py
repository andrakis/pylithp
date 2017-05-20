import math
import numbers
import random
import re

from lithptypes import *
from excepts import *
from lithpconstants import LithpConstants
from interpreter import Interpreter
from lithpparser import BootstrapParser

EmptyChain = OpChain()

AtomNumber = Atom.Get("number")
AtomString = Atom.Get("string")
AtomList   = Atom.Get("list")
AtomOpChain= Atom.Get("opchain")
AtomFunctionDefinition = Atom.Get("function")
AtomTuple  = Atom.Get("tuple")
AtomAtom   = Atom.Get("atom")
AtomDict   = Atom.Get("dict")
AtomObject = Atom.Get("object")

class Builtins(object):
	def __init__(self):
		self.builtins = Closure()
		self.builtin("head", ["List"], lambda List,Chain,Interp: Builtins.OpHead(List[0]))
		self.builtin("tail", ["List"], lambda List,Chain,Interp: Builtins.OpTail(List[0]))
		self.builtin("def", ["Name", "Body"], lambda Args,Chain,Interp: Builtins.OpDef(Args, Chain))
		self.builtin("get", ["Name"], lambda Args,Chain,Interp: Builtins.OpGet(Args, Chain))
		self.builtin("set", ["Name", "Value"], lambda Args,Chain,Interp: Builtins.OpSet(Args, Chain))
		self.builtin("var", ["Name", "Value"], lambda Args,Chain,Interp: Builtins.OpVar(Args, Chain))
		self.builtin("+/*", [], lambda Args,Chain,Interp: Builtins.OpAdd(Args))
		self.builtin("++/*", [], lambda Args,Chain,Interp: Builtins.OpAdd(Args))
		self.builtin("-/*", [], lambda Args,Chain,Interp: Builtins.OpSub(Args))
		self.builtin("*/*", [], lambda Args,Chain,Interp: Builtins.OpMult(Args))
		self.builtin("//*", [], lambda Args,Chain,Interp: Builtins.OpDiv(Args))
		self.builtin("print/*", [], lambda Args,Chain,Interp: Builtins.OpPrint(Args))
		self.builtin("scope", ["Target"], lambda Args,Chain,Interp: Builtins.OpScope(Args, Chain))
		self.builtin("==", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] == Args[1]))
		self.builtin("!=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] != Args[1]))
		self.builtin(">", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] > Args[1]))
		self.builtin(">=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] >= Args[1]))
		self.builtin("<", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] < Args[1]))
		self.builtin("<=", ["X", "Y"], lambda Args,Chain,Interp: Builtins.Truthy(Args[0] <= Args[1]))
		self.builtin("!", ["X"], lambda Args,Chain,Interp: Builtins.Truthy(not Args[0]))
		self.builtin("and/*", [], lambda Args,Chain,Interp: Builtins.OpAnd(Args[0]))
		self.builtin("or/*", [], lambda Args,Chain,Interp: Builtins.OpOr(Args[0]))
		self.builtin("?", ["Pred", "X", "Y"], lambda Args,Chain,Interp:
			Builtins.Truthy(Args[0] == Atom.True, Args[1], Args[2]))
		self.builtin("if/2", ["Test", "Action"], lambda Args,Chain,Interp:
			self.builtins["if/3"].body([Args[0], Args[1], EmptyChain], Chain, Interp))
		self.builtin("if/3", ["Test", "Action", "Else"], lambda Args,Chain,Interp:
			Builtins.TestIf(Args[0], Args[1], Args[2]))
		self.builtin("else", ["Chain"], lambda Args,Chain,Interp: Args[0].call_immediate())
		self.builtin("while", ["Test", "Action"], lambda Args,Chain,Interp:
			Builtins.OpWhile(Args[0], Args[1], Chain, Interp))
		self.builtin("list/*", [], lambda Args,Chain,Interp: Args[0])
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
		self.builtin("length", ["List"], lambda Args,Chain,Interp: len(Args[0]))
		self.builtin("parse-int", ["Str"], lambda Args,Chain,Interp: int(Args[0]))
		self.builtin("parse-float/1", ["Str"], lambda Args,Chain,Interp: float(Args[0]))
		self.builtin("call/*", [], lambda Args,Chain,Interp:
			   Builtins.OpCall(Args[0][0], Args[0][1:], Chain, Interp))
		self.builtin("apply/*", [], lambda Args,Chain,Interp:
			   Builtins.OpApply(Args[0], Chain, Interp))
		self.builtin("catch", ["OpChain"], lambda Args,Chain,Interp: Args[0])
		self.builtin("throw", ["Message"], lambda Args,Chain,Interp: Builtins.OpThrow(Args[0]))
		self.builtin("to-string", ["Arg"], lambda Args,Chain,Interp: str(Args[0]))
		self.builtin("export/*", [], lambda Args,Chain,Interp: Builtins.OpExport(Args[0], Chain, Interp))
		self.builtin("import", ["Path"], lambda Args,Chain,Interp: Builtins.OpImport(Args[0], Chain, Interp))
		self.builtin("recurse/*", [], lambda Args,Chain,Interp: Builtins.OpRecurse(Args[0], Chain))
		self.builtin("next/*", [], lambda Args,Chain,Interp: Builtins.OpNext(Args, AtomOpChain))
		self.builtin("tuple/*", [], lambda Args,Chain,Interp: Tuple(Args[0]))
		self.builtin("dict/*", [], lambda Args,Chain,Interp: Builtins.OpDict(Args[0]))
		self.builtin("dict-get", ["Dict", "Key"], lambda Args,Chain,Interp: Builtins.OpDictGet(Args[0], Args[1]))
		self.builtin("dict-set", ["Dict", "Key", "Value"], lambda Args,Chain,Interp: Builtins.OpDictSet(Args[0], Args[1], Args[2]))
		self.builtin("dict-present", ["Dict", "Key"], lambda Args,Chain,Interp: Builtins.OpDictPresent(Args[0], Args[1]))
		self.builtin("dict-remove", ["Dict", "Key"], lambda Args,Chain,Interp: Builtins.OpDictRemove(Args[0], Args[1]))
		self.builtin("dict-keys", ["Dict"], lambda Args,Chain,Interp: Builtins.OpDictKeys(Args[0]))
		self.builtin("typeof", ["Value"], lambda Args,Chain,Interp: Builtins.OpTypeof(Args[0]))
		self.builtin("function-arity", ["Fn"], lambda Args,Chain,Interp: Builtins.OpFunctionArity(Args[0]))
		self.builtin("define", ["Name", "Value"], lambda Args,Chain,Interp: Builtins.OpDefine(Args[0], Args[1], Chain))
		self.builtin("undefine", ["Name"], lambda Args,Chain,Interp: Builtins.OpUndefine(Args[0], Chain))
		self.builtin("defined", ["Name"], lambda Args,Chain,Interp: Builtins.OpDefined(Args[0], Chain))
		self.builtin("get-def", ["Name"], lambda Args,Chain,Interp: Builtins.OpGetDef(Args[0], Chain))
		self.builtin("definitions", [], lambda Args,Chain,Interp: Builtins.GetDefinitionDict(Chain))
		self.builtin("atom", ["Name"], lambda Args,Chain,Interp: Atom.Get(Args[0]))
		self.builtin("eval", ["Code"], lambda Args,Chain,Interp: Builtins.OpEval(Args[0], [], Chain, Interp))
		self.builtin("eval", ["Code", "ParamsDict"], lambda Args,Chain,Interp: Builtins.OpEval(Args[0], Args[1], Chain, Interp))
		self.builtin("tuple/*", [], lambda Args,Chain,Interp: Tuple(Args))
		self.builtin("py-bridge", ["FnDef"], lambda Args,Chain,Interp: Builtins.OpPyBridge(Args[0], Chain, Interp))
		self.builtin("true", [], lambda Args,Chain,Interp: Atom.True)
		self.builtin("false", [], lambda Args,Chain,Interp: Atom.False)
		self.builtin("nil", [], lambda Args,Chain,Interp: Atom.Nil)
		self.builtin("host", [], lambda Args,Chain,Interp: Atom.Get("python"))
		self.builtin("host-version", [], lambda Args,Chain,Interp: 1)
		self.builtin("index", ["List", "Index"], lambda Args,Chain,Interp: Args[0][Args[1]])
		self.builtin("index-set", ["List", "Index", "Value"], lambda Args,Chain,Interp:
			   Builtins.OpIndexSet(Args[0], Args[1], Args[2]))
		self.builtin("asc", ["Str"], lambda Args,Chain,Interp: ord(Args[0]))
		self.builtin("trim", ["Str"], lambda Args,Chain,Interp: Args[0].strip())
		self.builtin("floor", ["N"], lambda Args,Chain,Interp: math.floor(Args[0]))
		self.builtin("ceil", ["N"], lambda Args,Chain,Interp: math.ceil(Args[0]))
		self.builtin("rand", [], lambda Args,Chain,Interp: random.random())
		self.builtin("pi", [], lambda Args,Chain,Interp: math.pi)
		self.builtin("sqrt", ["N"], lambda Args,Chain,Interp: math.sqrt(Args[0]))
		self.builtin("regex", ["Regex"], lambda Args,Chain,Interp: re.compile(Args[0]))
		self.builtin("regex", ["Regex", "Flags"], lambda Args,Chain,Interp:
			   re.compile(Args[0], Builtins.GetRegexFlags(Args[1])))
		self.builtin("round", ["Number"], lambda Args,Chain,Interp: round(Args[0]))
		self.builtin("round", ["Number", "NDigits"], lambda Args,Chain,Interp: round(Args[0], Args[1]))
		self.builtin("slice", ["List"], lambda Args,Chain,Interp: Builtins.OpSlice(Args[0], None, None))
		self.builtin("slice", ["List", "Start"], lambda Args,Chain,Interp: Builtins.OpSlice(Args[0], Args[1], None))
		self.builtin("slice", ["List", "Start", "End"], lambda Args,Chain,Interp: Builtins.OpSlice(Args[0], Args[1], Args[2]))

	@staticmethod
	def GetRegexFlags(flags):
		result = 0
		for flag in flags:
			flag = flag.lower()
			if flag == "i":
				result |= re.IGNORECASE
			elif flag == "m":
				result |= re.MULTILINE
			elif flag == "l":
				result |= re.LOCALE
			elif flag == "s":
				result |= re.DOTALL
			elif flag == "u":
				result |= re.UNICODE
		return result

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
		if isinstance(Name, VariableReference) or isinstance(Name, Atom):
			Name = Name.name
		chain.closure.set_immediate(Name, Value)
		return Value

	@staticmethod
	def OpDef(Args, chain):
		[Name, Body] = Args
		if isinstance(Name, Atom) == False or isinstance(Body, FunctionDefinition) == False:
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
		result = Builtins.OpHead(Args)
		tail = Builtins.OpTail(Args)
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
		result = Builtins.OpHead(Args)
		tail = Builtins.OpTail(Args)
		for value in tail:
			result -= value
		return result

	@staticmethod
	def OpMult(Args):
		Args = Args[0]
		result = Builtins.OpHead(Args)
		tail = Builtins.OpTail(Args)
		for value in tail:
			result *= value
		return result

	@staticmethod
	def OpDiv(Args):
		Args = Args[0]
		result = Builtins.OpHead(Args)
		tail = Builtins.OpTail(Args)
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
		it = iter(List)
		return it.next()
	
	@staticmethod
	def OpTail(List):
		it = iter(List)
		it.next()
		return list(it)

	@staticmethod
	def OpScope(Args, Parent):
		[FnDef] = Args
		if not isinstance(FnDef, FunctionDefinition):
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
			val = Interp.invoke_functioncall(Chain, Fn, Args)
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
		destination = Builtins.ExportDestinations[-1]
		[dest_lithp, dest_chain] = destination
		top_chain = dest_chain.getTopParent()
		assert isinstance(top_chain, OpChain)
		fndefs = Builtins.exportFunctions(Interp, Names, Chain, top_chain)
		top_chain.importClosure(fndefs)
		return None

	@staticmethod
	def exportFunctions(Interp, Names, Chain, Top):
		assert isinstance(Interp, Interpreter)
		assert isinstance(Chain, OpChain)
		assert isinstance(Top, OpChain)

		dest = {}
		for name in Names:
			if isinstance(name, Atom):
				name = name.name
			result = Chain.closure.get_or_missing(name)
			if result == Atom.Missing:
				raise FunctionNotFoundError(name)
			fndef_named_function = result
			assert isinstance(fndef_named_function, FunctionDefinition)
			instance = Interp
			fndef_bridge = FunctionDefinitionNative(
				fndef_named_function.name,
				fndef_named_function.args,
				lambda Args,Chain,Interp: Interp.invoke_functioncall(Chain, fndef_named_function, Args)
			)
			dest[name] = fndef_bridge
		return dest

	@staticmethod
	def FindModule(Path, Chain, Interp):
		# TODO: Implement
		return Path + ".lithp"

	@staticmethod
	def OpImport(Path, Chain, Interp):
		if isinstance(Path, Atom):
			Path = Path.name
		Path = Builtins.FindModule(Path, Chain, Interp)
		importTable = [] # Defined(Chain, "_modules_imported")
		Interpreter.DebugMsg("Attempt to import: " + Path)
		if Path in importTable:
			Interpreter.DebugMsg("Skipping already imported module")
			return
		importTable.append(Path)
		h = open(Path)
		code = h.read()
		AST = False
		if Path.lower().endswith(".ast"):
			AST = True
		opts = {
			'finalize': True,
			'ast': AST
		}
		compiled = BootstrapParser(code, opts)
		compiled.parent = Chain
		compiled.closure.parent = Chain.closure
		compiled.closure.topmost = Chain.closure.topmost
		if Builtins.OpDefined("__AST__", Chain) == Atom.True:
			Builtins.OpDefine("__AST__", Atom.True, compiled)
		Builtins.ExportDestinations.append([Interp, Chain])
		Interp.run(compiled)
		Builtins.ExportDestinations.pop()
		
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
			fnAndArity = re.sub(LithpConstants.ReplaceNumberAtEnd, "*", fnAndArity)
			fndef = target.closure.get_or_missing(fnAndArity)
			if fndef == Atom.Missing:
				raise RuntimeError("Unknown function: " + fnAndArity)

		assert isinstance(fndef, FunctionDefinitionBase)
		for index, name in enumerate(fndef.args):
			target.closure.set_immediate(name, Params[index])

		# Nothing is returned, it's up to the given function to eventually stop recursion
		# and return a value.

	@staticmethod
	def OpNext(Args, Chain):
		assert isinstance(Chain, OpChain)

		fn = Builtins.OpHead(Args[0])
		params = Builtins.OpTail(Args[0])

		# Find target - last function entry
		target = Chain.parent
		while target != None and target.function_entry == None:
			target = target.parent
		if target == None:
			raise InvalidArguemntError()

		fnAndArity = fn + "/" + str(len(params))
		fndef = target.closure.get_or_missing(fnAndArity)
		if fndef == Atom.Missing:
			fnAndArity = re.sub(LithpConstants.ReplaceNumberAtEnd, "*", fnAndArity)
			fndef = target.closure.get_or_missing(fnAndArity)
			if fndef == Atom.Missing:
				raise InvalidArguemntError()

		assert isinstance(fndef, FunctionDefinition)
		target.replaceWith(fndef)
		for index, name in enumerate(fndef.args):
			target.closure.set_immediate(name, params[index])

		# Nothing is returned, it's up to the given function to eventually stop recursion
		# and return a value.

	@staticmethod
	def OpDict(values):
		result = {}
		for value in values:
			if not isinstance(value, Tuple):
				raise InvalidArguemntError()
			name = value[0]
			v    = value[1]
			result[name] = v
		return result

	@staticmethod
	def OpDictGet(d, key):
		return d[key]

	@staticmethod
	def OpDictSet(d, key, value):
		d[key] = value
		return d

	@staticmethod
	def OpDictPresent(d, key):
		if key in d.keys():
			return Atom.True
		else:
			return Atom.False

	@staticmethod
	def OpDictRemove(d, key):
		del d[key]
		return d

	@staticmethod
	def OpDictKeys(d, key):
		return d.keys()

	@staticmethod
	def OpTypeof(value):
		if isinstance(value, basestring):
			return AtomString
		elif isinstance(value, list):
			return AtomList
		elif isinstance(value, dict):
			return AtomDict
		elif isinstance(value, Tuple):
			return AtomTuple
		elif isinstance(value, Atom):
			return AtomATom
		elif isinstance(value, numbers.Number):
			return AtomNumber
		elif isinstance(value, FunctionDefinition):
			return AtomFunctionDefinition
		elif isinstance(value, Literal):
			return Builtins.OpTypeof(value.value)
		else:
			return AtomObject

	@staticmethod
	def OpFunctionArity(fndef):
		assert isinstance(fndef, FunctionDefinition)
		return fndef.arity

	DefinitionDictName = "__definition_dict"

	@staticmethod
	def GetDefinitionDict(chain):
		assert isinstance(chain, OpChain)
		topmost = chain.closure.topmost
		dict = topmost.get_or_missing(Builtins.DefinitionDictName)
		if dict == Atom.Missing:
			dict = {}
			dict[Builtins.DefinitionDictName] = True
			topmost.set_immediate(Builtins.DefinitionDictName, dict)
		return dict

	@staticmethod
	def OpDefine(name, value, chain):
		dict = Builtins.GetDefinitionDict(chain)
		dict[name] = value
		return value

	@staticmethod
	def OpUndefine(name, chain):
		dict = Builtins.GetDefinitionDict(chain)
		old = dict[name]
		del dict[name]
		return old

	@staticmethod
	def OpDefined(name, chain):
		dict = Builtins.GetDefinitionDict(chain)
		if name in dict:
			return Atom.True
		return Atom.False

	@staticmethod
	def OpGetDef(name, chain):
		dict = Builtins.GetDefinitionDict(chain)
		if not (name in dict):
			return Atom.False
		return dict[name]

	@staticmethod
	def OpDefinitions(chain):
		return Builtins.GetDefinitionDict(chain)

	@staticmethod
	def OpEval(code, params, chain, Interp):
		builtins = Builtins()
		compiled = BootstrapParser(code)
		compiled.parent = chain
		compiled.closure.parent = chain.closure
		compiled.closure.topmost = chain.closure.topmost
		for key in params:
			compiled.closure.set_immediate(key, params[key])
		return Interp.run(compiled)

	@staticmethod
	def OpIndexSet(list, name, value):
		list[name] = value
		return list

	@staticmethod
	def OpPyBridge(callback, chain, interp):
		assert isinstance(fndef, FunctionDefinition)
		assert isinstance(chain, OpChain)
		return lambda *result: Builtins.OpPyBridgeCallback(callback, result, chain, interp)

	@staticmethod
	def OpPyBridgeCallback(callback, result, chain, interp):
		assert isinstance(interp, Interpreter)
		return interp.invoke_functioncall(chain, callback, result)

	@staticmethod
	def OpAnd(Values):
		for v in Values:
			if v != Atom.True:
				return Atom.False
		return Atom.True

	@staticmethod
	def OpOr(Values):
		val = False
		for v in Values:
			val = (v == Atom.True) or val
		if val:
			return Atom.True
		else:
			return Atom.False

	@staticmethod
	def OpSlice(List, Start = None, End = None):
		return List[Start:End]
