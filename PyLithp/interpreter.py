import re
from lithptypes import *
from lithpconstants import LithpConstants

class Interpreter:

	MaxDebugLen = 100
	MaxDebugArrayLen = 20
	Debug = False
	DebugBuiltins = [
		"while", "call", "try", "eval", "apply", "next", "recurse"
	]

	@staticmethod
	def DebugMsg(msg):
		if Interpreter.Debug:
			print msg

	def __init__(self):
		self.last_chain = None
		self.functioncalls = 0
		self.depth = 0

	def run(self, chain):
		value = None
		while 1:
			op = chain.next()
			if op == None:
				break;
			if isinstance(op, OpChain):
				value = self.run(OpChain(chain, op.ops))
			elif isinstance(op, FunctionCall):
				value = self._do_functioncall(chain, op)
				if(value != None and isinstance(value, OpChain) and value.immediate == True):
					value = self.run(OpChain(chain, value.ops))
			elif isinstance(op, Literal):
				value = op.value
			elif isinstance(op, FunctionDefinitionNative):
				value = op
			else:
				raise Exception("Not implemented type: " + str(type(op)))
		return value
	
	def _do_functioncall(self, chain, fn):
		fn_name = fn.fn
		fndef = chain.closure.topmost.get_or_missing(fn_name)
		if fndef == Atom.Missing:
			fndef = chain.closure.topmost.get_or_missing(fn_name)
			if fndef == Atom.Missing:
				fn_name = re.sub(LithpConstants.ReplaceNumberAtEnd, "*", fn_name)
				fndef = chain.closure.topmost.get_or_missing(fn_name)
				if fndef == Atom.Missing:
					fn_name = fn.fn
					fndef = chain.closure.get_or_missing(fn_name)
					if fndef == Atom.Missing:
						fndef = chain.closure.get_or_missing(fn_name)
						if fndef == Atom.Missing:
							fn_name = re.sub(LithpConstants.ReplaceNumberAtEnd, "*", fn_name)
							fndef = chain.closure.get_or_missing(fn_name)
							if fndef == Atom.Missing:
								raise KeyNotFoundError(fn_name)
							fn.fn = fn_name
				else:
					fn.fn = fn_name
		params = list(map(lambda p: self.get_param_value(chain, p), fn.params))
		return self.invoke_functioncall(chain, fndef, params)

	def get_param_value(self, chain, p):
		if p == None:
			return None
		elif isinstance(p, FunctionCall):
			return self._do_functioncall(chain, p)
		elif isinstance(p, Literal):
			return p.value
		else:
			return p

	def lithpInspectParser(self, p, join = " ", maxDebug = None):
		if maxDebug == None:
			maxDebug = Interpreter.MaxDebugLen
		value = None
		if isinstance(p, basestring):
			value = '"' + p + '"'
		elif isinstance(p, list):
			value = "[" + ", ".join(map(lambda x: self.lithpInspectParser(x, join, maxDebug), p)) + "]"
		else:
			value = str(p)
		if len(value) > maxDebug:
			return "(too large)"
		return value

	def inspect_object(self, args, join = " ", maxDebugLen = None):
		if maxDebugLen == None:
			maxDebugLen = Interpreter.MaxDebugLen
		result = ""
		first = True
		for x in list(map(lambda v: self.lithpInspectParser(v, join, maxDebugLen), args)):
			if first == True:
				first = False
			else:
				result += " "
			result += x
		return result

	def Invoke(self, fn_name, params):
		fndef = chain.closure.get_or_missing(fn_name)
		if fndef == Atom.Missing:
			fn_name = re.sub(LithpConstants.ReplaceNumberAtEnd, "*", fn_name)
			fndef = chain.closure.get_or_missing(fn_name)
			if fndef == Atom.Missing:
				raise FunctionNotFoundError(fn_name)
		return self.invoke_functioncall(chain, fndef, params)

	def invoke_functioncall(self, chain, fndef, params):
		debug_str = ""
		self.functioncalls += 1
		if Interpreter.Debug == True:
			fn_name = fndef.readable_name
			if isinstance(fndef, FunctionDefinition):
				fn_name += "/" + str(fndef.arity)
			indent = "|"
			if self.depth < 20:
				indent = indent * (self.depth + 1)
			else:
				indent = "|             " + str(self.depth) + " | | "
			debug_str = "+ " + indent + " (" + fndef.readable_name + " " + self.inspect_object([params]) + ")"
		arity = fndef.arity
		self.depth += 1
		if isinstance(fndef, FunctionDefinitionNative):
			if Interpreter.Debug:
				if fndef.readable_name in Interpreter.DebugBuiltins:
					print debug_str
			if arity == "*":
				params = [params]
			val = fndef.body(params, chain, self)
		elif isinstance(fndef, FunctionDefinition):
			if Interpreter.Debug:
				print debug_str
			parent = chain
			if fndef.scoped == True:
				parent = fndef.scope
			call_chain = OpChain(parent, [fndef.body])
			if arity == "*":
				params = [params]
			# Set args in new function closure
			for index, name in enumerate(fndef.args):
				call_chain.closure.set_immediate(name, params[index])
				# Mark it as a function entry
			call_chain.function_entry = fndef.readable_name
			val = self.run(call_chain)
		else:
			raise LithpError()
		self.depth -= 1
		if Interpreter.Debug:
			debug_str += " :: " + str(self.inspect_object([val]))
			print debug_str
		return val