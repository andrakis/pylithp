import ast
import json
import re
import time

from lithptypes import *
from excepts import *
from JSIterator import JSListIterator

ArityBuiltins = {
	"print": "*",
	"and": "*",
	"or": "*",
	"+": "*",
	"++": "*",
	"-": "*",
	"/": "*",
	"\\": "*",
	"list": "*",
	"flatten": "*",
	"call": "*",
	"to-string": "*",
	"export": "*",
	"export-global": "*",
	"invoke": "*",
	"dict": "*"
}

SUPPORTED_ESCAPES = {
	"n": "\n",
	"r": "\r",
	"t": "\t",
	"\\": "\\\\"
}

VAR_REF_FUNCTIONS = [
	"get", "set", "var"
]

EX_LITERAL = 1 << 0              # Literal (1  2  "test")
EX_OPCHAIN = 1 << 1              # opening OpChain '('
EX_FUNCTIONCALL = 1 << 2         # opening FunctionCall '('
EX_NUMBER  = 1 << 3              # Collect number (whole or float: [0-9.]+f?$)
EX_ATOM    = 1 << 4              # Collect atom
EX_VARIABLE= 1 << 5              # Variables
EX_STRING_CHARACTER  = 1 << 6    # Collect character
EX_STRING_SINGLE = 1 << 7        # Expecting a single quote to end '
EX_STRING_DOUBLE = 1 << 8        # Expecting a double quote to end "
EX_PARAM_SEPARATOR   = 1 << 9    # Expecting a space
EX_CALL_END          = 1 << 10   # Expected a )  end of call
EX_OPCHAIN_END       = 1 << 11   # Expect a )  end of opchain
EX_COMMENT           = 1 << 12   # Comments
EX_COMPILED          = 1 << 13   # Already compiled
EX_FUNCTION_MARKER   = 1 << 14   # #     next: Arg1 Arg2 :: (...)
EX_FUNCTION_PARAM    = 1 << 15   # #     this: Arg1
EX_FUNCTION_PARAM_SEP= 1 << 16   # #Arg1 this:  
EX_FUNCTION_BODY     = 1 << 17;  # #Arg1 Arg2  this: ::

EX_TABLE = {
	"EX_LITERAL": EX_LITERAL,
	"EX_OPCHAIN": EX_OPCHAIN,
	"EX_FUNCTIONCALL": EX_FUNCTIONCALL,
	"EX_NUMBER": EX_NUMBER,
	"EX_ATOM": EX_ATOM,
	"EX_VARIABLE": EX_VARIABLE,
	"EX_STRING_CHARACTER": EX_STRING_CHARACTER,
	"EX_STRING_SINGLE": EX_STRING_SINGLE,
	"EX_STRING_DOUBLE": EX_STRING_DOUBLE,
	"EX_PARAM_SEPARATOR": EX_PARAM_SEPARATOR,
	"EX_CALL_END": EX_CALL_END,
	"EX_OPCHAIN_END": EX_OPCHAIN_END,
	"EX_COMMENT": EX_COMMENT,
	"EX_COMPILED": EX_COMPILED,
	"EX_FUNCTION_MARKER": EX_FUNCTION_MARKER,
	"EX_FUNCTION_PARAM": EX_FUNCTION_PARAM,
	"EX_FUNCTION_PARAM_SEP": EX_FUNCTION_PARAM_SEP,
	"EX_FUNCTION_BODY": EX_FUNCTION_BODY
}
# Map values to names in EX_TABLE
keys = []
for k in EX_TABLE:
	keys.append(k)

for k in keys:
	EX_TABLE[EX_TABLE[k]] = k

def parseString(s):
	match = re.match(r'(.*?)(\\.)', s)
	if match != None:
		pre    = match.group(1)
		symbol = match.group(2)[1:]
		if symbol in SUPPORTED_ESCAPES.keys():
			s = pre + SUPPORTED_ESCAPES[symbol]
		else:
			raise InvalidEscapeCharacter(symbol)
	return s

def GET_EX(n):
	parts = []
	for k in EX_TABLE:
		val = EX_TABLE[k]
		if isinstance(val, basestring):
			continue
		if val & n:
			parts.append(k)
	return " | ".join(parts)

characters = 0

