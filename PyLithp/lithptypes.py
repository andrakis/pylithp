import re

from excepts import *
from lithpconstants import LithpConstants

class LithpCore(object):
	pass

class LithpOpChainMember(LithpCore):
	pass

class Closure(LithpCore):
	def __init__(self, parent = None):
		self.closure = {}
		self.owner = None
		if isinstance(parent, OpChain):
			self.owner = parent
			parent = parent.closure
		self.parent = parent
		self.topmost = self
		if self.parent:
			self.topmost = self.parent.getTopOwner()

	def getOwner(self):
		return self.owner

	def getTopOwner(self):
		if self.parent:
			return self.parent.getTopOwner()
		return self
	
	def __setitem__(self, key, item):
		self.do_set(key, item)
	
	def __getitem__(self, key):
		return self.get(key)
	
	def __repr__(self):
		return self.closure
	
	def __len__(self):
		return len(self.closure)
	
	def __iter__(self):
		return iter(self.closure)
	
	def __delitem__(self, key):
		self.delitem(key)
	
	def has_key(self, key):
		return key in self.closure
	
	def do_set(self, key, item):
		if(self.has_key(key)):
			self.set_immediate(key, item)
			return True
		elif self.parent != None:
			if(parent.do_set(key, item)):
				return true
		self.set_immediate(key, item)
		return True

	def set_immediate(self, key, item):
		self.closure[key] = item

	def set(self, key, item):
		if self.try_set(key, item):
			return
		if parent != None and parent.try_set(key, item):
			return
		self.set_immediate(key, item)

	def try_set(self, key, item):
		if self.has_key(key):
			self.set_immediate(key, item)
			return True
		if self.parent != None and self.parent.try_set(key, item):
			return True
		return False
	
	def get(self, key):
		if(self.has_key(key)):
			return self.closure[key]
		if self.parent != None:
			return self.parent.get(key)
		raise KeyNotFoundError(key)

	def get_or_missing(self, key):
		if(self.has_key(key)):
			return self.closure[key]
		if self.parent != None:
			return self.parent.get_or_missing(key)
		return Missing

	def __str__(self):
		return Builtins.OpDictToString(self.closure)

class OpChain(LithpOpChainMember):
	def __init__(self, parent = None, ops = None):
		if ops == None:
			ops = []
		self.closure = Closure(parent)
		self.ops = ops
		self.immediate = False
		self.pos = -1
		self.current = None
		self.parent = parent
		self.function_entry = None
	
	def add(self, op):
		self.ops.append(op)

	def append(self, op):
		self.ops.append(op)
	
	def __iter__(self):
		return iter(self.ops)

	def rewind(self):
		self.pos = -1

	def next(self):
		self.pos += 1
		if self.pos >= len(self.ops):
			return None
		self.current = self.ops[self.pos]
		return self.current

	def get(self):
		return self.current

	def _set_variables(self, variables):
		if variables == None:
			variables = {}
		for key in variables:
			self.closure.set_immediate(key, variables[key])

	def call(self, variables = None):
		non_imm = OpChain(self.parent, self.ops)
		non_imm.closure.parent = self.closure
		non_imm._set_variables(variables)
		return imm

	def call_immediate(self, variables = None):
		imm = OpChain(self.parent, self.ops)
		imm.closure.parent = self.closure
		imm.immediate = True
		imm._set_variables(variables)
		return imm

class FunctionCall(LithpOpChainMember):
	def __init__(self, fn, params):
		self.fn = fn
		self.params = params
	
	def __str__(self):
		return "(" + self.fn + " " + " ".join(list(map(self.printp, self.params))) + ")"
	
	def printp(self, p):
		return str(p)

class Literal(LithpOpChainMember):
	def __init__(self, value):
		self.value = value
	
	def __str__(self):
		v = self.value
		if type(v) is str:
			v = '"' + v + '"'
		return str(v)

_atoms_dict = {}
_atoms_counter = 0

_atoms_dict["none"] = _atoms_dict["nil"] = None

class Atom(LithpOpChainMember):
	def __init__(self, name):
		global _atoms_counter
		self.name = name
		self.id = _atoms_counter
		_atoms_counter += 1

	@staticmethod
	def Get(name):
		return getAtom(name)

	@staticmethod
	def List():
		return _atoms_dict.items

	def __str__(self):
		return "'" + self.name + "'"

	def __repr__(self):
		return self.__str__()

def getAtom(name):
	global _atoms_dict
	if name not in _atoms_dict:
		a = Atom(name)
		_atoms_dict[name] = a
		_atoms_dict[a.id] = a
	return _atoms_dict[name]

Atom.Nil = None
Atom.True = Atom.Get("true")
Atom.False = Atom.Get("false")
Atom.Missing = Atom.Get("missing")

Missing = Atom.Missing

class Tuple(LithpOpChainMember):
	def __init__(self, values):
		self.values = values

	def __iter__(self):
		return iter(self.values)

	def __setitem__(self, key, item):
		self.values[key] = item
	
	def __getitem__(self, key):
		return self.values[key]
	
	def __repr__(self):
		return self.values
	
	def __len__(self):
		return len(self.values)

	def __str__(self):
		value = "{"
		value += ", ".join(map(lambda v: str(v), self.values))
		return value + "}"

class VariableReference(LithpOpChainMember):
	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()

class FunctionDefinitionBase(LithpOpChainMember):
	def __init__(self, name, args):
		readable_name = name
		match = re.search(LithpConstants.FunctionDefinitionMatch, name)
		arity = len(args)
		if match != None:
			readable_name = match.group(1)
			arity = match.group(2)
			if arity != "*" and arity != None:
				arity = int(arity)
		else:
			readable_name = name
			name = name + "/" + str(len(args))
		self.name = name
		self.args = args
		self.readable_name = readable_name
		self.arity = arity
		self.scoped = False

class FunctionDefinition(FunctionDefinitionBase):
	def __init__(self, parent, name, args, body, scope = None):
		FunctionDefinitionBase.__init__(self, name, args)
		self.args = args
		self.name = name
		self.body = OpChain(parent, body.ops)
		self.scoped = scope != None
		self.scope = scope

	def __str__(self):
		return "FnDef(" + ", ".join(self.args) + ")"

	def __repr__(self):
		return self.__str__()

	def cloneWithScope(self, scope):
		return FunctionDefinition(self.args, self.body, scope)

class FunctionDefinitionNative(FunctionDefinitionBase):
	def __init__(self, name, args, body):
		FunctionDefinitionBase.__init__(self, name, args)
		self.body = body

	def ArityStr(self):
		return str(self.arity)

	def __str__(self):
		return "[FnDef " + self.readable_name + "/" + self.ArityStr() + "]"

class AnonymousFunction(FunctionDefinition):
	AnonymousFnCounter = 0

	def __init__(self, parent, params, body):
		AnonymousFunction.AnonymousFnCounter += 1
		fn_name = "__anonymous" + str(AnonymousFunction.AnonymousFnCounter) + "/" + str(len(params))
		FunctionDefinition.__init__(self, parent, fn_name, params, body)

from builtins import *
