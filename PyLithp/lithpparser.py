import json
import re
import time

from lithptypes import *
from excepts import *

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
for k in EX_TABLE:
	EX_TABLE[EX_TABLE[k]] = k

class ParserState(object):
	def __init__(self, parent = None):
		self.ops = [[]]
		self.ops_it = iter(self.ops)
		self.current_word = "";
		self.expect = EX_OPCHAIN
		self.depth = 0
		self.in_variable = False
		self.in_atom = False
		self.quote_type = None
		self.line = 1
		self.character = 1
		self.lines = []

class LithpParser(object):
	"""Parse Lithp files"""

	pass

	EnableParserDebug = True
	@staticmethod
	def Debug(*args):
		if LithpParser.EnableParserDebug:
			print "PARSER: " + " ".join(map(str, args))

	TimeSpentParsing = 0

	def mapParam(self, P, chain, fnName):
		result = self.mapParamInner(P, chain, fnName)
		return result
	
	def mapParamInner(self, P, chain, fnName):
		if instanceof(P, list):
			return self.convert(chain, P)
		s = str(P)
		cls = self.classify(s)
		LithpParser.Debug("Classified: ", LithpParser.Classified(cls))
		if cls & EX_STRING_DOUBLE or cls & EX_STRING_SINGLE:
			# Get string without speech marks
			parsed = self.parseString(s[1:][:-1])
			if cls & EX_STRING_DOUBLE:
				return Literal(parsed)
			else:
				return Atom.Get(parsed)
		elif cls & EX_VARIABLE:
			if fnName in VAR_REF_FUNCTIONS:
				return VariableReference(s)
			return FunctionCall("get/1", [VariableReference(s)])
		elif cls & EX_NUMBER:
			return Literal(P)
		elif cls & EX_ATOM:
			return Atom.Get(s)
		else:
			raise InvalidArguemntError(P)

	def parseString(self, s):
		match = re.match(r'(.*?)(\\.)', s)
		if match != None:
			pre    = match.group(1)
			symbol = match.group(2)[1:]
			if symbol in SUPPORTED_ESCAPES.keys():
				s = pre + SUPPORTED_ESCAPES[symbol]
			else:
				raise InvalidEscapeCharacter(symbol)
		return s

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
		elif char == ",":
			result = EX_FUNCTION_BODY
		else:
			if re.match(r'^[a-z][a-zA-Z0-9_]*$', phrase) != None:
				result = EX_ATOM
			elif re.match(r'^[A-Z][A-Za-z0-9_]*$', phrase) != None:
				result = EX_VARIABLE
			elif re.match(r'^-?[0-9e][0-9e]*$', phrase) != None:
				result = EX_NUMBER | EX_ATOM | EX_NUMBER
			elif re.match(r'^-?[0-9e][0-9e.]*$', phrase) != None:
				result = EX_NUMBER | EX_ATOM | EX_NUMBER
			elif len(phrase) > 1 and re.test(r'^\".*\"$', phrase) != None:
				result = EX_STRING_DOUBLE
			elif len(phrase) > 1 and re.test(r"^'.*'$", phrase) != None:
				result = EX_STRING_SINGLE
			else:
				result = EX_ATOM
			result |= EX_STRING_CHARACTER
		return result
	
	def GET_EX(self, n):
		parts = []
		for k in EX_TABLE:
			if EX_TABLE[k] & n:
				parts.append(k)
		return " | ".join(parts)

	def convert(self, chain, curr):
		eleFirst = curr[0]
		clsFirst = self.classify(eleFirst)
		LithpParser.Debug("  First element: ", eleFirst)
		LithpParser.Debug("     Classified: ", self.GET_EX(clsFirst))
		if len(curr) == 0:
			return None

	@staticmethod
	def ParseAST(path):
		self = LithpParser()
		self.path = path
		with open(self.path) as fileData:
			asJson = json.load(fileData)
			self.ops = self.unexport(asJson)
	
	def unexport(self, ast):
		if isinstance(ast, dict):
			obj = {}
			code = self.unexport(ast["code"])
			obj["code"] = code
			obj["_fndef"] = ast["_fndef"]
			obj["_fnparams"] = ast["_fnparams"]
			return obj
		elif isinstance(ast, list):
			res = []
			for a in ast:
				res.append(self.unexport(a))
			return res
		else:
			return ast
	
	def finalize(self):
		chain = OpChain()
		for x in self.ops:
			c = self.convert(chain, x)
			chain.append(c)
		return chain
	

class ASTParser(LithpParser):
	pass