class ParserState(object):
	def __init__(self, parent = None):
		self.ops = [[]]
		self.ops_it = JSListIterator(self.ops)
		self.current_word = "";
		self.expect = EX_OPCHAIN
		self.depth = 0
		self.in_variable = False
		self.in_atom = False
		self.quote_type = None
		self.line = 1
		self.character = 1
		self.lines = []

	def mapParam(self, P, chain, fnName):
		assert isinstance(chain, OpChain)
		result = self.mapParamInner(P, chain, fnName)
		return result
	
	def mapParamInner(self, P, chain, fnName):
		assert isinstance(chain, OpChain)
		if isinstance(P, list) or isinstance(P, dict):
			return self.convert(chain, P)
		s = str(P)
		cls = self.classify(s)
		LithpParser.Debug("Classified: ", GET_EX(cls))
		if cls & EX_STRING_DOUBLE or cls & EX_STRING_SINGLE:
			# Get string without speech marks
			parsed = parseString(s[1:][:-1])
			if cls & EX_STRING_DOUBLE:
				return Literal(parsed)
			else:
				return Atom.Get(parsed)
		elif cls & EX_VARIABLE:
			if fnName in VAR_REF_FUNCTIONS:
				return VariableReference(s)
			return FunctionCall("get/1", [VariableReference(s)])
		elif cls & EX_NUMBER:
			value = ast.literal_eval(P)
			return Literal(value)
		elif cls & EX_ATOM:
			return Atom.Get(s)
		else:
			raise InvalidArguemntError(P)

	def classify(self, phrase):
		if not isinstance(phrase, basestring):
			return EX_COMPILED
		result = 0
		char = phrase[0]
		if ord(char) == 9:
			return EX_PARAM_SEPARATOR
		if char in ["\t", " ", "\r", "\n"]:
			result = EX_PARAM_SEPARATOR
		elif char == "(":
			result = EX_OPCHAIN | EX_FUNCTIONCALL
		elif char == ")":
			result = EX_CALL_END | EX_OPCHAIN_END
		elif char == "'":
			result = EX_STRING_SINGLE
		elif char == '"':
			result = EX_STRING_DOUBLE
		elif char == "%":
			result = EX_COMMENT
		elif char == "#":
			result = EX_FUNCTION_MARKER
		elif char == ",":
			result = EX_FUNCTION_PARAM_SEP
		elif char == ":":
			result = EX_FUNCTION_BODY
		else:
			if re.match(r'^[a-z][a-zA-Z0-9_]*$', phrase) != None:
				result = EX_ATOM
			elif re.match(r'^[A-Z][A-Za-z0-9_]*$', phrase) != None:
				result = EX_VARIABLE | EX_FUNCTION_PARAM
			elif re.match(r'^-?[0-9e][0-9e]*$', phrase) != None:
				result = EX_NUMBER | EX_ATOM | EX_NUMBER
			elif re.match(r'^-?[0-9e][0-9e.]*$', phrase) != None:
				result = EX_NUMBER | EX_ATOM | EX_NUMBER
			elif len(phrase) > 1 and re.match(r'^\".*\"$', phrase) != None:
				result = EX_STRING_DOUBLE
			elif len(phrase) > 1 and re.match(r"^'.*'$", phrase) != None:
				result = EX_STRING_SINGLE
			else:
				result = EX_ATOM
		result |= EX_STRING_CHARACTER
		return result
	
	def convert(self, chain, curr):
		assert isinstance(chain, OpChain)
		assert isinstance(curr, list) or isinstance(curr, dict)
		target = curr
		if isinstance(target, dict):
			target = curr["code"]
		eleFirst = target[0]
		clsFirst = self.classify(eleFirst)
		LithpParser.Debug("  First element: ", eleFirst)
		LithpParser.Debug("     Classified: ", GET_EX(clsFirst))
		if len(target) == 0:
			return None
		if isinstance(curr, dict) and curr["_fndef"] == True:
			LithpParser.Debug("FNDEF")
			LithpParser.Debug("Params: ", curr["_fnparams"])
			params = curr["_fnparams"]
			curr["_fndef"] = False
			body = self.convert(chain, curr)
			anon = AnonymousFunction(chain, params, body)
			LithpParser.Debug("Got body for function: ", body)
			return anon
		#elif clsFirst & EX_STRING_SINGLE:
			# Convert to a (call (get 'FnName') Params)
		elif clsFirst & EX_ATOM:
			# FunctionCall
			LithpParser.Debug(" PARSE TO FUNCTIONCALL: ", target)
			params = target[1:]
			params = map(lambda P: self.mapParam(P, chain, eleFirst), params)
			if len(params) == 0 and self.classify(eleFirst) & EX_NUMBER:
				LithpParser.Debug("CONVERT TO LITERAL")
				return self.mapParam(eleFirst, chain, eleFirst)
			else:
				plen = len(params)
				if eleFirst in ArityBuiltins:
					plen = ArityBuiltins[eleFirst]
				LithpParser.Debug("FUNCTIONCALL " + eleFirst + "/" + str(plen))
				op = FunctionCall(eleFirst + "/" + str(plen), params)
				return op
		elif isinstance(eleFirst, list):
			# Must be an OpChain
			newChain = OpChain(chain)
			for i in target:
				LithpParser.Debug("Member " + str(i))
				newChain.add(self.convert(newChain, i))
			return newChain
		elif isinstance(target, list):
			# Must be an OpChain
			LithpParser.Debug(" PARSE TO OPCHAIN")
			newChain = OpChain(chain)
			for i in target:
				LithpParser.Debug("Member " + str(i) + " of chain: " + str(target[i]))
				newChain.add(self.mapParam(newChain, i))
			return newChain
		else:
			raise InvalidArguemntError()

	def parseBody(self, it, dest):
		assert isinstance(it, JSListIterator)
		params = []
		if len(self.current_word) > 0:
			params = self.current_word.split(",")
		self.current_word = ""
		d = {}
		d["_fndef"] = True
		d["_fnparams"] = params
		d["code"] = []
		chain = self.parseSection(it, d)
		LithpParser.Debug(" Body chain: ", chain)
		return chain

	def parseSection(self, it, dest):
		assert isinstance(it, JSListIterator)
		assert isinstance(dest, list) or isinstance(dest, dict)

		target = dest
		if isinstance(dest, dict):
			target = dest["code"]

		ch = ""
		def moveNext():
			expect = self.expect
			ch = it.next()
			if ch == None:
				return ch
			def ignore_line():
				chCode = ord(ch)
				while chCode != 10:
					ch = it.next()
					characters += 1
					if ch == None:
						return ch
					chCode = ord(ch)
					if chCode == 10:
						self.character = 1
						self.line += 1
				ch = it.next()
				self.line += 1

			if self.line == 1 and self.character == 1 and ch == "#":
				ch = it.next()
				if ch == "!":
					# Shebang, ignore line
					ch = it.next()
					ignore_line()
				else:
					it.prev()

			LithpParser.characters += 1
			self.character += 1
			if ch == None:
				return ch

			if ch == "%" and not (self.expect & EX_STRING_CHARACTER):
				# Command and not in speech, ignore this line
				# Must keep running in a loop, in case there are more
				# comments.
				while ch == "%":
					LithpParser.Debug("COMMENT")
					ignore_line()
			return ch

		depth = 1
		while 1:
			ch = moveNext()
			if ch == None:
				break
			LithpParser.Debug("Parse character: ", ch, " ", ord(ch))

			# Classify the current character
			cls = self.classify(ch)
			LithpParser.Debug("      Type     : " + GET_EX(cls)) 
			LithpParser.Debug("  expect_current: 0x" + hex(self.expect) + " (" + GET_EX(self.expect) + ")")
			LithpParser.Debug("     In var    : ", self.in_variable)
			if(self.quote_type != None):
				LithpParser.Debug("     Quote Type: " + self.quote_type)

			# Skip spaces we are not expecting. This really only affects extra
			# space characters within a line.
			expect = self.expect
			if cls & EX_PARAM_SEPARATOR and \
				not (expect & EX_PARAM_SEPARATOR) and \
				not (expect & EX_STRING_CHARACTER):
					LithpParser.Debug("Space when not expecting, ignoring")
					continue

			if cls & EX_FUNCTION_BODY and \
				not (expect & EX_FUNCTION_BODY) and \
				not (expect & EX_STRING_CHARACTER):
					LithpParser.Debug("Found the extra :, ignoring")
					continue

			# When a variable goes from CAPStosmall
			if cls & EX_ATOM and \
				(expect & EX_VARIABLE or expect & EX_FUNCTION_PARAM) and \
				self.in_variable:
					LithpParser.Debug("Found atom but was expecting variable, supposing it is part of the name")
					self.current_word += ch
					continue

			# When an atom goes from smallToCaps
			if cls & EX_VARIABLE and expect & EX_ATOM and self.in_atom:
				LithpParser.Debug("Found variable but was expecting atom, supposing it is part of the name")
				self.current_word += ch
				continue

			# OpChain begin but expecting separator?
			if cls & EX_OPCHAIN and expect & EX_PARAM_SEPARATOR:
				# Change character to separater, nxt loop we will get the EX_OPCHAIN again.
				ch = ' '
				cls = self.classify(ch)
				it.prev()

			# Has the character been classified as something we are expecting?
			if not (cls & expect):
				print "Error on line", self.line, "at character", self.character
				print "  ", self.lines[self.line - 1]
				print "  ", (" " * (self.character - 3)), "^"
				print "Unexpected character at", self.line, ":", self.character, "'", ch, "' not expected (", GET_EX(self.expect)
				raise InvalidArguemntError()

			if cls & EX_OPCHAIN and not (expect & EX_STRING_CHARACTER):
				# Open an OpChain
				self.expect = EX_OPCHAIN | EX_LITERAL | EX_STRING_DOUBLE | EX_STRING_SINGLE | EX_ATOM | EX_FUNCTION_MARKER | EX_VARIABLE
				self.current_word = ""
				target.append(self.parseSection(it, []))
			elif cls & EX_OPCHAIN_END and not (expect & EX_STRING_CHARACTER):
				# Close an OpChain
				if len(self.current_word) > 0:
					target.append(self.current_word)
				self.expect = EX_OPCHAIN | EX_OPCHAIN_END | EX_FUNCTION_MARKER | EX_NUMBER | EX_STRING_SINGLE | EX_STRING_DOUBLE | EX_VARIABLE | EX_ATOM
				self.current_word = ''
				self.in_variable = False
				return dest
			elif cls & EX_ATOM and expect & EX_ATOM:
				# Continue an atom
				self.current_word += ch
				self.in_atom = True
				self.expect = EX_ATOM | EX_PARAM_SEPARATOR | EX_FUNCTION_MARKER | EX_OPCHAIN_END | EX_FUNCTIONCALL
			elif cls & EX_PARAM_SEPARATOR and expect & EX_PARAM_SEPARATOR and \
				not (expect & EX_STRING_CHARACTER) and \
				not (expect & EX_FUNCTION_PARAM):
					# Space not in string, param separator
					LithpParser.Debug("SEPARATOR")
					if len(self.current_word) > 0:
						target.append(self.current_word)
					self.current_word = ""
					self.expect = EX_OPCHAIN | EX_VARIABLE | EX_NUMBER | EX_LITERAL | EX_ATOM | EX_STRING_DOUBLE | EX_STRING_SINGLE | EX_ATOM | EX_FUNCTION_MARKER | EX_OPCHAIN_END
					self.in_variable = False
					self.in_atom = False
			elif cls & EX_STRING_SINGLE and self.quote_type != '"':
				# Start or end a single quote string, if not already in a double quote string
				if not (expect & EX_STRING_CHARACTER):
					LithpParser.Debug("START SINGLE QUOTE STRING")
					self.expect = EX_STRING_CHARACTER | EX_STRING_SINGLE
					self.current_word = ch
					self.quote_type = "'"
				else:
					LithpParser.Debug("END SINGLE QUOTE STRING")
					self.current_word += ch
					if len(self.current_word) > 0:
						target.append(self.current_word)
					self.expect = EX_PARAM_SEPARATOR | EX_OPCHAIN
					self.current_word = ""
					self.current_word = ""
					self.quote_type = None
			elif cls & EX_STRING_DOUBLE and self.quote_type != "'":
				# Start or end a double quote string, if not already in a string quote string
				if not (expect & EX_STRING_CHARACTER):
					LithpParser.Debug("START DOUBLE QUOTE STRING")
					self.expect = EX_STRING_CHARACTER | EX_STRING_DOUBLE
					self.current_word = ch
					self.quote_type = '"'
				else:
					LithpParser.Debug("END DOUBLE QUOTE STRING")
					self.current_word += ch
					if len(self.current_word) > 0:
						target.append(self.current_word)
					self.expect = EX_PARAM_SEPARATOR | EX_OPCHAIN
					self.current_word = ""
					self.quote_type = None
			elif cls & EX_STRING_CHARACTER and expect & EX_STRING_CHARACTER:
				# Continue string character reading
				self.current_word += ch
			elif cls & EX_VARIABLE and expect & EX_VARIABLE:
				# Start or continue variable
				self.in_variable = True
				self.current_word += ch
				self.expect = EX_VARIABLE | EX_PARAM_SEPARATOR | EX_OPCHAIN_END
			elif cls & EX_NUMBER and expect & EX_NUMBER:
				# Start or continue number
				self.current_word += ch
				self.expect = EX_NUMBER | EX_PARAM_SEPARATOR | EX_OPCHAIN_END
			elif cls & EX_FUNCTION_MARKER and expect & EX_FUNCTION_MARKER:
				# Start or begin function
				LithpParser.Debug("BEGIN FUNCTION MARKER")
				# Current: #
				# Next: Arg1[,Arg2] :: Ops
				self.expect = EX_FUNCTION_PARAM | EX_FUNCTION_PARAM_SEP | EX_FUNCTION_BODY | EX_PARAM_SEPARATOR
			elif (cls & EX_FUNCTION_PARAM or cls & EX_FUNCTION_PARAM_SEP) and \
				expect & EX_FUNCTION_PARAM:
					# Continue reading function parameters
					self.current_word += ch
					self.in_variable = True
					LithpParser.Debug("CONTINUE FUNCTION PARAM: " + self.current_word)
			elif cls & EX_PARAM_SEPARATOR and expect & EX_FUNCTION_PARAM_SEP:
				# Function parameters end, body starts soon
				LithpParser.Debug("PARAMS END")
				self.expect = EX_FUNCTION_BODY
				self.in_variable = False
			elif cls & EX_FUNCTION_BODY and expect & EX_FUNCTION_BODY:
				LithpParser.Debug("FUNCTION BODY STARTS, current word: " + self.current_word)
				self.expect = EX_OPCHAIN
				self.in_variable = False
				target.append(self.parseBody(it, []))
				self.current_word = ""
				return dest
			else:
				raise InvalidArguemntError()

			LithpParser.Debug("State current: ")
			LithpParser.Debug("  Ops: ", self.ops)
			LithpParser.Debug("  Expect: " + GET_EX(self.expect))
			LithpParser.Debug("  Current word: " + self.current_word)
			LithpParser.Debug("  Depth: ", self.depth)

		return dest

	def export(self):
		it = JSListIterator(self.ops)
		return self.export_section(it)

	def export_section(self, it):
		assert isinstance(it, JSListIterator)
		out = []
		curr = it.next()
		while curr != None:
			# Cut: section checking if _fndef is present. We deal only
			#      with lists and dicts now.
			if isinstance(curr, list):
				out.append(self.export_section(JSListIterator(curr)))
			else:
				out.append(curr)
			curr = it.next()
		return out

	def unexport(self, ast):
		if isinstance(ast, dict):
			return ast
		elif isinstance(ast, list):
			return list(map(lambda E: self.unexport(E), ast))
		return ast

	
	def finalize(self):
		chain = OpChain()
		for x in self.ops:
			c = self.convert(chain, x)
			if c != None:
				chain.append(c)
		return chain

class LithpParser(object):
	"""Parse Lithp files"""

	EnableParserDebug = False
	@staticmethod
	def Debug(*args):
		if LithpParser.EnableParserDebug:
			print "PARSER: " + " ".join(map(str, args))

	TimeSpentParsing = 0

def BootstrapParser(code, opts = {}):
	if not "finalize" in opts:
		opts["finalize"] = True
	if not "ast" in opts:
		opts["ast"] = False

	LithpParser.characters = 0
	state = ParserState()
	start = time.time()
	if opts["ast"]:
		parsed = code
		if isinstance(code, basestring):
			parsed = json.loads(code)
		state.ops = [state.unexport(parsed)]
	else:
		split = list(code)
		it = JSListIterator(split)
		state.lines = re.split(r'\r?\n\r?', code)
		state.ops = state.parseSection(it, [])
	if opts["finalize"]:
		fin = state.finalize()
		LithpParser.TimeSpentParsing += time.time() - start
		return fin
	else:
		return state

if __name__ == "__main__":
	print "Tests"

	code = '((def add #A,B :: ((+ (get A) (get B)))) (print "Add 5+10: " (add 5 10)))'
	print BootstrapParser(code)
